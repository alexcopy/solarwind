import time

from malina.solar_pond import SolarPond

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
        log_name = time.strftime("info")
        filename = current_path.joinpath(f'{log_name}.log')
        log_handler = logging.handlers.RotatingFileHandler(filename, maxBytes=5000000, backupCount=5)
        formatter = logging.Formatter(
            '%(asctime)s program_name [%(process)d]: %(message)s',
            '%b %d %H:%M:%S')
        formatter.converter = time.gmtime  # if you want UTC time
        log_handler.setFormatter(formatter)
        logger = logging.getLogger()
        logger.addHandler(log_handler)
        logger.setLevel(logging.DEBUG)
        error_handler = self.setup_logger(current_path, formatter, 'error.log')
        logger.addHandler(error_handler)
        warn_handler = self.setup_logger(current_path, formatter, 'warning.log')
        logger.addHandler(warn_handler)

    def setup_logger(self, current_path, formatter, log_file):
        # to log errors messages
        log = logging.FileHandler(os.path.join(current_path, log_file))
        log.setFormatter(formatter)
        log.setLevel(logging.ERROR)
        return log


if __name__ == '__main__':
    sl = SetupLogger()
    sp = SolarPond()
    sp.run_read_vals()
    while True:
        timestamp = int(time.time())
        time.sleep(SECS)
        sp.processing_reads()
        if timestamp % 600 == 0:
            sp.reset_ff()
