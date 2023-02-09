#!/usr/bin/env python


# V 1.0


# encoding: utf-8

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
PUMP_NAME = config['PUMP_NAME']


class PondPumpAuto():
    def __init__(self, logger):
        TUYA_LOGGER.setLevel(logging.DEBUG)
        self.logger = logger
        self.openapi = TuyaOpenAPI(ENDPOINT, ACCESS_ID, ACCESS_KEY, AuthType.CUSTOM)
        self.openapi.connect(USERNAME, PASSWORD)
        self.deviceManager = TuyaDeviceManager(self.openapi, TuyaOpenMQ(self.openapi))

    def send_pond_stats(self, is_working_mains: int, data_to_remote):
        try:

            data_to_remote.update({'from_main': is_working_mains})
            payload = json.dumps(data_to_remote)
            headers = {
                'Content-Type': 'application/json'
            }
            url = urljoin(BASE_URL, 'pondpump/')
            response = requests.request("POST", url, headers=headers, data=payload)
            return response.text
        except Exception as ex:
            print(ex)
            self.logger.error(ex)
            return ex

    def get_pump_status(self):
        pumps_status = {}
        try:
            device_status = self.deviceManager.get_device_status(DEVICE_ID)
            if device_status['success'] is False:
                self.logger.error(device_status)
                raise Exception(device_status)

            pond_pump = device_status['result']
            for k in pond_pump:
                if k['value'] is True:
                    k['value'] = 1
                elif k['value'] is False:
                    k['value'] = 0

                if k['code'] == 'P':
                    k['code'] = 'flow_speed'

                pumps_status.update({k['code']: k['value']})
            pumps_status.update({'name': PUMP_NAME})
            return pumps_status

        except Exception as ex:
            print(ex)
            self.logger.error(ex)
            return {'flow_speed': 0, "Power": 0, 'error': True}

    def adjust_pump_speed(self, value: int, is_working_mains: int):
        if value > 100:
            self.logger.error("The value of PumpSpeed is OUT of Range PLS Check %d" % value)
            value = 100
        command = [
            {
                "code": "P",
                "value": value
            }
        ]
        res = self.deviceManager.send_commands(DEVICE_ID, command)
        if res['success'] is True:
            self.logger.info("!!!!!   Pump's Speed successfully adjusted to: %d !!!!!!!!!" % value)
        else:
            self.logger.error("!!!!   Pump's Speed has failed to adjust in speed to: %d !!!!" % value)
            self.logger.error(res)

        # todo check for error in pump_status before sending
        status = self.get_pump_status()
        self.send_pond_stats(is_working_mains, status)
        return status
