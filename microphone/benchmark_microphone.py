"""Benchmark our microphone to see exactly how much many samples per
second we can query until the oscilloscope just returns the exact
same sequence (due to it not having enough time to actually calculate
the FFT with the new samples)"""

import argparse
import numpy as np
import time
from matplotlib import pyplot as plt
from oscilloscope import OscilloscopeMicrophone


def test_query_with_delay(oscilloscope, begin, end, delay):
    """Queries the FFT from the oscilloscope for the sample range
    [begin, end) with a delay (seconds) between each query. We
    will query 10 times and return True if they are all distinct,
    which means that the oscilloscope has time to recalculate the
    FFT values in between queries (which we really want!)"""
    lst = []
    for _ in range(10):
        try:
            lst.append(oscilloscope._fetch_fft_sample(begin, end))
            time.sleep(delay)
        except ValueError as v_err:
            # Usually happens when oscilloscope data gets corrupted and
            # can't be interpreted as a float or something
            print('Got error when fetching microphone data: %s' % str(v_err))
            # If there are corrupted data locations we can mark these by
            # placing -1 values
            lst.append(np.zeros(end - begin) - 1)
            time.sleep(delay)

    # check if the rows in an np array are the same. we can check if they
    # are the same by comparing the means of each sample taken.
    arr = np.array(lst, dtype=np.float32)
    # plt.plot(arr.mean(axis=0))
    # plt.show()

    sample_means = arr.mean(axis=1)


    num_unique = len(set(list(sample_means)))
    num_samples = len(sample_means)


    # Return that our queries are good if unique samples is at least 80% of
    # all of the samples.
    return num_unique >= num_samples - 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--sample-start', type=int, default=0, dest='start',
                        help='[sample-start, sample-end) query fft')
    parser.add_argument('--sample-end', type=int, default=10000, dest='end',
                        help='[sample-start, sample-end) query fft')
    args = parser.parse_args()


    mic = OscilloscopeMicrophone()
    start = args.start
    end = args.end
    print('Testing Oscilloscope querying from samples %d to %d' % (start, end))

    delay = 0.5
    for _ in range(10):
        is_good = test_query_with_delay(mic, start, end, delay)
        res_str = 'passed' if is_good else 'bad!'
        print('Delay: %02f s       Result: %s' % (delay, res_str))

        if is_good:
            delay *= 0.5
        else:
            delay *= 2
    
