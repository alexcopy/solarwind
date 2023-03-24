import time
import sys

import importlib.util

try:
    importlib.util.find_spec('RPi.GPIO')
    import RPi.GPIO as GPIO
except ImportError:

    import FakeRPi.GPIO as GPIO
    import FakeRPi.Utilities
    FakeRPi.Utilities.mode = FakeRPi.Utilities.PIN_TYPE_BOARD

TIME_TIK = 1
POND_RELAY = 11
INVER_RELAY = 12
INVER_CHECK = 10
CUT_OFF_VOLT = 21
SWITCH_ON_VOLT = 26
MIN_POND_SPEED = 10


GPIO.setmode(GPIO.BOARD)
GPIO.setup(POND_RELAY, GPIO.OUT)
GPIO.setup(INVER_RELAY, GPIO.OUT)
GPIO.setup(INVER_CHECK, GPIO.IN)



time.sleep(.5)
GPIO.output(INVER_RELAY, True)
time.sleep(.5)
GPIO.output(INVER_RELAY, False)

GPIO.cleanup()

