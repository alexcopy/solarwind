import sys
import time
import unittest
from unittest.mock import Mock

sys.path.append('../')
from malina.LIB.LoadRelayAutomation import LoadRelayAutomation


class LoadRelayAutoTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.logger = Mock()
        self.load_automation = LoadRelayAutomation(self.logger)

    def test_something(self):

        self.assertEqual(True, True)  # add assertion here
        self.load_automation.switch_on_load('9b8ae2c7b4add0e9e8dshh')
        time.sleep(5)
        self.load_automation.switch_off_load('9b8ae2c7b4add0e9e8dshh')

        print(self.load_automation.get_device_statuses)

if __name__ == '__main__':
    unittest.main()
