import logging
import os
import time

import yaml

from malina.LIB.Device import Device
from malina.LIB.TuyaAuthorisation import TuyaAuthorisation
from malina.LIB.TuyaController import TuyaController


class DeviceManager:
    def __init__(self):
        self._devices = {}
        self.logger = logging
        self._device_order = []
        self._power_limit = 10000
        self.tuya_controller = TuyaController(TuyaAuthorisation(self.logger).device_manager)

    def add_device(self, device):
        if device.get_id() in self._devices:
            raise ValueError(f"Device with ID '{device.get_id()}' already exists.")

        if device.get_name() in self._devices:
            raise ValueError(f"Device with ID '{device.get_id()}' and '{device.get_name()}' already exists.")
        self._devices[device.get_id()] = device
        self._device_order.append(device)

    def remove_device(self, device):
        if device not in self._devices.values():
            raise ValueError(f"Device with ID '{device.get_id()}' does not exist.")
        del self._devices[device.get_id()]
        self._device_order.remove(device)

    def get_devices(self):
        return self._device_order

    def get_device_by_id(self, device_id):
        if device_id not in self._devices:
            raise ValueError(f"Device with ID '{device_id}' does not exist.")
        return self._devices[device_id]

    def update_device_status(self, device_id, status):
        device = self.get_device_by_id(device_id)
        device.set_status(status)

    def device_switch_on(self, device_id):
        device = self.get_device_by_id(device_id)
        if device.is_device_ready_to_switch_on():
            dev_status = self.tuya_controller.switch_on_device(device)
            device.set_status(dev_status)
        else:
            logging.debug("-----Device with name %s isn't ready to switch on " % device.name)

    def device_switch_off(self, device_id):
        device = self.get_device_by_id(device_id)
        if device.is_device_ready_to_switch_off():
            dev_status = self.tuya_controller.switch_off_device(device)
            device.set_status(dev_status)
        else:
            logging.debug("-----Device with name %s isn't ready to switch off " % device.name)

    def get_devices_by_name(self, name):
        matching_devices = []
        for device in self._devices.values():
            if device.name == name:
                matching_devices.append(device)
        return matching_devices

    def update_all_statuses(self):
        self.tuya_controller.update_devices_status(self._device_order)

    def get_devices_by_device_type(self, dev_type: str):
        matching_devices = []
        for device in self._devices.values():
            if device.get_device_type.upper() == dev_type.upper():
                matching_devices.append(device)
        return matching_devices

    def sort_devices_by_priority(self):
        self._device_order.sort(key=lambda device: device.priority)

    def get_available_power(self):
        used_power = sum(int(device.power_consumption) for device in self._devices.values())
        return self._power_limit - used_power

    def read_device_configs(self, path):
        for file in os.scandir(path):
            if file.is_file() and file.name.endswith('.yaml'):
                with open(file.path) as f:
                    try:
                        config = yaml.safe_load(f)
                        for device_config in config:
                            device = Device(
                                id=device_config['id'],
                                name=device_config['name'],
                                desc=device_config['desc'],
                                extra=device_config['extra'],
                                status=device_config['status'],
                                api_sw=device_config['api_sw'],
                                min_volt=device_config['min_voltage'],
                                max_volt=device_config['max_voltage'],
                                priority=device_config['priority'],
                                device_type=device_config['device_type'],
                                coefficient=device_config['coefficient']
                            )
                            self.add_device(device)
                    except yaml.YAMLError as e:
                        print(f"Failed to read config file {file.path}: {e}")
