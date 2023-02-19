#!/usr/bin/env python
import sys
import unittest
import random as rnd
from freezegun import freeze_time

sys.path.append('../')
import malina.LIB.FiloFifo as FF
import malina.LIB.PrintLogs as SolarLogging
from mock import Mock
from dotenv import dotenv_values
import sonoff

config = dotenv_values(".env")

SONOFF_USERNAME = "redcopy@mail.ru"
SONOFF_PASSWORD = "Odessa01##"
API_REGION = "eu"
# SONOFF_USERNAME = config['SONOFF_USERNAME']
# SONOFF_PASSWORD = config['SONOFF_PASSWORD']
# API_REGION = config['API_REGION']
# import ewelink
# from ewelink import Client, DeviceOffline

mock_time = 60


class SonOffSwitchTestCase(unittest.TestCase):
    def setUp(self):
        pass

    # def test_check_connection(self):


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
