#!/usr/bin/env python

import time

INVERT_CHANNEL = 1
LEISURE_BAT_CHANNEL = 2
TIGER_BAT_CHANNEL = 3
SHUNT_IMP = 0.00159


class FiloFifo:
    def __init__(self, logging, shunt_load, bus_voltage='bus_voltage', wattage='wattage',
                 bat_current='bat_current'):

        self.shunt_bat = SHUNT_IMP
        self.logging = logging
        self.buffer_fields = [bus_voltage, wattage, bat_current]
        self.bus_voltage = bus_voltage
        self.wattage = wattage
        self.inverter_on = 0
        self.bat_current = bat_current
        self.prefixes = ['1s_', '10m_', '1h_']
        self.FILO = {}
        self.FIFO = {}
        self.REL_STATUS = {'inverter_relay': [], 'main_relay_status': [], 'status_check': []}
        self.shunt_load = shunt_load
        self.load_names = {'tiger': TIGER_BAT_CHANNEL, 'leisure': LEISURE_BAT_CHANNEL, 'inverter': INVERT_CHANNEL}
        self._setup_buffers()

    def _setup_buffers(self):
        self.FILO = self._make_filo_fields()
        self.FIFO = self._make_fifo_fields()

    def _make_filo_fields(self):
        return {p + l_n + '_' + i: [] for p in self.prefixes for l_n in self.load_names for i in
                self.buffer_fields}

    def _make_fifo_fields(self):
        return {p + l_n + '_' + i: [] for p in self.prefixes if p == '1s_' for l_n in self.load_names for i in
                self.buffer_fields}

    @staticmethod
    def avg(l):
        if len(l) == 0:
            return 0
        return float(round(sum(l, 0.0) / len(l), 2))

    @property
    def filo_buff(self):
        filo = self.FILO
        return filo

    @property
    def solar_current(self):
        ret_dict = {}
        field_name = "solar_current"
        for pref in self.prefixes:
            ret_dict.update({("%s%s" % (pref, field_name)):
                round(
                    sum([self.avg(v) for k, v in self.filo_buff.items() if
                         k.startswith(pref) and k.endswith(self.bat_current)]), 2)}
            )
        return ret_dict

    @property
    def fifo_buff(self):
        return self.FIFO

    def _update_filo_buffer(self):
        timestamp = int(time.time())
        if timestamp % 10 == 0:
            prefix = '10m_'
            for field in self.fifo_buff:
                m_field = field.replace('1s_', prefix)
                self.FILO[m_field].append(self.avg(self.filo_buff[field]))

        if timestamp % 60 == 0:
            prefix = '1h_'
            for field in self.filo_buff:
                if not '10m_' in field: continue
                h_field = field.replace('10m_', prefix)
                self.FILO[h_field].append(self.avg(self.filo_buff[field]))

    def _read_vals(self, channel):
        voltage = round(float(self.shunt_load.getBusVoltage_V(channel)), 2) + self.inverter_on
        current = round(float(self.shunt_load.getCurrent_mA(channel, self.shunt_bat)), 2)
        if abs(current) < 250:
            current = 0
        return {
            self.bus_voltage: voltage,
            self.bat_current: current,
            self.wattage: round((current / 1000) * voltage, 2),
        }

    def get_filo_value(self, pref, suffix):
        return [v for k, v in self.filo_buff.items() if
                k.startswith(pref) and k.endswith(suffix)]

    def _fill_buffers(self):

        channels = {
            'tiger': self._read_vals(TIGER_BAT_CHANNEL),
            'leisure': self._read_vals(LEISURE_BAT_CHANNEL),
            'inverter': self._read_vals(INVERT_CHANNEL)
        }

        for ch in channels:
            for val in channels[ch]:
                key = "1s_%s_%s" % (ch, val)
                self.FIFO[key] = channels[ch][val]
                self.FILO[key].append(channels[ch][val])

    def _cleanup_filo(self, filo, pos=-60):
        for v in filo:
            filo[v] = filo[v][pos:]

    def update_rel_status(self, statuses: dict):
        self.REL_STATUS['inverter_relay'].append(statuses['inverter_relay'])
        self.REL_STATUS['main_relay_status'].append(statuses['main_relay_status'])
        self.REL_STATUS['status_check'].append(statuses['status_check'])

    @property
    def get_main_rel_status(self):
        return self.avg(self.REL_STATUS['main_relay_status'])

    @property
    def get_avg_rel_stats(self):
        return {i: self.avg(val) for i, val in self.REL_STATUS.items()}

    @property
    def len_sts_chk(self):
        return len(self.REL_STATUS['status_check'])

    @property
    def get_avg_rel_status(self):
        return self.avg(self.REL_STATUS['status_check'])

    def buffers_run(self, inverter_state):
        self.inverter_on = inverter_state
        self._fill_buffers()
        self._update_filo_buffer()
        self._cleanup_filo(self.FILO)
        self._cleanup_filo(self.REL_STATUS, -10)
