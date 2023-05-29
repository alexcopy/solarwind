import time

import yaml
from malina.LIB.DeviceManager import DeviceManager
from malina.LIB.Device import Device
from malina.LIB.LoadRelayAutomation import LoadRelayAutomation

DEVICE_CONFIG = ".devices.yaml"


class InitiateDevices:
    def __init__(self, logger, tuya_device_manager):
        self.device_controller = DeviceManager()
        self.logger = logger
        self.rel_automation = LoadRelayAutomation(logger, device_manager=tuya_device_manager)

        with open(DEVICE_CONFIG) as f:
            devices = yaml.safe_load(f)
        for device_config in devices:
            device = Device(**device_config)
            dev_status = self.rel_automation.get_updated_status(device)
            device.set_status(dev_status)
            self.device_controller.add_device(device)
            time.sleep(2)

    @property
    def devices(self):
        return self.device_controller
