# -*- coding: utf-8 -*-
"""
Bad GCODE generator.
@author: wfus 

Simple tool to generate GCode.
"""
import argparse
import math
import numpy as np

# settings
# This is where you modify the settings for a test print
# At terms this should be moved in a json set-up file
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
      
workData = {    # not used yet
        "Task001": {
            "Type"  : "line",
            "Points": [ { "x": 0.0, "y": 10.0, "len": 50.0, "angl": 30.0}]
        },
        "Task002": {
            "Type"  : "rect",
            "Points": [ { "x": 0.0, "y": 20.0}, { "x": 50.0, "y": 30.0}]
        },
    }

################ Global variables should not be modified ######################
E         = 0                                                                  # (mm)  Extrusion length  
lastPoint = {"x": None, "y": None, "z": None}                                  # store the position after each move


def circle(x, y, r, n=20):                                                     # some premitives for testing
    print("  ## circle(x, y, r) ##")
    li = []
    a  = 2 * math.pi / n 
    for i in range(0, n+1): 
        ai = a * i
        Xi = x + r * math.cos(ai)
        Yi = y + r * math.sin(ai)
        li.append([Xi, Yi])
        print("[ " + str(Xi) + "\t, " + str(Yi) + "]")
    return li
     
def line(x, y, l, a):
     print("  ## line(x, y, l, a) ##")
     li = [[x, y], [x+l*math.cos(math.radians(a)), y+l*math.sin(math.radians(a))]]
     return li
   
def calcTime(speed, dist):                                                     # not correct but should be relatively proportional
    t = dist / speed
    return t
   
def move(x=None, y=None, z=None, e=None, speed=None, comment=None):            # Generate the move command with optional parameters
    global lastPoint
    s = "G1 "
    if x is not None: 
        s += "X" + str(x) + " "
        lastPoint["x"] = x 
    if y is not None: 
        s += "Y" + str(y) + " "
        lastPoint["y"] = y 
    if z is not None: 
        s += "Z" + str(z) + " "
        lastPoint["z"] = z 
    if e is not None: s += "E" + str(e) + " "
    if speed is not None: 
        if speed == "Weld"  : s += "F" + str(setupData["WeldSpeed"  ]) + " "
        if speed == "Travel": s += "F" + str(setupData["TravelSpeed"]) + " "
    if comment is not None:  s += "; " + comment    
    s += "\n"
    return s
    
def initiateArc(zMargin):
    #print "  ## move() ##"
    global lastPoint
    s = "M3 "
    s += "X" + str(setupData["IgnitCoord"]["x"]) + " "
    s += "Y" + str(setupData["IgnitCoord"]["y"]) + " "
    s += "Z" + str(setupData["IgnitCoord"]["z"]) + " "
    if zMargin is not None: s += "D" + str(zMargin) + " "
    s += "\n"
    lastPoint["x"] = setupData["IgnitCoord"]["x"] 
    lastPoint["y"] = setupData["IgnitCoord"]["y"] 
    lastPoint["z"] = setupData["IgnitCoord"]["z"]  
    return s
  
def printSegment(X1, Y1, X2, Y2):                                              # print a single segments
    #print "  # printSegment(X1, Y1, X2, Y2) #"
    printSeg  = "; Segment starts\n"
    
    global E
    global setupData
    dX    = X2 - X1
    dY    = Y2 - Y1
    dL    = math.sqrt(dX**2+dY**2)
    l     = 0.0
    steps = int(dL / setupData["RetractionTravel"])
    dXi   = dX/steps
    dYi   = dY/steps
    dl    = math.sqrt(dXi**2+dYi**2)

    if setupData["DryRun"]: 
        ret = 0.0
        ex  = 0.0        
    elif setupData["RetractionLen"] <= 0.0 :
        ret = 0.0
        ex  = dl * setupData["ExtrusionFactor"]                              # calculate extrusion to perform
    else:
        ret =     setupData["RetractionLen"   ]  +        setupData["RetractionPlay" ]
        ex  = ret*setupData["Retractionfactor"]  + 2*dl * setupData["ExtrusionFactor"]  # calculate extrusion to perform
    for i in range(0, steps):
        l += math.sqrt(dXi**2 + dYi**2)
        setupData["WeldSpeed"] = setupData["ColdWeldSpeed"] + setupData["ColdWeldSpeed"] * setupData["WeldSpeedHot"] * min(l/setupData["HotLength"] , 1)
        print("WS:%f" % setupData["WeldSpeed"])
        if ret > 0 :
            E        += ex
            printSeg += move( e=E, speed="Travel", comment="Weld"   )
            E        += -ret
            printSeg += move( e=E, speed="Travel", comment="Retract")
            printSeg += move( x=lastPoint["x"] + dXi, y=lastPoint["y"] + dYi,  speed="Weld", comment="Move"   )
        else:
            E        += ex
            printSeg += move( x=lastPoint["x"] + dXi, y=lastPoint["y"] + dYi,  e=E, speed="Weld", comment="Move"   )
    print("l:%f"  % l)
    print("dL:%f" % dL)
    return printSeg

def printSegments(li):                                                         #print a list of segments
    print("  ## printSegments() ##")
    ZTravel = setupData["Z0"] + setupData["TravelHeight"]
    ZWeld   = setupData["Z0"] + setupData["WeldHeight"]
    s  = "; Segments starts\n"
    s += move( z=ZTravel,              speed="Travel", comment="Raise torch" )
    s += move( x=li[0][0], y=li[0][1], speed="Travel", comment="Position start of weld" )
    s += move( z=ZWeld,                speed="Travel", comment="Lower torch" )
    s += "G4 P" + str(int(setupData["PuddleTime"  ]*1000.0)) + " ; Wait to create weld puddle\n"
    for i in range(1, len(li)):
        s += printSegment(li[i-1][0], li[i-1][1], li[i][0], li[i][1])
    return s
    
def pause(ms):
    """Pauses for a certain number of milliseconds. Command for most GCODE flavors is
        G4 P{} (number of milliseconds)
        G4 S{} (number of seconds)
    """
    return "G4 P{}\n".format(ms)


def startSequence():                                                           # The start sequance to be ready to print
    print("  ### startSequence() ###")
    startSeq = ""
    # startSeq += "; Initialisation Sequence \nG21    ; Set units to millimeters \nG28    ; Home all axes \nG90    ; Use absolute coordinates \nG92 E0 ; Reset extrusion distance \nM82    ; Use absolute distances for extrusion\n"
    # startSeq += "M204 S" + str(setupData["Acceleration"]) + " ; Set the default Acceleration\n" 
    # startSeq += move( z=100, speed="Travel", comment="Position Torch for ignition")
    # startSeq += move( x=setupData["IgnitCoord"]["x"],      y=setupData["IgnitCoord"]["y"], speed="Travel", comment="Position Torch for ignition")
    return startSeq

def printSequence():                                                           # The actual printing sequence  ######## TO be modified acording to your needs #######
    print("  ### printSequence() ###")
    global E
    global setupData
    x         = setupData["IgnitCoord"]["x"] - 5
    y         = setupData["IgnitCoord"]["y"] + 0
    E         = 0.0                                                            # initialise extrusion distance
    printSeq  = "; Welding starts\n"
    zMargin   = 0;
    # loop for each layers [speed, puddle time]
    for s in [[ 0.0, 5.0, 00],  
              [ 0.0, 6.0, 10],  
              [ 0.0, 8.0, 10],  
              [ 0.0,10.0, 10]]:
        setupData["Z0"           ]    = s[0]                                      # Change layer increment Z position
        setupData["ExtrusionFactor"]  = s[1]                                      # Set the puddle time
        setupData["IgnitCoord"]["y"] += s[2]
        y = setupData["IgnitCoord"]["y"]
        print( "Set WS to:%f" % setupData["ColdWeldSpeed" ])

        li        = line(x, y, 60, 00)                                         # print a line
        #li        = circle(x, y, 50, 40)                                      # Print a circle
        #printSeq += move( x=setupData["IgnitCoord"]["x"],      y=setupData["IgnitCoord"]["y"], z=setupData["IgnitCoord"]["z"], speed="Travel", comment="Position Torch for ignition")
        #print "Position Torch for ignition"
        printSeq += initiateArc(zMargin)
        printSeq += "; Puddle = " + str(setupData["PuddleTime"]) + "s \tSpeed = " + str(s[0]) + "mm/min \tdY = " + str(s[2]) + "\n"        # Comment for the GCode
        
        printSeq += printSegments(li)                                          # generate the GCode
        printSeq += move( x=lastPoint["x"] + 50.0, z=lastPoint["z"] + 100.0, speed="Travel", comment="Break Ark")
        printSeq += "G4 P" + str(int(setupData["layerWait"  ]*1000.0)) + " ; Wait between layers to cool down\n"
        setupData["IgnitCoord"]["z"] = 1
        zMargin   = 0.5;
    return printSeq

def stopSequence():                                                            # The stopping sequance to break the ark & return home
    print("  ### stopSequence( ) ###")
    stopSeq  = "; Welding Ends\n"
    stopSeq += move( x=0.0, y=0.0,      z=lastPoint["z"] + 50.0, speed="Travel", comment="Recenter")
    stopSeq += "G28 X0  ; home X axis\n"
    return stopSeq

def testExtrudeSequence():                                                     # The Extrude testing sequence to verify extrusion parameters without welding
    print("  ### testExtrudeSequence( ) ###")
    global E
    global setupData
    E        = 0.0   # initialise extrusion distance
    ret      = setupData["RetractionLen"] + setupData["RetractionPlay"]
    ex       = ret*setupData["Retractionfactor"] + 2*setupData["RetractionTravel"] * setupData["ExtrusionFactor"]  # calculate extrusion to perform
    print("ex :%f" % ex)
    print("ret:%f" % ret)
    
    testSeq  = "; Extrusion Test Starts\n"
    for _ in range(0, setupData["NExtrude"]):        
        E       +=  ex
        testSeq +=  move( e=E, speed="Travel", comment="Weld"   )
        testSeq +=  "G4 P20\n"
        E       += -ret
        testSeq +=  move( e=E, speed="Travel", comment="Retract")
        testSeq +=  "G4 P20\n"
    return testSeq

def saveData(mydata, fileName):                                                # save a string to a given filename
    print("  ### saveData(mydata, fileName) ###")
    if mydata != None:
        print("  #### data to be saved ####")
        try:
            f = open(fileName, "w")
            print("  #### o ####")
            f.write(mydata)
            print("  #### W ####")
        except:
            print("Failed to write file: %s" % fileName)
            raise FileNotFoundError


def testMoveSequence():                                                     # The Extrude testing sequence to verify extrusion parameters without welding
    print("  ### testMoveSequence( ) ###")
    global E
    global setupData
    testSeq = ""
    for _ in range(0, 100):        
        testSeq +=  move( x=200, y=200, z=50, speed="Travel")
        testSeq +=  move( x=0, y=0, z=40, speed="Travel")
    return testSeq


def move_grid(top_left, bottom_right, z=30, vres=1, hres=1, delay=2000):
    """Scans in a grid formation, from the top left to the bottom right. To make
    sure that movements take approximately the same time, we will try doing a
    snake formation."""
    cmds = ""
    x1, y1 = top_left
    x2, y2 = bottom_right 
    print("Moving on a grid with parameters: ")
    print("\txscan: {} -> {}".format(x1, x2))
    print("\tyscan: {} -> {}".format(y1, y2))
    n_hsteps = int(np.abs(x2 - x1) / hres) + 1
    n_vsteps = int(np.abs(y2 - y1) / vres) + 1
    points = [(x, y) for x in np.linspace(x1, x2, n_hsteps) for y in np.linspace(y1, y2, n_vsteps)]
    for px, py in points:
        cmds += move(x=px, y=py, z=z, speed="Travel")
        cmds += pause(delay)
    return cmds


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output', type=str, help='Output gcode file',
                        required=True)
    parser.add_argument('-p', '--path', type=str, choices=['grid'],
                        default='grid', help='Type of path to choose.')
    args = parser.parse_args()

    mydata = startSequence()
    if args.path == 'grid':
        mydata += move_grid((50, 50), (150, 150), z=150, vres=5, hres=5)
    else:
        mydata  = startSequence()
        mydata += testMoveSequence()
    print(mydata)                                      # Display it on the screen
    saveData(mydata, args.output)                               # Save it in the specified file
    
    
    