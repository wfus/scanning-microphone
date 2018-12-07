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

    def _record(self, n):
        """Records for n seconds, while blocking. Only returns control after
        recording is finished. For the oscilloscope, this returns our result
        as a numpy array, with dimensions (num_recordings, num_samples). We will
        try to do as many recordings as possible within the time limit.

        This commands may be specialized for the TEKTRONIX MDO3014 series,
        so this may have to be changed for other oscilloscopes.

        MAKE SURE MATH IS TURNED ON ON THE OSCILLOSCOPE OR IT MAY SAY THAT
        THE COMMAND HAS TIMED OUT!!!
        """
        end_time = time.time() + n
        lst = []
        while time.time() < end_time:
            lst.append(self._fetch_fft_sample())
        return np.array(lst)

    def record_to_file(self, n, fname):
        fname += '.pkl'
        frames = self._record(n)
        frames.dump(fname)

    def _fetch_fft_sample(self, samples=5000, range=None):
        """Gets a sample of an FFT from the MATH command. Command may be
        specialized for the TEKTRONIX MDO3014 Oscilloscope
        
        @param: number of samples to grab
        """
        self._write('MATH:DEFINE "FFT(CH1)"')
        self._write(':DATa:SOUrce MATH')
        self._write(':DATa:STARt 0')
        self._write(':DATa:STOP %d' % samples)
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
    y = mic._fetch_fft_sample()
    end = time.time()
    print("Took %s seconds to fetch fft data" % str(end - start))
    x = np.array(list(range(y.shape[0]))) * xscale

    plt.title('Oscilloscope FFT Grab')
    plt.xlabel('Frequency')
    plt.ylabel('Voltage')
    plt.plot(x, y)
    plt.show()

    #mic._query(':WFMOutpre?')
    
