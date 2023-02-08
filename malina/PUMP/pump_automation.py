#!/usr/bin/env python

import json
import logging
from urllib.parse import urljoin
import requests
from dotenv import dotenv_values

from tuya_iot import (
    TuyaOpenAPI,
    AuthType,
    TuyaOpenMQ,
    TuyaDeviceManager,
    TuyaHomeManager,
    TuyaDeviceListener,
    TuyaDevice,
    TuyaTokenInfo,
    TUYA_LOGGER
)

config = dotenv_values(".env")
ENDPOINT = config['ENDPOINT']
ACCESS_ID = config['ACCESS_ID']
ACCESS_KEY = config['ACCESS_KEY']
BASE_URL = config['API_URL']
USERNAME = config['USERNAME']
PASSWORD = config['PASSWORD']
DEVICE_ID = config['DEVICE_ID']


class PUMP():
    def __init__(self):
        TUYA_LOGGER.setLevel(logging.DEBUG)

        self.openapi = TuyaOpenAPI(ENDPOINT, ACCESS_ID, ACCESS_KEY, AuthType.CUSTOM)
        self.openapi.connect(USERNAME, PASSWORD)
        self.deviceManager = TuyaDeviceManager(self.openapi, TuyaOpenMQ(self.openapi))

    def send_pond_stats(self):
        try:
            pond_pump_status = self.deviceManager.get_device_status(DEVICE_ID)['result']
            data_to_remote = {}
            for k in pond_pump_status:
                if k['value'] is True:
                    k['value'] = 1
                elif k['value'] is False:
                    k['value'] = 0

                if k['code'] == 'P':
                    k['code'] = 'flow_speed'

                data_to_remote.update({k['code']: k['value']})

            data_to_remote.update({'name': 'pond_pump'})
            payload = json.dumps(data_to_remote)
            headers = {
                'Content-Type': 'application/json'
            }
            url = urljoin(BASE_URL, 'pondpump/')
            response = requests.request("POST", url, headers=headers, data=payload)
            return response.text
        except Exception as ex:
            print(ex)
            return ex


# if __name__ == '__main__':
#     automation = PUMP()
#     print(automation.send_pond_stats())

    # print("device test-> ", openapi.token_info.uid)
    # Get device list
    # assetManager = TuyaAssetManager(openapi)
    # devIds = assetManager.getDeviceList(ASSET_ID)

    # Update device status
    #
    # homeManager = TuyaHomeManager(openapi, openmq, deviceManager)
    # homeManager.update_device_cache()
