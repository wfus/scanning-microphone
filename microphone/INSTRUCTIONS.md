# Microphone Setup

## Pyaudio Installation

### Ubuntu 16.04

We'll be using pyaudio to capture microphone input while the CNC is scanning through 3D space. For the Ubuntu 16.04 setup inside Science Center 102, the following commands worked for installing pyaudio.

```bash
sudo apt-get install libasound-dev portaudio19-dev libportaudio2 libportaudiocpp0
sudo apt-get install ffmpeg libav-tools
```

Then, we'll be able to install it through pip.

```bash
sudo pip install pyaudio wave
```

## Debugging

A nice way to see if your microphone is connected is with

```bash
arecord -l
```