import scipy
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import EngFormatter

class AmplitudePlot:
    def __init__(self,
            sample_rate=48000,
            min_dBFS=None,
            max_dBFS=None,
            min_val=None,
            max_val=None
            ):
        self.sample_rate = sample_rate
        self.linewidth = 0.8
        self.min_dBFS = min_dBFS
        self.max_dBFS = max_dBFS
        self.min_linear = min_val
        self.max_linear = max_val
        self.fig, self.ax0, self.ax1 = self.format()


    def make(self, signal, filename=None):
        if not hasattr(self, 'amplitude_plot_path'):
            self.amplitude_plot_path = filename or 'amplitude_plot.png'
        self.signal = signal
        self.calcAmplitude()
        self.plot()

    def calcAmplitude(self):
        #self.signal_dBFS = 20 * np.log10(np.abs(self.signal)+1e-6)
        self.analytic_signal = scipy.signal.hilbert(self.signal)
        self.amplitude_envelope = np.abs(self.analytic_signal)
        self.amplitude_envelope_dBFS = 20 * np.log10(self.amplitude_envelope)
        self.num_samples = len(self.amplitude_envelope)

        self.time = np.linspace(start=0, stop=self.num_samples/self.sample_rate, num=self.num_samples)
        if self.time[-1] < 1:
            self.time *= 1000
            self.ax0_xlabel = 'Time in Milliseconds'
        else:
            self.ax0_xlabel = 'Time in Seconds'

    def plot(self):
        self.ax0.plot(self.time, self.signal, linewidth=self.linewidth, alpha=0.7, label='signal')
        self.ax0.plot(self.time, self.amplitude_envelope, linewidth=self.linewidth, alpha=1, label='envelope')
        self.ax0.legend(['signal', 'envelope'], loc='best')
        self.ax0.set_xlabel(self.ax0_xlabel)

        self.ax1.plot(self.time, self.amplitude_envelope_dBFS, linewidth=self.linewidth)
        self.ax1.legend(['envelope'], loc='best')


    def overlay(self):
        None


    def save(self):
        print(f'saving to {self.amplitude_plot_path}')
        plt.savefig(self.amplitude_plot_path)

    def format(self):
        fig, (ax0, ax1) = plt.subplots(nrows=2, figsize=(16,8))#figsize=(7, 9.6))

        #ax0.set_title('Signal')
        ax0.set_ylabel('Linear')
        ax0.xaxis.grid(b=True, which='both') # minor major both
        ax0.yaxis.grid(b=True, which='both') # minor major both
        ax0.set_ylim(ymin=self.min_linear, ymax=self.max_linear)

        #ax1.set_title('Amplitude')
        ax1.set_ylabel('dBFS')
        ax1.xaxis.grid(b=True, which='both') # minor major both
        ax1.yaxis.grid(b=True, which='both') # minor major both
        ax1.set_ylim(ymin=self.min_dBFS, ymax=self.max_dBFS)
        return fig, ax0, ax1



