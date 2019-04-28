# Postprocessing

Postprocessing will differ depending on how measurement was performed.
There should be a sample notebook for how to process the different ways
of scanning.

## Oscilloscope Scanning

### Scanning Point by Point

This method of scanning is by first specifying a list of coordinates that you
want to sample from.
Then, the basic control flow looks like:

1. Go to next point in list.
2. Stay still and record for <record_time> seconds. 
3. Recording means repeatedly querying the FFT from the oscilloscope.
4. Finish recording and repeat process with next point in list.

You're probably doing this if you're using the `scan_rectangular_lattice`
or `scan_rectangular_prism` command from the `Scanner` class.
The format expected for this type of scan is

```bash
folder/<x_coord>_<y_coord>_<z_coord>.pkl
```

where each pickle file contains a numpy array of dimensions
`NUM_SAMPLES x FFT_RESOLUTION`.


### Continuous Scanning in Lattice

This method is useful for scanning a 2D rectangular area or a prism.
Suppose that you want to scan a 2D grid of size 10 x 10.
Using this method, you can move at a constant velocity from (0, 0) to (0, 10),
and sample from the oscilloscope repeatedly and constantly while doing so.
Then, you do the same thing from (1, 0) to (1, 10), and repeat.

You're probably doing this if you're using the `scan_continuous_lattice`
command from the `Scanner` class.
The format expected for this type of scan is

```bash
folder/continuous_<x_start>_<x_end>_<y_coord>.pkl
```

where each pickle file contains a numpy array of dimensions
`NUM_SAMPLES_PER_CONTINUOUS_LINE x FFT_RESOLUTION`.

## Scanning with an Analog Microphone

TODO: Document this last, it's not that useful to be honest.
