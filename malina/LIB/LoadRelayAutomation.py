#!/usr/bin/env python
# V 1.0
# encoding: utf-8

import time

from dotenv import dotenv_values

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

    def load_switch_on(self, device_id):
        try:
            status = self.get_device_statuses_by_id(device_id)['switch_1']
            if not status:
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
            status = self.get_device_statuses_by_id(device_id)['switch_1']
            if status:
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
            status = self.deviceManager.get_device_list_status([device_id])
            device_status = status['result'][0]['status']
            sw_status = {v['code']: v['value'] for v in device_status}
            sw_status.update({'t': int(status['t'] / 1000), 'device_id': device_id})
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
