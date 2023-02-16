#!/usr/bin/env python

import time
import random as rnd

from mpmath import rand

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
        self.bat_current = bat_current
        self.prefixes = ['1s_', '10m_', '1h_']
        self.FILO = {}
        self.FIFO = {}
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

    def avg(self, l):
        if len(l) == 0:
            return 0
        return float(round(sum(l, 0.0) / len(l), 2))

    @property
    def filo_buff(self):
        filo = self.FILO
        return filo

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
        voltage = round(float(self.shunt_load.getBusVoltage_V(channel)), 2)
        current = round(float(self.shunt_load.getCurrent_mA(channel, self.shunt_bat)), 2)
        return {
            self.bus_voltage: voltage,
            self.bat_current: current,
            self.wattage: round(current * voltage, 2),
        }

    def fill_buffers(self):
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

    def cleanup_filo(self):
        for v in self.FILO:
            self.FILO[v] = self.FILO[v][-60:]

    def buffers_run(self):
        self.fill_buffers()
        self._update_filo_buffer()
        self.cleanup_filo()
