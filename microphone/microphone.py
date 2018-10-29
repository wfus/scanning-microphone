"""Class for handling the microphone during the 3D CNC controlled scan.
Different parameters may need to be set depending on the type of microphone
used. For our first test of the scanning microphone, we used a microphone from
Science Center 102 that plugs into the microphone jack in a desktop computer.
"""
import pyaudio
import numpy as np
import wave


class Microphone(object):
    """Class that manages microphone life and settings."""
    def __init__(self):
        # Takes the default microphone detected for now
        # TODO: Make a parameter that selects which microphone to use
        p = pyaudio.PyAudio()
        self._p = p

        # Get SR and NAME
        settings = p.get_default_input_device_info()
        self.settings = settings
        self.SR = settings['defaultSampleRate'] 
        self.NAME = settings['name']

        # Set some default parameters for recording
        self.FRAMES_PER_BUFF = 2048
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        
    def _record(self, n):
        """Records for n seconds, while blocking. Only returns control after
        recording is finished. Returns as sequence of chunks of 2 byte values.
        """
        stream = self._p.open(format=self.FORMAT,
                              channels=self.CHANNELS,
                              rate=int(self.SR),
                              input=True,
                              frames_per_buffer=self.FRAMES_PER_BUFF)
        nchunks = int(n * self.SR / self.FRAMES_PER_BUFF)
        frames = []
        for _ in range(nchunks):
            data = stream.read(self.FRAMES_PER_BUFF)
            frames.append(data)
        stream.stop_stream()
        stream.close()
        return frames
    
    def record_to_wav(self, n, fname):
        frames = self._record(n)
        # Save it to an actual file with proper parameters
        wavefile = wave.open(fname, 'wb')
        wavefile.setnchannels(self.CHANNELS)
        wavefile.setsampwidth(self._p.get_sample_size(self.FORMAT))
        wavefile.setframerate(self.SR)
        for frame in frames:
            wavefile.writeframes(frame)
        wavefile.close()
