#!/usr/bin/env python
from malina.INA3221 import SDL_Pi_INA3221
import importlib.util
import time
from pathlib import Path
import logging
import os
import requests
import logging.handlers
import json
from dotenv import dotenv_values
from apscheduler.schedulers.background import BackgroundScheduler

from malina.LIB import FiloFifo
from malina.LIB import PondPumpAuto
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
MAX_BAT_VOLT = float(config['MAX_BAT_VOLT'])
MIN_BAT_VOLT = float(config['MIN_BAT_VOLT'])
POND_SPEED_STEP = int(config["POND_SPEED_STEP"])

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
        self.shunt_load = SDL_Pi_INA3221.SDL_Pi_INA3221(addr=0x40)
        self.shunt_bat = 0.00159
        self.conf_logger()
        self.print_logs = SolarLogging(logging)
        self.filo_fifo = FiloFifo.FiloFifo(logging, self.shunt_load)
        self.automation = PondPumpAuto.PondPumpAuto(logging)
        self.pump_status = self.automation.get_pump_status()

        # self.switch_to_solar_power()

    def avg(self, l):
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
            logging.error("The  WRONG Signal to POND_RELAY SENT!!!!!  the signal is: %s " % on_off)
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

            self.print_logs.printing_vars(self.filo_fifo.fifo_buff, inv_status, self.filo_fifo.get_avg_rel_stats,
                                          self.pump_status)
            self.print_logs.log_run(self.filo_fifo.filo_buff, inv_status, self.pump_status)
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
        if len(inverter_voltage) > 15:
            logging.info(
                " ----It's too early to adjust %d pump_speed please wait until length over 15" % len(inverter_voltage))
            return 0
        volt_avg = self.avg(inverter_voltage)

        # in case if we're working from mains switching to minimum allowed speed
        if self.filo_fifo.get_main_rel_status > 0.7:
            return self.decrease_pump_speed(100)

        if volt_avg > MAX_BAT_VOLT:
            return self.increase_pump_speed(POND_SPEED_STEP)
        if volt_avg < MIN_BAT_VOLT:
            return self.decrease_pump_speed(POND_SPEED_STEP)

    def inverter_on_off(self):
        time.sleep(.5)
        GPIO.output(INVER_RELAY, True)
        time.sleep(.5)
        GPIO.output(INVER_RELAY, False)

    def send_ff_data(self, shunt_name: str):
        payload = json.dumps({
            "max_current": max(self.FILTER_FLUSH),
            "duration": len(self.FILTER_FLUSH) * TIME_TIK,
            "name": shunt_name
        })
        url_path = "%sfflash" % API_URL
        self.send_to_remote(url_path, payload)

    def send_to_remote(self, url_path, payload):
        self.print_logs.loger_remote(url_path)
        headers = {
            'Content-Type': 'application/json'
        }
        try:
            response = requests.request("POST", url_path, headers=headers, data=payload)
            return response.text
        except Exception as ex:
            logging.info(ex)
            return "error"

    def send_avg_data(self):
        filo_buff = self.filo_fifo.filo_buff
        for v in filo_buff:
            if not '1h' in v:
                continue
            val_type = "V"
            if 'current' in v:
                val_type = "A"

            payload = json.dumps({
                "value_type": val_type,
                "name": v,
                "inverter_status": GPIO.input(INVER_CHECK),
                "avg_value": self.avg(filo_buff[v]),
                "serialized": filo_buff[v],
            })
            url_path = "%ssolarpower" % API_URL
            self.send_to_remote(url_path, payload)

    def load_checks(self):
        self.inverter_run()
        self.adjust_pump_speed()

    def inverter_run(self):
        try:
            if time.strftime("%H:%M") == '12:00':
                self.switch_to_solar_power()
            inverter_voltage = self.get_inverter_values()
            # converter switch OFF
            if self.avg(inverter_voltage) < CUT_OFF_VOLT and len(
                    inverter_voltage) > 15:
                self.switch_to_main_power()
                self.send_avg_data()

            # converter switch ON
            if self.avg(inverter_voltage) > SWITCH_ON_VOLT and len(
                    inverter_voltage) > 30:
                self.switch_to_solar_power()
                self.send_avg_data()
            self.integrity_check()

        except Exception as ex:
            logging.warning(ex)

    def get_inverter_values(self, slot='1s', value='voltage'):
        inverter_voltage = self.filo_fifo.get_filo_value('%s_inverter' % slot, value)
        if len(inverter_voltage) == 0:
            return []
        return inverter_voltage.pop()

    def filter_flush_run(self):
        now_cc = self.avg(self.get_inverter_values('1s', 'current'))
        avg_cc = self.avg(self.get_inverter_values('10m', 'current'))
        cc_size = len(self.get_inverter_values('10s', 'current'))
        timestamp = int(time.time())
        if abs(now_cc - avg_cc) > 5000 and cc_size > 10:
            self.FILTER_FLUSH.append(now_cc)
        else:
            if len(self.FILTER_FLUSH) > 5:
                self.send_ff_data('inverter_current')
            self.FILTER_FLUSH = []
        return timestamp

    def reset_ff(self):
        if len(self.FILTER_FLUSH) < 5:
            self.FILTER_FLUSH = []

    # todo check for error in pump_status
    def send_pump_stats(self):
        relay_status = int(GPIO.input(POND_RELAY))
        self.pump_status = self.automation.get_pump_status()
        self.automation.send_pond_stats(relay_status, self.pump_status)

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
        # so in this case GPIO.input(POND_RELAY) should be in 0 meaning we're working from battery and vice versa
        # in case  we're working from mains Inverter should be in state GPIO.input(INVER_CHECK) == 0 and POND_RELAY
        # state should be 1 which mean relay isn't switched.

    def integrity_check(self):
        avg_status = self.filo_fifo.get_avg_rel_status
        if avg_status < 0.5 and self.filo_fifo.len_sts_chk > 8:
            logging.error("-------------Something IS VERY Wrong pls check logs -----------------")
            logging.error("-------------Switching to MAINS avg _status is: %3.2f ---------------" % avg_status)
            logging.error(
                "-------------Switching to POND RELAY status is: %d ------------------" % GPIO.input(POND_RELAY))
            logging.error(
                "-------------Switching to INVERTER RELAY status is: %d --------------" % GPIO.input(INVER_CHECK))
            logging.error("---------------------------------------------------------------------")
            self.switch_to_main_power()

    def increase_pump_speed(self, step):
        flow_speed = self.pump_status['flow_speed']
        new_speed = flow_speed + step

        if flow_speed > 95:
            return True
        if new_speed > 100:
            new_speed = 100
        self.pump_status = self.automation.adjust_pump_speed(new_speed, GPIO.input(POND_RELAY))
        return True

    def decrease_pump_speed(self, step):
        flow_speed = self.pump_status['flow_speed']
        new_speed = flow_speed - step
        if flow_speed == MIN_POND_SPEED:
            return True
        if new_speed < MIN_POND_SPEED:
            new_speed = MIN_POND_SPEED
        self.pump_status = self.automation.adjust_pump_speed(new_speed, GPIO.input(POND_RELAY))
        return True
