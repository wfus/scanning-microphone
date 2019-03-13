"""Main scanning routine that uses both the abstracted microphone class and
the printer class to scan and record audio samples. The resultant data may
have to be processed differently depending on what data source is used. The
current data sources have been:
    * raw FFT samples from an Oscilloscope
    * raw audio waveform from a microphone
The first one takes much less time since the FFT is being done onboard, so
usually we will be using raw FFT samples from the attached oscilloscope.
"""
import time
import sys
import numpy as np
import os
import tqdm
sys.path.append('./microphone')
sys.path.append('./printer')


# Switch up the import depending on which data collection device you're using
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

        if not self.p.online():
            raise RuntimeError("Printer is not online. Are you connecting to right USB?")
        

    def scan(self):
        raise NotImplementedError

    def scan_rectangular_lattice(self, begin_coord, end_coord, resolution,
                                 record_time=2.0, savepath="./data"):
        """Scans along a square lattice and saves each audio clip at each location.
        Audio clips will be saved the format:
            <savepath>/<time.time()>_<xloc>_<yloc>_<zloc>.wav
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
        for p_x, p_y in tqdm.tqdm(scan_points):
            dx = p_x - previous_coord[0]
            dy = p_y - previous_coord[1]
            self.move(x=dx, y=dy)
            fname = os.path.join(savefolder, "{}_{}_{}".format(p_x, p_y, 0))
            self.mic.record_to_file(record_time, fname)
            previous_coord = p_x, p_y

        # Move back to our original location. Important since we are using relative coordinates.
        self.move(x=-distance_x, y=-distance_y)

    def scan_rectangular_prism(self, begin_coord, end_coord, resolution,
                               resolution_z, record_time=2.0, savepath="./data"):
        """Scans along a square lattice and saves each audio clip at each
        location. Audio clips will be saved the format:
            <savepath>/<time.time()>_<xloc>_<yloc>_<zloc>.wav
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
        for index, z in enumerate(np.linspace(0, distance_z, resolution_z)):
            print('Scanning height z=%s, layer %d/%d' % (z, index + 1, resolution_z))
            scan_points = [(x, y) for x in np.linspace(0, distance_x, resolution) 
                                for y in np.linspace(0, distance_y, resolution)]
            
            # Beginning at the begin_coord, we are doing to stop and keep scanning
            previous_coord = begin_coord
            for p_x, p_y in tqdm.tqdm(scan_points):
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
    
    def move_speed(self, x=None, y=None, z=None, speed=500, delay=0.2):
        """
        TODO: FIX THIS FUNCTION YOU DOOFUS
        Move to coordinate at a certain speed. Will calculate the delay time
        needed for the program to wait during travel time by estimating the
        distance traveled and the speed.
        @param x (int): distance to travel in x axis (mm) 
        @param y (int): distance to travel in y axis (mm) 
        @param z (int): distance to travel in z axis (mm) 
        @param speed (int): speed of nozzle in mm/min
        """
        speed_per_second = float(speed) / 60.0
        dx = 0.0 if not x else x
        dy = 0.0 if not y else y
        dz = 0.0 if not z else z
        move_vector = np.array([dx, dy, dz])
        distance = np.sqrt((move_vector ** 2).sum())

        # Actually send the move command, overriding any previous command
        self.p.move_coord(x=x, y=y, z=z, speed=speed)
        # Sleep the amount of time while the nozzle is moving, plus a small
        # delay for tolerance reasons
        time.sleep(distance / speed_per_second + delay)
    
    def move_speed_noblock(self, x=None, y=None, z=None, speed=500, delay=0.2):
        """
        Move to coordinate at a certain speed. Will calculate the delay time
        needed for the program to wait during travel time by estimating the
        distance traveled and the speed. Will not block the main program
        while moving the nozzle; will return the time it will take to actually
        travel the distance. Allows us to record from the microphone as we are
        scanning this distance.
        @param x (int): distance to travel in x axis (mm) 
        @param y (int): distance to travel in y axis (mm) 
        @param z (int): distance to travel in z axis (mm) 
        @param speed (int): speed of nozzle in mm/min
        """
        speed_per_second = float(speed) / 60.0
        dx = 0.0 if not x else x
        dy = 0.0 if not y else y
        dz = 0.0 if not z else z
        move_vector = np.array([dx, dy, dz])
        distance = np.sqrt((move_vector ** 2).sum())

        # Actually send the move command, overriding any previous command
        self.p.move_coord(x=x, y=y, z=z, speed=speed)
        # Sleep the amount of time while the nozzle is moving, plus a small
        # delay for tolerance reasons
        return distance / speed_per_second

    def set_as_origin(self):
        # TODO: Set the current location as the origin (0, 0, 0) for the
        # scanner. The move seems to be a bit buggy with this though.
        raise NotImplementedError()

    def scan_continuous_lattice(self, end_coord, resolution, scan_speed=500, move_speed=3000,
        delay=0.1, sample_start=0, sample_end=10000, savepath="./data", note=""):
        """Scans lines across the x axis, with steps happening along the y axis.
        If we have a rectangular region, the scan lines will look like:
                |-------- x distance ----|
                __________________________
                __________________________
                ...
                __________________________
        When moving in a straight line, the microphone will be polled continuously
        during the time, so we can just linearly interpolate the location of
        the microphone at any given time here. The format of the saved files
        will be:
            <savepath>/<time.time()>/continuous_<xmin>_<xmax>_<yloc>.wav
        @param end_coord: tuple of x and y coordinate to scan until
        @param resolution: number of samples for the y dimension. For example,
            if we scan a 100 mm x 100 mm box, a scan size of 51 will mean
            a line every 2 mm on the y dimension
        @param savepath: folder that your saved wave files will be sent to.
        """
        start_time = time.time()
        # Create a folder to store all of our sound samples in
        print_begin_time = int(time.time())
        savefolder = os.path.join(savepath, str(print_begin_time))
        if not os.path.exists(savefolder):
            os.makedirs(savefolder)

        

        with open(os.path.join(savefolder, 'info'), 'w') as f:
            f.write("Scanning on grid, stopping at each point. Using parameters\n")
            f.write('SampleStart: %d\n' % sample_start)
            f.write('SampleEnd: %d\n' % sample_end)
            f.write('RecordTime: %d\n' % sample_start)
            f.write('end_coord: %s\n' % str(end_coord))
            f.write('resolution: %d\n' % resolution)
            f.write("\n\n")
            f.write("Additional notes:\n%s\n" % note)

        # since we are assuming that we start at the begin_coord, consider the relative coordinates where
        # begin_coord is just the origin already.
        # interweave the start and end points. The first start point is just the
        # origin, so we remove that.
        distance_x, distance_y = end_coord[0], end_coord[1]
        print("Expected Number of samples per line: %d" % int(scan_speed / 60.0 / delay / distance_x))
        scan_points = [[(0, y), (distance_x, y)] for y in np.linspace(0, distance_y, resolution)]
        scan_points = [item for sublist in scan_points for item in sublist]
        scan_points = scan_points[1:]
        
        # Beginning at the begin_coord, we are doing to stop and keep scanning
        # The even indices will be scanning/moving, while the odd indices
        # will be moving only.
        previous_coord = (0, 0)
        for idx, coord in tqdm.tqdm(list(enumerate(scan_points))):
            p_x, p_y = coord
            dx = p_x - previous_coord[0]
            dy = p_y - previous_coord[1]
            if idx % 2 == 0:
                fname = os.path.join(savefolder, "continuous_0_{}_{}".format(dx, p_y))
                record_time = self.move_speed_noblock(x=dx, y=dy, speed=scan_speed)
                self.mic.record_to_file(record_time, fname, delay=delay,
                    sample_start=sample_start, sample_end=sample_end)
                time.sleep(0.5)  # some padding time
            else:
                self.move_speed(x=dx, y=dy, speed=move_speed)
                time.sleep(0.5)  # some padding time
            previous_coord = p_x, p_y

        # Move back to our original location. Important since we are using relative coordinates.
        self.move(x=-distance_x, y=-distance_y)
        end_time = time.time()
        print('Total Scan Time: %s s' % str(end_time - start_time))


    def scan_grid(self, end_coord, resolution_x, resolution_y, scan_speed=4000, record_time=2.0, 
        delay=0.5, sample_start=0, sample_end=10000, savepath="./data", note=""):
        """Scans along a square lattice and saves each audio clip at each location.
        Audio clips will be saved the format:
            <savepath>/<time.time()>_<xloc>_<yloc>_<zloc>.wav
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

        with open(os.path.join(savefolder, 'info'), 'w') as f:
            f.write("Scanning on grid, stopping at each point. Using parameters\n")
            f.write('SampleStart: %d\n' % sample_start)
            f.write('SampleEnd: %d\n' % sample_end)
            f.write('RecordTime: %d\n' % sample_start)
            f.write('end_coord: %s\n' % str(end_coord))
            f.write('resolution (x): %d\n' % resolution_x)
            f.write('resolution (y): %d\n' % resolution_y)
            f.write("\n\n")
            f.write("Additional notes:\n%s\n" % note)

        # since we are assuming that we start at the begin_coord, consider the relative coordinates where
        # begin_coord is just the origin already.
        distance_x = end_coord[0]
        distance_y = end_coord[1]
        scan_points = [(x, y) for x in np.linspace(0, distance_x, resolution_x) 
                              for y in np.linspace(0, distance_y, resolution_y)]
        
        # Beginning at the begin_coord, we are doing to stop and keep scanning
        previous_coord = (0, 0)
        for p_x, p_y in tqdm.tqdm(scan_points):
            dx = p_x - previous_coord[0]
            dy = p_y - previous_coord[1]
            self.move_speed(x=dx, y=dy, speed=scan_speed)
            fname = os.path.join(savefolder, "{}_{}_{}".format(p_x, p_y, 0))
            self.mic.record_to_file(record_time, fname, delay=delay,
                sample_start=sample_start, sample_end=sample_end)
            previous_coord = p_x, p_y

        # Move back to our original location. Important since we are using relative coordinates.
        self.move_speed(x=-distance_x, y=-distance_y, speed=scan_speed)        


    def __str__(self):
        return "Scanner object"

    def __repr__(self):
        status = "Online" if self.p.online() else "Offline"
        return "Scanner [%s]" % status


if __name__ == '__main__':
    # Small test script for the TAZ 5 CNC machine in science center 102
    scan = Scanner(serial="/dev/ttyACM0")
    scan.scan_rectangular_lattice((0, 0), (10, 10), 11)
