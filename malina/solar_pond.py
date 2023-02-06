from INA3221 import SDL_Pi_INA3221
import importlib.util
import time
from pathlib import Path
import logging
import os
import requests
import logging.handlers
import json
from dotenv import dotenv_values
from apscheduler.schedulers.background import BackgroundScheduler

try:
    importlib.util.find_spec('RPi.GPIO')
    import RPi.GPIO as GPIO
except ImportError:

    import FakeRPi.GPIO as GPIO
    import FakeRPi.Utilities

    FakeRPi.Utilities.mode = FakeRPi.Utilities.PIN_TYPE_BOARD

TIME_TIK = 1
POND_RELAY = 11
INVER_RELAY = 13
INVER_CHECK = 15
CYCLE_COUNTER = 1
CUT_OFF_VOLT = 21
SWITCH_ON_VOLT = 26

config = dotenv_values(".env")
LOG_DIR = config['LOG_DIR']
API_URL = config["API_URL"]

OUTPUT_CHANNEL = 1
SOLAR_CELL_CHANNEL = 2
LIPO_BATTERY_CHANNEL = 3
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

GPIO.setmode(GPIO.BOARD)
GPIO.setup(POND_RELAY, GPIO.OUT)
GPIO.setup(INVER_RELAY, GPIO.OUT)
GPIO.setup(INVER_CHECK, GPIO.IN)


def handler(signum, frame):
    print('Ctrl+Z pressed, but ignored')
    GPIO.cleanup()
    os.system('kill -STOP %d' % os.getpid())


class SolarPond:
    def __init__(self):
        self.FILTER_FLUSH = []
        self.FIFO_BUFF = {}
        self.shunt_load = SDL_Pi_INA3221.SDL_Pi_INA3221(addr=0x40)
        self.shunt_bat = 0.00159
        self.conf_logger()

        self.FILO_BUFF = {
            'converter_current': [],
            'bat_voltage': [],
            'bat_current': [],
            'solar_current': [],
            'status_check': [],
            '10m_converter_current': [],
            '10m_bat_voltage': [],
            '10m_bat_current': [],
            '10m_solar_current': [],
            '1h_converter_current': [],
            '1h_bat_voltage': [],
            '1h_bat_current': [],
            '1h_solar_current': [],
        }
        self.read_vals()
        self.switch_to_solar_power()

    def avg(self, l):
        if len(l) == 0:
            return 0
        return float(round(sum(l, 0.0) / len(l), 2))

    def switch_to_solar_power(self):
        self.inverter_switch('ON')
        time.sleep(4)
        inverter_state = self.inverter_switch('ON')

        if inverter_state == 1:
            self.pond_relay_on_off('INV')
        else:
            self.switch_to_main_power()
            logging.error("CANNOT SWITCH ON THE INVERTER PLS CHECK  !!!!!  the signal is: %d " % inverter_state)
        return self.status_check

    def switch_to_main_power(self):
        self.inverter_switch('OFF')
        time.sleep(2)
        inverter_state = self.inverter_switch('OFF')
        if inverter_state == 0:
            logging.info("All good Inverter has been switched off successfully: %d " % inverter_state)
        else:
            logging.error("CANNOT SWITCH OFF THE INVERTER PLS CHECK  !!!!!  the signal is: %d " % inverter_state)

        logging.info("All good Switching to main power: %d " % inverter_state)
        self.pond_relay_on_off('MAIN')
        return self.status_check

    @property
    def status_check(self):
        return GPIO.input(POND_RELAY) ^ GPIO.input(INVER_CHECK)

    def pond_relay_on_off(self, on_off: str):
        on_off = on_off.upper()
        if on_off not in ['INV', 'MAIN']:
            logging.error("The  WRONG Signal to POND_RELAY SENT!!!!!  the signal is: %s " % on_off)
            return GPIO.output(POND_RELAY, True)
        if on_off == 'INV':
            return GPIO.output(POND_RELAY, False)
        elif on_off == 'MAIN':
            return GPIO.output(POND_RELAY, True)
        else:
            logging.error("SOMETHING IS WRONG !!!!!  the signal is: %s " % on_off)
        return GPIO.output(POND_RELAY, True)

    def conf_logger(self):
        current_path = Path(LOG_DIR)
        log_name = time.strftime("info")
        filename = current_path.joinpath(f'{log_name}.log')
        log_handler = logging.handlers.RotatingFileHandler(filename, maxBytes=6291456, backupCount=10)
        formatter = logging.Formatter(
            '%(asctime)s program_name [%(process)d]: %(message)s',
            '%b %d %H:%M:%S')
        formatter.converter = time.gmtime  # if you want UTC time
        log_handler.setFormatter(formatter)
        logger = logging.getLogger()
        logger.addHandler(log_handler)
        logger.setLevel(logging.DEBUG)

        # to log errors messages
        error_log = logging.FileHandler(os.path.join(current_path, 'error.log'))
        error_log.setFormatter(formatter)
        error_log.setLevel(logging.ERROR)
        logger.addHandler(error_log)

    def read_vals(self):
        busvoltage1 = float(self.shunt_load.getBusVoltage_V(LIPO_BATTERY_CHANNEL))
        shuntvoltage1 = float(self.shunt_load.getShuntVoltage_mV(LIPO_BATTERY_CHANNEL))
        bat_current = float(self.shunt_load.getCurrent_mA(LIPO_BATTERY_CHANNEL, self.shunt_bat)) - 350
        bat_voltage = float(busvoltage1 + (shuntvoltage1 / 1000))
        converter_current = float(self.shunt_load.getCurrent_mA(OUTPUT_CHANNEL, self.shunt_bat))

        if abs(bat_current) < 200:
            bat_current = 0

        if abs(converter_current) < 300:
            converter_current = 0
        solar_current = converter_current + bat_current
        self.FIFO_BUFF = {
            'busvoltage1': round(busvoltage1, 2),
            'bat_voltage': round(bat_voltage, 2),
            'shuntvoltage1': round(shuntvoltage1, 2),
            'bat_current': round(bat_current, 2),
            'converter_current': round(converter_current, 2),
            'solar_current': round(solar_current, 2),
        }
        self.FILO_BUFF['bat_voltage'].append(round(busvoltage1, 2))
        self.FILO_BUFF['bat_current'].append(round(bat_current, 2))
        self.FILO_BUFF['converter_current'].append(round(converter_current, 2))
        self.FILO_BUFF['solar_current'].append(round(solar_current, 2))
        self.FILO_BUFF['status_check'].append(self.status_check),

    def update_filo_buffer(self):
        timestamp = int(time.time())
        if timestamp % 10 == 0:
            self.FILO_BUFF['10m_bat_voltage'].append(self.avg(self.FILO_BUFF['bat_voltage']))
            self.FILO_BUFF['10m_bat_current'].append(self.avg(self.FILO_BUFF['bat_current']))
            self.FILO_BUFF['10m_converter_current'].append(self.avg(self.FILO_BUFF['converter_current']))
            self.FILO_BUFF['10m_solar_current'].append(self.avg(self.FILO_BUFF['solar_current']))

        if timestamp % 60 == 0:
            self.FILO_BUFF['1h_bat_voltage'].append(self.avg(self.FILO_BUFF['10m_bat_voltage']))
            self.FILO_BUFF['1h_bat_current'].append(self.avg(self.FILO_BUFF['10m_bat_current']))
            self.FILO_BUFF['1h_converter_current'].append(self.avg(self.FILO_BUFF['10m_converter_current']))
            self.FILO_BUFF['1h_solar_current'].append(self.avg(self.FILO_BUFF['10m_solar_current']))

    def cleanup_filo(self):
        for v in self.FILO_BUFF:
            self.FILO_BUFF[v] = self.FILO_BUFF[v][-60:]

    def ready_to_send_avg(self):
        return len(self.FILO_BUFF['1h_bat_voltage']) > 10

    def processing_reads(self):
        try:
            self.cleanup_filo()
            self.read_vals()
            self.update_filo_buffer()
            self.filter_flush_run()
            self.cleanup_filo()
            self.printing_vars()
            self.log_run()
        except Exception as ex:
            logging.warning(ex)

    def inverter_switch(self, on_off: str):
        on_off = on_off.upper()
        if not on_off in ['ON', 'OFF']:
            logging.error("The  WRONG Signal to INVERTER SWITCH SENT!!!!!  the signal is: %s " % on_off)
            return GPIO.input(INVER_CHECK)

        status = GPIO.input(INVER_CHECK)
        if on_off == 'ON' and status == 1:
            return 1
        if on_off == 'OFF' and status == 0:
            return 0
        self.inverter_on_off()
        return GPIO.input(INVER_CHECK)

    def inverter_on_off(self):
        time.sleep(.5)
        GPIO.output(INVER_RELAY, True)
        time.sleep(.5)
        GPIO.output(INVER_RELAY, False)

    def send_ff_data(self, shunt_name: str):
        payload = json.dumps({
            "max_current": max(self.FILTER_FLUSH),
            "duration": len(self.FILTER_FLUSH) * TIME_TIK,
            "name": shunt_name
        })
        url_path = "%sfflash" % API_URL
        self.send_to_remote(url_path, payload)

    def send_to_remote(self, url_path, payload):
        self._loger_remote(url_path)
        headers = {
            'Content-Type': 'application/json'
        }
        try:
            response = requests.request("POST", url_path, headers=headers, data=payload)
            return response.text
        except Exception as ex:
            logging.info(ex)
            return "error"

    def send_avg_data(self):
        for v in self.FILO_BUFF:
            if not '1h' in v:
                continue
            val_type = "V"
            if 'current' in v:
                val_type = "A"

            payload = json.dumps({
                "value_type": val_type,
                "name": v,
                "inverter_status": GPIO.input(INVER_CHECK),
                "avg_value": self.avg(self.FILO_BUFF[v]),
                "serialized": self.FILO_BUFF[v],
            })
            url_path = "%ssolarpower" % API_URL
            self.send_to_remote(url_path, payload)

    def _loger_remote(self, url_path):
        logging.info("------------SENDING TO REMOTE--------------")
        logging.info(url_path)
        logging.info("--------------------------------------------")

    def log_run(self):
        logging.info("--------------------------------------------")
        logging.info("AVG Battery Voltage:  %3.2f V" % self.avg(self.FILO_BUFF['bat_voltage']))
        logging.info("AVG Battery Current 1:  %3.2f mA" % self.avg(self.FILO_BUFF['bat_current']))
        logging.info("AVG Converter Current 3:  %3.2f mA" % self.avg(self.FILO_BUFF['converter_current']))
        logging.info("AVG  Solar Current:  %3.2f mA" % self.avg(self.FILO_BUFF['solar_current']))
        logging.info("--------------------------------------------")
        logging.info("AVG 10m Battery Voltage:  %3.2f V" % self.avg(self.FILO_BUFF['10m_bat_voltage']))
        logging.info("AVG 10m Battery Current 1:  %3.2f mA" % self.avg(self.FILO_BUFF['10m_bat_current']))
        logging.info("AVG 10m Converter Current 3:  %3.2f mA" % self.avg(self.FILO_BUFF['10m_converter_current']))
        logging.info("AVG 10m  Solar Current:  %3.2f mA" % self.avg(self.FILO_BUFF['10m_solar_current']))
        logging.info("--------------------------------------------")
        logging.info("AVG 1h  Battery Voltage:  %3.2f V" % self.avg(self.FILO_BUFF['1h_bat_voltage']))
        logging.info("AVG 1h  Battery Current 1:  %3.2f mA" % self.avg(self.FILO_BUFF['1h_bat_current']))
        logging.info("AVG 1h  Converter Current 3:  %3.2f mA" % self.avg(self.FILO_BUFF['1h_converter_current']))
        logging.info("AVG 1h   Solar Current:  %3.2f mA" % self.avg(self.FILO_BUFF['1h_solar_current']))
        logging.info("--------------------------------------------")
        wattage = (self.avg(self.FILO_BUFF['10m_bat_voltage']) * self.avg(self.FILO_BUFF['10m_solar_current'])) / 1000
        logging.info(" AVG 10 min Solar Wattage is: %3.2f  W" % wattage)
        logging.info(" Inverter Status is: %d  " % GPIO.input(INVER_CHECK))
        logging.info("############################################")
        logging.info("--------------------------------------------")
        print("--------------------------------------------")
        print("")

    def printing_vars(self):
        wattage = (self.avg(self.FILO_BUFF['10m_bat_voltage']) * self.avg(self.FILO_BUFF['10m_solar_current'])) / 1000
        print("")
        print("--------------------------------------------")
        print("Bus Voltage: %3.2f V " % self.FIFO_BUFF['busvoltage1'])
        print("Bat Voltage: %3.2f V " % self.FIFO_BUFF['bat_voltage'])
        print("SHUNT  Voltage: %3.2f V " % self.FIFO_BUFF['busvoltage1'])
        print("Battery Current 1:  %3.2f mA" % self.FIFO_BUFF['bat_current'])
        print("Converter Current 3:  %3.2f mA" % self.FIFO_BUFF['converter_current'])
        print("Solar Current:  %3.2f mA" % self.FIFO_BUFF['solar_current'])
        print("")
        print(" AVG 10 min Solar Wattage is: %3.2f  W" % wattage)
        print(" Inverter Status is: %d  " % GPIO.input(INVER_CHECK))
        print("############################################")

    def inverter_run(self):
        try:

            if time.strftime("%H:%M") == '12:00':
                self.switch_to_solar_power()

            # converter switch OFF
            if self.avg(self.FILO_BUFF['bat_voltage']) < CUT_OFF_VOLT and len(self.FILO_BUFF['bat_voltage']) > 15:
                self.switch_to_main_power()
                self.send_avg_data()

            # converter switch ON
            if self.avg(self.FILO_BUFF['bat_voltage']) > SWITCH_ON_VOLT and len(self.FILO_BUFF['bat_voltage']) > 30:
                self.switch_to_solar_power()
                self.send_avg_data()
            self.integrity_check()

        except Exception as ex:
            logging.warning(ex)

    def filter_flush_run(self):
        now_cc = self.FIFO_BUFF['converter_current']
        avg_cc = self.avg(self.FILO_BUFF['converter_current'])
        cc_size = len(self.FILO_BUFF['converter_current'])
        timestamp = int(time.time())
        if abs(now_cc - avg_cc) > 8000 and cc_size > 30:
            self.FILTER_FLUSH.append(now_cc)
        else:
            if len(self.FILTER_FLUSH) > 5:
                self.send_ff_data('converter_current')
            self.FILTER_FLUSH = []
        return timestamp

    def reset_ff(self):
        if len(self.FILTER_FLUSH) < 5:
            self.FILTER_FLUSH = []

    def run_read_vals(self):
        reed = BackgroundScheduler()
        hour = int(time.strftime("%H"))
        send_time_slot = 600
        inv_time_slot = 30

        # Don't need to send stats overnight
        if hour > 21 or hour < 5:
            send_time_slot = 1800

        reed.add_job(self.send_avg_data, 'interval', seconds=send_time_slot)
        reed.add_job(self.inverter_run, 'interval', seconds=inv_time_slot)
        reed.start()
        # reed.shutdown()

        # logical XOR in case of to equal states. Inverter is ON when GPIO.input(INVER_CHECK) == 1
        # so in this case GPIO.input(POND_RELAY) should be in 0 meaning we're working from battery and vice versa
        # in case  we're working from mains Inverter should be in state GPIO.input(INVER_CHECK) == 0 and POND_RELAY
        # state should be 1 which mean relay isn't switched.

    def integrity_check(self):
        avg_status = self.avg(self.FILO_BUFF['status_check'])
        if avg_status < 0.5:
            GPIO.input(INVER_CHECK)
            logging.error("-------------Something IS VERY Wrong pls check logs -----------------")
            logging.error("-------------Switching to MAINS avg _status is: %3.2f ---------------" % avg_status)
            logging.error(
                "-------------Switching to POND RELAY status is: %d ------------------" % GPIO.input(POND_RELAY))
            logging.error(
                "-------------Switching to INVERTER RELAY status is: %d --------------" % GPIO.input(INVER_CHECK))
            logging.error("---------------------------------------------------------------------")
            self.switch_to_main_power()


if __name__ == '__main__':
    sp = SolarPond()
    sp.run_read_vals()
    while True:
        timestamp = int(time.time())
        time.sleep(TIME_TIK)
        sp.processing_reads()
        if timestamp % 120 == 0:
            sp.reset_ff()
