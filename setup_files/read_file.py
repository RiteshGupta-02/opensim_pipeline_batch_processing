import pandas as pd
from scipy.signal import butter, filtfilt

'''
to read the opensim files with header and return the pandas dataframe
'''

def smooth_data(data, cutoff_freq=20, fs=1000):
    '''Applies a 2nd order butterworth filter to smooth the data.'''
    nyquist_freq = 0.5 * fs
    normal_cutoff = cutoff_freq / nyquist_freq
    b, a = butter(2, normal_cutoff, btype='low', analog=False)
    return pd.DataFrame(filtfilt(b, a, data, axis=0), columns=data.columns)

def read_file(file, sep='\t', skiprows = None, cutoff_freq=20, fs=1000):

    if skiprows is None:
        with open(file, 'r') as f:
            for i, line in enumerate(f):
                if 'endheader' in line.lower():
                    skiprows = i + 1
                    break

    data = pd.read_csv(
        file,
        sep=sep,
        skiprows=skiprows
    )

    data = smooth_data(data, cutoff_freq=cutoff_freq, fs=fs)
    return data