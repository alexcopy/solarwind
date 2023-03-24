#!/usr/bin/env python
# V 1.0
# encoding: utf-8

import time

from malina.LIB.SendApiData import SendApiData


class LoadRelayAutomation():
    def __init__(self, logger, device_manager):
        self.logger = logger
        self.deviceManager = device_manager
        self.deviceStatuses = {}
        self.remote_api = SendApiData(logger)
        self.main_status = 0

    def load_switch_on(self, device_id, name):
        try:
            status = self.get_device_statuses_by_id(device_id, name)['switch_1']
            if not status:
                command = [
                    {
                        "code": "switch_1",
                        "value": True
                    }]
                self.deviceManager.send_commands(device_id, command)
                time.sleep(2)
                self.update_status(device_id, name)
                self.remote_api.send_load_stats(self.get_device_statuses_by_id(device_id, name))
        except Exception as ex:
            self.logger.error("---------Problem in Load Switch ON---------")
            self.logger.error(ex)

    def load_switch_off(self, device_id, name):
        try:
            status = self.get_device_statuses_by_id(device_id, name)['switch_1']
            if status:
                command = [
                    {
                        "code": "switch_1",
                        "value": False
                    }]
                self.deviceManager.send_commands(device_id, command)
                time.sleep(2)
                self.update_status(device_id, name)
                self.remote_api.send_load_stats(self.get_device_statuses_by_id(device_id, name))
        except Exception as ex:
            self.logger.error("---------Problem in Load Switch OFF---------")
            self.logger.error(ex)

    def update_status(self, device_id, name):
        try:
            status = self.deviceManager.get_device_list_status([device_id])
            device_status = status['result'][0]['status']
            sw_status = {v['code']: v['value'] for v in device_status}
            extra_params = {'name': name, 'from_main': self.get_main_relay_status,
                            'status': int(sw_status['switch_1']), 't': int(status['t'] / 1000), 'device_id': device_id}
            sw_status.update(extra_params)
            self.deviceStatuses.update({device_id: sw_status})

        except Exception as ex:
            self.logger.error("---------Problem in update_status---------")
            self.logger.error(self.get_all_statuses)
            self.logger.error(ex)

    def update_main_relay_status(self, main_status: int):
        self.main_status = main_status

    @property
    def get_main_relay_status(self):
        return self.main_status

    @property
    def get_all_statuses(self):
        return self.deviceStatuses

    def get_device_statuses_by_id(self, device_id, name):
        if device_id not in self.deviceStatuses:
            self.update_status(device_id, name)
        return self.deviceStatuses[device_id]
