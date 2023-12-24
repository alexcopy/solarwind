#!/usr/bin/env python
import sys
import unittest
from io import StringIO
from unittest.mock import patch

sys.path.append('../')
from malina.LIB.PowerDeviceManager import PowerDeviceManager
mock_time = 60


class TestPowerDeviceManager(unittest.TestCase):
    def setUp(self):
        self.manager = PowerDeviceManager([])
        self.manager.add_device("Device1")
        self.manager.add_device("Device2")
        self.manager.add_device("Device3")
        self.manager.add_device("TestMean")
        self.manager.devices[0].daily_power_buffer = [10, 20, 30]
        self.manager.devices[1].daily_power_buffer = [15, 25, 35]
        self.manager.devices[2].daily_power_buffer = [5, 15, 25]
        self.manager.devices[3].daily_power_buffer = [10, 20, 30]
        self.manager.devices[3].hourly_power_buffer = [15, 25, 35]
        self.manager.devices[3].ten_minute_buffer = [5, 15, 25]
        self.test_device = self.manager.find_device_by_name("TestMean")[0]

    def test_find_device_by_name(self):
        devices = self.manager.find_device_by_name("Device1")
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].name, "Device1")

        devices = self.manager.find_device_by_name("Device4")
        self.assertEqual(len(devices), 0)

    def test_sort_devices_by_power(self):
        self.manager.remove_device_by_name("TestMean")
        sorted_devices = self.manager.sort_devices_by_power()
        self.assertEqual(sorted_devices[0].name, "Device2")  # Device2 имеет наибольшую мощность
        self.assertEqual(sorted_devices[1].name, "Device1")
        self.assertEqual(sorted_devices[2].name, "Device3")

    def test_display_all_devices(self):
        self.manager.remove_device_by_name("TestMean")
        with patch('sys.stdout', new=StringIO()) as fake_output:
            self.manager.display_all_devices()
            expected_output = "All Devices:\n1. Name: Device2, Mean Power: 25.0 kW\n2. Name: Device1, Mean Power: 20.0 kW\n3. Name: Device3, Mean Power: 15.0 kW\n"
            self.assertEqual(fake_output.getvalue(), expected_output)

    def test_get_mean_total(self):
        self.assertEqual(self.test_device.get_mean_total(), 20.0)

        self.test_device.daily_power_buffer = []  # Проверка с пустым суточным буфером
        self.assertEqual(self.test_device.get_mean_total(), 20.0)

        self.test_device.hourly_power_buffer = []  # Проверка с пустым часовым буфером
        self.assertEqual(self.test_device.get_mean_total(), 15.0)

        self.test_device.ten_minute_buffer = []  # Проверка с пустым буфером за 10 минут
        self.assertEqual(self.test_device.get_mean_total(), 0)

    def test_get_mean_hourly(self):
        self.assertEqual(self.test_device.get_sum_hourly(), 25.0)

        self.test_device.hourly_power_buffer = []  # Проверка с пустым часовым буфером
        self.assertEqual(self.test_device.get_sum_hourly(), 0)

    def test_get_mean_minutes(self):
        self.assertEqual(self.test_device.get_mean_minutes(), 15.0)

        self.test_device.ten_minute_buffer = []  # Проверка с пустым буфером за 10 минут
        self.assertEqual(self.test_device.get_mean_minutes(), 0)

    def test_remove_device_by_name(self):
        self.manager.remove_device_by_name("Device2")
        self.assertEqual(len(self.manager.devices), 3)  # Проверка, что устройство было удалено
        self.assertNotIn("Device2", [device.name for device in self.manager.devices])

        self.manager.remove_device_by_name("Device4")  # Проверка, что удаление не происходит при отсутствии устройства
        self.assertEqual(len(self.manager.devices), 3)

    def test_add_power_value_existing_device(self):
        self.manager.add_device("Device10")
        self.manager.update_ten_min_power_value("Device10", 10)
        self.assertEqual(self.manager.devices[0].ten_minute_buffer, [10])

    def test_add_power_value_nonexistent_device(self):
        result = self.manager.update_ten_min_power_value("Device30", 20)
        self.assertFalse(result)  # Ensure False is returned for a non-existing device

    def test_add_power_value_multiple_devices(self):
        self.manager.add_device("Device10")
        self.manager.add_device("Device20")
        self.manager.update_ten_min_power_value("Device10", 15)
        self.manager.update_ten_min_power_value("Device20", 25)
        self.assertEqual(self.manager.devices[0].ten_minute_buffer, [10, 15])
        self.assertEqual(self.manager.devices[1].ten_minute_buffer, [25])

if __name__ == '__main__':
    unittest.main()
