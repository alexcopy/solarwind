import sys
import unittest
from unittest.mock import Mock

sys.path.append('../')
from malina.LIB.LoadRelayAutomation import LoadRelayAutomation


class LoadRelayAutoTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.logger = Mock()
        self.load_Automation = LoadRelayAutomation(self.logger)

    def test_something(self):
        self.assertEqual(True, True)  # add assertion here


if __name__ == '__main__':
    unittest.main()
