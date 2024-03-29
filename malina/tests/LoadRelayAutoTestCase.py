import sys
import time
import unittest
from unittest.mock import Mock

sys.path.append('../')

from malina.LIB.TuyaController import TuyaController
from malina.LIB.InitiateDevices import InitiateDevices
from malina.LIB.TuyaAuthorisation import TuyaAuthorisation


class LoadRelayAutoTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.assertEqual(True, True)
        # self.logger = Mock()
        tua_manager = TuyaAuthorisation()
        device_manager = TuyaController(tua_manager)
        dev = InitiateDevices().device_controller
        self.devices  = dev.get_devices()
        extra = dev.get_device_by_id(" ").get_extra('weather')
        min_speed = dev.get_device_by_id(" ").get_extra('min_speed')

        temp = 1

        for i in extra:
            val_tmp = int(extra[i])
            print(i)

            if temp > int(i):
                min_speed = val_tmp
            else:
                min_speed = 20

        print("The min Speed is:", min_speed)

        # device_manager.update_devices_status(self.devices)

        # self.load_automation = LoadRelayAutomation(self.logger, device_manager)
        # self.devices = LoadDevices(Mock(), device_manager)/

    def test_something(self):
        self.assertEqual(True, True)
        # self.assertEqual(True, True)  # add assertion here
        # self.load_automation.switch_on_load('')
        # time.sleep(5)
        # self.load_automation.switch_off_load('')
        # time.sleep(5)
        # inv_id, inv_name = self.devices.get_invert_credentials
        # inv_status = self.load_automation.get_device_statuses_by_id(inv_id, inv_name).get('switch_1')
        #
        # print(self.load_automation.get_device_statuses_by_id(inv_id, inv_name))
        # print(self.load_automation.get_all_statuses)


if __name__ == '__main__':
    unittest.main()
