#!/usr/bin/env python
import asyncio
import logging
import time

import python_weather
from dotenv import dotenv_values

from malina.LIB.Device import Device

config = dotenv_values(".env")
BASE_URL = config['API_URL']
PUMP_ID = config['PUMP_ID']
PUMP_NAME = config['PUMP_NAME']
MAX_BAT_VOLT = float(config['MAX_BAT_VOLT'])
MIN_BAT_VOLT = float(config['MIN_BAT_VOLT'])
POND_SPEED_STEP = int(config["POND_SPEED_STEP"])
WEATHER_TOWN = config["WEATHER_TOWN"]
DAY_TIME_COMPENSATE = 1.5


class PondPumpAuto():
    def __init__(self, devices):
        self._min_speed = {'min_speed': 10, 'timestamp': int(time.time())}
        self.weather = {}
        self.devices = devices

    @property
    def local_weather(self):
        return self.weather

    def update_weather(self):
        self.weather = self.weather_data()

    def setup_minimum_pump_speed(self):
        temp = self.weather['temperature']
        self._min_speed['timestamp'] = int(time.time())
        min_speed = self._min_speed['min_speed']
        if temp < 8:
            min_speed = 10
        elif temp < 12:
            min_speed = 20

        elif temp < 17:
            min_speed = 30

        elif temp > 17:
            min_speed = 40
        return min_speed

    def weather_data(self):
        try:
            weather = asyncio.run(self._getweather())
            return {'temperature': int(weather.current.temperature), 'wind_speed': int(weather.current.wind_speed),
                    'visibility': int(weather.current.visibility), 'uv_index': int(weather.current.uv_index),
                    'humidity': int(weather.current.humidity), 'precipitation': float(weather.current.precipitation),
                    'type': str(weather.current.type), 'wind_direction': str(weather.current.wind_direction),
                    'feels_like': int(weather.current.feels_like), 'description': str(weather.current.description),
                    'pressure': float(weather.current.pressure), 'timestamp': int(time.time()), 'town': WEATHER_TOWN}

        except Exception as e:
            logging.error("Problem in weather data getter")
            logging.error(e)
            return {'temperature': 0, 'wind_speed': 0, 'visibility': 0, 'uv_index': 0, 'humidity': 0,
                    'precipitation': 0, 'type': "", 'wind_direction': "", 'description': "", 'feels_like': 0,
                    'pressure': 0, 'timestamp': int(time.time()), 'town': WEATHER_TOWN
                    }

    def _decrease_pump_speed(self, device: Device):
        flow_speed = device.get_status('P')
        min_pump_speed = int(device.get_extra('min_speed'))
        new_speed = flow_speed - int(device.get_extra('speed_step'))
        if flow_speed == min_pump_speed or new_speed < min_pump_speed:
            new_speed = min_pump_speed
        return self.check_pump_speed(new_speed)

    def _increase_pump_speed(self, device: Device):
        flow_speed = device.get_status('P')
        max_speed = int(device.get_extra('max_speed'))
        speed_step = int(device.get_extra('speed_step'))
        suggested_speed = flow_speed + speed_step
        devi_step = max_speed - (speed_step - 1)

        if flow_speed > devi_step or suggested_speed > devi_step:
            suggested_speed = max_speed
        return self.check_pump_speed(suggested_speed)

    def check_pump_speed(self, device: Device):
        flow_speed = int(device.get_status('P'))
        speed_step = int(device.get_extra('speed_step'))
        if not (flow_speed % speed_step == 0):
            rounded = round(int(flow_speed) / speed_step) * speed_step
            if rounded < speed_step:
                rounded = speed_step
            logging.error(
                "The device status is not divisible by POND_SPEED_STEP %d" % flow_speed)
            logging.error("Round UP to nearest  POND_SPEED_STEP value %d" % rounded)
            return rounded
        return flow_speed

    def pond_pump_adj(self, device: Device, inv_status):
        voltage = device.get_inverter_values()
        min_bat_volt = float(device.get_min_volt())
        max_bat_volt = float(device.get_max_volt())
        curr_speed = int(device.get_status('P'))
        speed_step = int(device.get_extra('speed_step'))

        if inv_status == 0:
            logging.info("----------Inverter switched off working from mains -------  ")
            return device.get_extra("min_speed")

        if not speed_step:
            logging.error(" Check Configuration, cannot get Speed step from Config")
            raise Exception(" Check Configuration, cannot get Speed step from Config")
        max_bat_volt, min_bat_volt = self.day_time_adjust(max_bat_volt, min_bat_volt)

        if min_bat_volt < voltage < max_bat_volt:
            return device.get_status("P")
        max_speed = int(device.get_extra('max_speed')) == curr_speed
        min_speed = int(device.get_extra('min_speed')) == curr_speed

        if voltage > max_bat_volt:
            if not max_speed and curr_speed < max_speed:
                return self._increase_pump_speed(device)
        if min_speed:
            return device.get_status("P")
        if voltage < min_bat_volt:
            return self._decrease_pump_speed(device)

    def day_time_adjust(self, max_bat_volt, min_bat_volt):
        hour = int(time.strftime("%H"))
        if hour > 17:
            min_bat_volt = min_bat_volt + 1.5
            max_bat_volt = max_bat_volt + 1.5
        if 6 < hour < 16:
            min_bat_volt = min_bat_volt - 1.5
            max_bat_volt = max_bat_volt - 1.5
        return max_bat_volt, min_bat_volt

    async def _getweather(self):
        # declare the client. format defaults to the metric system (celcius, km/h, etc.)
        async with python_weather.Client(format=python_weather.METRIC) as client:
            # fetch a weather forecast from a city
            weather = await client.get(WEATHER_TOWN)
            return weather
