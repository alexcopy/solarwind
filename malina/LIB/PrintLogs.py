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

    def integrity_error(self, avg_status, pond_relay, inverter):
        self.logging.error("-------------Switching to MAINS avg _status is: %3.2f ---------------" % avg_status)
        self.logging.error(
            "-------------Switching to POND RELAY status is: %d ------------------" % pond_relay)
        self.logging.error(
            "-------------Switching to INVERTER RELAY status is: %d --------------" % inverter)
        self.logging.error("---------------------------------------------------------------------")

    def log_run(self, filo_buffer: dict, invert_status, pump_status, solar_current):

        # sec_voltage = {k: v for k, v in filo_buffer.values() if k.startswith('1s') and k.endswith('voltage')}
        # sec_current = {k: v for k, v in filo_buffer.values() if k.startswith('1s') and k.endswith('current')}
        # sec_wattage = {k: v for k, v in filo_buffer.values() if k.startswith('1s') and k.endswith('wattage')}
        #
        # ten_voltage = {k: v for k, v in filo_buffer.values() if k.startswith('10m') and k.endswith('voltage')}
        # ten_current = {k: v for k, v in filo_buffer.values() if k.startswith('10m') and k.endswith('current')}
        # ten_wattage = {k: v for k, v in filo_buffer.values() if k.startswith('10m') and k.endswith('wattage')}
        #
        # ten_voltage = {k: v for k, v in filo_buffer.values() if k.startswith('10m') and k.endswith('voltage')}
        # ten_current = {k: v for k, v in filo_buffer.values() if k.startswith('10m') and k.endswith('current')}
        # ten_wattage = {k: v for k, v in filo_buffer.values() if k.startswith('10m') and k.endswith('wattage')}
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
        self.logging.info(" 1S Solar Current: %3.2f " % solar_current['1s_solar_current'])
        self.logging.info(" 10m Solar Current: %3.2f " % solar_current['10m_solar_current'])
        self.logging.info(" 10m Solar Current: %3.2f " % solar_current['1h_solar_current'])
        self.logging.info("--------------------------------------------")
        self.logging.info(" Pond Pump Speed: %d  " % pump_status['flow_speed'])
        self.logging.info(" Inverter Status is: %d  " % invert_status)
        self.logging.info("############################################")
        self.logging.info("--------------------------------------------")

    def printing_vars(self, fifo_buffer, inverter_status, statuses, pump_status, solar_current):
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
                units = "UN"
            name = i
            print("%s: %3.2f %s " % (name, fifo_buffer[i], units))

        print("")
        print(" Inverter Relay Status: %3.1f " % statuses['inverter_relay'])
        print(" Main Relay Status: %3.1f " % statuses['main_relay_status'])
        print(" Statuses Check: %3.1f " % statuses['status_check'])
        print(" 1S Solar Current: %3.2f " % solar_current['1s_solar_current'])
        print(" 10m Solar Current: %3.2f " % solar_current['10m_solar_current'])
        print("")
        print("---")

        status = "OFF"
        if inverter_status == 1:
            status = 'ON'

        m_r = "MAIN"
        if statuses['main_relay_status'] == 0:
            m_r = 'INVERT'

        print(" Inverter Status is: %s  " % status)
        print(" Main Relay works from: %s  " % m_r)
        print(" Solar 10m Power: %3.2f W " % solar_current['10m_solar_current'] * solar_current[
            '1s_inverter_bus_voltage'])
        print(" Pond Pump Speed: %d  " % pump_status['flow_speed'])
        print("---")
        print("--------------------------------------------")
