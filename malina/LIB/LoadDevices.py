import time

from dotenv import dotenv_values

from malina.LIB.LoadRelayAutomation import LoadRelayAutomation

POND_FOUNTAIN = "Pond Fountain"

UV_CLARIFIER = "UV_Clarifier"
INVERTER = "INVERTER"
AIRFLOW = "AIRFLOW"

config = dotenv_values(".env")

INVERT_ID = config["INVERT_ID"]
INVERT_STOP = float(config["INVERT_STOP_VOLT"])
INVERT_START = float(config["INVERT_START_VOLT"])

UV_DEVICE = config['SWITCH_UV_ID']
UV_START_VOLT = float(config['UV_START_VOLT'])
UV_STOP_VOLT = float(config['UV_STOP_VOLT'])

FNT_DEVICE = config['SWITCH_FNT_ID']
FNT_START_VOLT = float(config['FNT_START_VOLT'])
FNT_STOP_VOLT = float(config['FNT_STOP_VOLT'])

AIR_COMPRESS = config['AIR_COMPRESS']
DAY_TIME_COMPENSATE = 1


class LoadDevices:
    def __init__(self, logger, device_manager):
        self.load_auto = LoadRelayAutomation(logger, device_manager)
        self.uv_device_id = UV_DEVICE
        self.fnt_device_id = FNT_DEVICE
        self.inverter_id = INVERT_ID
        self.compensation = DAY_TIME_COMPENSATE
        self.switch_on_timer = {
            UV_DEVICE: int(time.time()),
            FNT_DEVICE: int(time.time()),
        }
        self.logging = logger

    @property
    def uv_sterilizer_id(self):
        return self.uv_device_id

    @property
    def fountain_id(self):
        return self.fnt_device_id

    @property
    def invert_id(self):
        return self.inverter_id

    def _is_uv_ready_to_start(self, inverter):
        if self.load_auto.get_main_relay_status == 0:
            return False
        start_volt = self.day_saving_start_adjustment(UV_START_VOLT)
        timer_ok = self._is_timer_ok(UV_DEVICE)
        return (inverter >= start_volt) and timer_ok

    def _is_uv_ready_to_stop(self, inverter):
        if self.load_auto.get_main_relay_status == 0:
            return True
        stop_volt = self.day_saving_stop_adjustment(UV_STOP_VOLT)
        timer_ok = self._is_timer_ok(UV_DEVICE)
        return (inverter <= stop_volt) and timer_ok

    def _is_fnt_ready_to_start(self, inverter):
        if self.load_auto.get_main_relay_status == 0:
            return False
        start_volt = self.day_saving_start_adjustment(FNT_START_VOLT)
        timer_ok = self._is_timer_ok(FNT_DEVICE)
        return (inverter >= start_volt) and timer_ok

    def _is_timer_ok(self, dev_name: str):
        timer_ok = (int(time.time()) - self.switch_on_timer[dev_name]) >= 300
        return timer_ok

    def _is_fnt_ready_to_stop(self, inverter):
        if self.load_auto.get_main_relay_status == 0:
            return True
        stop_volt = self.day_saving_stop_adjustment(FNT_STOP_VOLT)
        timer_ok = self._is_timer_ok(FNT_DEVICE)
        return (inverter <= stop_volt) and timer_ok

    @staticmethod
    def day_saving_stop_adjustment(stop_volt):
        hour = int(time.strftime("%H"))
        if hour >= 17:
            stop_volt = stop_volt + 1.5
        return stop_volt

    @staticmethod
    def day_saving_start_adjustment(start_volt):
        hour = int(time.strftime("%H"))
        if 8 < hour < 15:
            start_volt = start_volt - 1.5
        return start_volt

    def _is_invert_ready_to_stop(self, inverter):
        return inverter <= INVERT_STOP

    def _is_invert_ready_to_start(self, inverter):
        return inverter >= INVERT_START

    def uv_switch_on_off(self, inverter_volt):
        uv_id = self.uv_device_id
        if self._is_uv_ready_to_start(inverter_volt):
            self.switch_on_timer[UV_DEVICE] = int(time.time())
            self.load_auto.load_switch_on(AIR_COMPRESS, AIRFLOW)
            return self.load_auto.load_switch_on(uv_id, UV_CLARIFIER)

        if self._is_uv_ready_to_stop(inverter_volt):
            self.switch_on_timer[UV_DEVICE] = int(time.time())
            self.load_auto.load_switch_off(AIR_COMPRESS, AIRFLOW)
            self.load_auto.load_switch_off(uv_id, UV_CLARIFIER)

    def fnt_switch_on_off(self, inverter_volt):
        fnt_id = self.fnt_device_id
        if self._is_fnt_ready_to_start(inverter_volt):
            self.load_auto.load_switch_on(fnt_id, POND_FOUNTAIN)
            self.switch_on_timer[FNT_DEVICE] = int(time.time())
            return

        if self._is_fnt_ready_to_stop(inverter_volt):
            self.switch_on_timer[FNT_DEVICE] = int(time.time())
            return self.load_auto.load_switch_off(fnt_id, POND_FOUNTAIN)

    def invert_switch_on_off(self, inverter_volt):
        inv_id = self.inverter_id
        if self._is_invert_ready_to_start(inverter_volt):
            self.load_auto.load_switch_on(inv_id, INVERTER, "switch")

        if self._is_invert_ready_to_stop(inverter_volt):
            self.load_auto.load_switch_off(inv_id, INVERTER, "switch")

    def update_uv_stats_info(self):
        self.load_auto.update_status(self.uv_device_id, UV_CLARIFIER)

    def update_fnt_dev_stats(self):
        self.load_auto.update_status(self.fnt_device_id, POND_FOUNTAIN)

    def update_invert_stats(self):
        self.load_auto.update_status(self.inverter_id, INVERTER)

    @property
    def get_uv_sw_state(self):
        return self.load_auto.get_device_statuses_by_id(self.uv_device_id, UV_CLARIFIER)

    @property
    def get_fnt_sw_state(self):
        return self.load_auto.get_device_statuses_by_id(self.fnt_device_id, POND_FOUNTAIN)

    @property
    def get_invert_credentials(self):
        return self.inverter_id, INVERTER
