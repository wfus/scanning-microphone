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

# When we query the oscilloscope, it freezes the oscilloscope. Then, the scope
# has to get new samples to perform the FFT. Therefore, we have to wait until
# the oscilloscope can acquire the signal again and calculate a new FFT or else
# we will get the exact same values over and over (which is not good)
# RECORD_DELAY_TIME = 0.40
RECORD_DELAY_TIME = 0.50

class OscilloscopeMicrophone(object):
    """Implements the interface for the TEKTRONIX MDO3014 oscilloscope. The
    commands should be similar for any TEKTRONIX oscilloscope, but may differ
    slightly in the number of channels."""
    def __init__(self):
        # Try to connect to the first USBTMC oscilloscope found.
        rm = visa.ResourceManager('@py')
        devices = rm.list_resources()
        devnames = []
        for d in devices:
            # Oscilloscope should have USB and at least 4 pairs of semicolons
            # (bad critieria but whatever). Need to filter again later because
            # we also use USB for our signal generator
            if d.count(':') >= 8 and 'USB' in d:
                devnames.append(d) 

        if not devnames:
            print('Only found devices: %s' % str(devices))
            raise RuntimeError('Could not find an oscilloscope, check connection')
        
        rigol_devname = None
        for d in devnames:
            potential_device = rm.get_instrument(d)
            potential_device.write("*IDN?")
            time.sleep(0.2)  # give the device a bit of time to respond
            test_id = potential_device.read()
            print("Checking out device with ID: %s" % test_id)

            if 'tektronix' in test_id.lower():
                rigol_devname = d
                self.device = potential_device
                self.name = test_id
                break
            else:
                print("This is not a tektronix oscilloscope")
                potential_device.close()

        if not rigol_devname:
            raise RuntimeError('Could not find an Oscilloscope instrument, check connection')


    def _record(self, n, sample_start=0, sample_end=10000, delay=RECORD_DELAY_TIME):
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
            try:
                lst.append(self._fetch_fft_sample(sample_start, sample_end))
                time.sleep(delay)
            except ValueError as v_err:
                # Usually happens when oscilloscope data gets corrupted and
                # can't be interpreted as a float or something
                print('Got error when fetching microphone data: %s' % str(v_err))
                # If there are corrupted data locations we can mark these by
                # placing -1 values
                lst.append(np.zeros(sample_end - sample_start) - 1)
                time.sleep(delay)
        return np.array(lst)

    def record_to_file(self, num_seconds, fname, delay=0.5, sample_start=0, sample_end=10000):
        """Records <num_seconds> seconds of oscilloscope data and saves it as
        a numpy array to the file specified. User does not need to pass in a
        file extension."""
        fname += '.pkl'
        frames = self._record(num_seconds, delay=delay,
                              sample_start=sample_start,
                              sample_end=sample_end)
        frames.dump(fname)

    def _fetch_fft_sample(self, sample_start, sample_end):
        """Gets a sample of an FFT from the MATH command. Command may be
        specialized for the TEKTRONIX MDO3014 Oscilloscope. User specifies the
        range of the samples (corresponding to frequency range of interest).
        @param sample_start: sample number to start recording at
        @param sample_end: sample number to stop recording at
        """
        # self._write('MATH:DEFINE "FFT(CH1)"')
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

    def samples_to_frequency(self, sample_location):
        """Converts FFT sample locations to corresponding frequencies. Make
        sure that the unit of measurement is set to Hz on the oscilloscope,
        and that the active plot is on Math mode.
        @param sample_location (int): location of sample in fft data query
        @returns (int) frequency that corresponds to that sample location
        """
        try:
            xscale = self.device.query('MATH:HORIZONTAL:SCALE?')
            units = self.device.query('MATH:HORIZONTAL:UNITS?')
            if units:
                units = str(units).strip().replace('"', '').replace('\n', '')
            print('Oscilloscope FFT has 1 sample as %s %s' % (xscale, units))
            if units != "Hz":
                raise RuntimeError('Please set oscilloscope units to Hz')
            return sample_location * xscale

        except Exception as err:
            print("Are you sure you're on FFT mode with units of Hz? We got ")
            print("an error message: ")
            print(str(err))

    def frequency_to_samples(self, start_freq, end_freq):
        """Converts a range of frequencies to the FFT sample indices that would
        contain these range of frequencies. For example, if each sample is 10 Hz
        and we wanted the frequency range 27kHz-29kHz, this function would
        return (2700, 2800). Will make sure to fully enclose the frequency
        range."""
        try:
            xscale = self.device.query('MATH:HORIZONTAL:SCALE?')
            units = self.device.query('MATH:HORIZONTAL:UNITS?')
            if units:
                units = str(units).strip().replace('"', '').replace('\n', '')
            if xscale:
                xscale = xscale.strip()
            print('Oscilloscope FFT has 1 sample as %s %s' % (xscale, units))
            if units != "Hz":
                raise RuntimeError('Please set oscilloscope units to Hz')
            
            lower_sample_idx = np.floor(float(start_freq) / float(xscale))
            upper_sample_idx = np.ceil(float(end_freq) / float(xscale))
            return lower_sample_idx, upper_sample_idx
        except Exception as err:
            print("Are you sure you're on FFT mode with units of Hz? We got ")
            print("an error message: ")
            raise RuntimeError(str(err))

    def _write(self, b):
        self.device.write(b)
    
    def _query(self, b):
        print(self.device.query(b))

    def __repr__(self):
        return "Measurement Device: %s" % self.name


if __name__ == '__main__':
    mic = OscilloscopeMicrophone()
    
    from matplotlib import pyplot as plt

    NUM_SAMPLES = 10
    FREQUENCY_START = 0
    FREQUENCY_END = 100000

    xscale, yscale = mic.get_fft_scale()
    sample_start, sample_end = mic.frequency_to_samples(FREQUENCY_START, FREQUENCY_END)
    print(sample_start, sample_end)
    start = time.time()
    for _ in range(NUM_SAMPLES):
        y = mic._fetch_fft_sample(sample_start, sample_end)
    end = time.time()
    print("Took %s seconds to fetch FFT data %d times" % (str(end - start), NUM_SAMPLES))
    x = np.linspace(FREQUENCY_START, FREQUENCY_END, y.shape[0])

    plt.title('Oscilloscope FFT Grab')
    plt.xlabel('Frequency')
    plt.ylabel('Voltage')
    plt.plot(x, y)
    plt.show()
