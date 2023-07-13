import logging
import time
from datetime import datetime, timedelta

from malina.LIB.FiloFifo import FiloFifo


class Device:
    def __init__(self, id, device_type, status: dict, name: str, desc: str, api_sw: str, coefficient, min_volt,
                 max_volt, priority, bus_voltage=0, extra=None):
        if extra is None:
            extra = {'switch_time': 10}
        switch_time = int(extra['switch_time'])
        self.id = id
        self.device_type = device_type
        self.status = status
        self.name = name
        self.desc = desc
        self.coefficient = float(coefficient)
        self.min_voltage = float(min_volt)
        self.max_voltage = float(max_volt)
        self.priority = priority
        self.extra = extra
        self.api_sw = api_sw
        self.voltage = bus_voltage
        self.time_last_switched = int(datetime.now().timestamp())
        self.filo = FiloFifo()

    def get_id(self):
        return self.id

    @property
    def get_device_type(self):
        return self.device_type.upper()

    def get_device_desc(self):
        return self.desc

    def get_extra(self, key):
        if key in self.extra:
            return self.extra[key]
        else:
            return None

    def update_extra(self, key, value):
        if key in self.extra:
            self.extra.update({key: value})
        else:
            logging.error("Key is Unknown setup a new one")
            self.extra.update({key: value})

    def get_name(self):
        return self.name

    @property
    def get_api_sw(self):
        return self.api_sw

    def get_coefficient(self):
        return self.coefficient

    def get_min_volt(self):
        return self.min_voltage

    def get_max_volt(self):
        return self.max_voltage

    def get_priority(self):
        return self.priority

    def update_status(self, status):
        self.status.update(status)

    @property
    def last_switched(self):
        return self.time_last_switched

    @property
    def switched_delta(self):
        return self.time_last_switched - int(datetime.now().timestamp())

    def device_switched(self):
        self.time_last_switched = int(datetime.now().timestamp())

    def get_status(self, key=None):
        if key is None:
            return self.status
        return self.status.get(key)

    def _check_time(self):
        if self.time_last_switched is None:
            logging.error("The time of last switch is zerro")
            self.device_switched()

        if (int(datetime.now().timestamp()) - self.time_last_switched) < self.get_extra("switch_time"):
            return False
        return True

    def is_device_ready_to_switch_on(self):
        if self.get_status('switch_1'):
            logging.debug(f"The {self.get_name()} is already ON: no actions ")
            return False
        if not self._check_time():
            return False
        logging.debug(
            f"----------Debugging is_device_ready_to_switch_on NAme: {self.get_name()}  Device status: {self.get_status('switch_1')} min_volt {self.min_voltage} max voltage: {self.max_voltage}")
        if self.get_inverter_values() > self.max_voltage:
            return True
        return False

    def is_device_ready_to_switch_off(self):
        if not self.get_status('switch_1'):
            logging.debug(f"The {self.get_name()} is already OFF SW status is: {self.get_status('switch_1')}")
            return False

        if not self._check_time():
            logging.debug(f"The {self.get_name()} isn't ready to be switched as delta is: {self.switched_delta}")
            return False
        logging.debug(
            f"----------Debugging is_device_ready_to_switch_off Name: {self.get_name()} Device status: {self.get_status('switch_1')}  min_volt {self.min_voltage} max voltage: {self.max_voltage}")
        if self.get_inverter_values() < self.min_voltage:
            return True
        return False

    # todo finish this method, doesn't works at the moment:
    @property
    def power_consumption(self):
        return self.coefficient * (self.max_voltage - self.min_voltage)

    def get_inverter_values(self, slot='1s', value='bus_voltage'):
        inverter_voltage = self.filo.get_filo_value('%s_inverter' % slot, value)
        if len(inverter_voltage) == 0:
            return 0
        return FiloFifo.avg(inverter_voltage.pop())

    def summer_saving_adjustment(self, volt):
        hour = int(time.strftime("%H"))
        if hour >= 18:
            volt = volt + self.coefficient
        elif 8 < hour < 15:
            volt = volt - self.coefficient
        return volt

    def __eq__(self, other):
        return isinstance(other, Device) and self.id == other.id
