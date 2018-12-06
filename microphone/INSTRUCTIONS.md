# Microphone Setup

## Oscilloscope Setup

This section concerns setting up the scanning using an oscilloscope connection.

__TODO: Write up some easy docs__

## Normal Microphone Setup

This section concerns setting up a microphone that is connected to the computer's sound card. For example, something that is connected to the serial microphone jack on most desktops. A lot of our testing images were imaged using regular microphones, but for higher frequencies we used the Oscilloscope connection.

### Pyaudio Installation

#### Ubuntu 16.04

We'll be using pyaudio to capture microphone input while the CNC is scanning through 3D space. For the Ubuntu 16.04 setup inside Science Center 102, the following commands worked for installing pyaudio.

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