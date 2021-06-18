import scipy
import numpy as np
import statsmodels.api as sm
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import EngFormatter

class FrequencyPlot:
    def __init__(
            self,
            sample_rate = 48000,
            num_fft = 8192,
            smoothing_amount = 0.002,
            smoothen = True,
            ymin = None
            ):

        self.sample_rate = sample_rate
        self.nyquist = self.sample_rate // 2
        self.num_fft = num_fft
        self.ymin = ymin

        self.num_freqs = self.sample_rate // 2
        self.num_bins = self.num_fft//2+1
        self.make_freqs()

        self.min_value = 1e-6
        self.lin_log_oversampling = 1

        self.smoothing_amount = smoothing_amount # 0 to 0.04 recommended
        self.lowess_it = 1
        self.lowess_delta = 0.001 # High saves computation time

        self.smoothen = smoothen

    def make_freqs(self):
        self.freqs = np.linspace(start=0, stop=self.num_freqs, num=self.num_bins)

    def make_from_signal(self, signal, filename='frequency_plot.png'):
        self.frequency_plot_path = filename
        color = ['r', 'm', 'g', 'y']
        labels = ['1','2','3','4']
        fig, ax = self.format()
        if signal.ndim <= 1:
            fig, ax = self.doit(signal, fig=fig, ax=ax)
        else:
            for sig, col, lab in zip(signal, color, labels):
                print(col, sig.max())
                fig, ax = self.doit(sig, col, lab, fig, ax)
        ax.set_ylim(bottom=self.ymin or self.mag.max()-60, top=self.mag.max())
        fig.savefig(self.frequency_plot_path)


    def doit(self, signal, color='r', label=None, fig=None, ax=None):
        self.linewidth = 0.6
        mag = self.get_mag(signal)
        if self.smoothen:
            mag = self.smooth_exponentially(mag)
        mag = self.get_logmag(mag)
        self.mag = mag
        ax.plot(self.freqs, mag, linewidth=self.linewidth, color=color, label=label)

        return fig, ax

    def make_from_matcheq(self, source, target, correction, signal, filename='frequency_plot.png'):
        self.frequency_plot_path = filename
        self.linewidth = 1

        self.num_fft = (source.shape[0]-1) * 2
        self.make_freqs()

        result = self.get_mag(signal)

        if self.smoothen:
            source = self.smooth_exponentially(source)
            target = self.smooth_exponentially(target)
            result = self.smooth_exponentially(result)

            #correction = self.smooth_exponentially(correction)
        self.source = self.get_logmag(source)
        self.target = self.get_logmag(target)
        self.result = self.get_logmag(result)
        self.correction = self.get_logmag(correction)

        start = next(i for i, xn in enumerate(self.freqs) if xn >= 20)
        stop = next(i for i, xn in enumerate(self.freqs) if xn >= 70)
        self.correction_visual_adjust = np.mean(self.target[start:stop])
        self.correction = self.correction + self.correction_visual_adjust

        self.plot_frequency_curve_meq()

    def get_mag(self, signal):
        *_, stft = scipy.signal.stft(
            signal,
            fs = self.sample_rate,
            window = 'boxcar',
            nperseg = self.num_fft,
            noverlap = 0,
            boundary = None,
            padded = False
            )

        mag = np.abs(stft).mean(axis=1)
        return mag

    def get_logmag(self, fft):
        mag = np.abs(fft)
        mag[mag == 0] = self.min_value
        mag =  20 * np.log10(mag)
        return mag

    def smooth_lowess(self, array):
        # LOWESS (Locally Weighted Scatterplot Smoothing)
        result = sm.nonparametric.lowess(
            endog = array,
            exog = np.linspace(0, 1, len(array)),
            frac = self.smoothing_amount, # The fraction of the data used when estimating each y-value.
            it = self.lowess_it, # The number of residual-based reweightings to perform.
            delta = self.lowess_delta # Distance within which to use linear-interpolation instead of weighted regression.
            )[:, 1]
        return result

    def smooth_exponentially(self, arr):
        grid_linear = self.sample_rate * 0.5 * np.linspace(
            start = 0,
            stop = 1,
            num = self.num_bins
            )

        grid_logarithmic = self.sample_rate * 0.5 * np.logspace(
            start = np.log10(4/self.num_fft),
            stop = 0,
            num = (self.num_fft//2) * self.lin_log_oversampling + 1
            )

        interpolator = scipy.interpolate.interp1d(
            x = grid_linear,
            y = arr,
            kind = 'cubic'
            )

        arr_log = interpolator(grid_logarithmic)
        arr_log_filtered = self.smooth_lowess(array=arr_log)

        interpolator = scipy.interpolate.interp1d(
            x = grid_logarithmic,
            y = arr_log_filtered,
            kind = 'cubic',
            fill_value = 'extrapolate'
            )

        arr_filtered = interpolator(grid_linear)
        arr_filtered[0] = self.min_value
        arr_filtered[1] = arr[1]

        return arr_filtered

    def plot_frequency_curve(self):
        fig, ax0 = self.format()
        ax0.plot(self.freqs, self.mag, linewidth=self.linewidth)
        #ax0.set_ylim(bottom=self.ymin or self.mag.max()-60, top=self.mag.max())
        return fig, ax0

    def plot_frequency_curve_meq(self):
        fig, ax0 = self.format()
        ax0.plot(self.freqs, self.source, linewidth=self.linewidth, label='source')
        ax0.plot(self.freqs, self.target, linewidth=self.linewidth, label='target')
        ax0.plot(self.freqs, self.correction, linewidth=self.linewidth, label='correction')
        ax0.plot(self.freqs, self.result, linewidth=self.linewidth, label='result')
        ax0.legend(['source', 'target', f'correction {int(self.correction_visual_adjust)} dB', 'result'], loc='best')#loc='lower left')
        fig.savefig(self.frequency_plot_path)

    def format(self):
        fig, ax0 = plt.subplots(nrows=1, figsize=(16,8))#figsize=(7, 9.6))
        ax0.set_xscale('log')
        ax0.set_title('Frequency Curve')
        formatter0 = EngFormatter(unit='Hz')
        ax0.xaxis.set_major_formatter(formatter0)
        ax0.set_xlabel('Frequency')
        ax0.set_ylabel('dBFS')
        ax0.set_xlim(left=20, right=self.nyquist)
        ax0.set_xticks([20, 40, 70, 130, 250, 500, 1000, 2000, 4000, 8000, 16000, self.nyquist])
        #ax0.set_ylim(bottom=-60, top=None)
        ax0.xaxis.grid(b=True, which='major') # minor major both
        ax0.yaxis.grid(b=True, which='major') # minor major both
        plt.tight_layout()
        return fig, ax0


if __name__ == '__main__':
    None


