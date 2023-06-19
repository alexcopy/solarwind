import logging
from dotenv import dotenv_values
from tuya_iot import (
    TuyaOpenAPI,
    AuthType,
    TuyaOpenMQ,
    TuyaDeviceManager,
    TUYA_LOGGER
)

config = dotenv_values(".env")
ENDPOINT = config['ENDPOINT']
ACCESS_ID = config['ACCESS_ID']
ACCESS_KEY = config['ACCESS_KEY']
USERNAME = config['USERNAME']
PASSWORD = config['PASSWORD']


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class TuyaAuthorisation(metaclass=SingletonMeta):
    def __init__(self, logger):
        TUYA_LOGGER.setLevel(logging.INFO)
        self.logger = logger
        self.openapi = TuyaOpenAPI(ENDPOINT, ACCESS_ID, ACCESS_KEY, AuthType.CUSTOM)

        self.openapi.connect(USERNAME, PASSWORD)
        self.deviceManager = TuyaDeviceManager(self.openapi, TuyaOpenMQ(self.openapi))
        self.deviceStatuses = {}

    @property
    def device_manager(self):
        return self.deviceManager

