import time

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
    def __init__(self, logger, device_manager):
        self.load_auto = LoadRelayAutomation(logger, device_manager)
        self.uv_device_id = UV_DEVICE
        self.fnt_device_id = FNT_DEVICE
        self.logging = logger
        self.main_status = 0
        self.update_uv_stats_info()
        self.update_fnt_dev_stats()

    @property
    def uv_sterilizer_id(self):
        return self.uv_device_id

    def update_main_relay_status(self, main_status: int):
        self.main_status = main_status

    @property
    def get_main_relay_status(self):
        return self.main_status

    @property
    def fountain_id(self):
        return self.fnt_device_id

    def _is_uv_ready_to_start(self, inverter):
        return inverter >= UV_START_VOLT

    def _is_uv_ready_to_stop(self, inverter, pump_flow_speed):
        return inverter <= UV_STOP_VOLT or pump_flow_speed <= 50

    def _is_fnt_ready_to_start(self, inverter):
        return inverter >= FNT_START_VOLT

    def _is_fnt_ready_to_stop(self, inverter, pump_flow_speed):
        return inverter <= FNT_STOP_VOLT or pump_flow_speed <= 70

    def check_uv_devices(self, inverter_volt, pump_flow_speed):
        uv_id = self.uv_device_id
        api_data = self.get_uv_sw_state

        if self._is_uv_ready_to_start(inverter_volt):
            self.load_auto.load_switch_on(uv_id, api_data)

        if self._is_uv_ready_to_stop(inverter_volt, pump_flow_speed):
            self.load_auto.load_switch_off(uv_id, api_data)

    def check_fnt_device(self, inverter_volt, pump_flow_speed):
        fnt_id = self.fnt_device_id
        api_data = self.get_fnt_sw_state
        if self._is_fnt_ready_to_start(inverter_volt):
            self.load_auto.load_switch_on(fnt_id, api_data)

        if self._is_fnt_ready_to_stop(inverter_volt, pump_flow_speed):
            self.load_auto.load_switch_off(fnt_id, api_data)

    def update_uv_stats_info(self):
        self.load_auto.update_status(self.uv_device_id)

    def update_fnt_dev_stats(self):
        self.load_auto.update_status(self.fnt_device_id)

    @property
    def get_uv_sw_state(self):
        status = self.load_auto.get_device_statuses_by_id(self.uv_device_id)
        xtra_data = {'name': "UV_Clarifier", 'from_main': self.get_main_relay_status, 'status': int(status['switch_1'])}
        return status.update(xtra_data)

    @property
    def get_fnt_sw_state(self):
        status = self.load_auto.get_device_statuses_by_id(self.fnt_device_id)
        xtra_data = {'name': "Pond Fountain", 'from_main': self.get_main_relay_status,
                     'status': int(status['switch_1'])}
        return status.update(xtra_data)
