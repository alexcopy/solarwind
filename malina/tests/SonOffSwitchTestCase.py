#!/usr/bin/env python
import sys
import time
import unittest
import hashlib
import hmac
import base64
import json
from unittest.mock import Mock

import requests
import python_weather
import asyncio
import os

from malina.LIB.InitiateDevices import InitiateDevices
from malina.LIB.TuyaController import TuyaController

sys.path.append('../')
from malina.LIB.TuyaAuthorisation import TuyaAuthorisation


from dotenv import dotenv_values



mock_time = 60


class SonOffSwitchTestCase(unittest.TestCase):
    def test_valid_structure_without_values(self):
        tuya_auth = TuyaAuthorisation(Mock())
        tuya_controller = TuyaController(tuya_auth)
        devices = InitiateDevices(Mock()).devices


        fontan = devices.get_devices_by_name("inverter")[0] # fontan
        print("-------------------------STATUS_______________")
        print(fontan.get_status())
        tuya_controller.switch_off_device(fontan)
        time.sleep(2)
        tuya_controller.update_status(fontan)
        print("-------------------------STATUS____ON___________")
        print(fontan.get_status())
        print("-------------------------STATUS_______________")
        time.sleep(5)
        tuya_controller.switch_on_device(fontan)
        print("-------------------------STATUS OFF_______________")
        time.sleep(5)
        tuya_controller.update_status(fontan)

        print("-------------------------STATUS_______________")
        print(fontan.get_status())
        print("-----------------Single Status--------STATUS_______________")
        print(fontan.get_status('status'))

if __name__ == '__main__':
    unittest.main()
