#!/usr/bin/env python
import sys
import unittest
import random as rnd
from freezegun import freeze_time

sys.path.append('../')
import malina.LIB.FiloFifo as FF
from mock import Mock

mock_time = 60


class TestOs(Mock):
    def __int__(self):
        self.test = []
        self.shunt_voltage = 0
        self.bat_current = 0
        self.bus_voltage = 0

    def getBusVoltage_V(self, ch, defined_val=20):
        self.bus_voltage = rnd.uniform(0, 100)
        return self.bus_voltage

    def getCurrent_mA(self, ch, shunt_bat, defined_val=20):
        self.bat_current = rnd.uniform(0, 100)
        return self.bat_current


class FiloFifoTestCase(unittest.TestCase):

    def setUp(self):
        self.shunt = TestOs()
        self.test_fields = ['test_field_1', 'test_field_2', 'test_field_3']
        self.logger = Mock()
        self.test_fifo_buf = {'1s_tiger_test_field_1': [], '1s_tiger_test_field_2': [], '1s_tiger_test_field_3': [],
                              '1s_leisure_test_field_1': [], '1s_leisure_test_field_2': [],
                              '1s_leisure_test_field_3': [], '1s_inverter_test_field_1': [],
                              '1s_inverter_test_field_2': [], '1s_inverter_test_field_3': []}

        self.test_filo_buf = {'1s_tiger_test_field_1': [], '1s_tiger_test_field_2': [], '1s_tiger_test_field_3': [],
                              '1s_leisure_test_field_1': [], '1s_leisure_test_field_2': [],
                              '1s_leisure_test_field_3': [], '1s_inverter_test_field_1': [],
                              '1s_inverter_test_field_2': [], '1s_inverter_test_field_3': [],
                              '10m_tiger_test_field_1': [], '10m_tiger_test_field_2': [], '10m_tiger_test_field_3': [],
                              '10m_leisure_test_field_1': [], '10m_leisure_test_field_2': [],
                              '10m_leisure_test_field_3': [], '10m_inverter_test_field_1': [],
                              '10m_inverter_test_field_2': [], '10m_inverter_test_field_3': [],
                              '1h_tiger_test_field_1': [], '1h_tiger_test_field_2': [], '1h_tiger_test_field_3': [],
                              '1h_leisure_test_field_1': [], '1h_leisure_test_field_2': [],
                              '1h_leisure_test_field_3': [], '1h_inverter_test_field_1': [],
                              '1h_inverter_test_field_2': [], '1h_inverter_test_field_3': []}

        self.ff_buff = FF.FiloFifo(self.logger, self.shunt, 'test_field_1', 'test_field_2', 'test_field_3')
        self.current_only = {'1s_tiger_test_field_1': [0.0, 0.0], '1s_tiger_test_field_2': [0.0, 0.0],
                             '1s_tiger_test_field_3': [300.0, 300.0], '1s_leisure_test_field_1': [0.0, 0.0],
                             '1s_leisure_test_field_2': [0.0, 0.0], '1s_leisure_test_field_3': [300.0, 300.0],
                             '1s_inverter_test_field_1': [0.0, 0.0], '1s_inverter_test_field_2': [0.0, 0.0],
                             '1s_inverter_test_field_3': [300.0, 300.0], '10m_tiger_test_field_1': [0.0, 0.0],
                             '10m_tiger_test_field_2': [0.0, 0.0], '10m_tiger_test_field_3': [300.0, 300.0],
                             '10m_leisure_test_field_1': [0.0, 0.0], '10m_leisure_test_field_2': [0.0, 0.0],
                             '10m_leisure_test_field_3': [300.0, 300.0], '10m_inverter_test_field_1': [0.0, 0.0],
                             '10m_inverter_test_field_2': [0.0, 0.0], '10m_inverter_test_field_3': [300.0, 300.0],
                             '1h_tiger_test_field_1': [0.0, 0.0], '1h_tiger_test_field_2': [0.0, 0.0],
                             '1h_tiger_test_field_3': [300.0, 300.0], '1h_leisure_test_field_1': [0.0, 0.0],
                             '1h_leisure_test_field_2': [0.0, 0.0], '1h_leisure_test_field_3': [300.0, 300.0],
                             '1h_inverter_test_field_1': [0.0, 0.0], '1h_inverter_test_field_2': [0.0, 0.0],
                             '1h_inverter_test_field_3': [300.0, 300.0]}

    def testInit(self):
        read_vals = self.ff_buff._read_vals(1)
        self.assertEqual(True, len(read_vals) == 3 and type(read_vals) == dict, "Passed")
        self.assertEqual(True, len(self.ff_buff.FIFO) == len(self.test_fields * 3) and type(self.ff_buff.FIFO) == dict)

        self.assertEqual(self.test_fifo_buf, self.ff_buff.FIFO)
        self.assertEqual(self.test_filo_buf, self.ff_buff.FILO)

    # checking for 10 sec comes into filo buffer
    @freeze_time("2012-01-01 00:00:10")
    def test_update_filo_buffer_10m(self):
        times_to_run = 12
        for l in range(0, times_to_run):
            self.ff_buff._fill_buffers()
            self.ff_buff._update_filo_buffer()
            filo_buff = self.ff_buff.filo_buff
            fifo_buff = self.ff_buff.fifo_buff

            # check if all values  comes from fifo to filo in to corresponding fields
            # all values are randomised so checking value by value
            for i in fifo_buff:
                val_fifo = fifo_buff[i]
                ten_min_field = i.replace('1s', '10m')
                hour_field = i.replace('1s', '1h')
                self.assertEqual(len(filo_buff[i]), l + 1)
                avg_1s_field = self.ff_buff._avg(filo_buff[i])
                self.assertEqual(val_fifo, filo_buff[i][l])
                # assert what 10min filed has an average value from 1s list field
                self.assertEqual(filo_buff[ten_min_field][l], avg_1s_field)
                # doesn't go anything into 1hour field
                self.assertEqual(len(filo_buff[hour_field]), 0)

    # checking for 10 sec comes into filo buffer
    @freeze_time("2012-01-01 00:00:00")
    def test_update_filo_buffer_1h(self):
        times_to_run = 10
        for l in range(0, times_to_run):
            self.ff_buff._fill_buffers()
            self.ff_buff._update_filo_buffer()
            filo_buff = self.ff_buff.filo_buff
            fifo_buff = self.ff_buff.fifo_buff

            # check if all values  comes from fifo to filo in to corresponding fields
            # all values are randomised so checking value by value
            for i in fifo_buff:
                val_fifo = fifo_buff[i]
                ten_min_field = i.replace('1s', '10m')
                hour_field = i.replace('1s', '1h')
                self.assertEqual(len(filo_buff[i]), l + 1)
                avg_1s_field = self.ff_buff._avg(filo_buff[i])
                self.assertEqual(val_fifo, filo_buff[i][l])
                # assert what 10min filed has an average value from 1s list field
                self.assertEqual(filo_buff[ten_min_field][l], avg_1s_field)
                # doesn't go anything into 1hour field
                self.assertNotEqual(len(filo_buff[hour_field]), 0)
                # assert what averege from each  10m field goes to 1h field
                ten_min_avg = self.ff_buff._avg(filo_buff[ten_min_field])
                self.assertEqual(filo_buff[hour_field][l], ten_min_avg)

    @freeze_time("2012-01-01 00:00:00")
    def test_cleanup_filo(self):
        times_to_run = 100
        max_buf_length = 60
        for l in range(0, times_to_run):
            self.ff_buff._fill_buffers()
            self.ff_buff._update_filo_buffer()

        filo_buff = self.ff_buff.filo_buff
        for i in filo_buff:
            self.assertEqual(len(filo_buff[i]), times_to_run)
        self.ff_buff._cleanup_filo()

        for i in filo_buff:
            self.assertEqual(len(filo_buff[i]), max_buf_length)

    @freeze_time("2012-01-01 00:00:00")
    def test_solar_current(self):
        times_to_run = 2
        for l in range(0, times_to_run):
            self.ff_buff.buffers_run(1)
        solar_cur = self.ff_buff.solar_current
        self.assertEqual(len(solar_cur), 3)
        self.ff_buff.FILO = self.current_only
        solar_current = self.ff_buff.solar_current
        for fild, val in solar_current.items():
            self.assertEqual(val, 900.0)


if __name__ == '__main__':
    unittest.main()
