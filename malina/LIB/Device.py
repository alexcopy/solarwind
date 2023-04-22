class Device:
    def __init__(self, id, device_type, status, name, coefficient, min_volt, max_volt, priority):
        self.id = id
        self.device_type = device_type
        self.status = status
        self.name = name
        self.coefficient = coefficient
        self.min_volt = min_volt
        self.max_volt = max_volt
        self.priority = priority

    def get_id(self):
        return self.id

    def get_device_type(self):
        return self.device_type

    def get_name(self):
        return self.name

    def get_coefficient(self):
        return self.coefficient

    def get_min_volt(self):
        return self.min_volt

    def get_max_volt(self):
        return self.max_volt

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

    @property
    def power_consumption(self):
        return self.coefficient * (self.max_volt - self.min_volt)

    def __eq__(self, other):
        return isinstance(other, Device) and self.id == other.id
