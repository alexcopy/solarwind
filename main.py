# -*- coding: utf-8 -*-
import traceback
from datetime import datetime
import schedule as schedule
from malina.solar_pond import SolarPond
import logging
import logging.handlers
import time
from pathlib import Path

last_run = 0


class SetupLogger():
    def __init__(self):
        self.conf_logger()

    def conf_logger(self):
        current_path = Path('logs')
        current_path.mkdir(parents=True, exist_ok=True)  # Создаем папку logs, если она не существует
        log_name = time.strftime("%Y-%m-%d_%H-%M-%S")
        filename = current_path.joinpath(f'{log_name}.log')

        # Создаем обработчик для основного лога
        log_handler = logging.handlers.RotatingFileHandler(filename, maxBytes=3000000, backupCount=5)
        formatter = logging.Formatter('%(asctime)s program_name [%(process)d]: %(message)s', '%b %d %H:%M:%S')
        formatter.converter = time.gmtime  # Если вы хотите использовать время в формате UTC
        log_handler.setFormatter(formatter)

        # Создаем объект логгера и устанавливаем уровень логирования
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        # Добавляем обработчик к логгеру
        logger.addHandler(log_handler)

        # Создаем обработчики для разных уровней логирования
        error_handler = self.setup_logger(current_path, formatter, 'error.log', logging.ERROR)
        logger.addHandler(error_handler)
        warn_handler = self.setup_logger(current_path, formatter, 'warning.log', logging.WARNING)
        logger.addHandler(warn_handler)
        info_handler = self.setup_logger(current_path, formatter, 'info.log', logging.INFO)
        logger.addHandler(info_handler)
        debug_handler = self.setup_logger(current_path, formatter, 'debug.log', logging.DEBUG)
        logger.addHandler(debug_handler)

    @staticmethod
    def setup_logger(current_path, formatter, filename, level):
        handler = logging.handlers.RotatingFileHandler(current_path.joinpath(filename), maxBytes=3000000, backupCount=5)
        handler.setFormatter(formatter)
        handler.setLevel(level)
        return handler


def _stats():
    global last_run
    hour = int(time.strftime("%H"))
    timestamp = int(datetime.now().timestamp())
    # Проверяем, находимся ли мы в диапазоне с 19:00 до 6:00
    if hour >= 19 or hour < 6:
        if (timestamp - last_run) >= 600:
            logging.debug(f"Update Stats every 600 sec {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            sp.update_devs_stats()
            last_run = timestamp
    else:
        logging.debug(f"Update Stats every 120 sec: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        sp.update_devs_stats()


if __name__ == '__main__':
    sl = SetupLogger()
    sp = SolarPond()
    # Инициализация планировщика
    scheduler = schedule.Scheduler()
    # Добавление задач в планировщик
    scheduler.every(5).seconds.do(sp.filter_flush_run)
    scheduler.every(5).seconds.do(sp.load_checks)
    scheduler.every(2).seconds.do(sp.show_logs)
    scheduler.every(5).minutes.do(sp.reset_ff)
    scheduler.every(1).minutes.do(_stats)
    scheduler.every(10).minutes.do(sp.power_devs_update)
    scheduler.every(30).minutes.do(sp.send_stats_to_api)
    scheduler.every(60).minutes.do(sp.weather_check_update)
    scheduler.every(30).minutes.do(sp.send_temp_sensors)
    scheduler.every().hour.at(":00").do(sp.send_avg_hr_power_to_server)
    # Добавление задачи на отправку данных каждый час в 00 минут
    scheduler.every().day.at("00:00").do(sp.reset_power_buffers_daily)
    # todo change timing after testing
    # scheduler.every(2).minutes.do(sp.send_avg_data)

    while True:
        try:
            sp.processing_reads()
            scheduler.run_pending()
            time.sleep(1)
        except Exception as ex:
            traceback.print_exc()
            logging.error(f"Exception in one of the schedules failed: {ex}")
            logging.error(f"{traceback.format_exc()}")
            exit(1)
