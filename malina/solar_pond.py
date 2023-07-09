#!/usr/bin/env python
import logging
import logging.handlers
import time
from pathlib import Path

from dotenv import dotenv_values

from malina.LIB import FiloFifo
from malina.LIB import SendApiData
from malina.LIB.InitiateDevices import InitiateDevices
from malina.LIB.PrintLogs import SolarLogging
from malina.LIB.TuyaAuthorisation import TuyaAuthorisation
from malina.LIB.TuyaController import TuyaController

config = dotenv_values(".env")
LOG_DIR = config['LOG_DIR']
POND_SPEED_STEP = int(config["POND_SPEED_STEP"])
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)


class SolarPond():
    def __init__(self):
        self.FILTER_FLUSH = []
        self.print_logs = SolarLogging(logging)
        self.filo_fifo = FiloFifo.FiloFifo()
        self.tuya_auth = TuyaAuthorisation(logging)
        self.tuya_controller = TuyaController(self.tuya_auth)
        self.new_devices = InitiateDevices().devices

        self.send_data = SendApiData.SendApiData(logging)
        # self.switch_to_solar_power()
        self.new_devices.update_all_statuses()

    @staticmethod
    def avg(l):
        if len(l) == 0:
            return 0
        return float(round(sum(l, 0.0) / len(l), 2))

    def switch_to_solar_power(self):
        inver = self.new_devices.get_devices_by_name("inverter")[0]
        self.tuya_controller.switch_on_device(inver)

    def switch_to_main_power(self):
        inver = self.new_devices.get_devices_by_name("inverter")[0]
        self.tuya_controller.switch_off_device(inver)

    def processing_reads(self):
        try:
            inv_status = self.new_devices.get_devices_by_name("inverter")[0].get_status('switch_1')
            self.filo_fifo.buffers_run(inv_status)
            self.filter_flush_run()
            self.filo_fifo.update_rel_status({
                'status_check': 1,
                'inverter_relay': inv_status,
                'main_relay_status': inv_status,
            })
        except IOError as io_err:
            logging.error(
                f"problem in processing_reads please have a look in IOError {self.new_devices.get_devices_by_name('inverter')[0].get_status()}")
            logging.info(io_err)

        except Exception as ex:
            logging.error(
                f"problem in processing_reads please have a look in Exception {self.new_devices.get_devices_by_name('inverter')[0].get_status()}")
            logging.error(ex)

    def _logs(self, inv_status, pump_status):
        solar_current = self.filo_fifo.solar_current
        hour = int(time.strftime("%H"))
        diviser = 4
        if hour > 21 or hour < 5:
            diviser = 30
        cur_t = int(time.time())
        if cur_t % diviser == 0:
            self.print_logs.printing_vars(inv_status, pump_status, self.new_devices)
            self.print_logs.log_run(inv_status, pump_status)

    def load_checks(self):
        inv_status = self.new_devices.get_devices_by_name("inverter")[0].get_status('switch_1')
        self.tuya_controller.switch_on_off_all_devices(self.new_devices.get_devices_by_device_type("SWITCH"))
        # self.weather_check_update()
        pumps = self.new_devices.get_devices_by_name("pump")
        self.tuya_controller.adjust_devices_speed(pumps, inv_status)

    def weather_check_update(self):
        weather_timer = self.automation.local_weather.get('timestamp', 0)
        if int(time.time()) - weather_timer > 1800:
            self.automation.refresh_min_speed()
        if weather_timer == 0:
            self.automation.update_weather()

    def get_inverter_values(self, slot='1s', value='bus_voltage'):
        inverter_voltage = self.filo_fifo.get_filo_value('%s_inverter' % slot, value)
        if len(inverter_voltage) == 0:
            return []
        return inverter_voltage.pop()

    def filter_flush_run(self):
        now_cc = self.filo_fifo.fifo_buff['1s_inverter_bat_current']
        avg_cc = self.avg(self.get_inverter_values('10m', 'current'))
        cc_size = len(self.get_inverter_values('1s', 'current'))
        timestamp = int(time.time())
        curr_diff = abs(now_cc - avg_cc)
        if curr_diff > 5000 and cc_size > 10:
            self.FILTER_FLUSH.append(now_cc)
        else:
            if len(self.FILTER_FLUSH) > 8:
                self.send_data.send_ff_data('inverter_current', self.FILTER_FLUSH, curr_diff)
            self.FILTER_FLUSH = []
        return timestamp

    def reset_ff(self):
        if len(self.FILTER_FLUSH) < 5:
            self.FILTER_FLUSH = []

    def update_devs_stats(self):
        devices = self.new_devices.get_devices()
        self.tuya_controller.update_devices_status(devices)

    def send_avg_data(self):
        inv_status = self.new_devices.get_devices_by_name("inverter")[0].get_status('switch_1')
        self.send_data.send_avg_data(self.filo_fifo, inv_status)
        # self.send_data.send_weather(self.automation.local_weather)

    def run_read_vals(self):
        curr = int(time.time())
        inv_status = self.new_devices.get_devices_by_name("inverter")[0].get_status('switch_1')
        pump_status = self.new_devices.get_devices_by_name("pump")[0].get_status('P')

        if curr % 5 == 0:
            self.processing_reads()

        if curr % 5 == 0:
            self._logs(inv_status, pump_status)
            # self.send_avg_data()  # run every seconds=1200
        if curr % 30 == 0:
            print("UPDATING READ_VALS")
            self.update_devs_stats()  # run every seconds=300 / 5
        # if curr % 50 == 0:
        #     self.send_stats_api()  # run every seconds=300 + 60
        if curr % 10 == 0:
          self.load_checks()  # run every seconds=30

    def send_stats_api(self):
        devices = self.new_devices.get_devices()
        for device in devices:
            self.send_data.send_load_stats(device)

# todo:
#  add weather to table and advance in table pond self temp from future gauge
#  add proper error handling for api calls
#  refactor code in sendAPI Data for api calls
