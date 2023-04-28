import sys
import time
from unittest.mock import MagicMock

sys.path.append('../')

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from malina.LIB.TuyaController import TuyaController
from tuya_iot import TuyaDevice


class TestTuyaController(unittest.TestCase):

    def setUp(self):
        self.mock_device1 = MagicMock(spec=TuyaDevice)
        self.mock_device2 = MagicMock(spec=TuyaDevice)
        self.mock_device3 = MagicMock(spec=TuyaDevice)

        self.mock_device1.device_id = "1"
        self.mock_device1.name = "Device 1"
        self.mock_device2.device_id = "2"
        self.mock_device2.name = "Device 2"
        self.mock_device3.device_id = "3"
        self.mock_device3.name = "Device 3"

        self.mock_device1.get_status.return_value = "Off"
        self.mock_device2.get_status.return_value = "On"
        self.mock_device3.get_status.return_value = "Off"

        self.mock_device1.last_toggle_time = datetime.now() - timedelta(seconds=400)
        self.mock_device2.last_toggle_time = datetime.now() - timedelta(seconds=200)
        self.mock_device3.last_toggle_time = datetime.now() - timedelta(seconds=100)

        self.mock_device_manager = MagicMock()
        self.mock_device_manager.devices = [self.mock_device1, self.mock_device2, self.mock_device3]

        self.mock_tuya_authorisation = MagicMock()
        self.mock_tuya_authorisation.device_manager = self.mock_device_manager

        self.controller = TuyaController(self.mock_tuya_authorisation)

    def test_is_device_ready_to_switch_on(self):
        result = self.controller.is_device_ready_to_switch_on(self.mock_device1)
        self.assertTrue(result)

        result = self.controller.is_device_ready_to_switch_on(self.mock_device2)
        self.assertFalse(result)

        result = self.controller.is_device_ready_to_switch_on(self.mock_device3)
        self.assertTrue(result)

    def test_is_device_ready_to_switch_off(self):
        result = self.controller.is_device_ready_to_switch_off(self.mock_device1)
        self.assertFalse(result)

        result = self.controller.is_device_ready_to_switch_off(self.mock_device2)
        self.assertTrue(result)

        result = self.controller.is_device_ready_to_switch_off(self.mock_device3)
        self.assertTrue(result)

    @patch('tuya_controller.sleep')
    def test_switch_on_device(self, mock_sleep):
        self.controller.switch_on_device(self.mock_device1)
        self.mock_device1.switch_on.assert_called_once_with()
        self.assertEqual(self.mock_device1.last_toggle_time, datetime.now())
        mock_sleep.assert_called_once_with(300)

    @patch('tuya_controller.sleep')
    def test_switch_off_device(self, mock_sleep):
        self.controller.switch_off_device(self.mock_device2)
        self.mock_device2.switch_off.assert_called_once_with()
        self.assertEqual(self.mock_device2.last_toggle_time, datetime.now())
        mock_sleep.assert_called_once_with(300)

    def test_switch_on_all_devices(self):
        self.controller.switch_on_all_devices()
        self.mock_device1.switch_on.assert_called_once_with()
        self.mock_device2.switch_on.assert_not_called()
        self.mock_device3.switch_on.assert_called_once_with()

    def test_switch_off_all_devices(self):
        self.controller.switch_off_all_devices()
        self.mock_device1.switch_off.assert_not_called()
        self.mock_device2.switch_off.assert_called_once_with()
        self.mock_device3.switch_off.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
