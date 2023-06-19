import yaml

from malina.LIB.Device import Device
from malina.LIB.DeviceManager import DeviceManager

DEVICE_CONFIG = ".devices.yaml"


class InitiateDevices:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "initialized"):
            return
        self.device_controller = DeviceManager()

        with open(DEVICE_CONFIG) as f:
            devices = yaml.safe_load(f)
        for device_config in devices:
            device = Device(**device_config)
            self.device_controller.add_device(device)

        self.initialized = True

    @property
    def devices(self):
        return self.device_controller
