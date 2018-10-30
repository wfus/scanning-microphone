"""Main scanning routine that uses both the abstracted microphone class and
the printer class to scan and record audio samples."""
import time
import sys
sys.path.append('./microphone')
sys.path.append('./printer')
from microphone import Microphone
from printer import Printer


PRINTER_CONNECT_TIME = 0.2

class Scanner(object):
    """Scanner object that manages the printer and the microphone. Each object
    should represent any sequence of scans using the same microphone and
    printer"""
    def __init__(self, serial='/dev/ttyACM0'):
        self.mic = Microphone()
        print('Trying to connect printer through USB port {}'.format(serial))
        self.p = Printer(serial=serial)

        # Wait some time for handshake to occur with printer
        time.sleep(PRINTER_CONNECT_TIME)

        if not self.p.online():
            raise RuntimeError("Printer is not online. Are you connecting to right USB?")
        

    def scan(self):
        pass

    def __str__(self):
        pass

    def __repr__(self):
        pass


if __name__ == '__main__':
    pass