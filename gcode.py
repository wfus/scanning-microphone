"""Bad GCODE generator.
@author: wfus 

Simple tool to generate GCode for 3D printers.
Used for the scanning microphone project.
"""
import argparse
import math
import numpy as np

setupData = {
    "Mode":          "TestExtrude",   # (Str) If Mode set to "Weld" perform welding job, if "TestExtrude" perform extrusion test without welding
    "DryRun":          True,   # (Bol) If DryRun true, do not extrude the wire
    "MaxZ":           320.0,   # (mm)  Height of the machine 
    "PrintRadius":    300.0,   # (mm)  Printable radius 
    "Z0":               0.0,   # (mm)  correction of the zero
    "WeldHeight":       2.2,   # (mm)  distance between weld tip & part
    "ApproachHeight":  10.0,   # (mm)  safe height for approach
    "TravelHeight":     5.0,   # (mm)  safe height for travel with arc
    "layerWait"  :     20.0,   # (s)   Time to wait between layers
    
    "ColdWeldSpeed": 2000.0,   # (mm/min) speed while welding
    "WeldSpeedHot":     0.4,   # (-)      ratio of hot weld speed to cold
    "HotLength":       40.0,   # (mm)     length over which the speed ratio is varied
    "WeldSpeedUp":      0.3,   # (%/s)    percentage of speed increase per seconds for welding
    "TravelSpeed":   5000.0,   # (mm/min) travel speed 

    "ExtrMxSpeed":   5000.0,   # (mm/min) Max wire speed
    
    "Acceleration":   100.0,   # (mm/s^2) Default Acceleration for the machine
    
    "PuddleTime":       0.0,   # (s)  Time stationary to create the weld puddle
    "ExtrusionFactor":  1.0,   # (-)  Multiplier of filament extruded over length
    "RetractionLen":   -1.0,   # (mm) If < 0 no retraction
    "Retractionfactor": 1.007, # (mm) disymetry between retract & extrude
    "RetractionPlay":   0.6,   # (mm)
    "RetractionTravel": 5.0,   # (mm)
    
    "NExtrude":       100,     # (-) number of extrudes/retract to be performed in the extrusion test
    "IgnitCoord": { "x":-30.0, "y":25.0, "z":8 ,"len": 20.0 },  # initial coordinates
 }


class GCodeProgram(object):
    def __init__(self, startup=True, verbose=False):
        self.gcode = []
        self.last_point = {"x": None, "y": None, "z": None}  # store the position after each move
        self.verbose = verbose

    def move(self, x=None, y=None, z=None, e=None, speed=None, comment=None):
        s = "G1 "
        if x is not None: 
            s += "X" + str(x) + " "
            self.last_point["x"] = x 
        if y is not None: 
            s += "Y" + str(y) + " "
            self.last_point["y"] = y 
        if z is not None: 
            s += "Z" + str(z) + " "
            self.last_point["z"] = z 
        if e is not None: s += "E" + str(e) + " "
        if speed is not None: 
            if speed == "Weld"  : s += "F" + str(setupData["WeldSpeed"]) + " "
            if speed == "Travel": s += "F" + str(setupData["TravelSpeed"]) + " "
        if comment is not None:  s += "; " + comment    
        self.gcode.append(s)

    def pause(self, ms):
        """Pauses for a certain number of milliseconds. Command for most GCODE flavors is
        G4 P{} (number of milliseconds)
        G4 S{} (number of seconds)
        """
        self.gcode.append("G4 P{}".format(ms))

    def __str__(self):
        return "\n".join(self.gcode)

    def save(self, fname):
        """Saves the generated GCODE to a local file"""
        with open(fname, 'w') as f:
            f.writelines(str(self))


if __name__ == '__main__':
    gcode = GCodeProgram()
        