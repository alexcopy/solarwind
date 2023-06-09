#!/usr/bin/env python
import logging
import logging.handlers
import time
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import dotenv_values

from malina.LIB.InitiateDevices import InitiateDevices
from malina.LIB import SendApiData
from malina.LIB.DeviceManager import DeviceManager
from malina.LIB.PrintLogs import SolarLogging
from malina.LIB.TuyaAuthorisation import TuyaAuthorisation
from malina.LIB import FiloFifo
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
        self.new_devices = InitiateDevices(logging).devices
        self.dev_manager = DeviceManager
        self.send_data = SendApiData.SendApiData(logging)
        self.switch_to_solar_power()

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
            pump_status = self.new_devices.get_devices_by_name("pump")[0].get_status('P')
            self.filo_fifo.buffers_run(inv_status)
            self.filter_flush_run()
            self.filo_fifo.update_rel_status({
                'status_check': 1,
                'inverter_relay': inv_status,
                'main_relay_status': inv_status,
            })
            solar_current = self.filo_fifo.solar_current
            cur_t = int(time.time())
            hour = int(time.strftime("%H"))
            diviser = 4
            if hour > 21 or hour < 5:
                diviser = 30

            if cur_t % diviser == 0:
                self.print_logs.printing_vars(self.filo_fifo.fifo_buff, inv_status, self.filo_fifo.get_avg_rel_stats,
                                             pump_status, solar_current, self.new_devices)
                self.print_logs.log_run(self.filo_fifo.filo_buff, inv_status,pump_status,
                                        solar_current)
        except IOError as io_err:
            logging.error(f"problem in processing_reads please have a look in IOError {self.new_devices.get_devices_by_name('inverter')[0].get_status()}")
            logging.info(io_err)

        except Exception as ex:
            logging.error(f"problem in processing_reads please have a look in Exception {self.new_devices.get_devices_by_name('inverter')[0].get_status()}")
            logging.error(ex)


    def load_checks(self):
        self.tuya_controller.switch_on_off_all_devices(self.new_devices.get_devices_by_device_type("SWITCH"))
        # self.weather_check_update()
        self.new_devices.get_devices_by_name("pump")
        self.tuya_controller.adjust_devices_speed()


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
        self.send_data.send_weather(self.automation.local_weather)

    def run_read_vals(self):
        reed = BackgroundScheduler()
        hour = int(time.strftime("%H"))
        time_now = time.strftime("%H:%M")
        when_reset = ['21:30', '01:00', '05:00', '07:00', '07:00', '12:00']
        send_time_slot = 1200
        load_time_slot = 30
        pump_stats = 300

        # Don't need to send stats overnight
        if hour >= 21 or hour <= 5:
            send_time_slot = 2400
            pump_stats = 1800
            load_time_slot = 120

        if time_now in when_reset:
            reed.shutdown()

        reed.add_job(self.send_avg_data, 'interval', seconds=send_time_slot)
        reed.add_job(self.update_devs_stats, 'interval', seconds=pump_stats / 5)
        reed.add_job(self.send_stats_api, 'interval', seconds=pump_stats + 60)
        reed.add_job(self.load_checks, 'interval', seconds=load_time_slot)
        reed.start()

    def send_stats_api(self):
        self.send_data.send_load_stats(self.new_devices.get_devices_by_name("uv")[0])
        self.send_data.send_load_stats(self.new_devices.get_devices_by_name("air")[0])
        self.send_data.send_load_stats(self.new_devices.get_devices_by_name("fountain")[0])
        self.send_data.send_load_stats(self.new_devices.get_devices_by_name("pump")[0])

# todo:
#  add weather to table and advance in table pond self temp from future gauge
#  add proper error handling for api calls
#  refactor code in sendAPI Data for api calls
