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

GPIO.setmode(GPIO.BOARD)
GPIO.setup(7, GPIO.OUT)
GPIO.setup(11, GPIO.OUT)

for x in range(10):
    GPIO.output(7, True)
    GPIO.output(11, False)
    time.sleep(.5)
    GPIO.output(7, False)
    GPIO.output(11, True)
    time.sleep(.5)


GPIO.cleanup()