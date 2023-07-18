import os
import sys
import unittest
import yaml

sys.path.append('../')

from malina.LIB.DeviceManager import DeviceManager
from malina.LIB.Device import Device


class InitiateDevicesTestCase(unittest.TestCase):

    def setUp(self):
        self.device_manager = DeviceManager()

    def test_sort_devices_by_priority(self):
        with open('device_example.yaml') as f:
            devices = yaml.safe_load(f)
        for device_config in devices:
            device = Device(**device_config)
            self.device_manager.add_device(device)

        self.device_manager.sort_devices_by_priority()
        sorted_devices = self.device_manager.get_devices()
        expected_order = ['3', '2', '1']
        self.assertEqual([device.id for device in sorted_devices], expected_order)

    def test_read_device_configs(self):
        # Create a YAML file with device configurations
        dir_path = os.path.dirname(os.path.realpath(__file__))  # get current working directory
        device_configs = [
            {"id": "1", "status": {"on": False}, "min_volt": 110, "max_volt": 220,
             "priority": 1, 'api_sw': "switch_1",  'extra': {},
             "name": "Light bulb", "desc": "Light bulb", "device_type": "light", "coefficient": 0.8},

            {"id": "2", "type": "fan", "status": {"on": True}, "min_volt": 110, "max_volt": 220, "priority": 2,
             "name": "Ceiling fan", 'api_sw': "switch_1",  'extra': {}, "desc": "Ceiling fan", "device_type": "fan",
             "coefficient": 1.2},

            {"id": "3", "type": "oven", "status": {"on": True}, "min_volt": 220, "max_volt": 240, "priority": 3,
             "name": "Electric oven", "desc": "Electric oven", 'api_sw': "switch_1",  'extra': {}, "device_type": "oven",
             "coefficient": 2.5}
        ]
        config_file_path = os.path.join(dir_path, 'test_device_configs.yaml')
        with open(config_file_path, 'w') as f:
            yaml.dump(device_configs, f)

        # Read device configurations from the YAML file
        self.device_manager.read_device_configs(dir_path)

        # Check that the devices were added to the device manager
        self.assertEqual(len(self.device_manager.get_devices()), 3)

        # Check the details of each device
        device_1 = self.device_manager.get_device_by_id("1")
        self.assertEqual(device_1.device_type, "light")
        self.assertEqual(device_1.status, {"on": False})
        self.assertEqual(device_1.min_volt, 110)
        self.assertEqual(device_1.max_volt, 220)
        self.assertEqual(device_1.priority, 1)
        self.assertEqual(device_1.name, "Light bulb")
        self.assertEqual(device_1.desc, "Light bulb")
        self.assertEqual(device_1.coefficient, 0.8)

        device_2 = self.device_manager.get_device_by_id("2")
        self.assertEqual(device_2.device_type, "fan")
        self.assertEqual(device_2.status, {"on": True})
        self.assertEqual(device_2.min_volt, 110)
        self.assertEqual(device_2.max_volt, 220)
        self.assertEqual(device_2.priority, 2)
        self.assertEqual(device_2.name, "Ceiling fan")
        self.assertEqual(device_2.desc, "Ceiling fan")
        self.assertEqual(device_2.coefficient, 1.2)

        device_3 = self.device_manager.get_device_by_id("3")
        self.assertEqual(device_3.device_type, "oven")
        self.assertEqual(device_3.status, {"on": True})
        self.assertEqual(device_3.min_volt, 220)
        self.assertEqual(device_3.max_volt, 240)
        self.assertEqual(device_3.priority, 3)
        self.assertEqual(device_3.name, "Electric oven")
        self.assertEqual(device_3.desc, "Electric oven")
        self.assertEqual(device_3.coefficient, 2.5)

        # Remove the test YAML file
        os.remove(config_file_path)


if __name__ == '__main__':
    unittest.main()
