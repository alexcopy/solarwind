import logging
from dotenv import dotenv_values
from tuya_connector import TuyaOpenAPI
from tuya_iot import (
    AuthType,
    TuyaOpenMQ,
    TuyaDeviceManager,
    TUYA_LOGGER,
    TuyaCloudOpenAPIEndpoint
)

config = dotenv_values(".env")
ENDPOINT = TuyaCloudOpenAPIEndpoint.EUROPE
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
    def __init__(self):
        TUYA_LOGGER.setLevel(logging.INFO)
        self.openapi = TuyaOpenAPI(ENDPOINT, ACCESS_ID, ACCESS_KEY)
        self.openapi.connect()
        self.openapi.auth_type = AuthType.SMART_HOME
        self.deviceManager = TuyaDeviceManager(self.openapi, TuyaOpenMQ(self.openapi))
        self.deviceStatuses = {}
    @property
    def device_manager(self):
        return self.deviceManager
