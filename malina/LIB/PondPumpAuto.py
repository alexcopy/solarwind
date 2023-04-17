#!/usr/bin/env python
import asyncio
import time
import python_weather
from dotenv import dotenv_values
from malina.LIB.LoadDevices import LoadDevices

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
    def __init__(self, logger, device_manager, remote_api):
        self.logger = logger
        self.deviceManager = device_manager
        self.pump_status = {'flow_speed': 0}
        self.remote_api = remote_api
        self.refresh_pump_status()
        self._min_speed = self.min_pump_speed
        self.weather = {}

    def refresh_pump_status(self):
        try:
            device_status = self.deviceManager.get_device_status(PUMP_ID)
            if device_status['success'] is False:
                self.logger.error(device_status)
                raise Exception(device_status)
            self._update_pump_status(device_status)

        except Exception as ex:
            print(ex)
            self.logger.error(ex)
            return {'flow_speed': 0, "Power": 0, 'error': True}

    @property
    def min_pump_speed(self):
        self.refresh_min_speed()
        return self._min_speed

    @property
    def local_weather(self):
        return self.weather

    def refresh_min_speed(self):
        self.weather = self.weather_data()
        self._setup_minimum_pump_speed()

    def update_weather(self):
        self.weather = self.weather_data()

    def _setup_minimum_pump_speed(self):
        temp = self.weather['temperature']
        self._min_speed = 10
        if temp < 8:
            self._min_speed = 10
        elif temp < 12:
            self._min_speed = 20

        elif temp < 14:
            self._min_speed = 30

        elif temp > 14:
            self._min_speed = 40

    def _update_pump_status(self, tuya_responce):
        pump = {}
        pond_pump = tuya_responce['result']
        for k in pond_pump:
            if k['value'] is True:
                k['value'] = 1
            elif k['value'] is False:
                k['value'] = 0

            if k['code'] == 'P':
                k['code'] = 'flow_speed'

            pump.update({k['code']: self.is_integer(k['value'])})
        pump.update({'name': PUMP_NAME})
        pump.update({'timestamp': time.time()})
        self.pump_status = pump

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
            self.logger.error(e)
            return {'temperature': 0, 'wind_speed': 0, 'visibility': 0, 'uv_index': 0, 'humidity': 0,
                    'precipitation': 0, 'type': "", 'wind_direction': "", 'description': "", 'feels_like': 0,
                    'pressure': 0, 'timestamp': int(time.time()), 'town': WEATHER_TOWN
                    }

    def change_pump_speed(self, value: int, is_working_mains: int):
        if value > 100:
            self.logger.error("The value of PumpSpeed is OUT of Range PLS Check %d" % value)
            value = 100
        command = [
            {
                "code": "P",
                "value": value
            }
        ]
        res = self.deviceManager.send_commands(PUMP_ID, command)
        if res['success'] is True:
            self.logger.info("!!!!!   Pump's Speed successfully adjusted to: %d !!!!!!!!!" % value)
        else:
            self.logger.error("!!!!   Pump's Speed has failed to adjust in speed to: %d !!!!" % value)
            self.logger.error(res)

        self.refresh_pump_status()
        resp = self.remote_api.send_pump_stats(not is_working_mains, self.get_current_status)
        erros_resp = resp['errors']
        if erros_resp:
            time.sleep(5)
            self.refresh_pump_status()
            self.remote_api.send_pump_stats(not is_working_mains, self.get_current_status)

    def is_minimum_speed(self, min_speed):
        return min_speed == self.get_current_status['flow_speed']

    @property
    def is_max_speed(self):
        return self.pump_status['flow_speed'] == 100

    @property
    def get_current_status(self):
        if self.pump_status['flow_speed'] == 0:
            self.refresh_pump_status()
        return self.pump_status

    def _decrease_pump_speed(self, step, min_pump_speed, mains_relay_status):
        flow_speed = self.pump_status['flow_speed']
        new_speed = flow_speed - step
        if flow_speed == min_pump_speed or new_speed < min_pump_speed:
            new_speed = min_pump_speed

        self.change_pump_speed(new_speed, mains_relay_status)
        return self.pump_status

    def _increase_pump_speed(self, step, mains_relay_status):
        flow_speed = self.pump_status['flow_speed']
        new_speed = flow_speed + step
        if flow_speed > 95 or new_speed > 95:
            new_speed = 100
        self.change_pump_speed(new_speed, mains_relay_status)
        return self.pump_status

    def pond_pump_adj(self, min_speed, volt_avg, mains_relay_status):
        min_bat_volt = MIN_BAT_VOLT
        max_bat_volt = MAX_BAT_VOLT
        hour = int(time.strftime("%H"))
        speed_step = POND_SPEED_STEP
        if hour > 17:
            min_bat_volt = min_bat_volt + 1.5
            max_bat_volt = max_bat_volt + 1.5

        if 8 < hour < 15:
            min_bat_volt = min_bat_volt - 1.5
            max_bat_volt = max_bat_volt - 1.5

        mains_relay_status = int(round(mains_relay_status, 0))
        if mains_relay_status == 0:
            if not self.is_minimum_speed(min_speed):
                return self._decrease_pump_speed(100, min_speed, mains_relay_status)

        if min_bat_volt < volt_avg < max_bat_volt:
            return True

        if volt_avg > max_bat_volt:
            if not self.is_max_speed:
                return self._increase_pump_speed(speed_step, mains_relay_status)

        if self.is_minimum_speed(min_speed):
            return True
        if volt_avg < min_bat_volt:
            return self._decrease_pump_speed(speed_step, min_speed, mains_relay_status)

    async def _getweather(self):
        # declare the client. format defaults to the metric system (celcius, km/h, etc.)
        async with python_weather.Client(format=python_weather.METRIC) as client:
            # fetch a weather forecast from a city
            weather = await client.get(WEATHER_TOWN)
            return weather

    def is_integer(self, n):
        try:
            return int(n)
        except ValueError:
            flag = False
        if not flag:
            try:
                return float(n)
            except ValueError:
                return str(n)
