from datetime import datetime, timedelta


class Device:
    def __init__(self, id, device_type, status, name, desc, api_sw, coefficient, min_volt, max_volt, priority,
                 bus_voltage=18):
        self.id = id
        self.device_type = device_type
        self.status = status
        self.name = name
        self.desc = desc
        self.coefficient = coefficient
        self.min_voltage = min_volt
        self.max_voltage = max_volt
        self.priority = priority
        self.api_sw = api_sw
        self.voltage = bus_voltage
        self.time_last_switched = datetime.now() - timedelta(seconds=300)

    def get_id(self):
        return self.id

    def get_device_type(self):
        return self.device_type

    def get_device_desc(self):
        return self.desc

    def get_name(self):
        return self.name

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
        self.status.update(status)

    def get_status(self, key=None):
        if key is None:
            return self.status
        return self.status.get(key)

    def is_device_ready_to_switch_on(self):
        if self.time_last_switched is not None and (datetime.now() - self.time_last_switched).total_seconds() < 300:
            return False
        if self.voltage < self.min_voltage:
            return False
        if self.voltage > self.max_voltage:
            return False

        return True

    def is_device_ready_to_switch_off(self):
        if self.time_last_switched is not None and (datetime.now() - self.time_last_switched).total_seconds() < 300:
            return False
        if self.voltage < self.min_voltage:
            return True
        if self.voltage > self.max_voltage:
            return True
        return False

    @property
    def power_consumption(self):
        return self.coefficient * (self.max_voltage - self.min_voltage)

    def __eq__(self, other):
        return isinstance(other, Device) and self.id == other.id
