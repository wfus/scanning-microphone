"""Class that manages using an oscilloscope as the preferred Microphone
source. Should use the exact same API as the original Microphone class in
order to make it easy to switch between the two.

Some of the command we use to interface with the oscilloscope can be found
https://download.tek.com/manual/MDO4000-B-MSO-DPO4000B-and-MDO3000-Oscilloscope-Programmer-Manual-Rev-A.pdf
"""
import visa
import time
import numpy as np
import pickle


class OscilloscopeMicrophone(object):
    """Implements the interface for the TEKTRONIX MDO3014 oscilloscope. The
    commands should be similar for any TEKTRONIX oscilloscope, but may differ
    slightly in the number of channels."""
    def __init__(self):
        # Try to connect to the first USBTMC oscilloscope found.
        rm = visa.ResourceManager('@py')
        devices = rm.list_resources()
        devname = None
        for d in devices:
            # Oscilloscope should have USB and at least 4 pairs
            # of semicolons (bad critieria but whatever)
            if d.count(':') >= 8 and 'USB' in d:
                devname = d
                break

        if not devname:
            print('Only found devices: %s' % str(devices))
            raise RuntimeError('Could not find an oscilloscope, check connection')
        
        self.device = rm.get_instrument(devname)

        # Sanity check - print out the device name through the pretty
        # universal command "*IDN?"
        res = self.device.query('*IDN?')
        print('Using oscilloscope: %s' % res)

    def _record(self, n, sample_start=0, sample_end=5000):
        """Records for n seconds, while blocking. Only returns control after
        recording is finished. For the oscilloscope, this returns our result
        as a numpy array, with dimensions (num_recordings, num_samples). We will
        try to do as many recordings as possible within the time limit.

        This commands may be specialized for the TEKTRONIX MDO3014 series,
        so this may have to be changed for other oscilloscopes.

        MAKE SURE MATH IS TURNED ON ON THE OSCILLOSCOPE OR IT MAY SAY THAT
        THE COMMAND HAS TIMED OUT! The best setting is to turn the display for
        all channels off and math on, so the FFT is the only thing rendering
        on the display at the time.

        To figure out which range of samples of the FFT to record, you may have
        to convert your frequency range of interest into samples range by
        querying the units that the oscilloscope is currently on.

        @param sample_start (int): start of FFT samples to collect
        @param sample_end (int): end of FFT samples to collect
        """
        end_time = time.time() + n
        lst = []
        while time.time() < end_time:
            lst.append(self._fetch_fft_sample(sample_start, sample_end))
        return np.array(lst)

    def record_to_file(self, num_seconds, fname):
        """Records <num_seconds> seconds of oscilloscope data and saves it as
        a numpy array to the file specified. User does not need to pass in a
        file extension."""
        fname += '.pkl'
        frames = self._record(num_seconds)
        frames.dump(fname)

    def _fetch_fft_sample(self, sample_start, sample_end):
        """Gets a sample of an FFT from the MATH command. Command may be
        specialized for the TEKTRONIX MDO3014 Oscilloscope. User specifies the
        range of the samples (corresponding to frequency range of interest).
        @param sample_start: sample number to start recording at
        @param sample_end: sample number to stop recording at
        """
        self._write('MATH:DEFINE "FFT(CH1)"')
        self._write(':DATa:SOUrce MATH')
        self._write(':DATa:STARt %d' % sample_start)
        self._write(':DATa:STOP %d' % sample_end)
        self._write(':WFMOutpre:ENCdg ASCii')
        self._write(':HEADer 0')
        self._write(':VERBose 0')
        return np.array(self.device.query_ascii_values('CURVE?'))

    def _print_fft_units(self):
        self._query('MATH:HORIZONTAL:SCALE?')
        self._query('MATH:VERTICAL:SCALE?')
        self._query('MATH:HORIZONTAL:UNITS?')
        self._query('MATH:VERTICAL:UNITS?')

    def get_fft_scale(self):
        """Returns x and y scale in Hz and volts, respectively"""
        xscale = self.device.query('MATH:HORIZONTAL:SCALE?')
        yscale = self.device.query('MATH:VERTICAL:SCALE?')
        # TODO: Figure why everything is off by a factor of 10^3
        return float(xscale) / 1000.0, float(yscale)

    def _write(self, b):
        self.device.write(b)
    
    def _query(self, b):
        print(self.device.query(b))


if __name__ == '__main__':
    mic = OscilloscopeMicrophone()
    
    from matplotlib import pyplot as plt
    import numpy as np

    xscale, yscale = mic.get_fft_scale()
    start = time.time()
    y = mic._fetch_fft_sample(0, 5000)
    end = time.time()
    print("Took %s seconds to fetch fft data" % str(end - start))
    x = np.array(list(range(y.shape[0]))) * xscale

    plt.title('Oscilloscope FFT Grab')
    plt.xlabel('Frequency')
    plt.ylabel('Voltage')
    plt.plot(x, y)
    plt.show()
