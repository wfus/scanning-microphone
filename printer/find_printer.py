"""First tries to see if we can connect to a printer. That's probably the
hardest part of this entire thing unfortunately. For our first test, we're
using the TAZ LULZBOT, which connects through USB, so most likely the settings
are going to be
    * /dev/ttyACM0 OR /dev/ttyUSB0 OR /dev/ttyUSB1
    * Baud Rate: 250000 OR 115200, most likely the first
"""
from printer import Printer


if __name__ == '__main__':
    print('Creating the printer object.')
    printer = Printer()
    print('Baud rate set to %s' % str(printer.baudrate))
