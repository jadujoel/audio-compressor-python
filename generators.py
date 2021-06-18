import numpy as np
import scipy

def sine(sample_rate=48000, frequency = 1000, duration = 1, dBFS = -10):
    samples = np.arange(duration * sample_rate) / sample_rate
    signal = np.sin(2 * np.pi * frequency * samples)
    return signal * (10**(dBFS/20))

def chirp(start_freq=20.0, stop_freq=20000, duration=1, dBFS=-10, sample_rate=48000, method='linear'):
    # method{‘linear’, ‘quadratic’, ‘logarithmic’, ‘hyperbolic’}, optional
    t = np.linspace(start=0, stop=duration, num=(sample_rate*duration))
    #signal = scipy.signal.chirp(t=t, f0=start_freq, t1=t[-1], f1=stop_freq, method=method)
    signal = scipy.signal.chirp(t=t, f0=start_freq, t1=duration, f1=stop_freq, method=method)
    signal *= 10**(dBFS/20)
    return signal

def silence(sample_rate=48000, duration=1):
    return np.zeros((int(duration*sample_rate)))
