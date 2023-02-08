#!/usr/bin/env python


# V 1.0


# encoding: utf-8

class SolarLogging:
    def __init__(self, logging):
        self.logging = logging

    def avg(self, l):
        if len(l) == 0:
            return 0
        return float(round(sum(l, 0.0) / len(l), 2))

    def loger_remote(self, url_path):
        self.logging.info("------------SENDING TO REMOTE--------------")
        self.logging.info(url_path)
        self.logging.info("--------------------------------------------")

    def log_run(self, filo_buffer, invert_status, wattage):
        self.logging.info("--------------------------------------------")
        self.logging.info("AVG Battery Voltage:  %3.2f V" % self.avg(filo_buffer['bat_voltage']))
        self.logging.info("AVG Battery Current 1:  %3.2f mA" % self.avg(filo_buffer['bat_current']))
        self.logging.info("AVG Converter Current 3:  %3.2f mA" % self.avg(filo_buffer['converter_current']))
        self.logging.info("AVG  Solar Current:  %3.2f mA" % self.avg(filo_buffer['solar_current']))
        self.logging.info("--------------------------------------------")
        self.logging.info("AVG 10m Battery Voltage:  %3.2f V" % self.avg(filo_buffer['10m_bat_voltage']))
        self.logging.info("AVG 10m Battery Current 1:  %3.2f mA" % self.avg(filo_buffer['10m_bat_current']))
        self.logging.info("AVG 10m Converter Current 3:  %3.2f mA" % self.avg(filo_buffer['10m_converter_current']))
        self.logging.info("AVG 10m  Solar Current:  %3.2f mA" % self.avg(filo_buffer['10m_solar_current']))
        self.logging.info("--------------------------------------------")
        self.logging.info("AVG 1h  Battery Voltage:  %3.2f V" % self.avg(filo_buffer['1h_bat_voltage']))
        self.logging.info("AVG 1h  Battery Current 1:  %3.2f mA" % self.avg(filo_buffer['1h_bat_current']))
        self.logging.info("AVG 1h  Converter Current 3:  %3.2f mA" % self.avg(filo_buffer['1h_converter_current']))
        self.logging.info("AVG 1h   Solar Current:  %3.2f mA" % self.avg(filo_buffer['1h_solar_current']))
        self.logging.info("--------------------------------------------")
        self.logging.info(" AVG 10 min Solar Wattage is: %3.2f  W" % wattage)
        self.logging.info(" Inverter Status is: %d  " % invert_status)
        self.logging.info("############################################")
        self.logging.info("--------------------------------------------")
        print("--------------------------------------------")
        print("")

    def printing_vars(self, fifo_buffer, inverter_status, wattage):
        print("")
        print("--------------------------------------------")
        print("Bus Voltage: %3.2f V " % fifo_buffer['busvoltage1'])
        print("Bat Voltage: %3.2f V " % fifo_buffer['bat_voltage'])
        print("SHUNT  Voltage: %3.2f V " % fifo_buffer['busvoltage1'])
        print("Battery Current 1:  %3.2f mA" % fifo_buffer['bat_current'])
        print("Converter Current 3:  %3.2f mA" % fifo_buffer['converter_current'])
        print("Solar Current:  %3.2f mA" % fifo_buffer['solar_current'])
        print("")
        print(" AVG 10 min Solar Wattage is: %3.2f  W" % wattage)
        print(" Inverter Status is: %d  " % inverter_status)
        print("############################################")
