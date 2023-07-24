import logging
import time
from datetime import datetime, timedelta


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

    def get_id(self):
        return self.id

    @property
    def get_device_type(self):
        return self.device_type.upper()

    @property
    def get_desc(self):
        return self.desc

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
        return float(self.min_voltage)

    def get_max_volt(self):
        return float(self.max_voltage)

    def get_priority(self):
        return self.priority

    def update_status(self, status):
        self.status.update(status)

    @property
    def last_switched(self):
        return self.time_last_switched

    @property
    def switched_delta(self):
        return int(datetime.now().timestamp()) - self.time_last_switched

    def device_switched(self):
        self.time_last_switched = int(datetime.now().timestamp())

    @property
    def is_device_on(self):
        return bool(self.get_status(self.api_sw))

    def get_status(self, key=None):
        if key is None:
            return self.status
        return self.status.get(key, None)

    def _check_time(self):
        if self.time_last_switched is None:
            logging.error("The time of last switch is zerro")
            self.device_switched()
            return False

        if (int(datetime.now().timestamp()) - self.time_last_switched) < self.get_extra("switch_time"):
            logging.info(
                f"The {self.get_name()} is NOT ready to be switched OFF/ON as delta is: {self.switched_delta} and should be more then: {self.get_extra('switch_time')}")
            return False
        return True

    # todo investigate why int in switch_1 and not bool
    def extract_status_params(self, device_status):
        sw_status = {v['code']: v['value'] for v in device_status}
        if "Power" in sw_status:
            sw_status.update({"switch_1": int(sw_status.get("Power"))})
        if "switch_1" not in sw_status and "switch" in sw_status:
            sw_status.update({"switch_1": int(sw_status.get("switch")), "switch": int(sw_status.get("switch"))})
        extra_params = {
            'status': int(sw_status['switch_1']), 't': int(datetime.now().timestamp()), 'device_id': self.get_id(),
            'success': True}
        sw_status.update(extra_params)
        return sw_status

    def is_device_ready_to_switch_on(self, inverter_voltage):
        if bool(self.get_status('switch_1')):
            logging.info(f"The {self.get_name()} is already ON: no actions status {bool(self.get_status(self.api_sw))}")
            return False

        if not self._check_time():
            return False

        if inverter_voltage < 10:
            logging.error(f" !!!!!! Something went wrong for Inverter: {inverter_voltage} Needs to be checked !!!! ")
            return False

        if inverter_voltage > self.max_voltage:
            return True
        return False

    def is_device_ready_to_switch_off(self, inverter_voltage, invert_state):

        if not invert_state:
            return True

        if inverter_voltage < float(self.get_extra('min_trashhold')):
            return True

        if not self.is_device_on:
            logging.info(
                f"The {self.get_name()} is already OFF SW status is: {bool(self.get_status('switch_1'))} so no actions requires")
            return False

        if not self._check_time():
            return False

        if inverter_voltage < 10:
            logging.error(f" !!!!!! Something went wrong for Inverter: {inverter_voltage} Needs to be checked !!!! ")
            return False

        if inverter_voltage < self.min_voltage:
            return True
        return False

    # todo finish this method, doesn't works at the moment:
    @property
    def power_consumption(self):
        return self.coefficient * (self.max_voltage - self.min_voltage)

    def summer_saving_adjustment(self, volt):
        hour = int(time.strftime("%H"))
        if hour >= 18:
            volt = volt + self.coefficient
        elif 8 < hour < 15:
            volt = volt - self.coefficient
        return volt

    def __eq__(self, other):
        return isinstance(other, Device) and self.id == other.id
