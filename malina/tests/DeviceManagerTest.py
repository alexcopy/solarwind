import sys
import unittest

sys.path.append('../')

from malina.LIB.DeviceManager import DeviceManager
from malina.LIB.Device import Device


class DeviceManagerTest(unittest.TestCase):

    def setUp(self):
        self.device_1 = Device(id="1", device_type="light", status={"on": False}, min_volt=220, max_volt=240,
                               priority=2, name="Light bulb", coefficient=0.8)
        self.device_2 = Device(id="2", device_type="fan", status={"on": True}, min_volt=110, max_volt=220, priority=1,
                               name="Ceiling fan", coefficient=1.2)

        self.device_manager = DeviceManager()

    def test_add_device(self):
        self.device_manager.add_device(self.device_1)
        self.assertEqual(len(self.device_manager.get_devices()), 1)
        self.assertEqual(self.device_manager.get_device_by_id("1"), self.device_1)

    def test_add_duplicate_device(self):
        self.device_manager.add_device(self.device_1)
        with self.assertRaises(ValueError):
            self.device_manager.add_device(self.device_1)

    def test_remove_device(self):
        self.device_manager.add_device(self.device_1)
        self.device_manager.add_device(self.device_2)
        self.device_manager.remove_device(self.device_1)
        devices = self.device_manager.get_devices()
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0], self.device_2)

    def test_remove_nonexistent_device(self):
        with self.assertRaises(ValueError):
            self.device_manager.remove_device(self.device_1)

    def test_get_device_by_id(self):
        self.device_manager.add_device(self.device_1)
        self.device_manager.add_device(self.device_2)
        self.assertEqual(self.device_manager.get_device_by_id("1"), self.device_1)
        self.assertEqual(self.device_manager.get_device_by_id("2"), self.device_2)

    def test_get_device_by_nonexistent_id(self):
        with self.assertRaises(ValueError):
            self.device_manager.get_device_by_id("3")

    def test_update_device_status(self):
        self.device_manager.add_device(self.device_1)
        device_id = "1"
        status = {"on": True, "mode": "auto"}
        self.device_manager.update_device_status(device_id, status)
        device = self.device_manager.get_device_by_id(device_id)
        self.assertEqual(device.get_status(), status)

    def test_device_switch_on(self):
        self.device_manager.add_device(self.device_1)
        self.device_manager.device_switch_on("1")
        device = self.device_manager.get_device_by_id("1")
        self.assertTrue(device.get_status("on"))

    def test_device_switch_off(self):
        self.device_manager.add_device(self.device_2)
        self.device_manager.device_switch_off("2")
        device = self.device_manager.get_device_by_id("2")
        self.assertFalse(device.get_status("on"))

    def test_get_devices_by_name(self):
        self.device_manager.add_device(self.device_1)
        self.device_manager.add_device(self.device_2)
        devices = self.device_manager.get_devices_by_name("Light bulb")
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0], self.device_1)

    def test_get_devices_by_nonexistent_name(self):
        self.device_manager.add_device(self.device_1)
        self.device_manager.add_device(self.device_2)
        devices = self.device_manager.get_devices_by_name("tv")
        self.assertEqual(len(devices), 0)

    def test_sort_devices_by_priority(self):
        self.device_manager.add_device(self.device_1)
        self.device_manager.add_device(self.device_2)
        self.device_manager.sort_devices_by_priority()
        devices = self.device_manager.get_devices()
        self.assertEqual(devices, [self.device_2, self.device_1])

    def test_get_available_power(self):
        self.device_manager.add_device(self.device_1)
        self.assertEqual(self.device_manager.get_available_power(), 9984.0)
        # Add a high power device and check if available power is updated
        device_3 = Device(id="3", device_type="oven", status={"on": True}, min_volt=220, max_volt=240, priority=1,
                          name="Electric oven", coefficient=2.5)
        self.device_manager.add_device(device_3)
        self.assertEqual(self.device_manager.get_available_power(), 9934)
        # Remove a device and check if available power is updated
        self.device_manager.remove_device(self.device_1)
        self.assertEqual(self.device_manager.get_available_power(), 9950)


if __name__ == '__main__':
    unittest.main()
