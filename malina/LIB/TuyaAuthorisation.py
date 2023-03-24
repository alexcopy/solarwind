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


class TuyaAuthorisation():
    def __init__(self, logger):
        TUYA_LOGGER.setLevel(logging.DEBUG)
        self.logger = logger
        self.openapi = TuyaOpenAPI(ENDPOINT, ACCESS_ID, ACCESS_KEY, AuthType.CUSTOM)

        self.openapi.connect(USERNAME, PASSWORD)
        self.deviceManager = TuyaDeviceManager(self.openapi, TuyaOpenMQ(self.openapi))
        self.deviceStatuses = {}

    @property
    def device_manager(self):
        return self.deviceManager
