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
import serial
import logging
from serial import SerialException
from printcore import printcore


logger = logging.getLogger(__name__)

class Printer(object):

    def __init__(self, serial=None, baudrate=250000):
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

        # PARAMETERS THAT MAY NEED TO BE CHANGED
        self.baudrate = baudrate

        # Connect using lower level printcore system
        try:
            self._p = printcore(port=self.serial, baud=self.baudrate)
        except SerialException as e:
            # Currently, there is no errno, but it should be there in the future
            if e.errno == 2:
                raise ValueError("Error: You are trying to connect to a non-existing port.")
            elif e.errno == 8:
                output = "Error: You don't have permission to open %s.\n" % port
                output += "You might need to add yourself to the dialout group."
                raise RuntimeError(output)
            else:
                raise RuntimeError(str(e))
            # Kill the scope anyway
            return False
        except OSError as e:
            if e.errno == 2:
                raise ValueError("Error: You are trying to connect to a non-existing port.")
            else:
                raise RuntimeError(str(e))
            return False


    def __del__(self):
        self._p.disconnect()
    
    def reset(self):
        '''resets the internal implementation of the printer'''
        self._p.reset()
    
    def move_now(self, l):
        """Executes an immediate move command in the form <axis> <number"""
        if len(l.split()) < 2:
            logger.error("Invalid move command specified")
            return
        if self._p.printing:
            logger.error("Printer is currently printing. Please pause the print before you issue manual commands.")
            return
        if not self._p.online:
            logger.error("Printer is not online. Unable to move.")
            return
        l = l.split()
        if l[0].lower() == "x":
            axis = "X"
        elif l[0].lower() == "y":
            axis = "Y"
        elif l[0].lower() == "z":
            axis = "Z"
        else:
            logger.error("Unknown axis.")
            return
        try:
            float(l[1])  # check if distance can be a float
        except:
            logger.error("Invalid distance for move command")
            return
        self._p.send_now("G91")
        self._p.send_now("G0 " + axis + str(l[1]))
        self._p.send_now("G90")

    


    @classmethod
    def scanserial(cls):
        '''scans serial ports for possible USB connections.'''
        def _bluetoothfilter(serial):
            return not ("Bluetooth" in serial or "FireFly" in serial)
        baselist = []
        for g in ['/dev/ttyUSB*', '/dev/ttyACM*', "/dev/tty.*", "/dev/cu.*", "/dev/rfcomm*"]:
            baselist += glob.glob(g)
        return [p for p in baselist if _bluetoothfilter(p)]
