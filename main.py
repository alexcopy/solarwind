import time

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
    # sp.run_read_vals()

    while True:
        curr = int(time.time())
        with concurrent.futures.ProcessPoolExecutor(max_workers=6) as executor:
            timestamp = int(time.time())
            time.sleep(SECS)
            if timestamp % 600 == 0:
                sp.reset_ff()
            if curr % 5 == 0:
                executor.map(sp.load_checks)
            if curr % 5 == 0:
                executor.map(sp.update_devs_stats)

            if curr % 5 == 0:
                executor.map(sp.show_logs)
                executor.map(sp.show_logs)
            if curr % 60 == 0:
                executor.map(sp.update_devs_stats)
