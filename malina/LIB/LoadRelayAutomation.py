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


class LoadRelayAutomation():
    def __init__(self, logger, device_manager):
        self.logger = logger
        self.deviceManager = device_manager
        self.deviceStatuses = {}

    # def send_load_stats(self, is_working_mains: int):
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

    def load_switch_on(self, device_id):
        try:
            status = self.update_status(device_id)
            if not status['switch_1']:
                command = [
                    {
                        "code": "switch_1",
                        "value": True
                    }]
                self.deviceManager.send_commands(device_id, command)
                time.sleep(2)
                self.update_status(device_id)
        except Exception as ex:
            self.logger.error(ex)

    def load_switch_off(self, device_id):
        try:
            status = self.update_status(device_id)
            if status['switch_1']:
                command = [
                    {
                        "code": "switch_1",
                        "value": False
                    }]
                self.deviceManager.send_commands(device_id, command)
                time.sleep(2)
                self.update_status(device_id)
        except Exception as ex:
            self.logger.error(ex)

    def update_status(self, device_id):
        try:
            device_status = self.deviceManager.get_device_list_status([device_id])['result'][0]['status']
            sw_status = {v['code']: v['value'] for v in device_status}
            self.deviceStatuses.update({device_id: sw_status})
            return sw_status
        except Exception as ex:
            self.logger.error(ex)

    @property
    def get_all_statuses(self):
        return self.deviceStatuses

    def get_device_statuses_by_id(self, device_id):
        if device_id not in self.deviceStatuses:
            self.update_status(device_id)
        return self.deviceStatuses[device_id]
