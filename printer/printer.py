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
import threading
from serial import SerialException
from printcore import printcore
import time

logger = logging.getLogger(__name__)

class Status(object):

    def __init__(self):
        self.extruder_temp = 0
        self.extruder_temp_target = 0
        self.bed_temp = 0
        self.bed_temp_target = 0
        self.print_job = None
        self.print_job_progress = 1.0

    def update_tempreading(self, tempstr):
        temps = parse_temperature_report(tempstr)
        if "T0" in temps and temps["T0"][0]: hotend_temp = float(temps["T0"][0])
        elif "T" in temps and temps["T"][0]: hotend_temp = float(temps["T"][0])
        else: hotend_temp = None
        if "T0" in temps and temps["T0"][1]: hotend_setpoint = float(temps["T0"][1])
        elif "T" in temps and temps["T"][1]: hotend_setpoint = float(temps["T"][1])
        else: hotend_setpoint = None
        if hotend_temp is not None:
            self.extruder_temp = hotend_temp
            if hotend_setpoint is not None:
                self.extruder_temp_target = hotend_setpoint
        bed_temp = float(temps["B"][0]) if "B" in temps and temps["B"][0] else None
        if bed_temp is not None:
            self.bed_temp = bed_temp
            setpoint = temps["B"][1]
            if setpoint:
                self.bed_temp_target = float(setpoint)

    @property
    def bed_enabled(self):
        return self.bed_temp != 0

    @property
    def extruder_enabled(self):
        return self.extruder_temp != 0


class Printer(object):

    def __init__(self, serial=None, baudrate=250000, block=True):
        '''initializes our printer class. Will choose the first USB device
        detected if serial was not specified.
        
        @param serial:
        @param baudrate: baudrate setting of your 3D printer/CNC
        @param block: will we block until printer has been connected?
        '''
        # Set the current status of the printer
        self.status = Status()
        self.statuscheck = False
        self.status_thread = None
        self.paused = False
        self.userm114 = 0
        self.userm105 = 0
        self.m105_waitcycles = 0
        self.monitor_interval = 3

        # Temperatures (we will be using OFF
        self.temps = {"pla": "185", "abs": "230", "off": "0"}
        self.bedtemps = {"pla": "60", "abs": "110", "off": "0"}

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
        except OSError as e:
            if e.errno == 2:
                raise ValueError("Error: You are trying to connect to a non-existing port.")
            else:
                raise RuntimeError(str(e))
        
        self.statuscheck = True
        self.status_thread = threading.Thread(target = self.statuschecker)
        self.status_thread.start()

    
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

    #  --------------------------------------------------------------
    #  Printer status monitoring
    #  --------------------------------------------------------------
    def disconnect(self):
        self._p.disconnect()

    def statuschecker_inner(self, do_monitoring=True):
        if self._p.online:
            if self._p.writefailures >= 4:
                logger.error("Disconnecting after 4 failed writes.")
                self.status_thread = None
                self.disconnect()
                return
            if do_monitoring:
                if not self.paused:
                    self._p.send_now("M27")
                if self.m105_waitcycles % 10 == 0:
                    self._p.send_now("M105")
                self.m105_waitcycles += 1
        cur_time = time.time()
        wait_time = 0
        while time.time() < cur_time + self.monitor_interval - 0.25:
            if not self.statuscheck:
                break
            time.sleep(0.25)
            # Safeguard: if system time changes and goes back in the past,
            # we could get stuck almost forever
            wait_time += 0.25
            if wait_time > self.monitor_interval - 0.25:
                break
        # Always sleep at least a bit, if something goes wrong with the
        # system time we'll avoid freezing the whole app this way
        time.sleep(0.25)


    def statuschecker(self):
        while self.statuscheck:
            self.statuschecker_inner()