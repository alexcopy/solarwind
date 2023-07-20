#!/usr/bin/env python
from malina.LIB import FiloFifo
from colorama import Fore, Style
import logging


class SolarLogging:
    def __init__(self):
        self.fifo = FiloFifo.FiloFifo()

    def avg(self, l):
        if len(l) == 0:
            return 0
        return float(round(sum(l, 0.0) / len(l), 2))

    @staticmethod
    def loger_remote(url_path):
        logging.info("------------SENDING TO REMOTE--------------")
        logging.info(url_path)
        logging.info("--------------------------------------------")

    def log_run(self, invert_status, pump_status):
        logging.debug("--------------------------------------------")

    def printing_vars(self, inverter_status, pump_status, load_devices):
        logging.info("\n\n")
        logging.info("--------------------------------------------")
        for i in self.fifo.filo_buff:
            if not i.startswith('1s'):
                continue
            val = self.avg(self.fifo.filo_buff[i])
            if 'voltage' in i:
                _with_col = f'AVG {i.ljust(30)}: {Fore.RED}{val: 3.2f} V {Style.RESET_ALL}'
            elif 'current' in i:
                _with_col = f'AVG {i.ljust(30)}: {Fore.GREEN}{val / 1000: 3.2f} A {Style.RESET_ALL}'
            elif 'wattage' in i:
                _with_col = f'AVG {i.ljust(30)}: {Fore.GREEN}{val: 3.2f} W {Style.RESET_ALL}'
            else:
                _with_col = "UN"
            logging.info(_with_col)

        sol_current = self.fifo.solar_current
        logging.info("")
        logging.info(f"{'1S Solar Current'.ljust(20)}: {sol_current['1s_solar_current'] / 1000:3.2f} A")
        logging.info(f"{'10m Solar Current'.ljust(20)}: {sol_current['10m_solar_current'] / 1000:3.2f} A")
        logging.info("")
        logging.info("---")

        logging.info(
            " Main Relay works from: %s  " % ("INVERT" if (inverter_status == 1) else "MAIN"))
        logging.info("")

        devices = load_devices.get_devices_by_device_type("SWITCH")
        for device in devices:
            logging.info(f"{device.get_desc.ljust(20)}: %s " % (
                "ON" if (device.get_status('switch_1')) else "OFF"))

        _pump_text = "Pump Speed"
        formatted_string = f'{_pump_text.ljust(20)}'
        _with_color = f'{Fore.RED}{pump_status}%{Style.RESET_ALL}'
        logging.info(f"{formatted_string}: {_with_color}")
        logging.info("")

        wtg = (sol_current['1s_solar_current'] * self.avg(self.fifo.filo_buff['1s_inverter_bus_voltage'])) / 1000
        logging.info(f"{'Solar Power'.ljust(20)}: {Fore.GREEN}{wtg:3.2f} W{Style.RESET_ALL}")
        logging.info("---")
        logging.info("--------------------------------------------")
        logging.info("--------------------------------------------")
