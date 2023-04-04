#!/usr/bin/env python

import json
import logging
import time
import requests
from urllib.parse import urljoin
from dotenv import dotenv_values

from malina.LIB.FiloFifo import FiloFifo
from malina.LIB.PrintLogs import SolarLogging
config = dotenv_values(".env")
API_URL = config["API_URL"]

class SendApiData():
    def __init__(self, logger):
        self.logger = logger
        self.api_url = API_URL
        self.print_logs = SolarLogging(logger)

    def send_to_remote(self, url_path, payload):
        self.print_logs.loger_remote(url_path)
        headers = {
            'Content-Type': 'application/json'
        }
        try:
            response = requests.request("POST", url_path, headers=headers, data=payload)
            return response.json()
        except Exception as ex:
            self.logger.error(ex)
            return {'errors': True}

    def send_pump_stats(self, is_working_mains: int, pump_status):
        try:
            pump_status.update({'from_main': is_working_mains})
            payload = json.dumps(pump_status)
            headers = {
                'Content-Type': 'application/json'
            }
            url = urljoin(self.api_url, 'pondpump/')
            response = requests.request("POST", url, headers=headers, data=payload).json()
            if response['errors']:
                self.logger.error(response['payload'])
                self.logger.error(response['errors_msg'])
            return response
        except Exception as ex:
            print(ex)
            self.logger.error(ex)
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

    def send_ff_data(self, shunt_name: str, filter_flush, avg_cc,  tik_time=1):
        payload = json.dumps({
            "max_current": max(filter_flush),
            "current_diff":  avg_cc,
            "duration": len(filter_flush) * tik_time,
            "name": shunt_name
        })
        url_path = "%sfflash" % self.api_url
        resp = self.send_to_remote(url_path, payload)
        erros_resp = resp['errors']

        if erros_resp:
            logging.error(resp)

    def send_load_stats(self, status):
        try:

            payload = json.dumps(status)
            headers = {
                'Content-Type': 'application/json'
            }
            url = urljoin(self.api_url, 'pondswitch/')
            response = requests.request("POST", url, headers=headers, data=payload).json()
            if response['errors']:
                self.logger.error(response['payload'])
                self.logger.error(response['errors_msg'])
            return response
        except Exception as ex:
            print(ex)
            self.logger.error(ex)
            time.sleep(10)
            return {'errors': True}
