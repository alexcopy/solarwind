#!/usr/bin/env python

import json
import logging
import time
from urllib.parse import urljoin

import requests
from dotenv import dotenv_values

from malina.LIB.Device import Device
from malina.LIB.InitiateDevices import InitiateDevices
from malina.LIB.FiloFifo import FiloFifo
from malina.LIB.PrintLogs import SolarLogging

config = dotenv_values(".env")
API_URL = config["API_URL"]


class SendApiData():
    def __init__(self):
        self.device_manager = InitiateDevices().device_controller
        self.api_url = API_URL
        self.print_logs = SolarLogging()

    def send_to_remote(self, url_path, payload):
        SolarLogging().loger_remote(url_path)
        headers = {
            'Content-Type': 'application/json'
        }
        try:
            response = requests.request("POST", url_path, headers=headers, data=payload)
            return response.json()
        except Exception as ex:
            logging.error("Getting error in sending to remote API data ")
            logging.error(ex)
            return {'errors': True}

    def send_pump_stats(self, device: Device):
        try:
            pump_status = device.get_status()
            is_working_mains = self.device_manager.get_devices_by_name("inverter")[0].get_status('switch_1')
            pump_status.update({"description": pump_status.get("desc"), 'from_main': is_working_mains})
            payload = json.dumps(pump_status)
            headers = {
                'Content-Type': 'application/json'
            }
            url = urljoin(self.api_url, 'pondpump/')
            response = requests.request("POST", url, headers=headers, data=payload).json()
            if response['errors']:
                logging.error(response['payload'])
                logging.error(response['errors_msg'])
            return response
        except Exception as ex:
            logging.error("Getting error in send_pump_stats to remote API data ")
            print(ex)
            logging.error(ex)
            time.sleep(10)
            return {'errors': True}

    def send_avg_data(self, filo_fifo: FiloFifo, inverter_status):

        for v in filo_fifo.filo_buff:
            if not '1h' in v:
                continue
            val_type = "V"
            if 'current' in v:
                val_type = "A"

            if 'wattage' in v:
                val_type = "W"

            payload = json.dumps({
                "value_type": val_type,
                "name": v,
                "inverter_status": inverter_status,
                "avg_value": FiloFifo.avg(filo_fifo.filo_buff[v]),
                "serialized": filo_fifo.filo_buff[v],
            })
            url_path = "%ssolarpower" % self.api_url
            self.send_to_remote(url_path, payload)

    def send_ff_data(self, shunt_name: str, filter_flush, avg_cc, tik_time=1):
        payload = json.dumps({
            "max_current": max(filter_flush),
            "current_diff": avg_cc,
            "duration": len(filter_flush) * tik_time,
            "name": shunt_name
        })
        url_path = "%sfflash" % self.api_url
        resp = self.send_to_remote(url_path, payload)
        erros_resp = resp['errors']

        if erros_resp:
            logging.error(resp)

    def _send_switch_stats(self, device, api_path='pondswitch/'):
        try:
            status = device.get_status()
            status.update({"description": status.get("desc")})
            payload = json.dumps(status)
            headers = {
                'Content-Type': 'application/json'
            }
            url = urljoin(self.api_url, api_path)
            response = requests.request("POST", url, headers=headers, data=payload).json()
            if response['errors']:
                logging.error(response['payload'])
                logging.error(response['errors_msg'])
            return response
        except Exception as ex:
            logging.error("Getting error in send_load_stats to remote API data ")
            print(ex)
            logging.error(ex)
            time.sleep(10)
            return {'errors': True}

    def send_load_stats(self, device):
        if device.get_device_type == "SWITCH":
            self._send_switch_stats(device)
        elif device.get_device_type == "PUMP":
            self.send_pump_stats(device)

    def send_weather(self, local_weather):
        try:
            payload = json.dumps(local_weather)
            headers = {
                'Content-Type': 'application/json'
            }
            url = urljoin(self.api_url, 'pondweather/')
            response = requests.request("POST", url, headers=headers, data=payload).json()
            if response['errors']:
                logging.error(response['payload'])
                logging.error(response['errors_msg'])
            return response
        except Exception as ex:
            logging.error("Getting error in send_weather to remote API data ")
            print(ex)
            logging.error(ex)
            time.sleep(10)
            return {'errors': True}
