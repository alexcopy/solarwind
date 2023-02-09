import logging
from dotenv import dotenv_values

from tuya_iot import (
    TuyaOpenAPI,
    AuthType,
    TuyaOpenMQ,
    TuyaDeviceManager,
    TuyaHomeManager,
    TuyaDeviceListener,
    TuyaDevice,
    TuyaTokenInfo,
    TUYA_LOGGER
)

TUYA_LOGGER.setLevel(logging.DEBUG)
config = dotenv_values(".env")

ENDPOINT = config['ENDPOINT']

ACCESS_ID = config['ACCESS_ID']
ACCESS_KEY = config['ACCESS_KEY']

# Select an endpoint base on your project availability zone


# Project configuration
USERNAME = config['USERNAME']
PASSWORD = config['PASSWORD']

DEVICE_ID = config['DEVICE_ID']

# Init
openapi = TuyaOpenAPI(ENDPOINT, ACCESS_ID, ACCESS_KEY, AuthType.CUSTOM)

openapi.connect(USERNAME, PASSWORD)
openmq = TuyaOpenMQ(openapi)
# openmq.start()

# print("device test-> ", openapi.token_info.uid)
# Get device list
# assetManager = TuyaAssetManager(openapi)
# devIds = assetManager.getDeviceList(ASSET_ID)


# Update device status
deviceManager = TuyaDeviceManager(openapi, openmq)

# homeManager = TuyaHomeManager(openapi, openmq, deviceManager)
# homeManager.update_device_cache()


# # deviceManager.updateDeviceCaches(devIds)
# device = deviceManager.deviceMap.get(DEVICE_ID)


# class tuyaDeviceListener(TuyaDeviceListener):
#     def update_device(self, device: TuyaDevice):
#         print("_update-->", '')
#
#     # def add_device(self, device: TuyaDevice):
#     #     print("_add-->", device)
#     #
#     # def remove_device(self, device_id: str):
#     #     pass
#
#
# # deviceManager.add_device_listener(tuyaDeviceListener())
#
# print('status: ', deviceManager.get_device_status(DEVICE_ID))

# Turn on the light
# deviceManager.sendCommands(device.id, [{'code': 'switch_led', 'value': True}])
# time.sleep(1)
# print('status: ', device.status)

# # Turn off the light
# deviceManager.sendCommands(device.id, [{'code': 'switch_led', 'value': False}])
# time.sleep(1)
# print('status: ', device.status)

command = [
    {
        "code": "P",
        "value": 120
    }
]
res = deviceManager.send_commands(DEVICE_ID, command)

print(res)



# flag = True
# while True:
#     input()
#     flag = not flag
#     commands = {'commands': [{'code': 'switch_led', 'value': flag}]}
#     openapi.post('/v1.0/iot-03/devices/{}/commands'.format(DEVICE_ID), commands)
