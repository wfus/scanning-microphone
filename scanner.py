"""Main scanning routine that uses both the abstracted microphone class and
the printer class to scan and record audio samples.
"""
import time
import sys
import numpy as np
import os
sys.path.append('./microphone')
sys.path.append('./printer')
# from microphone import Microphone
from oscilloscope import OscilloscopeMicrophone as Microphone
from printer import Printer


PRINTER_CONNECT_TIME = 2.0
MOVEMENT_DELAY_TIME = 0.2
MOVEMENT_DELAY_MULTIPLIER = 0.1

class Scanner(object):
    """Scanner object that manages the printer and the microphone. Each object
    should represent any sequence of scans using the same microphone and
    printer"""
    def __init__(self, serial=None):
        self.mic = Microphone()
        print('Trying to connect printer through USB port {}'.format(serial))
        self.p = Printer(serial=serial)

        # Wait some time for handshake to occur with printer
        time.sleep(PRINTER_CONNECT_TIME)

        print(self.p._p.online)
        if not self.p.online():
            raise RuntimeError("Printer is not online. Are you connecting to right USB?")
        

    def scan(self):
        raise NotImplementedError

    def scan_rectangular_lattice(self, begin_coord, end_coord, resolution, record_time=2.0, savepath="./data"):
        """Scans along a square lattice and saves each audio clip at each location. Audio clips
        will be saved the format <savepath>/<time.time()>_<xloc>_<yloc>_<zloc>.wav

        @param begin_coord: tuple of x and y coordinate to start out with. Since the current code
                            is location agnostic, it is assume the CNC is over begin_coord already
                            TODO: Write a re-centering script or something lmao
        @param end_coord: tuple of x and y coordinate to scan until
        @param resolution: number of samples for each dimension. If 10 is selected, we'll scan 100 points.
        @param savepath: folder that your saved wave files will be sent to.
        """
        # Create a folder to store all of our sound samples in
        print_begin_time = int(time.time())
        savefolder = os.path.join(savepath, str(print_begin_time))
        if not os.path.exists(savefolder):
            os.makedirs(savefolder)
        # since we are assuming that we start at the begin_coord, consider the relative coordinates where
        # begin_coord is just the origin already.
        distance_x = end_coord[0] - begin_coord[0]
        distance_y = end_coord[1] - begin_coord[1]
        scan_points = [(x, y) for x in np.linspace(0, distance_x, resolution) 
                              for y in np.linspace(0, distance_y, resolution)]
        
        # Beginning at the begin_coord, we are doing to stop and keep scanning
        previous_coord = begin_coord
        for p_x, p_y in scan_points:
            dx = p_x - previous_coord[0]
            dy = p_y - previous_coord[1]
            self.move(x=dx, y=dy)
            fname = os.path.join(savefolder, "{}_{}_{}".format(p_x, p_y, 0))
            self.mic.record_to_file(record_time, fname)
            previous_coord = p_x, p_y

        # Move back to our original location. Important since we are using relative coordinates.
        self.move(x=-distance_x, y=-distance_y)

    def scan_rectangular_prism(self, begin_coord, end_coord, resolution, resolution_z, record_time=2.0, savepath="./data"):
        """Scans along a square lattice and saves each audio clip at each location. Audio clips
        will be saved the format <savepath>/<time.time()>_<xloc>_<yloc>_<zloc>.wav

        @param begin_coord: tuple of x, y, z coordinate to start out with. Since the current code
                            is location agnostic, it is assume the CNC is over begin_coord already
                            TODO: Write a re-centering script or something lmao
        @param end_coord: tuple of x, y, z coordinate to scan until
        @param resolution: number of samples for each dimension. If 10 is selected, we'll scan 100 points.
        @param savepath: folder that your saved wave files will be sent to.
        """
        # Create a folder to store all of our sound samples in
        print_begin_time = int(time.time())
        savefolder = os.path.join(savepath, str(print_begin_time))
        if not os.path.exists(savefolder):
            os.makedirs(savefolder)
        # since we are assuming that we start at the begin_coord, consider the relative coordinates where
        # begin_coord is just the origin already.
        distance_x = end_coord[0] - begin_coord[0]
        distance_y = end_coord[1] - begin_coord[1]
        distance_z = end_coord[2] - begin_coord[2]
        for z in np.linspace(0, distance_z, resolution_z):
            scan_points = [(x, y) for x in np.linspace(0, distance_x, resolution) 
                                for y in np.linspace(0, distance_y, resolution)]
            
            # Beginning at the begin_coord, we are doing to stop and keep scanning
            previous_coord = begin_coord
            for p_x, p_y in scan_points:
                dx = p_x - previous_coord[0]
                dy = p_y - previous_coord[1]
                self.move(x=dx, y=dy)
                fname = os.path.join(savefolder, "{}_{}_{}".format(p_x, p_y, z))
                self.mic.record_to_file(record_time, fname)
                previous_coord = p_x, p_y

            # Move back to our original location. Important since we are using relative coordinates.
            self.move(x=-distance_x, y=-distance_y)

            # Move up Z coordinates
            self.move(z=(distance_z / resolution_z))
        
        # Move back to our original location in z
        self.move(z=-distance_z)

    def move(self, x=None, y=None, z=None, delay=MOVEMENT_DELAY_TIME, delay_factor=MOVEMENT_DELAY_MULTIPLIER):
        """Displaces the head of the CNC x, y, z units. Will find the shortest distances to get to the
        endpoint by moving stepper motors simultaneously. Delay will pause control sequence to give
        the CNC time to move to the location, since we are NOT BLOCKING!"""
        if not self.p.online():
            raise RuntimeError("Cannot move - printer is not connected.")
        
        self.p.move_coord(x=x, y=y, z=z)
        # Will sleep for a factor of the amount of distance we need to travel
        dx = 0 if not x else x
        dy = 0 if not y else y
        dz = 0 if not z else z
        distance = (dx**2 + dy**2 + dz**2) ** 0.5
        time.sleep(delay + distance * delay_factor)

    def __str__(self):
        pass

    def __repr__(self):
        pass


if __name__ == '__main__':
    # Small test script for the TAZ 5 CNC machine in science center 102
    scan = Scanner(serial="/dev/ttyACM0")
    scan.scan_rectangular_lattice((0, 0), (10, 10), 11)
