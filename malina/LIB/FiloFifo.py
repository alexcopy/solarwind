#!/usr/bin/env python
from malina.INA3221 import SDL_Pi_INA3221

import schedule
import time
import logging
import threading
import copy

INVERT_CHANNEL = 1
LEISURE_BAT_CHANNEL = 2
TIGER_BAT_CHANNEL = 3
SHUNT_IMP = 0.00155


class FiloFifo:
    _instance_lock = threading.Lock()
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super(FiloFifo, cls).__new__(cls)
        return cls._instance

    def __init__(self, bus_voltage='bus_voltage', wattage='wattage', bat_current='bat_current'):

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
        self.shunt_load = SDL_Pi_INA3221.SDL_Pi_INA3221(addr=0x40)
        self.load_names = {'tiger': TIGER_BAT_CHANNEL, 'leisure': LEISURE_BAT_CHANNEL, 'inverter': INVERT_CHANNEL}
        self._setup_buffers()
        # Create locks for thread safety
        self.filo_lock = threading.Lock()
        self.fifo_lock = threading.Lock()
        self.filo_buff_lock = threading.Lock()

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
        filo = copy.deepcopy(self.FILO)
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
        return copy.deepcopy(self.FIFO)

    def _read_vals(self, channel):
        voltage = round(float(self.shunt_load.getBusVoltage_V(channel)), 2)
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

    def update_rel_status(self, statuses: dict):
        self.REL_STATUS['inverter_relay'].append(statuses['inverter_relay'])
        self.REL_STATUS['main_relay_status'].append(statuses['main_relay_status'])
        self.REL_STATUS['status_check'].append(statuses['status_check'])

    def _update_filo_buffer(self):
        timestamp = int(time.time())
        if timestamp % 10 == 0:
            prefix = '10m_'
            for field in self.fifo_buff:
                m_field = field.replace('1s_', prefix)
                self.filo_lock.acquire()
                self.FILO[m_field].append(self.avg(self.filo_buff[field]))
                self.filo_lock.release()

        if timestamp % 60 == 0:
            prefix = '1h_'
            for field in self.fifo_buff:
                if not '10m_' in field:
                    continue
                h_field = field.replace('10m_', prefix)
                self.filo_lock.acquire()
                self.FILO[h_field].append(self.avg(self.filo_buff[field]))
                self.filo_lock.release()

    def _fill_buffers(self):
        channels = {
            'tiger': self._read_vals(TIGER_BAT_CHANNEL),
            'leisure': self._read_vals(LEISURE_BAT_CHANNEL),
            'inverter': self._read_vals(INVERT_CHANNEL)
        }

        for ch in channels:
            for val in channels[ch]:
                key = "1s_%s_%s" % (ch, val)
                self.fifo_lock.acquire()
                self.FIFO[key] = channels[ch][val]
                self.fifo_lock.release()

                self.filo_lock.acquire()
                self.FILO[key].append(channels[ch][val])
                self.filo_lock.release()

    def _cleanup_filo(self, filo, pos=-60):
        for v in filo:
            self.filo_lock.acquire()
            filo[v] = filo[v][pos:]
            self.filo_lock.release()

    def buffers_run(self, inverter_state):
        self.inverter_on = inverter_state

        self.filo_lock.acquire()
        self.fifo_lock.acquire()
        self._fill_buffers()
        self.fifo_lock.release()
        self.filo_lock.release()

        self.filo_lock.acquire()
        self._update_filo_buffer()
        self.filo_lock.release()

        self.filo_lock.acquire()
        self._cleanup_filo(self.FILO)
        self._cleanup_filo(self.REL_STATUS, -10)
        self.filo_lock.release()
