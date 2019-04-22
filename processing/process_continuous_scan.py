import time
import glob
import pickle
import os
import argparse
import skimage

import numpy as np
from matplotlib import pyplot as plt


def compile_data_to_array(data_dir, sample_start=None, sample_end=None):
    fnames = list(sorted(glob.glob(os.path.join(data_dir, "*.pkl"))))
    
    print('Found %s records' % len(fnames))
    # Load into a list of tuples of xmin, xmax, y, data
    data = []
    XMIN = None
    XMAX = None
    for fname in fnames:
        with open(fname, 'rb') as f:
            fft_data = pickle.load(f)

        # Isolate the frequency range we're interested in if we collected
        # extra frequencies. otherwise, just take the argmax along the freqbins
        _, n_freq_bins = fft_data.shape
        if not sample_start: sample_start = 0
        if not sample_end: sample_end = n_freq_bins
        amplitudes = fft_data[:, sample_start:sample_end].max(axis=1)
        argmaxes = fft_data[:].argmax(axis=1)
        # print(argmaxes)

        name = os.path.basename(fname).replace('.pkl', '').replace('continuous_', '')
        coords = [float(coord) for coord in name.split('_')]
        xmin, xmax, y = coords
        XMIN = xmin
        XMAX = xmax
        data.append((xmin, xmax, y, amplitudes))
        
    # Sort by y coordinate (xmin and xmax are expected to be the same for all)
    data = list(sorted(data))
    if not data: raise RuntimeError('No Data Found')
        
    # Just get the amplitudes and stack them on each other to form an image
    ampdata = [d[-1] for d in data]

    # Get the minimum size of any of these, so we can interpolate to a fixed array length
    target_size = np.median(np.array([len(x) for x in ampdata]))
    print('Median number of records in continguous strip: %s' % str(target_size))
    resized_ampdata = [np.interp(np.linspace(XMIN, XMAX, target_size),
                       np.linspace(XMIN, XMAX, len(d)), d)
                       for d in ampdata]
    resized_ampdata = np.array(resized_ampdata)

    return resized_ampdata


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True, type=str, dest="data",
                        help="Path to data folder with .pkl dumps")
    parser.add_argument('--start', default=None, type=int, dest="start",
                        help="Sample number to start calculating from in "
                        "frequency bins from FFT")
    parser.add_argument('--end', default=None, type=int, dest="end",
                        help="Sample number to end calculating from in "
                        "frequency bins from FFT")
    parser.add_argument('--save', default=None, type=str, dest="save",
                        help="Where to save resulting image on disk")
    args = parser.parse_args()


    ampdata = compile_data_to_array(args.data, args.start, args.end)
    fig = plt.figure(figsize=(16, 16)) 
    long_side = max(list(ampdata.shape))
    short_side = min(list(ampdata.shape))
    plt.imshow(skimage.transform.resize(ampdata, (short_side, short_side)), cmap='seismic')
    # plt.imshow(ampdata, cmap='seismic')
    if args.save:
        fig.savefig(args.save)
    else:
        plt.show()