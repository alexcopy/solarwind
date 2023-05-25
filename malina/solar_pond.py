#!/usr/bin/env python
import logging
import logging.handlers
import os
import time
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import dotenv_values

from malina.INA3221 import SDL_Pi_INA3221
from malina.LIB import FiloFifo
from malina.LIB import PondPumpAuto
from malina.LIB import SendApiData
from malina.LIB.DeviceManager import DeviceManager
from malina.LIB.LoadDevices import LoadDevices
from malina.LIB.InitiateDevices import  InitiateDevices
from malina.LIB.LoadRelayAutomation import LoadRelayAutomation
from malina.LIB.PrintLogs import SolarLogging
from malina.LIB.TuyaAuthorisation import TuyaAuthorisation

TIME_TIK = 1
CONFIGS_YAML = 'devices.yaml'
config = dotenv_values(".env")
LOG_DIR = config['LOG_DIR']
POND_SPEED_STEP = int(config["POND_SPEED_STEP"])
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)


class SolarPond():
    def __init__(self):
        self.FILTER_FLUSH = []
        tuya_auth = TuyaAuthorisation(logging)
        device_manager = tuya_auth.device_manager
        self.send_data = SendApiData.SendApiData(logging)
        self.shunt_load = SDL_Pi_INA3221.SDL_Pi_INA3221(addr=0x40)
        self.print_logs = SolarLogging(logging)
        self.filo_fifo = FiloFifo.FiloFifo(logging, self.shunt_load)
        self.automation = PondPumpAuto.PondPumpAuto(logging, device_manager, self.send_data)
        self.devices = LoadDevices(logging, device_manager)

        self.new_devices=InitiateDevices.devices

        self.dev_manager = DeviceManager

        self.load_automation = LoadRelayAutomation(logging, device_manager)
        self.invert_status = 1
        self.devices.update_invert_stats()
        time.sleep(2)
        self.devices.update_uv_stats_info()
        time.sleep(2)
        self.devices.update_fnt_dev_stats()

        self.switch_to_solar_power()

    @staticmethod
    def avg(l):
        if len(l) == 0:
            return 0
        return float(round(sum(l, 0.0) / len(l), 2))

    def switch_to_solar_power(self):
        inv_id, inv_name = self.devices.get_invert_credentials
        self.load_automation.load_switch_on(inv_id, inv_name, "switch")
        status = self.load_automation.get_device_statuses_by_id(inv_id, inv_name).get('switch_1')
        return status

    def switch_to_main_power(self):
        inv_id, inv_name = self.devices.get_invert_credentials
        self.load_automation.load_switch_off(inv_id, inv_name, "switch")
        status = self.load_automation.get_device_statuses_by_id(inv_id, inv_name).get('switch_1')
        return status

    def check_inverter_off_on(self):
        try:
            inverter_voltage = self.get_inverter_values()
            self.devices.invert_switch_on_off(self.avg(inverter_voltage))
        except Exception as ex:
            logging.error(ex)

    def processing_reads(self):
        try:
            inv_status = self._invert_status()
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
                                              self.automation.get_current_status, solar_current, self.devices)
                self.print_logs.log_run(self.filo_fifo.filo_buff, inv_status, self.automation.get_current_status,
                                        solar_current)
        except IOError as io_err:
            logging.info(io_err)

        except Exception as ex:
            logging.error(ex)

    def adjust_pump_speed(self):
        inverter_voltage = self.get_inverter_values()
        if len(inverter_voltage) < 15:
            logging.error(
                " ----It's too early to adjust %d pump_speed please wait until length over 15" % len(inverter_voltage))
            return 0
        # in case if we're working from mains switching to minimum allowed speed
        volt_avg = self.avg(inverter_voltage)
        min_speed = self.automation.min_pump_speed
        mains_relay_status = self.filo_fifo.get_main_rel_status
        if int(self.automation.get_current_status['mode']) == 6:
            self.automation.pond_pump_adj(min_speed, volt_avg, mains_relay_status)
        else:
            logging.info("Pump working mode is not 6 so no adjustments could be done ")

    def check_pump_speed(self):
        if not self.automation.pump_status['flow_speed'] % POND_SPEED_STEP == 0:
            rounded = round(int(self.automation.pump_status['flow_speed']) / 10) * 10
            if rounded < POND_SPEED_STEP:
                rounded = POND_SPEED_STEP
            logging.error(
                "The device status is not divisible by POND_SPEED_STEP %d" % self.automation.pump_status['flow_speed'])
            logging.error("Round UP to nearest  POND_SPEED_STEP value %d" % rounded)
            inv_id, inv_name = self.devices.get_invert_credentials
            inv_status = self.load_automation.get_device_statuses_by_id(inv_id, inv_name).get('switch_1')
            self.automation.change_pump_speed(rounded, inv_status)

    def load_checks(self):
        self.update_invert_stats()
        self.check_load_devices()
        self.check_inverter_off_on()
        self.weather_check_update()
        self._pump_speed_adjust()

    def _pump_speed_adjust(self):
        # switch management only if pond pump in mode =6
        pump_params = self.automation.get_current_status
        if int(pump_params['mode']) == 6:
            self.adjust_pump_speed()
            self.check_pump_speed()

    def weather_check_update(self):
        weather_timer = self.automation.local_weather.get('timestamp', 0)
        if int(time.time()) - weather_timer > 1800:
            self.automation.refresh_min_speed()
        if weather_timer == 0:
            self.automation.update_weather()

    def update_invert_stats(self):
        inv_status = self._invert_status()
        self.load_automation.set_main_sw_status(inv_status)

    def _invert_status(self):
        inv_id, inv_name = self.devices.get_invert_credentials
        inv_status = int(self.load_automation.get_device_statuses_by_id(inv_id, inv_name).get('switch'))
        return inv_status

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

    def check_load_devices(self):
        avg_invert_volt = self.avg(self.get_inverter_values())
        pump_params = self.automation.get_current_status

        # switch management only if pond pump in mode =6
        if int(pump_params['mode']) == 6:
            self.devices.uv_switch_on_off(avg_invert_volt)
            self.devices.fnt_switch_on_off(avg_invert_volt)

    def update_devs_stats(self):
        self.automation.refresh_pump_status()
        time.sleep(2)
        self.devices.update_uv_stats_info()
        time.sleep(2)
        self.devices.update_fnt_dev_stats()
        time.sleep(2)
        self.devices.update_invert_stats()

    def pump_stats_to_server(self):
        inv_status = self._invert_status()
        resp = self.send_data.send_pump_stats(inv_status, self.automation.get_current_status)
        err_resp = resp['errors']
        if err_resp:
            time.sleep(5)
            self.automation.refresh_pump_status()
            self.send_data.send_pump_stats(inv_status, self.automation.get_current_status)

    def send_avg_data(self):
        inv_status = int(not self._invert_status())
        self.send_data.send_avg_data(self.filo_fifo, inv_status)
        self.send_data.send_weather(self.automation.local_weather)

    def run_read_vals(self):
        reed = BackgroundScheduler()
        hour = int(time.strftime("%H"))
        time_now = time.strftime("%H:%M")
        when_reset = ['21:30', '01:00', '05:00', '07:00', '07:00', '12:00']
        send_time_slot = 1200
        load_time_slot = 10
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
        self.pump_stats_to_server()
        time.sleep(3)
        self.send_data.send_load_stats(self.devices.get_uv_sw_state)
        self.send_data.send_load_stats(self.devices.get_fnt_sw_state)

# todo:
#  add weather to table and advance in table pond self temp from future gauge
#  add proper error handling for api calls
#  refactor code in sendAPI Data for api calls
