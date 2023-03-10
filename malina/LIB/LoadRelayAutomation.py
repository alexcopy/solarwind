#!/usr/bin/env python


# V 1.0


# encoding: utf-8

import json
import logging
import time
from urllib.parse import urljoin

import requests
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
BASE_URL = config['API_URL']
USERNAME = config['USERNAME']
PASSWORD = config['PASSWORD']
DEVICE_ID = config['DEVICE_ID']
PUMP_NAME = config['PUMP_NAME']


class LoadRelayAutomation():
    def __init__(self, logger):
        TUYA_LOGGER.setLevel(logging.DEBUG)
        self.logger = logger
        self.openapi = TuyaOpenAPI(ENDPOINT, ACCESS_ID, ACCESS_KEY, AuthType.CUSTOM)

        self.openapi.connect(USERNAME, PASSWORD)
        self.deviceManager = TuyaDeviceManager(self.openapi, TuyaOpenMQ(self.openapi))
        self.deviceStatuses = {}

    # def send_pump_stats(self, is_working_mains: int):
    #     try:
    #         self.pump_status.update({'from_main': is_working_mains})
    #         payload = json.dumps(self.get_current_status)
    #         headers = {
    #             'Content-Type': 'application/json'
    #         }
    #         url = urljoin(BASE_URL, 'pondpump/')
    #         response = requests.request("POST", url, headers=headers, data=payload).json()
    #         if response['errors']:
    #             self.logger.error(response['payload'])
    #         return response
    #     except Exception as ex:
    #         print(ex)
    #         self.logger.error(ex)
    #         time.sleep(10)
    #         return {'errors': True}

    def switch_on_load(self, device_id):
        status = self.update_status(device_id)
        if not status['switch_1']:
            command = [
                {
                    "code": "switch_1",
                    "value": True
                }]
            self.deviceManager.send_commands(device_id, command)

    def switch_off_load(self, device_id):
        status = self.update_status(device_id)
        if status['switch_1']:
            command = [
                {
                    "code": "switch_1",
                    "value": False
                }]
            self.deviceManager.send_commands(device_id, command)

    def update_status(self, device_id):
        device_status = self.deviceManager.get_device_list_status([device_id])['result'][0]['status']
        sw_status = {v['code']: v['value'] for v in device_status}
        self.deviceStatuses.update({device_id: sw_status})
        return sw_status

    @property
    def get_device_statuses(self):
        return self.deviceStatuses
