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
from SonoffBasic.sonoff import Sonoff

from dotenv import dotenv_values

config = dotenv_values(".env")

SONOFF_USERNAME = config['SONOFF_USERNAME']
SONOFF_PASSWORD = config['SONOFF_PASSWORD']
API_REGION = config['API_REGION']

mock_time = 60


class SonOffSwitchTestCase(unittest.TestCase):
    def setUp(self):
        pass

    # def test_check_connection(self):
    # #     sonoff = Sonoff(username=SONOFF_USERNAME,
    # #                     password=SONOFF_PASSWORD,
    # #
    # #                     region='eu')
    #
    #     # print(sonoff.devices)
    #
    #
    #
    #     data = {
    #         "email": SONOFF_USERNAME,
    #         "password": SONOFF_PASSWORD,
    #         "countryCode": "+1"
    #     }
    #     message = json.dumps(data)
    #     Sign = self.makeSign(key='OdPuCZ4PkPPi0rVKRVcGmll2NM6vVk0c', message=message)
    #     url = "https://cn-apia.coolkit.cn/v2/family"
    #
    #     url = "https://eu-apia.coolkit.cc/v2/user/login"
    #
    #     payload = json.dumps({
    #         "email": SONOFF_USERNAME,
    #         "password": SONOFF_PASSWORD,
    #         "countryCode": "+44"
    #     })
    #     headers = {
    #         'X-CK-Appid': 'xxx',
    #         'X-CK-Nonce': 'SvxkvKTX',
    #         'Authorization': 'Sign %s' % Sign,
    #         'Content-Type': 'application/json'
    #     }
    #
    #     response = requests.request("GET", url, headers=headers, data=payload)
    #
    #     print(response.text)
    #
    #     print(Sign)
    # cE/Wl57Ithy21Elieq5wFsYwJWl2IrkBxlmuCnwI73c=

    # def test_check_connection(self):
    #     from SonoffBasic.sonoff import Sonoff
    #     sonoff = Sonoff(username=SONOFF_USERNAME,
    #                     password=SONOFF_PASSWORD,
    #                     timezone='GMT',
    #                     region='eu')

    # @ewelink.login('password', 'user.address@email.com')
    # async def main(client: Client):
    #     print(client.region)
    #     print(client.user.info)
    #     print(client.devices)
    #
    #     device = client.get_device('10008ecfd9')  # single channel device
    #     device2 = client.get_device('10007fgah9')  # four channel device
    #
    #     print(device.params)
    #     # Raw device specific properties
    #     # can be accessed easily like: device.params.switch or device.params['startup'] (a subclass of dict)
    #
    #     print(device.state)
    #     print(device.created_at)
    #     print("Brand Name:", device.brand.name, "Logo URL:", device.brand.logo.url)
    #     print("Device online?", device.online)
    #
    #     try:
    #         await device.on()
    #     except DeviceOffline:
    #         print("Device is offline!")


if __name__ == '__main__':
    unittest.main()
