"""Tries to connect to any 3D printer. You'll most likely have to specify the
USB device that it is connected with. The easiest way is to unplug the
connector from the 3D printer, and then type in

    dmesg | grep usb

Then, connect the connector into the 3D printer and type it again

    dmesg | grep usb

You'll most likely see that the new entry will be something connected to
/dev/ttyUSB0 or /dev/ttyACM0 or something, which will then be the USB that you
will specify here. Also, you may have to change around the Baud Rate for this
to work. The TAZ LULZBOT 3D printer that we use has a baud rate of 2500000.
"""
import glob
import numpy as np


class Printer(object):

    def __init__(self, serial=None):
        '''initializes our printer class. Will choose the first USB device
        detected if serial was not specified.'''
        if not serial:
            possible_serials = self.scanserial()
            if not possible_serials:
                raise RuntimeError('No possible USB connections found')
            self.serial = possible_serials[0]
        else:
            self.serial = serial
        print('Attempting to look for connections on: %s' % self.serial)

    @classmethod
    def scanserial(cls):
        '''scans serial ports for possible USB connections.'''
        def _bluetoothfilter(serial):
            return not ("Bluetooth" in serial or "FireFly" in serial)
        baselist = []
        for g in ['/dev/ttyUSB*', '/dev/ttyACM*', "/dev/tty.*", "/dev/cu.*", "/dev/rfcomm*"]:
            baselist += glob.glob(g)
        return [p for p in baselist if _bluetoothfilter(p)]
