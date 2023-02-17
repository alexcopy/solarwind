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

    def log_run(self, filo_buffer, invert_status, pump_status):
        self.logging.info("--------------------------------------------")
        for i in filo_buffer:
            if 'voltage' in i:
                units = "V"
            elif 'current' in i:
                units = "mA"
            elif 'wattage' in i:
                units = "W"
            else:
                continue
            name = i.title().replace('_', " ")
            self.logging.info("AVG %s: %3.2f %s " % (name, self.avg(filo_buffer[i]), units))

        self.logging.info(" ")
        self.logging.info("--------------------------------------------")
        self.logging.info(" Pond Pump Speed: %d  " % pump_status['flow_speed'])
        self.logging.info(" Inverter Status is: %d  " % invert_status)
        self.logging.info("############################################")
        self.logging.info("--------------------------------------------")
        print("--------------------------------------------")
        print("")

    def printing_vars(self, fifo_buffer, inverter_status, pump_status):
        print("")
        print("--------------------------------------------")
        for i in fifo_buffer:
            if 'voltage' in i:
                units = "V"
            elif 'current' in i:
                units = "mA"
            elif 'wattage' in i:
                units = "Watt"
            else:
                continue
            name = i.title().replace('_', " ")
            print("%s: %3.2f %s " % (name, fifo_buffer[i], units))

        print("")
        print(" Inverter Status is: %d  " % inverter_status)
        print(" Pond Pump Speed: %d  " % pump_status['flow_speed'])
        print(" ")
        print("--------------------------------------------")
