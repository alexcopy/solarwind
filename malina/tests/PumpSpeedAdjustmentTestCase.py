import sys
import unittest

sys.path.append('../')
from malina.LIB.Device import Device
from malina.LIB.PondPumpAuto import PondPumpAuto


class PumpSpeedAdjustmentTestCase(unittest.TestCase):
    def test_setup_minimum_pump_speed(self):
        # Assuming YourClass has a setup_minimum_pump_speed method
        pond_pump_auto = PondPumpAuto()

        # Setting up a dummy Device with weather conditions
        pump_device = Device(
            id=1,
            device_type='your_device_type',
            status={'P': 20},
            name='Device_Name',
            desc='Description',
            api_sw='http:',
            coefficient=1.0,
            min_volt=10.0,
            max_volt=20.0,
            priority=1,
            bus_voltage=15.0,
            extra={
                'min_speed': 20,
                'weather_town': "New York",
                'weather': {
                    -40: 0,
                    -4: 0,
                    -2: 0,
                    -1: 5,
                    0: 5,
                    5: 10,
                    10: 10,
                    12: 20,
                    15: 30,
                    20: 40,
                    25: 40,
                    50: 40
                }}
        )
        #
        # # Setting up dummy weather in pond_pump_auto
        pond_pump_auto.weather = {'is_valid': True, 'temperature': 15}
        # Test 1: Check if the setup_minimum_pump_speed returns the expected value
        result = pond_pump_auto.setup_minimum_pump_speed(pump_device)
        self.assertEqual(result, 30)

        # Test 2: Check if the method returns the default min_speed when weather is not valid
        pond_pump_auto.weather['is_valid'] = False
        result = pond_pump_auto.setup_minimum_pump_speed(pump_device)
        self.assertEqual(result, 20)

        # Test 3: Check if the method returns the default min_speed when an exception occurs

        pond_pump_auto.weather = {'is_valid': True, 'temperature': 16}
        pump_device.update_status({'P': 25})
        result = pond_pump_auto.setup_minimum_pump_speed(pump_device)
        self.assertEqual(result, 30)

        pond_pump_auto.weather = {'is_valid': True, 'temperature': 3}
        pump_device.update_status({'P': 100})
        result = pond_pump_auto.setup_minimum_pump_speed(pump_device)
        self.assertEqual(result, 5)

        pond_pump_auto.weather = {'is_valid': True, 'temperature': 0}
        pump_device.update_status({'P': 100})
        result = pond_pump_auto.setup_minimum_pump_speed(pump_device)
        self.assertEqual(result, 5)

        pond_pump_auto.weather = {'is_valid': True, 'temperature': -1}
        pump_device.update_status({'P': 100})
        result = pond_pump_auto.setup_minimum_pump_speed(pump_device)
        self.assertEqual(result, 5)

        pump_device.update_status({'P': 30})
        pond_pump_auto.weather['temperature'] = -5
        result = pond_pump_auto.setup_minimum_pump_speed(pump_device)
        self.assertEqual(result, 0)

        pump_device.update_status({'P': 35})
        pond_pump_auto.weather['temperature'] = 25
        result = pond_pump_auto.setup_minimum_pump_speed(pump_device)
        self.assertEqual(result, 40)


if __name__ == '__main__':
    unittest.main()
