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
MAX_BAT_VOLT = float(config['MAX_BAT_VOLT'])
MIN_BAT_VOLT = float(config['MIN_BAT_VOLT'])
POND_SPEED_STEP = int(config["POND_SPEED_STEP"])


class PondPumpAuto():
    def __init__(self, logger):
        TUYA_LOGGER.setLevel(logging.DEBUG)
        self.logger = logger
        self.openapi = TuyaOpenAPI(ENDPOINT, ACCESS_ID, ACCESS_KEY, AuthType.CUSTOM)
        self.openapi.connect(USERNAME, PASSWORD)
        self.deviceManager = TuyaDeviceManager(self.openapi, TuyaOpenMQ(self.openapi))
        self.pump_status = {'flow_speed': 0}
        self.refresh_pump_status()

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

    def refresh_pump_status(self):
        try:
            device_status = self.deviceManager.get_device_status(DEVICE_ID)
            if device_status['success'] is False:
                self.logger.error(device_status)
                raise Exception(device_status)
            self._update_pump_status(device_status)

        except Exception as ex:
            print(ex)
            self.logger.error(ex)
            return {'flow_speed': 0, "Power": 0, 'error': True}

    def _update_pump_status(self, tuya_responce):
        pump = {}
        pond_pump = tuya_responce['result']
        for k in pond_pump:
            if k['value'] is True:
                k['value'] = 1
            elif k['value'] is False:
                k['value'] = 0

            if k['code'] == 'P':
                k['code'] = 'flow_speed'

            pump.update({k['code']: k['value']})
        pump.update({'name': PUMP_NAME})
        pump.update({'timestamp': time.time()})
        self.pump_status = pump

    def _adjust_pump_speed(self, value: int, is_working_mains: int):
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

        self.refresh_pump_status()
        self.send_pond_stats(is_working_mains)

    def is_minimum_speed(self, min_speed):
        return min_speed == self.get_current_status['flow_speed']

    @property
    def is_max_speed(self):
        return self.pump_status['flow_speed'] == 100

    @property
    def get_current_status(self):
        if self.pump_status['flow_speed'] == 0:
            self.refresh_pump_status()
        return self.pump_status

    def _decrease_pump_speed(self, step, min_pump_speed, mains_relay_status):
        flow_speed = self.pump_status['flow_speed']
        new_speed = flow_speed - step
        if flow_speed == min_pump_speed or new_speed < min_pump_speed:
            new_speed = min_pump_speed

        self._adjust_pump_speed(new_speed, mains_relay_status)
        return self.pump_status

    def _increase_pump_speed(self, step, mains_relay_status):
        flow_speed = self.pump_status['flow_speed']
        new_speed = flow_speed + step
        if flow_speed > 95 or new_speed > 95:
            new_speed = 100
        self._adjust_pump_speed(new_speed, mains_relay_status)
        return self.pump_status

    def pond_pump_adj(self, min_speed, volt_avg, mains_relay_status):
        min_bat_volt = MIN_BAT_VOLT
        max_bat_volt = MAX_BAT_VOLT
        speed_step = POND_SPEED_STEP
        mains_relay_status = int(round(mains_relay_status, 0))
        if mains_relay_status == 1:
            if not self.is_minimum_speed(min_speed):
                return self._decrease_pump_speed(100, min_speed, mains_relay_status)

        if min_bat_volt < volt_avg < max_bat_volt:
            return True

        if volt_avg > max_bat_volt:
            if not self.is_max_speed:
                return self._increase_pump_speed(speed_step, mains_relay_status)

        if self.is_minimum_speed(min_speed):
            return True
        if volt_avg < min_bat_volt:
            return self._decrease_pump_speed(speed_step, min_speed, mains_relay_status)
