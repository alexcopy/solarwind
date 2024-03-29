#!/usr/bin/env python
import asyncio
import logging
import time
from asyncio.log import logger
import python_weather
from malina.LIB.Device import Device

DAY_TIME_COMPENSATE = 1.5


class PondPumpAuto():
    def __init__(self):
        self.weather = None
        self._min_speed = {'min_speed': 10, 'timestamp': int(time.time())}

    @property
    def local_weather(self):
        return self.weather

    def update_weather(self, weather_town):
        try:
            from malina.LIB.SendApiData import SendApiData
            self.weather = self.weather_data(weather_town)
            if self.weather is not None and self.weather['is_valid']:
                api_data = SendApiData()
                api_data.send_weather(self.weather)
        except Exception as e:
            logging.error(f"Cannot update weather the error is: {str(e)}")

    def setup_minimum_pump_speed(self, device: Device):
        weather_conds = device.get_extra('weather')
        weather_town = device.get_extra('weather_town')
        min_speed = 20
        try:
            logger.debug(
                f"Setting up the minimum speed for device {device.name} with weather table: {weather_conds}")
            min_speed = device.get_extra('min_speed')
            self.update_weather(weather_town)

            if not self.weather['is_valid']:
                logger.error(f"The weather has not been updated or is not valid, min speed remains: {min_speed}")
                return min_speed

            temp = self.weather['temperature']
            min_speed = 20  # Default min_speed
            previous_speed = 0

            for fx_temp in sorted(weather_conds.keys()):
                fx_pump_speed = int(weather_conds[fx_temp])

                if temp < int(fx_temp):
                    return previous_speed
                previous_speed = fx_pump_speed
            return min_speed
        except Exception as e:
            logger.error(f"Error setting up minimum pump speed: {e}")
            return min_speed

    def weather_data(self, weather_town):
        try:
            weather = asyncio.run(self._getweather(weather_town))
            return {'temperature': int(weather.current.temperature), 'wind_speed': int(weather.current.wind_speed),
                    'visibility': int(weather.current.visibility), 'uv_index': int(weather.current.uv_index),
                    'humidity': int(weather.current.humidity), 'precipitation': float(weather.current.precipitation),
                    'type': str(weather.current.type), 'wind_direction': str(weather.current.wind_direction),
                    'feels_like': int(weather.current.feels_like), 'description': str(weather.current.description),
                    'pressure': float(weather.current.pressure), 'timestamp': int(time.time()), 'town': weather_town,
                    'is_valid': True}

        except Exception as e:
            logging.error("Problem in weather data getter")
            logging.error(e)
            return {'temperature': 10, 'wind_speed': 0, 'visibility': 0, 'uv_index': 0, 'humidity': 0,
                    'precipitation': 0, 'type': "", 'wind_direction': "", 'description': "", 'feels_like': 0,
                    'pressure': 0, 'timestamp': int(time.time()), 'town': weather_town, 'is_valid': False
                    }

    def _decrease_pump_speed(self, device: Device):
        flow_speed = device.get_status('P')
        min_pump_speed = int(device.get_extra('min_speed'))
        new_speed = flow_speed - int(device.get_extra('speed_step'))
        if flow_speed == min_pump_speed or new_speed < min_pump_speed:
            new_speed = min_pump_speed
        return new_speed

    def _increase_pump_speed(self, device: Device):

        try:
            max_speed = int(device.get_extra('max_speed'))
            speed_step = int(device.get_extra('speed_step'))
            flow_speed = device.get_status("P")
            suggested_speed = flow_speed + speed_step
            devi_step = max_speed - (speed_step - 1)

            if flow_speed > devi_step or suggested_speed > devi_step:
                suggested_speed = max_speed
            return suggested_speed
        except Exception as e:
            logging.error(f'Something is wrong in _increase_pump_speed   {str(e)} {device}')
            return device.get_extra('min_speed')

    def check_pump_speed(self, device: Device):
        flow_speed = int(device.get_status('P'))
        speed_step = int(device.get_extra('speed_step'))
        if not (flow_speed % speed_step == 0):
            rounded = round(int(flow_speed) / speed_step) * speed_step
            if rounded < speed_step:
                rounded = speed_step
            logging.error(
                "The device status is not divisible by POND_SPEED_STEP %d" % flow_speed)
            logging.debug("Round UP to nearest  POND_SPEED_STEP value %d" % rounded)
            return rounded
        return flow_speed

    def pond_pump_adj(self, device: Device, inv_status, invert_voltage):
        voltage = invert_voltage
        min_bat_volt = device.get_min_volt()
        max_bat_volt = device.get_max_volt()
        logging.debug(f"Getting speed curr_speed ")
        curr_speed = int(device.get_status("P"))
        speed_step = int(device.get_extra('speed_step'))

        if inv_status == 0:
            return device.get_extra("min_speed")

        if not speed_step:
            logging.debug(" Check Configuration, cannot get Speed step from Config")
            raise Exception(" Check Configuration, cannot get Speed step from Config")
        max_bat_volt, min_bat_volt = self.day_time_adjust(max_bat_volt, min_bat_volt)

        if min_bat_volt < voltage < max_bat_volt:
            return device.get_status("P")
        max_speed = int(device.get_extra('max_speed'))
        is_max_speed = max_speed == curr_speed
        is_min_speed = int(device.get_extra('min_speed')) == curr_speed

        logging.info(f"The INVERT Voltage is {voltage}  and max  {max_bat_volt}")
        logging.debug(f"The Max Speed is {is_max_speed} and curr_speed is {curr_speed} mx speed is {max_speed} ")
        if voltage > max_bat_volt:
            if (not is_max_speed) and curr_speed < max_speed:
                logging.debug(f"The PUMP speed needs more speed")
                new_speed = self._increase_pump_speed(device)
                logging.info(f"The PUMP speed needs to INCREASE {new_speed}")
                return new_speed
        if is_min_speed:
            logging.debug(f"The PUMP speed needs min speed is: {device}")
            return device.get_status("P")
        if voltage < min_bat_volt:
            pump_speed = self._decrease_pump_speed(device)
            logging.info(f"The PUMP speed needs to DECREASE {pump_speed}")
            return pump_speed
        return curr_speed

    def day_time_adjust(self, max_bat_volt, min_bat_volt):
        hour = int(time.strftime("%H"))
        if hour > 17:
            min_bat_volt = min_bat_volt + 1.5
            max_bat_volt = max_bat_volt + 1.5
        if 6 < hour < 16:
            min_bat_volt = min_bat_volt - 1.5
            max_bat_volt = max_bat_volt - 1.5
        return max_bat_volt, min_bat_volt

    async def _getweather(self, weather_town):
        # declare the client. format defaults to the metric system (celcius, km/h, etc.)
        async with python_weather.Client(format=python_weather.METRIC) as client:
            # fetch a weather forecast from a city
            weather = await client.get(weather_town)
            return weather
