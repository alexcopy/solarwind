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
from malina.LIB.PrintLogs import SolarLogging

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
        self.send_data = SendApiData.SendApiData(logging, API_URL)
        self.shunt_load = SDL_Pi_INA3221.SDL_Pi_INA3221(addr=0x40)
        self.shunt_bat = 0.00159
        self.conf_logger()
        self.print_logs = SolarLogging(logging)
        self.filo_fifo = FiloFifo.FiloFifo(logging, self.shunt_load)
        self.automation = PondPumpAuto.PondPumpAuto(logging)

        # self.switch_to_solar_power()

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
        return GPIO.input(POND_RELAY) ^ GPIO.input(INVER_CHECK)

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
            inv_status = GPIO.input(INVER_CHECK)
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

            if cur_t % diviser==0:
                self.print_logs.printing_vars(self.filo_fifo.fifo_buff, inv_status, self.filo_fifo.get_avg_rel_stats,
                                              self.automation.get_current_status, solar_current)
                self.print_logs.log_run(self.filo_fifo.filo_buff, inv_status, self.automation.get_current_status,
                                        solar_current)
        except Exception as ex:
            logging.warning(ex)

    def inverter_switch(self, on_off: str):
        on_off = on_off.upper()
        if not on_off in ['ON', 'OFF']:
            logging.error("The  WRONG Signal to INVERTER SWITCH SENT!!!!!  the signal is: %s " % on_off)
            return GPIO.input(INVER_CHECK)

        status = GPIO.input(INVER_CHECK)
        if on_off == 'ON' and status == 1:
            return 1
        if on_off == 'OFF' and status == 0:
            return 0
        self.inverter_on_off()
        return GPIO.input(INVER_CHECK)

    def adjust_pump_speed(self):
        inverter_voltage = self.get_inverter_values()
        if len(inverter_voltage) < 15:
            logging.info(
                " ----It's too early to adjust %d pump_speed please wait until length over 15" % len(inverter_voltage))
            return 0

        # in case if we're working from mains switching to minimum allowed speed

        volt_avg = self.avg(inverter_voltage)
        min_speed = MIN_POND_SPEED

        mains_relay_status = self.filo_fifo.get_main_rel_status
        self.automation.pond_pump_adj(min_speed, volt_avg, mains_relay_status)

    def inverter_on_off(self):
        time.sleep(.5)
        GPIO.output(INVER_RELAY, True)
        time.sleep(.5)
        GPIO.output(INVER_RELAY, False)

    def load_checks(self):
        self.adjust_pump_speed()
        self.inverter_run()

    def inverter_run(self):
        try:
            if time.strftime("%H:%M") == '12:00':
                self.switch_to_solar_power()
            inverter_voltage = self.get_inverter_values()
            # converter switch OFF
            if self.avg(inverter_voltage) < CUT_OFF_VOLT and len(
                    inverter_voltage) > 15:
                self.switch_to_main_power()
                self.send_data.send_avg_data(self.filo_fifo, GPIO.input(INVER_CHECK))

            # converter switch ON
            if self.avg(inverter_voltage) > SWITCH_ON_VOLT and len(
                    inverter_voltage) > 30:
                self.switch_to_solar_power()
                self.send_data.send_avg_data(self.filo_fifo, GPIO.input(INVER_CHECK))
            self.integrity_check()

        except Exception as ex:
            logging.warning(ex)

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

    # todo check for error in pump_status
    def send_pump_stats(self):
        relay_status = int(GPIO.input(POND_RELAY))
        self.automation.refresh_pump_status()
        self.automation.send_pond_stats(relay_status)

    def send_avg_data(self):
        self.send_data.send_avg_data(self.filo_fifo, GPIO.input(INVER_CHECK))

    def run_read_vals(self):
        reed = BackgroundScheduler()
        hour = int(time.strftime("%H"))
        send_time_slot = 600
        load_time_slot = 10

        # Don't need to send stats overnight
        if hour > 21 or hour < 5:
            send_time_slot = 1800
            load_time_slot = 60

        reed.add_job(self.send_avg_data, 'interval', seconds=send_time_slot)
        reed.add_job(self.send_pump_stats, 'interval', seconds=300)
        reed.add_job(self.load_checks, 'interval', seconds=load_time_slot)
        reed.start()
        # reed.shutdown()

        # logical XOR in case of to equal states. Inverter is ON when GPIO.input(INVER_CHECK) == 1
        # so in this case GPIO.input(mains_relay_status) should be in 0 meaning we're working from battery and vice versa
        # in case  we're working from mains Inverter should be in state GPIO.input(INVER_CHECK) == 0 and mains_relay_status
        # state should be 1 which mean relay isn't switched.

    def integrity_check(self):
        avg_status = self.filo_fifo.get_avg_rel_status
        if avg_status < 0.5 and self.filo_fifo.len_sts_chk > 8:
            self.print_logs.integrity_error(avg_status, GPIO.input(POND_RELAY), GPIO.input(INVER_CHECK))
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
