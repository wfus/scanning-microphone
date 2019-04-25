# Microphone Setup

## Normal Microphone Setup

This section concerns setting up a microphone that is connected to the
computer's sound card. For example, something that is connected to the serial
microphone jack on most desktops. A lot of our testing images were imaged using
regular microphones, but for higher frequencies we used the Oscilloscope connection.

### Pyaudio Installation

#### Ubuntu 16.04/18.04

We'll be using pyaudio to capture microphone input while the CNC is scanning
through 3D space. For the Ubuntu 16.04 setup inside Science Center 102, 
the following commands worked for installing pyaudio.

```bash
sudo apt-get install libasound-dev portaudio19-dev libportaudio2 libportaudiocpp0
sudo apt-get install ffmpeg libav-tools
```

Then, we'll be able to install it through pip.

```bash
sudo pip install pyaudio wave
```

#### Debugging

A nice way to see if your microphone is connected is with

```bash
arecord -l
```

## Oscilloscope Setup

This section concerns setting up the scanning using an oscilloscope connection.

The oscilloscope we used was borrowed from Science Center 102, and it is a
Tektronix MDO3014.

### Setup

We're going to need a way to communicate with most oscilloscopes. This is made
easier with [Python-USBTMC](https://github.com/python-ivi/python-usbtmc), so we
can actually send the commands to the oscilloscope and get data from it.

```bash
pip install pyusb
pip install python-usbtmc
```

Then, we actually have to add a group for the oscilloscope devices. You will
only have to do this step once.

```bash
sudo apt-get install libusb-dev
sudo groupadd usbtmc
# Command is: sudo usermod -a -G usbtmc <current_user>
sudo usermod -a -G usbtmc metamaterials
```



Now, connect to oscilloscope and find the vendor ID numbers. The easiest way to do this is through lsusb or dmesg. Unplug and plug back in the oscilloscope, and then run `dmesg`.

```bash
$ dmesg

[ 3294.893192] usb 1-1.5: USB disconnect, device number 8
[ 3456.141296] usb 1-1.5: new high-speed USB device number 10 using ehci-pci
[ 3456.352455] usb 1-1.5: New USB device found, idVendor=0699, idProduct=0408
[ 3456.352462] usb 1-1.5: New USB device strings: Mfr=2, Product=3, SerialNumber=4
[ 3456.352466] usb 1-1.5: Product: MDO3014
[ 3456.352470] usb 1-1.5: Manufacturer: Tektronix
[ 3456.352474] usb 1-1.5: SerialNumber: C021660
[ 3456.432415] usbcore: registered new interface driver usbtmc
```

In this case, our Tektronix oscilloscope has idVendor 0x0699 and idProduct
0x0408 (these values are in hex!). Record those numbers down and let's add them
into our `udev` rules.

```bash
sudo vim /etc/udev/rules.d/usbtmc.rules
```

and add a section for our current oscilloscope

```
# USBTMC instruments
# Basement Oscilloscope (Borrowed from Science Center 102)
# Tektronix MDO3014
# This is the one in the metamaterials room
SUBSYSTEMS=="usb", ACTION=="add", ATTRS{idVendor}=="0699", ATTRS{idProduct}=="0408", GROUP="usbtmc", MODE="0660"
```
