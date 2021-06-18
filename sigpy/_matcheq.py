from scipy import signal, interpolate
import numpy as np
import statsmodels.api as sm

class MatchEQ:
    def __init__(self, sample_rate=48000, smoothing = 0.0375, fft_size=4096, min_freq=100, max_freq=8000, mix=1):
        self.sample_rate = sample_rate
        self.fft_size = fft_size
        self.lowess_frac = smoothing
        self.lowess_it = 0
        self.lowess_delta = 0.001
        self.lin_log_oversampling = 4
        self.min_value = 1e-6
        self.min_freq = min_freq
        self.max_freq = max_freq
        self.mix = mix

    def create_fft(self, audio):
        *_, specs = signal.stft(
            audio,
            fs = self.sample_rate,
            window = 'boxcar',
            nperseg = self.fft_size,
            noverlap = 0,
            boundary = None,
            padded = False
            )
        return specs

    def get_ifft(self,fft):
        t, x = signal.istft(fft,
            fs = self.sample_rate,
            window = 'boxcar',
            nperseg = self.fft_size, #None,
            noverlap = 0,
            nfft = None,
            input_onesided = True,
            boundary = None,#True,
            time_axis = -1,
            freq_axis = -2
            )
        return x

    def average_fft(self, specs):
        return np.abs(specs).mean(axis=1)

    def smooth_lowess(self, array: np.ndarray) -> np.ndarray:
        result = sm.nonparametric.lowess(
            endog = array,
            exog = np.linspace(0, 1, len(array)),
            frac = self.lowess_frac,
            it = self.lowess_it,
            delta = self.lowess_delta
            )[:, 1]
        return result

    def smooth_exponentially(self, matching_fft: np.ndarray) -> np.ndarray:

        grid_linear = self.sample_rate * 0.5 * np.linspace(
            start = 0,
            stop = 1,
            num = (self.fft_size//2+1)
            )

        grid_logarithmic = self.sample_rate * 0.5 * np.logspace(
            start = np.log10(4/self.fft_size),
            stop = 0,
            num = (self.fft_size//2) * self.lin_log_oversampling + 1
            )

        interpolator = interpolate.interp1d(
            x = grid_linear,
            y = matching_fft,
            kind = 'cubic'
            )

        matching_fft_log = interpolator(grid_logarithmic)
        matching_fft_log_filtered = self.smooth_lowess(array=matching_fft_log)

        interpolator = interpolate.interp1d(
            x = grid_logarithmic,
            y = matching_fft_log_filtered,
            kind = 'cubic',
            fill_value = 'extrapolate'
            )

        matching_fft_filtered = interpolator(grid_linear)
        matching_fft_filtered[0] = 0
        matching_fft_filtered[1] = matching_fft[1]

        return matching_fft_filtered

    def get_fir(self, fft):
        fir = np.fft.irfft(fft)
        fir = np.fft.ifftshift(fir) * signal.windows.hann(len(fir))
        return fir

    def convolve(self, source, target):
        result = signal.fftconvolve(target, source, 'same')
        return result

    def __call__(self, source, target, min_freq=100):
        self.source = source
        self.target = target

        self.create_source_from_signal()

        if isinstance(target, str):
            self.get_target_from_savefile()
        else:
            self.create_target_from_signal()

        #self.limit_target()
        self.adjust_to_mean()


        self.get_match_fir()

        result = signal.fftconvolve(in1 = self.source, in2 = self.match_fir, mode='same')

        return result

    def create_source_from_signal(self):
        source_fft = self.create_fft(self.source)
        self.source_average_fft = self.average_fft(source_fft)

    def create_target_from_signal(self):
        self.target_fft = self.create_fft(self.target)
        self.target_average_fft = self.average_fft(self.target_fft)

    def get_target_from_savefile(self):
        self.target_average_fft = np.load(self.target)

    def adjust_to_mean(self):
        source_average = np.mean(self.source_average_fft)
        target_average = np.mean(self.target_average_fft)
        #print(np.min(self.target_average_fft), np.max(self.target_average_fft))
        print(np.mean(self.source_average_fft), np.mean(self.target_average_fft))
        self.target_average_fft = self.target_average_fft * (source_average/target_average)
        self.target_average_fft[self.target_average_fft <= 0] = self.min_value
        #idxs = np.where(self.target_average_fft <= 0, self.target_average_fft)
        #print(idxs)
        #print(source_average, target_average)
        #print(np.min(self.source_average_fft), np.max(self.source_average_fft))
        #print(np.min(self.target_average_fft), np.max(self.target_average_fft))
        print(np.mean(self.source_average_fft), np.mean(self.target_average_fft))
        #quit()

    #def limit_target(self):
        #np.maximum(self.min_value, self.target_average_fft, out=self.target_average_fft)


    def get_match_fir(self):
        self.match_fft = self.target_average_fft / self.source_average_fft
        self.match_fft = self.smooth_exponentially(self.match_fft)

        self.apply_mix()
        self.ignore_extremes()
        self.match_fir = self.get_fir(self.match_fft)

    def apply_mix(self):
        self.match_fft = np.log10(self.match_fft)
        self.match_fft = self.mix*self.match_fft
        self.match_fft = 10**self.match_fft

    def ignore_extremes(self):
        self.freqs = np.linspace(start=0, stop=self.sample_rate//2, num=self.fft_size//2)

        min_bin = next(i for i, f in enumerate(self.freqs) if f >= self.min_freq)
        min_bin_half = next(i for i, f in enumerate(self.freqs) if f >= self.min_freq/2)

        max_bin = next(i for i, f in reversed(list(enumerate(self.freqs))) if f <= self.max_freq)
        max_bin_double = next(i for i, f in reversed(list(enumerate(self.freqs))) if f <= self.max_freq*2)

        #double_hi = hi *2
        #if double_hi > self.sample_rate /2:
         #   double_hi = self.freqs[-1]

        minfade = np.linspace(
            start = 1,
            stop = self.match_fft[min_bin],
            num = min_bin - min_bin_half,
            )

        maxfade = np.linspace(
            start = self.match_fft[max_bin],
            stop = 1,
            num = max_bin_double - max_bin,
            )

        self.match_fft[min_bin_half : min_bin] = minfade
        self.match_fft[max_bin : max_bin_double] = maxfade
        self.match_fft[:min_bin_half] = 1
        self.match_fft[max_bin_double:] = 1


        #print(self.match_fft.min(), self.match_fft.max(), self.match_fft.mean())
        #quit()
