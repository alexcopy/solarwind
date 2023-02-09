import time

from malina.solar_pond import SolarPond

SECS = 1

if __name__ == '__main__':
    sp = SolarPond()
    sp.run_read_vals()
    while True:
        timestamp = int(time.time())
        time.sleep(SECS)
        sp.processing_reads()
        if timestamp % 600 == 0:
            sp.reset_ff()
