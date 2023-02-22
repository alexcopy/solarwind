#!/usr/bin/env python

import requests
import json

from malina.LIB.PrintLogs import SolarLogging
from malina.LIB.FiloFifo import FiloFifo


class SendApiData():
    def __init__(self, logger, api_url):
        self.logger = logger
        self.api_url = api_url
        self.print_logs = SolarLogging(logger)

    def send_to_remote(self, url_path, payload):
        self.print_logs.loger_remote(url_path)
        headers = {
            'Content-Type': 'application/json'
        }
        try:
            response = requests.request("POST", url_path, headers=headers, data=payload)
            return response.text
        except Exception as ex:
            self.logger.error(ex)
            return "error"

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

    def send_ff_data(self, shunt_name: str, filter_flush, tik_time=1):
        payload = json.dumps({
            "max_current": max(filter_flush),
            "duration": len(filter_flush) * tik_time,
            "name": shunt_name
        })
        url_path = "%sfflash" % self.api_url
        self.send_to_remote(url_path, payload)
