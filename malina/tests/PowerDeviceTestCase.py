#!/usr/bin/env python
import datetime
import sys
import unittest
from datetime import datetime, timedelta
from io import StringIO
from unittest.mock import patch

from colorama import Fore, Style

sys.path.append('../')

from malina.LIB.PowerDevice import PowerDevice

mock_time = 60


class PowerDeviceTestCase(unittest.TestCase):
    def setUp(self):
        self.device = PowerDevice("TestDevice")

    def test_add_power_value(self):
        self.device.add_power_value(10)
        self.assertEqual(self.device.ten_minute_buffer, [])

        # Проверка на ограничение времени между добавлениями
        self.device.last_added_time -= timedelta(seconds=541)
        self.device.add_power_value(15)
        self.assertEqual(self.device.ten_minute_buffer, [15])

        # Проверка добавления значений для формирования часового буфера
        for i in range(6):
            self.device.last_added_time -= timedelta(seconds=542)
            self.device.add_power_value(i * 2)
        self.assertEqual(self.device.hourly_power_buffer, [5.8])

        for i in range(24):
            self.device.last_added_time -= timedelta(hours=1)
            self.device.add_power_value(i * 3)
        self.assertEqual(self.device.hourly_power_buffer, [5.8, 6.7, 22.5, 40.5, 58.5])

        # Проверка добавления значений для формирования суточного буфера
        for i in range(144):
            self.device.last_added_time -= timedelta(hours=1)
            self.device.add_power_value(i * 3)
        self.assertEqual(self.device.daily_power_buffer, [137.9])

    def test_get_daily_energy(self):
        # Проверка, что при пустом буфере вернется 0
        self.assertEqual(self.device.get_daily_energy(), 0)

        # Проверка корректного вычисления среднего суточного потребления
        self.device.daily_power_buffer = [10, 20, 30]
        self.assertEqual(self.device.get_daily_energy(), 20)

    def test_get_mean_hourly(self):
        # Проверка, что при пустом буфере вернется 0
        self.assertEqual(self.device.get_mean_hourly(), 0)

        # Проверка корректного вычисления среднего часового потребления
        self.device.hourly_power_buffer = [5, 10, 15]
        self.assertEqual(self.device.get_mean_hourly(), 10)

    def test_get_mean_minutes(self):
        # Проверка, что при пустом буфере вернется 0
        self.assertEqual(self.device.get_mean_minutes(), 0)

        # Проверка корректного вычисления среднего потребления за 10 минут
        self.device.ten_minute_buffer = [2, 4, 6, 8]
        self.assertEqual(self.device.get_mean_minutes(), 5)

    def test_get_mean_total_with_empty_buffers(self):
        # Проверка, что при пустых буферах вернется 0
        self.assertEqual(self.device.get_mean_total(), 0)

    def test_get_mean_total_with_partial_data(self):
        # Проверка корректного вычисления среднего общего потребления с частичными данными
        self.device.daily_power_buffer = [10, 20]
        self.assertEqual(self.device.get_mean_total(), 15)  # Среднее из суточных данных

        self.device.daily_power_buffer = []  # Очистка суточных данных
        self.device.hourly_power_buffer = [5, 10]
        self.assertEqual(self.device.get_mean_total(), 7.5)  # Среднее из часовых данных

        self.device.hourly_power_buffer = []  # Очистка часовых данных
        self.device.ten_minute_buffer = [2, 4]
        self.assertEqual(self.device.get_mean_total(), 3)  # Среднее из 10-минутных данных

    def test_add_power_value_with_last_added_time(self):
        # Проверка, что время последнего добавления корректно обновляется
        initial_time = self.device.last_added_time
        self.device.last_added_time -= timedelta(seconds=543)
        self.device.add_power_value(10)

        new_time = self.device.last_added_time
        self.assertNotEqual(initial_time, new_time)  # Проверка, что время изменилось после добавления

        # Проверка, что нельзя добавить значение, если прошло менее 9 минут с последнего добавления
        self.device.last_added_time -= timedelta(seconds=60)
        self.device.add_power_value(15)
        self.assertEqual(self.device.ten_minute_buffer, [10])  # Проверка, что значение не добавлено

    def test_get_mean_total(self):
        # Проверка, что при пустых буферах вернется 0
        self.assertEqual(self.device.get_mean_total(), 0)

        # Проверка корректного вычисления среднего общего потребления
        self.device.daily_power_buffer = [5, 5]
        self.device.hourly_power_buffer = [2, 4]
        self.device.ten_minute_buffer = [1, 2, 3]
        self.assertEqual(self.device.get_mean_total(), 3.3)

    def test_print_device_logs(self):
        self.device.ten_minute_buffer = [10, 20, 30]
        self.device.hourly_power_buffer = [15, 25, 35]
        self.device.daily_power_buffer = [5, 15, 25]
        with patch('sys.stdout', new=StringIO()) as fake_output:
            self.device.print_device_logs()
            expected_output = (
                f"{Fore.GREEN}Device Name: TestDevice{Style.RESET_ALL}\n"
                f"{Fore.CYAN}10-Minute Power Values: [10, 20, 30]{Style.RESET_ALL}\n"
                f"{Fore.YELLOW}Hourly Power Values: [15, 25, 35]{Style.RESET_ALL}\n"
                f"{Fore.RED}Daily Power Values: [5, 15, 25]{Style.RESET_ALL}\n"
            )
            self.assertEqual(fake_output.getvalue(), expected_output)

    def test_print_mean_values(self):
        self.device.ten_minute_buffer = [10, 20, 30]
        self.device.hourly_power_buffer = [15, 25, 35]
        self.device.daily_power_buffer = [5, 15, 25]
        with patch('sys.stdout', new=StringIO()) as fake_output:
            self.device.print_mean_values()
            expected_output = (
                f"{Fore.GREEN}Mean Values for Device: TestDevice{Style.RESET_ALL}\n"
                f"{Fore.CYAN}Mean 10-Minute Power: 20.0{Style.RESET_ALL}\n"
                f"{Fore.YELLOW}Mean Hourly Power: 25.0{Style.RESET_ALL}\n"
                f"{Fore.RED}Mean Daily Power: 15.0{Style.RESET_ALL}\n"
            )
            self.assertEqual(fake_output.getvalue(), expected_output)

    def test_get_daily_or_hourly_avg_power_with_hourly_buffer(self):
        # Adding values to hourly buffer
        self.device.hourly_power_buffer = [10, 15, 20, 25]
        result = self.device.get_daily_or_hourly_avg_power()
        self.assertEqual(result, 17.5)

    def test_get_daily_or_hourly_avg_power_with_daily_buffer(self):
        # Adding values to daily buffer
        self.device.daily_power_buffer = [100, 150, 200, 250]
        result = self.device.get_daily_or_hourly_avg_power()
        self.assertEqual(result, 250)

    #
    def test_get_daily_or_hourly_avg_power_with_minute_buffer(self):
        # Adding values to ten-minute buffer
        self.device.ten_minute_buffer = [5, 10, 15]
        result = self.device.get_daily_or_hourly_avg_power()
        self.assertEqual(result, 10)

    #
    def test_get_daily_or_hourly_avg_power_with_empty_buffers(self):
        result = self.device.get_daily_or_hourly_avg_power()
        self.assertEqual(result, 0)

    def test_get_hourly_or_minute_avg_power_with_hourly_buffer(self):
        # Adding values to hourly buffer
        self.device.hourly_power_buffer = [10, 15, 20, 25]
        result = self.device.get_hourly_or_minute_avg_power()
        self.assertEqual(result, 25)

    def test_get_hourly_or_minute_avg_power_with_daily_buffer(self):
        # Adding values to daily buffer
        self.device.daily_power_buffer = [100, 150, 200, 250]
        result = self.device.get_hourly_or_minute_avg_power()
        self.assertEqual(result, 0)

    #
    def test_get_hourly_or_minute_avg_power_with_minute_buffer(self):
        # Adding values to ten-minute buffer
        self.device.ten_minute_buffer = [5, 10, 15]
        result = self.device.get_hourly_or_minute_avg_power()
        self.assertEqual(result, 10)

    #
    def test_get_hourly_or_minute_avg_power_with_empty_buffers(self):
        result = self.device.get_hourly_or_minute_avg_power()
        self.assertEqual(result, 0)


if __name__ == '__main__':
    unittest.main()
