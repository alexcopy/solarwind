import time
import datetime

from pathlib import Path
import logging
import signal
import os
import requests
import json

from INA3221 import SDL_Pi_INA3221
import importlib.util

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
LOG_DIR = 'dir_with_logs'
API_URL = "https://test.com/"

OUTPUT_CHANNEL = 1
SOLAR_CELL_CHANNEL = 2
LIPO_BATTERY_CHANNEL = 3

Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

GPIO.setmode(GPIO.BOARD)
GPIO.setup(POND_RELAY, GPIO.OUT)
GPIO.setup(INVER_RELAY, GPIO.OUT)
GPIO.setup(INVER_CHECK, GPIO.IN)

FILO_BUFF = {
    'converter_current': [],
    'bat_voltage': [],
    'bat_current': [],
    'solar_current': [],
    '10m_converter_current': [],
    '10m_bat_voltage': [],
    '10m_bat_current': [],
    '10m_solar_current': [],
    '1h_converter_current': [],
    '1h_bat_voltage': [],
    '1h_bat_current': [],
    '1h_solar_current': [],
}
FILTER_FLUSH = []


def avg(l):
    if len(l) == 0:
        return 0
    return sum(l, 0.0) / len(l)


def inverter_switch(on_off: str):
    on_off = on_off.upper()
    status = GPIO.input(INVER_CHECK)
    if on_off == 'ON' and status == 1:
        return 1
    if on_off == 'OFF' and status == 0:
        return 0
    time.sleep(.4)
    GPIO.output(INVER_RELAY, True)
    time.sleep(.2)
    GPIO.output(INVER_RELAY, False)
    return GPIO.input(INVER_CHECK)


def conf_logger(dir, level):
    format = '%(asctime)s %(levelname)s {%(module)s} [%(funcName)s] %(message)s'
    s = time.strftime("%d_%m_%Y_%H_%M_%S")
    filename = dir.joinpath(f'{s}.log')
    datefmt = '%m/%d/%Y %I:%M:%S %p'
    logging.basicConfig(format=format, filename=filename, filemode='wt', level=level, datefmt=datefmt)
    return logging.getLogger()


logger = conf_logger(Path(LOG_DIR), logging.INFO)

print("")
print("Program Started at:" + time.strftime("%Y-%m-%d %H:%M:%S"))
print("")

filename = time.strftime("%Y-%m-%d%H:%M:%SRTCTest") + ".txt"
starttime = datetime.datetime.utcnow()
shunt_bat = 0.00159
shunt_conv = 0.1

shunt_load = SDL_Pi_INA3221.SDL_Pi_INA3221(addr=0x40)


# inverter_switch('on')
# GPIO.output(POND_RELAY, False)


def handler(signum, frame):
    print('Ctrl+Z pressed, but ignored')
    GPIO.cleanup()
    os.system('kill -STOP %d' % os.getpid())


def send_ff_data(shunt_name: str):
    payload = json.dumps({
        "max_current": max(FILTER_FLUSH),
        "duration": len(FILTER_FLUSH) * TIME_TIK,
        "name": shunt_name
    })
    url_path = "%sfflash" % API_URL
    send_to_remote(url_path, payload)


def send_to_remote(url_path, payload):
    logger.info("------------SENDING TO REMOTE--------------")
    logger.info(url_path)
    logger.info("--------------------------------------------")
    headers = {
        'Content-Type': 'application/json'
    }
    try:
        response = requests.request("POST", url_path, headers=headers, data=payload)
        return response.text
    except Exception as ex:
        logger.info(ex)
        return "error"


def send_avg_data(avg_buffer, counter):
    for v in avg_buffer:
        if not '1h' in v:
            continue
        val_type = "V"
        if 'current' in v:
            val_type = "A"

        payload = json.dumps({
            "value_type": val_type,
            "name": v,
            "inverter_status": GPIO.input(INVER_CHECK),
            "avg_value": avg(avg_buffer[v]),
            "serialized": avg_buffer[v],
        })
        url_path = "%ssolarpower" % API_URL
        send_to_remote(url_path, payload)


signal.signal(signal.SIGTSTP, handler)


def _logging():
    print("Bus Voltage: %3.2f V " % busvoltage1)
    print("Bat Voltage: %3.2f V " % bat_voltage)
    print("SHUNT  Voltage: %3.2f V " % busvoltage1)
    print("Battery Current 1:  %3.2f mA" % bat_current)
    print("Converter Current 3:  %3.2f mA" % converter_current)
    print("Solar Current:  %3.2f mA" % solar_current)
    # logger.info("Battery Voltage:  %3.2f V" % bat_voltage)
    # logger.info("Battery Current 1:  %3.2f mA" % bat_current)
    # logger.info("Converter Current 3:  %3.2f mA" % converter_current)
    # logger.info("Solar Current:  %3.2f mA" % solar_current)
    logger.info("--------------------------------------------")
    logger.info("AVG Battery Voltage:  %3.2f V" % avg(FILO_BUFF['bat_voltage']))
    logger.info("AVG Battery Current 1:  %3.2f mA" % avg(FILO_BUFF['bat_current']))
    logger.info("AVG Converter Current 3:  %3.2f mA" % avg(FILO_BUFF['converter_current']))
    logger.info("AVG  Solar Current:  %3.2f mA" % avg(FILO_BUFF['solar_current']))
    logger.info("--------------------------------------------")
    logger.info("AVG 10m Battery Voltage:  %3.2f V" % avg(FILO_BUFF['10m_bat_voltage']))
    logger.info("AVG 10m Battery Current 1:  %3.2f mA" % avg(FILO_BUFF['10m_bat_current']))
    logger.info("AVG 10m Converter Current 3:  %3.2f mA" % avg(FILO_BUFF['10m_converter_current']))
    logger.info("AVG 10m  Solar Current:  %3.2f mA" % avg(FILO_BUFF['10m_solar_current']))
    logger.info("--------------------------------------------")
    logger.info("AVG 1h  Battery Voltage:  %3.2f V" % avg(FILO_BUFF['1h_bat_voltage']))
    logger.info("AVG 1h  Battery Current 1:  %3.2f mA" % avg(FILO_BUFF['1h_bat_current']))
    logger.info("AVG 1h  Converter Current 3:  %3.2f mA" % avg(FILO_BUFF['1h_converter_current']))
    logger.info("AVG 1h   Solar Current:  %3.2f mA" % avg(FILO_BUFF['1h_solar_current']))
    logger.info(" Inverter Status is: %d  " % GPIO.input(INVER_CHECK))
    logger.info("############################################")
    logger.info("--------------------------------------------")
    print("--------------------------------------------")
    print("")


while True:
    try:
        print("------------------------------")
        logger.info("--------------------------------------------")
        busvoltage1 = shunt_load.getBusVoltage_V(LIPO_BATTERY_CHANNEL)
        shuntvoltage1 = shunt_load.getShuntVoltage_mV(LIPO_BATTERY_CHANNEL)

        bat_current = shunt_load.getCurrent_mA(LIPO_BATTERY_CHANNEL, shunt_bat)

        bat_voltage = busvoltage1 + (shuntvoltage1 / 1000)
        converter_current = shunt_load.getCurrent_mA(OUTPUT_CHANNEL, shunt_bat)

        if abs(bat_current) < 200:
            bat_current = 0

        if abs(converter_current) < 300:
            converter_current = 0

        solar_current = converter_current + bat_current

        FILO_BUFF['bat_voltage'].append(round(busvoltage1, 2))
        FILO_BUFF['bat_current'].append(round(bat_current, 2))
        FILO_BUFF['converter_current'].append(round(converter_current, 2))
        FILO_BUFF['solar_current'].append(round(solar_current, 2))

        _logging()

        # keeping buffer size equal to 60 elements FILO
        for v in FILO_BUFF:
            FILO_BUFF[v] = FILO_BUFF[v][-60:]

        if CYCLE_COUNTER % 10 == 0:
            FILO_BUFF['10m_bat_voltage'].append(avg(FILO_BUFF['bat_voltage']))
            FILO_BUFF['10m_bat_current'].append(avg(FILO_BUFF['bat_current']))
            FILO_BUFF['10m_converter_current'].append(avg(FILO_BUFF['converter_current']))
            FILO_BUFF['10m_solar_current'].append(avg(FILO_BUFF['solar_current']))

        if CYCLE_COUNTER % 60 == 0:
            FILO_BUFF['1h_bat_voltage'].append(avg(FILO_BUFF['10m_bat_voltage']))
            FILO_BUFF['1h_bat_current'].append(avg(FILO_BUFF['10m_bat_current']))
            FILO_BUFF['1h_converter_current'].append(avg(FILO_BUFF['10m_converter_current']))
            FILO_BUFF['1h_solar_current'].append(avg(FILO_BUFF['10m_solar_current']))


# converter switch OFF
        if avg(FILO_BUFF['bat_voltage']) < 21 and len(FILO_BUFF['bat_voltage']) > 30:
            GPIO.output(POND_RELAY, True)
            inverter_switch('OFF')
            send_avg_data(FILO_BUFF,  CYCLE_COUNTER)

# converter switch ON
        if avg(FILO_BUFF['bat_voltage']) > 26 and len(FILO_BUFF['bat_voltage']) > 30:
            GPIO.output(POND_RELAY, False)
            inverter_switch('ON')
            send_avg_data(FILO_BUFF,  CYCLE_COUNTER)

        if abs(converter_current) > 11000:
            FILTER_FLUSH.append(converter_current)
        else:
            if len(FILTER_FLUSH) > 0:
                send_ff_data('converter_current')
            FILTER_FLUSH = []

# send off data to remote API
        if CYCLE_COUNTER % 60 == 0:
            send_avg_data(FILO_BUFF,  CYCLE_COUNTER)

        if CYCLE_COUNTER > 84600:
            CYCLE_COUNTER = 1

        time.sleep(TIME_TIK)
        CYCLE_COUNTER += TIME_TIK
    except Exception as ex:
        print(ex)
