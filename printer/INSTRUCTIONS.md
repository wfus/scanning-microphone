# Printer setup

We'll be using some code to control the printer, taken from `Printrun`. Since
we want direct control over the 3D printer or other CNC setup we will only
use the core class.

For some additional instructions on setting up the science center 3D printer,
see [here](INSTRUCTIONS_SCICEN_PRINTER.md).

## Installation and Permissions

First we have to install a few packages. __The code requires the use of Python
3__!

```bash
sudo pip3 install pyserial dbus-python psutil
```

You'll also have to add your user into the permissions group for USB and serial 
devices, unless you want to run all of the scripts with root access 
*(Protip: you don't)*.

```bash
# Command is sudo adduser <username> dialout
$ sudo adduser metamaterials dialout
```

__YOU WILL HAVE TO RESTART FOR THE CHANGES TO TAKE EFFECT.__ If you're wondering why that
didn't work, that is the reason most likely.


## Finding the printer

The printer should have a USB connection to the computer. An easy way to see if it is connected
is through the USB pipes in `/dev`. So unplug the USB connecting the computer to the 3D printer
and check the list of USB devices added. There is a helpful script in the `./printer` folder
that displays the devices and the port is it connected to.

```bash
$ cd printer
$ bash searchusb.sh
/dev/input/event5 - PixArt_Dell_MS116_USB_Optical_Mouse
/dev/input/mouse0 - PixArt_Dell_MS116_USB_Optical_Mouse
/dev/input/event4 - 413c_Dell_KB216_Wired_Keyboard
/dev/input/event3 - 413c_Dell_KB216_Wired_Keyboard
/dev/input/event6 - 04b3_USB_Optical_Mouse
/dev/input/mouse1 - 04b3_USB_Optical_Mouse
/dev/ttyACM0 - UltiMachine__ultimachine.com__RAMBo_6403636363835120E062
/dev/sdb - Innostor_Innostor_1989192216-0:0
/dev/sdb1 - Innostor_Innostor_1989192216-0:0
```

In this case, our printer was `UltiMachine__ultimachine.com__RAMBo_6403636363835120E062` 
with a device name __/dev/ttyACM0__. You will need the device name to connect later!

## Testing

To test to see if the printer is connected, go to the top level
directory and spin up a python interactive terminal. I recommend
using ipython for convenience.

```python
>>>from scanner import Scanner
>>>a = Scanner('/dev/ttyACM0')
ALSA lib pcm_dsnoop.c:618:(snd_pcm_dsnoop_open) unable to open slave
ALSA lib pcm_dmix.c:1052:(snd_pcm_dmix_open) unable to open slave
ALSA lib pcm.c:2495:(snd_pcm_open_noupdate) Unknown PCM cards.pcm.rear
ALSA lib pcm.c:2495:(snd_pcm_open_noupdate) Unknown PCM cards.pcm.center_lfe
ALSA lib pcm.c:2495:(snd_pcm_open_noupdate) Unknown PCM cards.pcm.side
ALSA lib pcm_dmix.c:1052:(snd_pcm_dmix_open) unable to open slave
Trying to connect printer through USB port /dev/ttyACM0
Attempting to look for connections on: /dev/ttyACM0
True

>>>a.p.move_coord(x=10)
```

If everything goes correctly, the CNC should move! Make sure to swap
out the device location if it isn't `/dev/ttyACM0` - use the 
previous script to find the device name you should use.