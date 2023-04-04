#!/usr/bin/env python
import sys
import unittest
import hashlib
import hmac
import base64
import json
import requests
import python_weather
import asyncio
import os

sys.path.append('../')


from dotenv import dotenv_values

config = dotenv_values(".env")

SONOFF_USERNAME = config['SONOFF_USERNAME']
SONOFF_PASSWORD = config['SONOFF_PASSWORD']
API_REGION = config['API_REGION']

mock_time = 60


class SonOffSwitchTestCase(unittest.TestCase):
    def setUp(self):
        pass




if __name__ == '__main__':
    unittest.main()
