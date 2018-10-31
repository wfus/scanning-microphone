# Scanning

The file `scanning.py` provides a lot of functionality for controlling an audio scan. The `Scanning` class
controls both the microphone and the CNC machine.

## A Simple Test

An easy test of our scanning microphone is by playing a single frequency to a headphone situated
along our CNC baseplate. Then, we play the single frequency and measure the 3D amplitude of this
frequency throughout space. This serves as a nice sanity check. Our first test will use Apple
Headphones connected to the same computer we use to control our CNC. We use `sox`, an open source
library, to play our sound while scanning.

```bash
sudo apt install sox
```

Now, we will send a 1 channel signal, for 100000 seconds (to kill just control c), with a frequency
of 6000. The -c controls the number of channels, and the first and second parameter are the number
of seconds and the frequency respectively.

```bash
play -n -c1 synth 100000 sine 6000
```
