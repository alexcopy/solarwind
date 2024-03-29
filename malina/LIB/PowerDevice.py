import datetime
import logging
from colorama import Fore, Style


class PowerDevice:
    def __init__(self, name):
        self.name = name
        self.ten_minute_buffer = []
        self.hourly_power_buffer = []
        self.daily_power_buffer = []
        self.last_added_time = datetime.datetime.now()

    def add_power_value(self, power_value):
        current_time = datetime.datetime.now()
        if (
                current_time - self.last_added_time).total_seconds() <= 540:  # Проверка, прошло ли более 9 минут с последнего добавления
            logging.info("Нельзя добавить значение. Последнее добавление было менее 500 sec назад.")
            return

        self.last_added_time = current_time
        self.ten_minute_buffer.append(power_value)
        if len(self.ten_minute_buffer) >= 6:
            hour_min_power = self.get_mean_minutes()
            self.hourly_power_buffer.append(hour_min_power)
            self.ten_minute_buffer = []

        if len(self.hourly_power_buffer) >= 24 or (current_time.hour == 0 and current_time.minute == 0):
            daily_power = self.get_sum_hourly()
            self.daily_power_buffer.append(daily_power)
            self.hourly_power_buffer = []

    def get_daily_energy(self):
        if len(self.hourly_power_buffer) > 0:
            return round(sum(self.hourly_power_buffer), 1)
        return 0

    def get_sum_hourly(self):
        if len(self.hourly_power_buffer) > 0:
            return round(sum(self.hourly_power_buffer), 1)
        return 0

    def get_mean_minutes(self):
        if len(self.ten_minute_buffer) > 0:
            return round(sum(self.ten_minute_buffer) / len(self.ten_minute_buffer), 1)
        return 0

    def get_mean_total(self):
        total_values = []
        if self.daily_power_buffer:
            total_values.append(sum(self.daily_power_buffer) / len(self.daily_power_buffer))

        if self.hourly_power_buffer:
            total_values.append(sum(self.hourly_power_buffer) / len(self.hourly_power_buffer))

        if self.ten_minute_buffer:
            total_values.append(sum(self.ten_minute_buffer) / len(self.ten_minute_buffer))

        if total_values:
            return round(sum(total_values) / len(total_values), 1)
        return 0

    def print_device_logs(self):
        logging.info(f"{Fore.GREEN}Device Name: {self.name}{Style.RESET_ALL}")
        if self.ten_minute_buffer:
            logging.info(f"{Fore.CYAN}10-Minute Power Values: {self.ten_minute_buffer}{Style.RESET_ALL}")
        if self.hourly_power_buffer:
            logging.info(f"{Fore.YELLOW}Hourly Power Values: {self.hourly_power_buffer}{Style.RESET_ALL}")
        if self.daily_power_buffer:
            logging.info(f"{Fore.RED}Daily Power Values: {self.daily_power_buffer}{Style.RESET_ALL}")

    def print_mean_values(self):
        print(f"{Fore.GREEN}Mean Values for Device: {self.name}{Style.RESET_ALL}")
        mean_10_min = self.get_mean_minutes()
        if mean_10_min:
            print(f"{Fore.CYAN}Mean 10-Minute Power: {mean_10_min}{Style.RESET_ALL}")
        sum_hourly = self.get_sum_hourly()
        if sum_hourly:
            print(f"{Fore.YELLOW}Sum Hourly Power: {sum_hourly}{Style.RESET_ALL}")
        mean_daily = self.get_daily_energy()
        if mean_daily:
            print(f"{Fore.RED}Mean Daily Power: {mean_daily}{Style.RESET_ALL}")

    def get_hourly_or_minute_avg_power(self):
        if len(self.ten_minute_buffer) == 0 and len(self.hourly_power_buffer) != 0:
            return self.hourly_power_buffer[-1]  # Берем последний элемент из часового буфера
        else:
            return self.get_mean_minutes()

    def get_last_min_power(self):
        if len(self.ten_minute_buffer) == 0 and len(self.hourly_power_buffer) != 0:
            return self.hourly_power_buffer[-1]  # Берем последний элемент из дневного буфера
        elif len(self.ten_minute_buffer) == 0 and len(self.hourly_power_buffer) == 0:
            return 0
        else:
            return self.ten_minute_buffer[-1]

    def get_daily_or_hourly_avg_power(self):
        if len(self.hourly_power_buffer) == 0 and len(self.daily_power_buffer) != 0:
            return self.daily_power_buffer[-1]  # Берем последний элемент из дневного буфера
        elif len(self.hourly_power_buffer) == 0 and len(self.daily_power_buffer) == 0:
            return self.get_mean_minutes()
        else:
            return self.get_sum_hourly()
