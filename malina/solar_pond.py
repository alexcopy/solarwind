#!/usr/bin/env python
import asyncio
import importlib.util
import logging
import logging.handlers
import os
import time
from pathlib import Path

import python_weather
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import dotenv_values

from malina.INA3221 import SDL_Pi_INA3221
from malina.LIB import FiloFifo
from malina.LIB import PondPumpAuto
from malina.LIB import SendApiData
from malina.LIB.LoadDevices import LoadDevices
from malina.LIB.LoadRelayAutomation import LoadRelayAutomation
from malina.LIB.PrintLogs import SolarLogging
from malina.LIB.TuyaAuthorisation import TuyaAuthorisation

try:
    importlib.util.find_spec('RPi.GPIO')
    import RPi.GPIO as GPIO
except ImportError:

    import FakeRPi.GPIO as GPIO
    import FakeRPi.Utilities

    FakeRPi.Utilities.mode = FakeRPi.Utilities.PIN_TYPE_BOARD

TIME_TIK = 1
POND_RELAY = 11
INVER_RELAY = 12
INVER_CHECK = 10
CUT_OFF_VOLT = 21
SWITCH_ON_VOLT = 26
MIN_POND_SPEED = 10

config = dotenv_values(".env")
LOG_DIR = config['LOG_DIR']
API_URL = config["API_URL"]
POND_SPEED_STEP = int(config["POND_SPEED_STEP"])
WEATHER_TOWN = config["WEATHER_TOWN"]

INVERT_CHANNEL = 1
LEISURE_BAT_CHANNEL = 2
TIGER_BAT_CHANNEL = 3
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

GPIO.setmode(GPIO.BOARD)
GPIO.setup(POND_RELAY, GPIO.OUT)
GPIO.setup(INVER_RELAY, GPIO.OUT)
GPIO.setup(INVER_CHECK, GPIO.IN)


def handler(signum, frame):
    print('Ctrl+Z pressed, but ignored')
    GPIO.cleanup()
    os.system('kill -STOP %d' % os.getpid())


class SolarPond():
    def __init__(self):
        self.FILTER_FLUSH = []
        tuya_auth = TuyaAuthorisation(logging)
        self.send_data = SendApiData.SendApiData(logging, API_URL)
        self.shunt_load = SDL_Pi_INA3221.SDL_Pi_INA3221(addr=0x40)
        self.conf_logger()
        self.print_logs = SolarLogging(logging)
        self.filo_fifo = FiloFifo.FiloFifo(logging, self.shunt_load)
        self.automation = PondPumpAuto.PondPumpAuto(logging, tuya_auth.device_manager, self.send_data)
        self.devices = LoadDevices(logging, tuya_auth.device_manager)
        self.invert_status = 1
        self.switch_to_solar_power()

    @staticmethod
    def avg(l):
        if len(l) == 0:
            return 0
        return float(round(sum(l, 0.0) / len(l), 2))

    def switch_to_solar_power(self):
        self.inverter_switch('ON')
        time.sleep(4)
        inverter_state = self.inverter_switch('ON')

        if inverter_state == 1:
            self.pond_relay_on_off('INV')
        else:
            self.switch_to_main_power()
            logging.error("CANNOT SWITCH ON THE INVERTER PLS CHECK  !!!!!  the signal is: %d " % inverter_state)
        return self.status_check

    def switch_to_main_power(self):
        self.inverter_switch('OFF')
        time.sleep(2)
        inverter_state = self.inverter_switch('OFF')
        if inverter_state == 0:
            logging.info("All good Inverter has been switched off successfully: %d " % inverter_state)
        else:
            logging.error("CANNOT SWITCH OFF THE INVERTER PLS CHECK  !!!!!  the signal is: %d " % inverter_state)

        logging.info("All good Switching to main power: %d " % inverter_state)
        self.pond_relay_on_off('MAIN')
        return self.status_check

    @property
    def status_check(self):
        return GPIO.input(POND_RELAY) ^ self.inver_status_check()

    def inver_status_check(self):
        return self.invert_status
        # return GPIO.input(INVER_CHECK) todo in case of ENCOA inverter with switch off

    def pond_relay_on_off(self, on_off: str):
        on_off = on_off.upper()
        if on_off not in ['INV', 'MAIN']:
            logging.error("The  WRONG Signal to mains_relay_status SENT!!!!!  the signal is: %s " % on_off)
            return GPIO.output(POND_RELAY, True)
        if on_off == 'INV':
            return GPIO.output(POND_RELAY, False)
        elif on_off == 'MAIN':
            return GPIO.output(POND_RELAY, True)
        else:
            logging.error("SOMETHING IS WRONG !!!!!  the signal is: %s " % on_off)
        return GPIO.output(POND_RELAY, True)

    def conf_logger(self):
        current_path = Path(LOG_DIR)
        log_name = time.strftime("info")
        filename = current_path.joinpath(f'{log_name}.log')
        log_handler = logging.handlers.RotatingFileHandler(filename, maxBytes=5000000, backupCount=5)
        formatter = logging.Formatter(
            '%(asctime)s program_name [%(process)d]: %(message)s',
            '%b %d %H:%M:%S')
        formatter.converter = time.gmtime  # if you want UTC time
        log_handler.setFormatter(formatter)
        logger = logging.getLogger()
        logger.addHandler(log_handler)
        logger.setLevel(logging.DEBUG)

        # to log errors messages
        error_log = logging.FileHandler(os.path.join(current_path, 'error.log'))
        error_log.setFormatter(formatter)
        error_log.setLevel(logging.ERROR)
        logger.addHandler(error_log)

    def processing_reads(self):
        try:
            inv_status = self.inver_status_check()
            self.filo_fifo.buffers_run(inv_status)
            self.filter_flush_run()
            self.filo_fifo.update_rel_status({
                'status_check': self.status_check,
                'inverter_relay': inv_status,
                'main_relay_status': GPIO.input(POND_RELAY),
            })
            solar_current = self.filo_fifo.solar_current
            cur_t = int(time.time())
            hour = int(time.strftime("%H"))
            diviser = 4
            if hour > 21 or hour < 5:
                diviser = 30

            if cur_t % diviser == 0:
                self.print_logs.printing_vars(self.filo_fifo.fifo_buff, inv_status, self.filo_fifo.get_avg_rel_stats,
                                              self.automation.get_current_status, solar_current, self.devices)
                self.print_logs.log_run(self.filo_fifo.filo_buff, inv_status, self.automation.get_current_status,
                                        solar_current)
        except IOError as io_err:
            logging.info(io_err)

        except Exception as ex:
            logging.error(ex)

    def inverter_switch(self, on_off: str):
        on_off = on_off.upper()
        if not on_off in ['ON', 'OFF']:
            logging.error("The  WRONG Signal to INVERTER SWITCH SENT!!!!!  the signal is: %s " % on_off)
            return self.inver_status_check()

        status = self.inver_status_check()
        if on_off == 'ON' and status == 1:
            return 1
        if on_off == 'OFF' and status == 0:
            return 0
        self.inverter_on_off()
        return self.inver_status_check()

    def adjust_pump_speed(self):
        inverter_voltage = self.get_inverter_values()
        if len(inverter_voltage) < 15:
            logging.error(
                " ----It's too early to adjust %d pump_speed please wait until length over 15" % len(inverter_voltage))
            return 0
        # in case if we're working from mains switching to minimum allowed speed
        volt_avg = self.avg(inverter_voltage)
        min_speed = MIN_POND_SPEED
        mains_relay_status = self.filo_fifo.get_main_rel_status
        if int(self.automation.get_current_status['mode']) == 6:
            self.automation.pond_pump_adj(min_speed, volt_avg, mains_relay_status)
        else:
            logging.info("Pump working mode is not 6 so no adjustments could be done ")

    def adjust_speed_non_stepped_val(self):
        if not self.automation.pump_status['flow_speed'] % POND_SPEED_STEP == 0:
            rounded = round(int(self.automation.pump_status['flow_speed']) / 10) * 10
            if rounded < POND_SPEED_STEP:
                rounded = POND_SPEED_STEP
            logging.error(
                "The device status is not divisible by POND_SPEED_STEP %d" % self.automation.pump_status['flow_speed'])
            logging.error("Round UP to nearest  POND_SPEED_STEP value %d" % rounded)
            relay_status = int(GPIO.input(POND_RELAY))
            self.automation.change_pump_speed(rounded, relay_status)

    def inverter_on_off(self):
        self.invert_status = int(not self.invert_status)
        # todo in case ENCOA inverter
        # time.sleep(.5)
        # GPIO.output(INVER_RELAY, True)
        # time.sleep(.5)
        # GPIO.output(INVER_RELAY, False)

    def load_checks(self):
        self.adjust_pump_speed()
        self.inverter_run()
        self.adjust_speed_non_stepped_val()
        self.check_load_devices()

    def inverter_run(self):
        try:
            if time.strftime("%H:%M") == '12:00':
                self.switch_to_solar_power()
            inverter_voltage = self.get_inverter_values()
            # converter switch OFF
            if self.avg(inverter_voltage) < CUT_OFF_VOLT and len(
                    inverter_voltage) > 15:
                self.switch_to_main_power()
                self.send_data.send_avg_data(self.filo_fifo, self.inver_status_check())

            # converter switch ON
            if self.avg(inverter_voltage) > SWITCH_ON_VOLT and len(
                    inverter_voltage) > 30:
                if self.is_average_relays_on():
                    # all good relay is ON
                    return True
                self.switch_to_solar_power()
                self.send_data.send_avg_data(self.filo_fifo, self.inver_status_check())
            self.integrity_check()

        except Exception as ex:
            logging.error(ex)

    def is_average_relays_on(self):
        invert_status = self.filo_fifo.get_avg_rel_stats
        return invert_status['inverter_relay'] > 0.3 and invert_status['status_check'] > 0.3

    def get_inverter_values(self, slot='1s', value='voltage'):
        inverter_voltage = self.filo_fifo.get_filo_value('%s_inverter' % slot, value)
        if len(inverter_voltage) == 0:
            return []
        return inverter_voltage.pop()

    def filter_flush_run(self):
        now_cc = self.filo_fifo.fifo_buff['1s_inverter_bat_current']
        avg_cc = self.avg(self.get_inverter_values('10m', 'current'))
        cc_size = len(self.get_inverter_values('1s', 'current'))
        timestamp = int(time.time())
        if abs(now_cc - avg_cc) > 5000 and cc_size > 10:
            self.FILTER_FLUSH.append(now_cc)
        else:
            if len(self.FILTER_FLUSH) > 5:
                self.send_data.send_ff_data('inverter_current', self.FILTER_FLUSH)
            self.FILTER_FLUSH = []
        return timestamp

    def reset_ff(self):
        if len(self.FILTER_FLUSH) < 5:
            self.FILTER_FLUSH = []

    def check_load_devices(self):
        avg_invert_volt = self.avg(self.get_inverter_values())
        flow_speed = self.automation.get_current_status['flow_speed']
        self.devices.check_uv_devices(avg_invert_volt, flow_speed)
        self.devices.check_fnt_device(avg_invert_volt, flow_speed)

    def update_devs_stats(self):
        self.automation.refresh_pump_status()
        time.sleep(3)
        self.devices.update_uv_stats_info()
        time.sleep(3)
        self.devices.update_fnt_dev_stats()

    def pump_stats_to_server(self):
        relay_status = int(GPIO.input(POND_RELAY))
        resp = self.send_data.send_pump_stats(relay_status, self.automation.get_current_status)
        err_resp = resp['errors']
        if err_resp:
            time.sleep(5)
            self.automation.refresh_pump_status()
            self.send_data.send_pump_stats(relay_status, self.automation.get_current_status)

    def send_avg_data(self):
        self.send_data.send_avg_data(self.filo_fifo, self.inver_status_check())

    def run_read_vals(self):
        reed = BackgroundScheduler()
        hour = int(time.strftime("%H"))
        send_time_slot = 1200
        load_time_slot = 10
        pump_stats = 300

        # Don't need to send stats overnight
        if hour > 21 or hour < 5:
            send_time_slot = 2400
            pump_stats = 1800
            load_time_slot = 120

        reed.add_job(self.send_avg_data, 'interval', seconds=send_time_slot)
        reed.add_job(self.update_devs_stats, 'interval', seconds=pump_stats)
        reed.add_job(self.send_stats_api, 'interval', seconds=pump_stats + 60)
        reed.add_job(self.load_checks, 'interval', seconds=load_time_slot)
        reed.start()
        # reed.shutdown()

    def send_stats_api(self):
        relay_status = int(GPIO.input(POND_RELAY))
        self.pump_stats_to_server()
        time.sleep(3)
        uv_data = self.devices.get_uv_sw_state
        fnt_sw = self.devices.get_fnt_sw_state
        uv_data.update({'name': "UV_Clarifier ", 'from_main': relay_status})
        fnt_sw.update({'name': "Pond Fountain ", 'from_main': relay_status})
        self.send_data.send_load_stats(uv_data)
        self.send_data.send_load_stats(fnt_sw)


    def integrity_check(self):
        avg_status = self.filo_fifo.get_avg_rel_status
        if avg_status < 0.3 and self.filo_fifo.len_sts_chk > 8:
            self.print_logs.integrity_error(avg_status, GPIO.input(POND_RELAY), self.inver_status_check())
            self.switch_to_main_power()

    async def _getweather(self):
        # declare the client. format defaults to the metric system (celcius, km/h, etc.)
        async with python_weather.Client(format=python_weather.METRIC) as client:
            # fetch a weather forecast from a city
            weather = await client.get(WEATHER_TOWN)

            return weather

    def weather_data(self):
        weather = asyncio.run(self._getweather())
        return {'temperature': weather.current.temperature, 'wind_speed': weather.current.wind_speed,
                'visibility': weather.current.visibility, 'uv_index': weather.current.uv_index,
                'humidity': weather.current.humidity, 'precipitation': weather.current.precipitation, }

# todo: improve pump speed adjustments (sometime it's very slow to speedup or slow down,
#  add another level of logging (debug or warnings)
#  add weather to table and advance in table pond self temp from future gauge
#  finish switch automation
