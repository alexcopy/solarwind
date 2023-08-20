import gc
import math
import array
# from utime import sleep_ms, sleep_us, ticks_us, ticks_diff
# from machine import ADC, Timer, idle, enable_irq, disable_irq, Pin, SPI
#
#
# acquire ADC values. The paramters of the constructor are:
# 1. the mains frequency (number, typically 50 or 60)
# 2. the sampling period (ms). The default is 2 ms.
#
# class Acquire:
#     def __init__(self, freq=50, *, sample_period=2):
#         self.sample_period = sample_period
#         self.omega = 2.0 * math.pi * freq / (1000 / sample_period)
#         self.coeff = 2.0 * math.cos(self.omega)
#         self.freq = freq
#         self.adc = ADC(bits=9)
#
#     def start(self, pin1, pin2, time=200):
#         gc.collect() # avoids automatic gc during sampling
#         self.pin_adc1 = self.adc.channel(pin=pin1, attn=ADC.ATTN_11DB)
#         self.pin_adc2 = self.adc.channel(pin=pin2, attn=ADC.ATTN_11DB)
#         self.samples = time // self.sample_period
#
#         # Test code for creating the artificial signal for phase noise
#         # self.pi_f = (2 * math.pi * self.freq) / 1000000  # angle step per us
#         # self.start_us = ticks_us()
#
#         self.count = 0
#         self.busy = True
#         self.q1_1 = 0.0
#         self.q2_1 = 0.0
#         self.q1_2 = 0.0
#         self.q2_2 = 0.0
#         self.alarm = Timer.Alarm(self.read_adc, 0, us=(self.sample_period * 1000 - 3), periodic=True)
#
#     def stop(self):
#         self.alarm.cancel()
#
#     def read_adc(self, alarm):
#         state = disable_irq()
#         v1 = self.pin_adc1()
#         v2 = self.pin_adc2()
#         # Test code using an artificial Signal
#         # v1 = math.sin(ticks_diff(ticks_us(), self.start_us) * self.pi_f)
#         # v2 = math.sin(ticks_diff(ticks_us(), self.start_us) * self.pi_f)
#         enable_irq(state)
#
#         self.q0_1 = v1 + self.coeff * self.q1_1 - self.q2_1
#         self.q2_1 = self.q1_1
#         self.q1_1 = self.q0_1
#
#         self.q0_2 = v2 + self.coeff * self.q1_2 - self.q2_2
#         self.q2_2 = self.q1_2
#         self.q1_2 = self.q0_2
#
#         self.count += 1
#         if self.count >= self.samples:
#             self.alarm.cancel()
#             self.busy = False
#
#     def result(self):
#         while self.busy == True:
#             sleep_ms(self.sample_period)
#
#         real = self.q1_1 - self.q2_1 * math.cos(self.omega)
#         imag = self.q2_1 * math.sin(self.omega)
#         amplitude_1 = 2 * math.sqrt(real * real + imag * imag) / self.count
#         phase_1 = math.atan2(real, imag)
#
#         real = self.q1_2 - self.q2_2 * math.cos(self.omega)
#         imag = self.q2_2 * math.sin(self.omega)
#         amplitude_2 = 2 * math.sqrt(real * real + imag * imag) / self.count
#         phase_2 = math.atan2(real, imag)
#         #
#         diff = 40e-6 * 2 * self.freq * math.pi # phase diff caused by 40µs sampling delay
#         phase = phase_1 - phase_2 - diff #
#         if phase > math.pi:
#             phase -= 2 * math.pi
#         elif phase < -math.pi:
#             phase += 2 * math.pi
#         return amplitude_1, amplitude_2, phase
#
#     def reading(self, pin1, pin2, time):
#         self.start(pin1, pin2, time)
#         return self.result()
# #
#
# def run(period = 500, n=10):
#     acq = Acquire(50.0, sample_period=1) # 50 Hz
#     l=[]
#     for _ in range(n):
#         value = acq.reading("P13", "P14", period)
#         l.append(value[0])
#         print (value, math.cos(value[2]))
#     avg = sum(l)/n
#     sqsum  = 0
#     for _ in l:
#         sqsum += (_ - avg) * (_ - avg)
#     print ("average: ", avg, "SDev:", math.sqrt(sqsum/n))
#
