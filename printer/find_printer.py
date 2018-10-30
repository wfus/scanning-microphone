"""First tries to see if we can connect to a printer. That's probably the
hardest part of this entire thing unfortunately. For our first test, we're
using the TAZ LULZBOT, which connects through USB, so most likely the settings
are going to be
    * /dev/ttyACM0 OR /dev/ttyUSB0 OR /dev/ttyUSB1
    * Baud Rate: 250000 OR 115200, most likely the first
"""
from printer import Printer
import time


if __name__ == '__main__':
    print('Creating the printer object.')
    p = Printer(serial="/dev/ttyACM0")
    print('Baud rate set to %s' % str(p.baudrate))
    time.sleep(2.0)
    print(p._p.online)
    time.sleep(2.0)
    for x in range(20):
        time.sleep(0.5)
        p.move_now("x {}".format(x))
        time.sleep(0.5)
        p.move_now("y {}".format(x))
        time.sleep(0.5)
        p.move_now("x -{}".format(x))
        time.sleep(0.5)
        p.move_now("y -{}".format(x))
        time.sleep(0.5)
