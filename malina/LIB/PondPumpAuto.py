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
        self.pump_status = {'flow_speed': 0}

    def send_pond_stats(self, is_working_mains: int):
        try:

            self.pump_status.update({'from_main': is_working_mains})
            payload = json.dumps(self.get_current_status)
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
        try:
            device_status = self.deviceManager.get_device_status(DEVICE_ID)
            if device_status['success'] is False:
                self.logger.error(device_status)
                raise Exception(device_status)

            self.update_pump_status(device_status)
            return self.pumps_status

        except Exception as ex:
            print(ex)
            self.logger.error(ex)
            return {'flow_speed': 0, "Power": 0, 'error': True}

    def update_pump_status(self, tuya_responce):
        self.pumps_status = {}
        pond_pump = tuya_responce['result']
        if not 'result' in tuya_responce:
            print(tuya_responce)
            exit()
        for k in pond_pump:
            if k['value'] is True:
                k['value'] = 1
            elif k['value'] is False:
                k['value'] = 0

            if k['code'] == 'P':
                k['code'] = 'flow_speed'

            self.pumps_status.update({k['code']: k['value']})
        self.pumps_status.update({'name': PUMP_NAME})
        self.pumps_status.update({'timestamp': time.time()})

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

        status = self.get_pump_status()
        if 'error' in status and status['error'] is True:
            return status
        self.update_pump_status(status)
        self.send_pond_stats(is_working_mains)
        return status

    def is_adj_needed(self):



    def is_minimum_speed(self, min_speed):
        return min_speed == self.get_current_status['flow_speed']

    @property
    def is_max_speed(self):
        return self.pump_status['flow_speed'] == 100

    @property
    def get_current_status(self):
        if self.pump_status['flow_speed'] == 0:
            self.get_pump_status()
        return self.pump_status

    def decrease_pump_speed(self, step, min_pump_speed, mains_relay_status):
        flow_speed = self.pump_status['flow_speed']
        new_speed = flow_speed - step
        if flow_speed == min_pump_speed or new_speed < min_pump_speed:
            new_speed = min_pump_speed

        self.adjust_pump_speed(new_speed, mains_relay_status)
        return self.pump_status

    def increase_pump_speed(self, step, mains_relay_status):
        flow_speed = self.pump_status['flow_speed']
        new_speed = flow_speed + step
        if flow_speed > 95 or new_speed > 95:
            new_speed = 100
        self.adjust_pump_speed(new_speed, mains_relay_status)
        return self.pump_status
