import logging
import time
from datetime import datetime, timedelta

from malina.LIB.FiloFifo import FiloFifo


class Device:
    def __init__(self, id, device_type, status: dict, name: str, desc: str, api_sw: str, coefficient, min_volt,
                 max_volt, priority, bus_voltage=0, extra=None):
        if extra is None:
            extra = {}
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
        self.time_last_switched = datetime.now() - timedelta(seconds=300)
        self.filo = FiloFifo()

    def get_id(self):
        return self.id

    @property
    def get_device_type(self):
        return self.device_type

    def get_device_desc(self):
        return self.desc

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

    def set_status(self, status):
        if not self.status.get('status') == status.get("status"):
            self.set_last_switched(datetime.now())
        self.status = status

    def set_last_switched(self, time_switch):
        self.last_switch = time_switch

    def get_status(self, key=None):
        if key is None:
            return self.status
        return self.status.get(key)

    def is_device_ready_to_switch_on(self):
        if self.time_last_switched is not None and (datetime.now() - self.time_last_switched).total_seconds() < 300:
            return False
        voltage = self.get_inverter_values()
        logging.error(f"----------Debugging is_device_ready_to_switch_on voltage: {voltage} min_volt {self.min_voltage} max voltage: {self.max_voltage}")
        if voltage < self.summer_saving_adjustment(self.min_voltage):
            return False
        if voltage > self.summer_saving_adjustment(self.max_voltage):
            return False
        return True

    def is_device_ready_to_switch_off(self):
        if self.time_last_switched is not None and (datetime.now() - self.time_last_switched).total_seconds() < 300:
            return False
        voltage = self.get_inverter_values()
        logging.error( f"----------Debugging is_device_ready_to_switch_off voltage: {voltage} min_volt {self.min_voltage} max voltage: {self.max_voltage}")
        if voltage < self.summer_saving_adjustment(self.min_voltage):
            return True
        if voltage > self.summer_saving_adjustment(self.max_voltage):
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
