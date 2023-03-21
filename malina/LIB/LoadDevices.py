from dotenv import dotenv_values

from malina.LIB.LoadRelayAutomation import LoadRelayAutomation

config = dotenv_values(".env")
UV_DEVICE = config['SWITCH_UV_ID']
FNT_DEVICE = config['SWITCH_FNT_ID']

UV_START_VOLT = float(config['UV_START_VOLT'])
UV_STOP_VOLT = float(config['UV_STOP_VOLT'])
FNT_START_VOLT = float(config['FNT_START_VOLT'])
FNT_STOP_VOLT = float(config['FNT_STOP_VOLT'])


class LoadDevices:
    def __init__(self, logger):
        self.uv_device_id = UV_DEVICE
        self.fnt_device_id = FNT_DEVICE
        self.logging = logger
        self.load_auto = LoadRelayAutomation(logger)
        self.update_uv_stats_info()
        self.update_fnt_dev_stats()

    @property
    def uv_sterilizer(self):
        return self.uv_device_id

    @property
    def fountain(self):
        return self.fnt_device_id

    def _is_uv_ready_to_start(self, inverter):
        return inverter >= UV_START_VOLT

    def _is_uv_ready_to_stop(self, inverter):
        return inverter <= UV_STOP_VOLT

    def _is_fnt_ready_to_start(self, inverter):
        return inverter >= FNT_START_VOLT

    def _is_fnt_ready_to_stop(self, inverter):
        return inverter <= FNT_STOP_VOLT

    def check_uv_devices(self, inverter_volt):
        uv_id = self.uv_device_id
        if self._is_uv_ready_to_start(inverter_volt):
            self.load_auto.load_switch_on(uv_id)

        if self._is_uv_ready_to_stop(inverter_volt):
            self.load_auto.load_switch_off(uv_id)

    def check_fnt_device(self, inverter_volt):
        fnt_id = self.fnt_device_id
        if self._is_fnt_ready_to_start(inverter_volt):
            self.load_auto.load_switch_on(fnt_id)

        if self._is_fnt_ready_to_stop(inverter_volt):
            self.load_auto.load_switch_off(fnt_id)

    def update_uv_stats_info(self):
        self.load_auto.update_status(self.uv_device_id)

    def update_fnt_dev_stats(self):
        self.load_auto.update_status(self.fnt_device_id)

    @property
    def get_uv_sw_state(self):
        return self.load_auto.get_device_statuses_by_id(self.uv_device_id)['switch_1']

    @property
    def get_fnt_sw_state(self):
        return self.load_auto.get_device_statuses_by_id(self.fnt_device_id)['switch_1']
