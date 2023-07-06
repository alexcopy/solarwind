import logging
import os

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
        self.tuya_controller = TuyaController(TuyaAuthorisation(self.logger))

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
