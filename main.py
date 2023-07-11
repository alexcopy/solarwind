import time

import schedule as schedule

from malina.solar_pond import SolarPond
import concurrent.futures

SECS = 1
import logging
import logging.handlers
import os
import time
from pathlib import Path


class SetupLogger():
    def __init__(self):
        self.conf_logger()

    def conf_logger(self):
        current_path = Path('logs')
        log_name = time.strftime("debug")
        filename = current_path.joinpath(f'{log_name}.log')
        log_handler = logging.handlers.RotatingFileHandler(filename, maxBytes=3000000, backupCount=5)
        formatter = logging.Formatter(
            '%(asctime)s program_name [%(process)d]: %(message)s',
            '%b %d %H:%M:%S')
        formatter.converter = time.gmtime  # if you want UTC time
        log_handler.setFormatter(formatter)
        logger = logging.getLogger()
        logger.addHandler(log_handler)
        logger.setLevel(logging.DEBUG)
        error_handler = self.setup_logger(current_path, formatter, 'error.log', logging.ERROR)
        logger.addHandler(error_handler)
        warn_handler = self.setup_logger(current_path, formatter, 'warning.log', logging.WARNING)
        logger.addHandler(warn_handler)
        info_handler = self.setup_logger(current_path, formatter, 'info.log', logging.INFO)
        logger.addHandler(info_handler)

    def setup_logger(self, current_path, formatter, log_file, level):
        log = logging.handlers.RotatingFileHandler(os.path.join(current_path, log_file), maxBytes=3000000,
                                                   backupCount=5)
        log.setFormatter(formatter)
        log.setLevel(level)
        return log


if __name__ == '__main__':
    sl = SetupLogger()
    sp = SolarPond()
    # Инициализация планировщика
    scheduler = schedule.Scheduler()

    # Добавление задач в планировщик
    scheduler.every(1).seconds.do(sp.processing_reads)
    scheduler.every(10).minutes.do(sp.reset_ff)
    scheduler.every(5).seconds.do(sp.load_checks)
    scheduler.every(2).seconds.do(sp.show_logs)
    scheduler.every(1).minutes.do(sp.update_devs_stats)
    scheduler.every(10).minutes.do(sp.weather_check_update)
    # todo uncomment after testing
    # scheduler.every(1).hour.do(sp.weather_check_update)

    while True:
        scheduler.run_pending()
        time.sleep(1)