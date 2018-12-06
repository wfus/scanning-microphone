# Printer setup

We'll be using some code to control the printer, taken from `Printrun`. Since
we want direct control over the 3D printer or other CNC setup we will only
use the core class.

## Installation

First we have to install a few packages. __The code requires the use of Python
3__!

```bash
sudo pip3 install pyserial dbus-python psutil
```

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