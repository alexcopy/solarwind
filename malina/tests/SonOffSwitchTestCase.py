#!/usr/bin/env python
import sys
import time
import unittest
import hashlib
import hmac
import base64
import json
import logging
from unittest.mock import Mock
from tuya_iot import (
    TuyaOpenAPI,
    AuthType,
    TuyaOpenMQ,
    TuyaDeviceManager,
    TUYA_LOGGER, TuyaCloudOpenAPIEndpoint
)
# from tuya_connector import (
# 	TuyaOpenAPI,
# 	TuyaOpenPulsar,
# 	TuyaCloudPulsarTopic,
# )

import requests
import python_weather
import asyncio
import os

sys.path.append('../')

from malina.LIB.InitiateDevices import InitiateDevices
from malina.LIB.TuyaController import TuyaController

from malina.LIB.TuyaAuthorisation import TuyaAuthorisation

from dotenv import dotenv_values

ACCESS_ID = "vwny7twaucf3qx8ec39n"
ACCESS_KEY = "7758cc1c3a064802ab3b505870c2c8a2"
ENDPOINT = TuyaCloudOpenAPIEndpoint.EUROPE



TUYA_LOGGER.setLevel(logging.DEBUG)
openapi = TuyaOpenAPI(ENDPOINT, ACCESS_ID, ACCESS_KEY)
openapi.connect()
openapi.auth_type = AuthType.SMART_HOME
deviceManager = TuyaDeviceManager(openapi, TuyaOpenMQ(openapi))
print(deviceManager.get_device_status("bf8a065d2b72c26f0breco"))


