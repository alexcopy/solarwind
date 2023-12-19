#!/usr/bin/env python

import json
import logging
import time
from urllib.parse import urljoin
import concurrent.futures
import requests
from dotenv import dotenv_values
from malina.LIB.Device import Device

config = dotenv_values(".env")
API_URL = config["API_URL"]
MAX_WORKERS = 10


class SendApiData():
    def __init__(self):
        self.api_url = API_URL

    @staticmethod
    def avg(l):
        if len(l) == 0:
            return 0
        return float(round(sum(l, 0.0) / len(l), 2))

    @staticmethod
    def _to_remote(url_path, payload):
        if payload is None:
            logging.error("Payload is None, skipping...")
            return None

        logging.info("------------SENDING TO REMOTE--------------")
        logging.info(url_path)
        logging.info("--------------------------------------------")
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

    def send_to_remote(self, url_path, payloads):
        if payloads is None:
            logging.error("Payloads is None, exiting...")
            return

        url_path = url_path % self.api_url
        with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(self._to_remote, url_path, payload) for payload in payloads]

            for future, payload in zip(concurrent.futures.as_completed(futures), payloads):
                try:
                    result = future.result()
                    logging.error(f"The result for payload {payload} is: {result}")
                except Exception as ex:
                    logging.error(f"Getting error in sending to remote API data for payload {payload}")
                    logging.error(ex)

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

    def send_ff_data(self, shunt_name: str, filter_flush, avg_cc, tik_time=1):
        payload = json.dumps({
            "max_current": max(filter_flush),
            "current_diff": avg_cc,
            "duration": len(filter_flush) * tik_time,
            "name": shunt_name
        })
        self.send_to_remote("%sfflash", [payload])

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

    def send_hourly_daily_averages_to_server(self, power_device, send_type):
        try:
            average_data = None
            if send_type == 'hourly':
                payload = json.dumps({
                    'name': power_device.name,
                    'type': 'hourly',
                    'average': power_device.get_mean_hourly()
                })
            elif send_type == 'daily':
                payload = json.dumps({
                    'name': power_device.name,
                    'type': 'daily',
                    'average': power_device.get_daily_energy()
                })
            else:
                logging.warning("Invalid send_type provided")
                return {'errors': True, 'message': 'Invalid send_type provided'}

            headers = {
                'Content-Type': 'application/json'
            }
            url = urljoin(self.api_url, 'power_averages/')
            response = requests.post(url, headers=headers, data=payload)

            if response.status_code == 200:
                data = response.json()
                if data.get('errors'):
                    logging.error(data.get('payload'))
                    logging.error(data.get('errors_msg'))
                return data
            else:
                logging.error(f"Failed to send averages. Status code: {response.status_code}")
                return {'errors': True, 'message': 'Failed to send data'}

        except Exception as ex:
            logging.exception("Getting error in send_hourly_daily_averages_to_server")
            return {'errors': True, 'message': str(ex)}

    def send_weather(self, local_weather):
        try:
            payload = json.dumps(local_weather)
            headers = {'Content-Type': 'application/json'}
            url = urljoin(self.api_url, 'pondweather/')
            response = requests.post(url, headers=headers, data=payload).json()
            if response.get('errors'):
                logging.error(response.get('payload'))
                logging.error(response.get('errors_msg'))
            return response

        except requests.RequestException as req_ex:
            logging.error(f"RequestException in send_weather to remote API data: {req_ex}")
            time.sleep(10)
            return {'errors': True, 'message': str(req_ex)}

        except json.JSONDecodeError as json_ex:
            logging.error(f"JSONDecodeError in send_weather: {json_ex}")
            return {'errors': True, 'message': str(json_ex)}

        except Exception as ex:
            logging.exception("Getting error in send_weather to remote API data")
            return {'errors': True, 'message': str(ex)}
