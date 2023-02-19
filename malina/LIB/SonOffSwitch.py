#!/usr/bin/env python

import time
import random as rnd

from mpmath import rand

import sonoff
import requests
from dotenv import dotenv_values


config = dotenv_values(".env")
ENDPOINT = config['ENDPOINT']
ACCESS_ID = config['ACCESS_ID']
ACCESS_KEY = config['ACCESS_KEY']
BASE_URL = config['API_URL']
USERNAME = config['USERNAME']
PASSWORD = config['PASSWORD']
DEVICE_ID = config['DEVICE_ID']
PUMP_NAME = config['PUMP_NAME']

s = sonoff.Sonoff(config.username, config.password, config.api_region)
devices = s.get_devices()
if devices:
    # We found a device, lets turn something on
    device_id = devices[0]['deviceid']
    s.switch('on', device_id, None)

# update config
config.api_region = s.get_api_region
config.user_apikey = s.get_user_apikey
config.bearer_token = s.get_bearer_token