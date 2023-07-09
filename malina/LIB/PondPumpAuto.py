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

    def refresh_min_speed(self):
        # self.weather = self.weather_data()
        self._setup_minimum_pump_speed()

    def update_weather(self):
        self.weather = self.weather_data()

    def _setup_minimum_pump_speed(self):
        if (int(time.time()) - self._min_speed['timestamp']) >= 3600:
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
            self._min_speed['min_speed'] = min_speed

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

    def is_minimum_speed(self, device: Device):
        return self._min_speed['min_speed'] == device.get_status('P')

    def is_max_speed(self, device):
        return device.get_status('P') == 100

    def _decrease_pump_speed(self, device: Device):
        self.refresh_min_speed()
        flow_speed = device.get_status('P')
        min_pump_speed = self._min_speed['min_speed']
        new_speed = flow_speed - int(device.get_extra('speed_step'))
        if flow_speed == min_pump_speed or new_speed < min_pump_speed:
            new_speed = min_pump_speed
        return new_speed

    def _increase_pump_speed(self, device: Device):
        flow_speed = device.get_status('P')
        new_speed = flow_speed + int(device.get_extra('speed_step'))
        if flow_speed > 95 or new_speed > 95:
            new_speed = 100
        return new_speed

    def check_pump_speed(self, device: Device):
        flow_speed = device.get_status('P')
        speed_step = device.get_extra('speed_step')
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
        min_bat_volt = device.get_min_volt()
        max_bat_volt = device.get_max_volt()
        hour = int(time.strftime("%H"))
        speed_step = int(device.get_extra('speed_step'))

        if inv_status == 0:
            self.refresh_min_speed()
            logging.info("----------Inverter switched off working from mains -------  ")
            return device.get_extra("min_speed")

        if not speed_step:
            logging.error(" Check Configuration, cannot get Speed step from Config")
            raise Exception(" Check Configuration, cannot get Speed step from Config")
        if hour > 17:
            min_bat_volt = min_bat_volt + 1.5
            max_bat_volt = max_bat_volt + 1.5

        if 6 < hour < 16:
            min_bat_volt = min_bat_volt - 1.5
            max_bat_volt = max_bat_volt - 1.5

        if min_bat_volt < voltage < max_bat_volt:
            return device.get_status("P")

        if voltage > max_bat_volt:
            if not self.is_max_speed(device):
                return self._increase_pump_speed(device)
        self.refresh_min_speed()
        if self.is_minimum_speed(device):
            return device.get_status("P")
        if voltage < min_bat_volt:
            return self._decrease_pump_speed(device)

    async def _getweather(self):
        # declare the client. format defaults to the metric system (celcius, km/h, etc.)
        async with python_weather.Client(format=python_weather.METRIC) as client:
            # fetch a weather forecast from a city
            weather = await client.get(WEATHER_TOWN)
            return weather
