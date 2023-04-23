import os

import yaml

from malina.LIB.Device import Device


class DeviceManager:
    def __init__(self):
        self._devices = {}
        self._device_order = []
        self._power_limit = 10000

    def add_device(self, device):
        if device.get_id() in self._devices:
            raise ValueError(f"Device with ID '{device.get_id()}' already exists.")
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
        device.set_status({"on": True})

    def device_switch_off(self, device_id):
        device = self.get_device_by_id(device_id)
        device.set_status({"on": False})

    def get_devices_by_name(self, name):
        matching_devices = []
        for device in self._devices.values():
            if device.name == name:
                matching_devices.append(device)
        return matching_devices

    def sort_devices_by_priority(self):
        self._device_order.sort(key=lambda device: device.priority)

    def get_available_power(self):
        used_power = sum(int(device.power_consumption) for device in self._devices.values())
        return self._power_limit - used_power

    def read_device_configs(self, path):
        for file in os.scandir(path):
            if file.is_file() and file.name.endswith('configs.yaml'):
                with open(file.path) as f:
                    try:
                        config = yaml.safe_load(f)
                        for device_config in config:
                            device = Device(
                                id=device_config['id'],
                                name=device_config['name'],
                                status=device_config['status'],
                                min_volt=device_config['min_volt'],
                                max_volt=device_config['max_volt'],
                                priority=device_config['priority'],
                                device_type=device_config['device_type'],
                                coefficient=device_config['coefficient']
                            )
                            self.add_device(device)
                    except yaml.YAMLError as e:
                        print(f"Failed to read config file {file.path}: {e}")
