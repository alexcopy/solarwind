#!/usr/bin/env python
from malina.LIB import FiloFifo


class SolarLogging:
    def __init__(self, logging):
        self.logging = logging
        self.fifo = FiloFifo.FiloFifo()

    def avg(self, l):
        if len(l) == 0:
            return 0
        return float(round(sum(l, 0.0) / len(l), 2))

    def loger_remote(self, url_path):
        self.logging.info("------------SENDING TO REMOTE--------------")
        self.logging.info(url_path)
        self.logging.info("--------------------------------------------")

    def integrity_error(self, avg_status, pond_relay, inverter):
        self.logging.error("-------------Switching to MAINS avg _status is: %3.2f ---------------" % avg_status)
        self.logging.error(
            "-------------Switching to POND RELAY status is: %d ------------------" % pond_relay)
        self.logging.error(
            "-------------Switching to INVERTER RELAY status is: %d --------------" % inverter)
        self.logging.error("---------------------------------------------------------------------")

    def log_run(self, invert_status, pump_status):
        sol_current = self.fifo.solar_current
        self.logging.debug("--------------------------------------------")
        for i in self.fifo.filo_buff:
            if 'bus_voltage' in i:
                units = "V"
            elif 'current' in i:
                units = "mA"
            elif 'wattage' in i:
                units = "W"
            else:
                continue

            name = i.title().replace('_', " ")
            self.logging.debug("AVG %s: %3.2f %s " % (name, self.avg(self.fifo.filo_buff[i]), units))

        self.logging.debug(" ")
        self.logging.debug(" 1S Solar Current: %3.2f " % sol_current['1s_solar_current'])
        self.logging.debug(" 10m Solar Current: %3.2f " % sol_current['10m_solar_current'])
        self.logging.debug(" 10m Solar Current: %3.2f " % sol_current['1h_solar_current'])
        self.logging.debug("--------------------------------------------")
        self.logging.debug(" Pond Pump Speed: %d  " % pump_status)
        self.logging.debug(" Inverter Status is: %d  " % invert_status)
        self.logging.debug("############################################")
        self.logging.debug("--------------------------------------------")

    def printing_vars(self, inverter_status, pump_status, load_devices):

        self.logging.info("--------------------------------------------")
        for i in self.fifo.filo_buff:
            if 'voltage' in i:
                units = "V"
            elif 'current' in i:
                units = "mA"
            elif 'wattage' in i:
                units = "Watt"
            else:
                units = "UN"

            name = i
            if name.startswith('1s_'):
                self.logging.info("AVG %s: %3.2f %s " % (name, self.avg(self.fifo.filo_buff[i]), units))

        self.logging.info("")
        sol_current = self.fifo.solar_current
        self.logging.info(" 1S Solar Current: %3.2f A" % float(sol_current['1s_solar_current'] / 1000))
        self.logging.info(" 10m Solar Current: %3.2f A" % float(sol_current['10m_solar_current'] / 1000))
        self.logging.info("")
        self.logging.info("---")

        self.logging.info(
            " Main Relay works from: %s  " % ("INVERT" if (inverter_status == 1) else "MAIN"))
        self.logging.info("")

        devices = load_devices.get_devices_by_device_type("SWITCH")

        for device in devices:
            self.logging.info(f"{device.get_desc()} %s " % (
                "ON" if (device.get_status('switch_1')) else "OFF"))
            self.logging.info("")

        wtg = (sol_current['1s_solar_current'] * self.avg(self.fifo.filo_buff['1s_inverter_bus_voltage'])) / 1000
        self.logging.info(" 1S Solar Power: %3.2f W " % wtg)
        self.logging.info(" Pond Pump Speed: %d  " % pump_status)
        self.logging.info("---")
        self.logging.info("--------------------------------------------")
        self.logging.info("--------------------------------------------")
