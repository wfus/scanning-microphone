"""Class that manages using an oscilloscope as the preferred Microphone
source. Should use the exact same API as the original Microphone class in
order to make it easy to switch between the two.

Some of the command we use to interface with the oscilloscope can be found
https://download.tek.com/manual/MDO4000-B-MSO-DPO4000B-and-MDO3000-Oscilloscope-Programmer-Manual-Rev-A.pdf
"""
import visa


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
        recording is finished. Returns as sequence of chunks of 2 byte values.

        This commands may be specialized for the TEKTRONIX MDO3014 series,
        so this may have to be changed for other oscilloscopes.

        MAKE SURE MATH IS TURNED ON ON THE OSCILLOSCOPE OR IT MAY SAY THAT
        THE COMMAND HAS TIMED OUT!!!
        """
        pass
        
    
    def _fetch_fft_sample(self):
        """Gets a sample of an FFT from the MATH command. Command may be
        specialized for the TEKTRONIX MDO3014 Oscilloscope"""
        self._write('MATH:DEFINE "FFT(CH1)"')
        self._write(':DATa:SOUrce MATH')
        self._write(':DATa:STARt 0')
        self._write(':DATa:STOP 10000')
        self._write(':WFMOutpre:ENCdg ASCii')
        self._write(':HEADer 0')
        self._write(':VERBose 0')
        return self.device.query_ascii_values('CURVE?')

    def _print_fft_units(self):
        print(self._query('MATH:HORIZONTAL:UNITS?'))
        print(self._query('MATH:VERTICAL:UNITS?'))

    def _write(self, b):
        self.device.write(b)
    
    def _query(self, b):
        print(self.device.query(b))


if __name__ == '__main__':
    mic = OscilloscopeMicrophone()
    
    from matplotlib import pyplot as plt
    print(mic._query('MATH?'))
    plt.plot(mic._fetch_fft_sample())
    plt.show()

    #mic._query(':WFMOutpre?')
    
