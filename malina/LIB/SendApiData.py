#!/usr/bin/env python

import json
import logging
import time
from urllib.parse import urljoin

import requests
import copy
from dotenv import dotenv_values

from malina.LIB.Device import Device
from malina.LIB import FiloFifo
from malina.LIB.PrintLogs import SolarLogging

config = dotenv_values(".env")
API_URL = config["API_URL"]


class SendApiData():
    def __init__(self):
        self.api_url = API_URL
        self.print_logs = SolarLogging()
        self.fifo = FiloFifo.FiloFifo()

    @staticmethod
    def avg(l):
        if len(l) == 0:
            return 0
        return float(round(sum(l, 0.0) / len(l), 2))

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

    def send_pump_stats(self, device: Device, inv_status):
        pump_status = device.get_status()
        try:
            pump_status.update({
                "description": device.get_desc,
                'name': device.get_name(),
                'flow_speed': device.get_status('P'),
                'from_main': not inv_status
            })
            logging.debug(f"Debugging:{json.dumps(pump_status)}")
            payload = json.dumps(pump_status)

            headers = {
                'Content-Type': 'application/json'
            }
            url = urljoin(self.api_url, 'pondpump/')
            logging.debug(f"Debugging URL :{url}")
            response = requests.request("POST", url, headers=headers, data=payload).json()
            if response['errors']:
                logging.error(response['payload'])
                logging.error(response['errors_msg'])
            return response
        except Exception as ex:
            logging.error(f"Getting error in send_pump_stats to remote API data {json.dumps(pump_status)}")
            logging.error(ex)
            time.sleep(10)
            return {'errors': True}

    def send_avg_data(self, inverter_status):
        buff = copy.deepcopy(self.fifo.filo_buff)
        logging.error(f"Debugging: Sending FIFO data to remote API data {json.dumps(buff)}")
        logging.error("\n\n\n\n")
        for v in buff:
            logging.error(f" The Param is: {v}")
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
                "avg_value": self.avg(buff[v]),
                "serialized": buff[v],
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

    def _send_switch_stats(self, device: Device, inv_status, api_path='pondswitch/'):
        status = device.get_status()
        try:
            status.update({
                "description": device.get_desc,
                "relay_status": int(device.get_status('switch_1')),
                'from_main': not inv_status
            })

            payload = json.dumps(status)
            headers = {
                'Content-Type': 'application/json'
            }
            url = urljoin(self.api_url, api_path)
            logging.debug(f"Debugging URL: {url}")
            logging.debug(f"Debugging json: {json.dumps(status)}")
            response = requests.request("POST", url, headers=headers, data=payload).json()
            if response['errors']:
                logging.error(response['payload'])
                logging.error(response['errors_msg'])
            return response
        except Exception as ex:
            logging.error(f"Getting error in _send_switch_stats  to remote API data: {json.dumps(status)}")
            logging.error(ex)
            time.sleep(10)
            return {'errors': True}

    def send_load_stats(self, device, inv_status):
        if device.get_device_type == "SWITCH":
            self._send_switch_stats(device, inv_status)
        elif device.get_device_type == "PUMP":
            self.send_pump_stats(device, inv_status)

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
