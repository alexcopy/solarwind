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

        # self.assertEqual(True, True)  # add assertion here
        # self.load_automation.switch_on_load('')
        # time.sleep(5)
        # self.load_automation.switch_off_load('')
        # time.sleep(5)
        print(self.load_automation.get_all_statuses)
        print(self.load_automation.get_device_statuses_by_id(''))


if __name__ == '__main__':
    unittest.main()
