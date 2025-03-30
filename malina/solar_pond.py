#!/usr/bin/env python
import json
import logging
import logging.handlers
import time
from pathlib import Path
import traceback
from dotenv import dotenv_values

from malina.LIB import FiloFifo
from malina.LIB import SendApiData
from malina.LIB.InitiateDevices import InitiateDevices
from malina.LIB.PrintLogs import SolarLogging
from malina.LIB.TuyaAuthorisation import TuyaAuthorisation
from malina.LIB.TuyaController import TuyaController
from malina.LIB.PowerDeviceManager import PowerDeviceManager

from colorama import Fore, Style

LOG_DIR = "logs"
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)


class SolarPond():
    def __init__(self):
        self.power_devices_manager = PowerDeviceManager(
            ['tiger_wattage', 'leisure_wattage', 'inverter_wattage', 'solar_wattage'])
        self.FILTER_FLUSH = []
        self.print_logs = SolarLogging()
        self.filo_fifo = FiloFifo.FiloFifo()
        self.tuya_auth = TuyaAuthorisation()
        self.tuya_controller = TuyaController(self.tuya_auth)
        self.new_devices = InitiateDevices().device_controller
        self.send_data = SendApiData.SendApiData()
        self.new_devices.update_all_statuses()


    @staticmethod
    def avg(l):
        if len(l) == 0:
            return 0
        return float(round(sum(l, 0.0) / len(l), 2))

    def switch_to_solar_power(self):
        inver = self.to_bool(self.new_devices.get_devices_by_name("inverter")[0])
        self.tuya_controller.switch_on_device(inver)


    def reset_power_buffers_daily(self):
        self.power_devices_manager.reset_buffers()

    def send_avg_hr_power_to_server(self, timely="hourly"):
        for pwr_device in self.power_devices_manager.devices:
            self.send_data.send_hourly_daily_averages_to_server(pwr_device, timely)

    def power_devs_update(self):
        tiger_wattage = self.avg(self.filo_fifo.filo_buff['10m_tiger_wattage'])
        leisure_wattage = self.avg(self.filo_fifo.filo_buff['10m_leisure_wattage'])
        inverter_wattage = self.avg(self.filo_fifo.filo_buff['10m_inverter_wattage'])
        solar_wattage = (self.filo_fifo.solar_current['10m_solar_current'] * self.avg(self.filo_fifo.filo_buff['10m_inverter_bus_voltage'])) / 1000

        self.power_devices_manager.update_ten_min_power_value("tiger_wattage", tiger_wattage)
        self.power_devices_manager.update_ten_min_power_value("leisure_wattage", leisure_wattage)
        self.power_devices_manager.update_ten_min_power_value("inverter_wattage", inverter_wattage)
        self.power_devices_manager.update_ten_min_power_value("solar_wattage", round(solar_wattage, 1))
        self.send_avg_hr_power_to_server("ten_minutes")

    def switch_to_main_power(self):
        inver = self.new_devices.get_devices_by_name("inverter")[0]
        self.tuya_controller.switch_off_device(inver)

    def processing_reads(self):
        try:
            inv_status = self.to_bool(self.new_devices.get_devices_by_name("inverter")[0].get_status('switch_1'))
            self.filo_fifo.buffers_run(inv_status)
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
            logging.error(f"problem in processing_reads please have a look in Exception{ex}")
            traceback.print_exc()
            logging.error("-----------------END--------------------")

    def show_logs(self):
        inv_status = self.to_bool(self.new_devices.get_devices_by_name("inverter")[0].get_status('switch_1'))
        pump_status = self.new_devices.get_devices_by_name("pump")[0].get_status('P')
        self.print_logs.printing_vars(self.filo_fifo, inv_status, pump_status, self.new_devices)
        self.power_devices_manager.print_all_devices_logs()

    def load_checks(self):
        pump = self.new_devices.get_devices_by_name("pump")[0]
        switches = self.new_devices.get_devices_by_device_type("SWITCH")
        only_loads = [device for device in switches if device.get_name() != "inverter"]
        inverter = next((d for d in switches if d.get_name() == "inverter"), None)
        if inverter is None:
            logging.info("!!!!!  Inverter not found in the Devices LIST  !!!!!!!!")
            return
        inv_status = inverter.is_device_on
        # Manual mode
        if int(pump.get_status("mode")) == 6:
            self.tuya_controller.switch_on_off_all_devices(self.filo_fifo, switches)
            self.tuya_controller.adjust_devices_speed(pump, inv_status, self.filo_fifo)
        # Custom mode
        elif int(pump.get_status("mode")) == 1:
            self.tuya_controller.switch_all_on_hard(only_loads)
            self.tuya_controller.switch_on_off_all_devices(self.filo_fifo, [inverter, pump])
            logging.info(
                f"{Fore.RED} Pump working in VERY STRICT CUSTOM MODE mode= {pump.get_status('mode')}  "
                f" ALL switches wouldn't be AUTO controlled except the INVERTER {Style.RESET_ALL}")
            return True
        # Summer mode
        elif int(pump.get_status("mode")) == 4:
            self.tuya_controller.switch_on_off_all_devices(self.filo_fifo, [inverter, pump])
            logging.info(
                f"{Fore.YELLOW} Pump working in SUMMER MODE mode= {pump.get_status('mode')}  "
                f" ALL switches IS NOT FORCED ON BUT not controlled except the INVERTER {Style.RESET_ALL}")
            return True

        # winter or night mode
        elif int(pump.get_status("mode")) == 5:
            except_fountain = [device for device in switches if device.get_name() != "fountain"]
            self.tuya_controller.switch_on_off_all_devices(self.filo_fifo, except_fountain)
            logging.info(
                f"{Fore.YELLOW} Pump working in WINTER MODE mode= {pump.get_status('mode')}  "
                f" Только Фонтан не управляется {Style.RESET_ALL}")
            return True

        else:
            logging.info(
                f"Pump working mode= {pump.get_status('mode')}  "
                f"switches wouldn't be AUTO controlled the only INVERTER AUTO controlled")
            self.tuya_controller.switch_on_off_all_devices(self.filo_fifo, [inverter, pump])
            return False

    def weather_check_update(self):
        self.tuya_controller.adjust_min_pump_speed(self.new_devices.get_devices_by_name("pump"))

    def get_inverter_values(self, slot='1s', value='bus_voltage'):
        inverter_voltage = self.filo_fifo.get_filo_value('%s_inverter' % slot, value)
        if len(inverter_voltage) == 0:
            return []
        return inverter_voltage.pop()

    def filter_flush_run(self):
        try:
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
        except:
            logging.error('The Problem in FlushRun')

    def reset_ff(self):
        if len(self.FILTER_FLUSH) < 5:
            self.FILTER_FLUSH = []

    def to_bool(self, val):
        if isinstance(val, bool):
            return val
        if isinstance(val, int):
            return val == 1
        if isinstance(val, str):
            return val.strip().lower() in ["1", "true", "yes"]
        return False

    def update_devs_stats(self):
        devices = self.new_devices.get_devices()
        self.tuya_controller.update_devices_status(devices)

    def send_stats_to_api(self):
        inv_status = self.to_bool(self.new_devices.get_devices_by_name("inverter")[0].get_status('switch_1'))
        devices = self.new_devices.get_devices()
        for device in devices:
            self.send_data.send_load_stats(device, inv_status)


    def send_avg_data(self):
        payloads = []
        try:
            inv_status = self.to_bool(self.new_devices.get_devices_by_name("inverter")[0].get_status('switch_1'))
            buff = self.filo_fifo.filo_buff
            for v in buff:
                buff_v_ = buff[v]
                if not '1h' in v:
                    continue
                avg_val = self.avg(buff_v_)
                val_type = "V"
                name = v.lower()

                if 'current' in v:
                    val_type = "A"

                if 'wattage' in v:
                    val_type = "W"

                payload = json.dumps({
                    "value_type": val_type,
                    "name": name,
                    "inverter_status": inv_status,
                    "avg_value": avg_val,
                    "serialized": json.dumps(buff_v_),
                })
                payloads.append(payload)
            url_path = "%ssolarpower"
            self.send_data.send_to_remote(url_path, payloads)
        except Exception as e:
            logging.error(f"ERROR: {e}")

    def send_temp_sensors(self):
        temp_sensors = self.new_devices.get_devices_by_device_type("termo")
        for sensor in temp_sensors:
            self.send_data.send_temp_sensor(sensor)

# todo:
#  add weather to table and advance in table pond self temp from future gauge
#  add proper error handling for api calls
#  refactor code in sendAPI Data for api calls
