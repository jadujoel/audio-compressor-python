import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import time

from _plot_frequency import FrequencyPlot
from _plot_amplitude import AmplitudePlot

class Plot:
    """ For use in class FFmpeg """
    def plot_lufs(self, filename=''):
        self.get_lufs()
        fig, ax = plt.subplots(nrows=1, figsize=(16,8))
        #fig, ax = plt.subplots()
        color1 = '#01cdfe'
        color2 = '#ff71ce'
        color3 = '#05ffa1'
        plt.plot(
            self.loudness_time,
            self.loudness_momentary,
            color=color3
            )
        plt.plot(
            self.loudness_time,
            self.loudness_short_term,
            color=color2
            )
        plt.plot(
            self.loudness_time,
            self.loudness_integrated,
            color=color1
            )

        formatter = matplotlib.ticker.FuncFormatter(
            lambda s, x: time.strftime('%M:%S', time.gmtime(s)))

        ax.xaxis.set_major_formatter(formatter)
        #fig.suptitle("Loudness / LUFS")
        #fig.suptitle(f"Loudness / LUFS  {str(self.loudness_summary)[1:-1]}")
        ax.set_title(f"Loudness / LUFS  {str(self.loudness_summary)[1:-1]}")
        ax.set_xlabel("Time")#, fontdict=font)
        ax.set_ylabel("dBFS")#, fontdict=font)
        ax.set_ylim(-46, 0)

        ax.xaxis.grid(b=True, which='major') # minor major both
        ax.yaxis.grid(b=True, which='major') # minor major both

        handle1 = mpatches.Patch(color=color1, label='integrated')
        handle2 = mpatches.Patch(color=color2, label='short term')
        handle3 = mpatches.Patch(color=color3, label='momentary')

        fig.legend(handles = [handle1, handle2, handle3], loc='best')

        if filename == '':
            f = self.name_ext(self.filename)
            filename = f'{f[0]}_loudness.png'

        plt.tight_layout()
        plt.savefig(filename)
        plt.close()

    def plot_freq(self, filename=''):
        self.make_mono()

        if filename == '':
            f = self.name_ext(self.filename)
            filename = f'{f[0]}_frequency_plot.png'

        frequency_plot = FrequencyPlot(
            sample_rate = self.sample_rate,
            num_fft = 8192,
            smoothing_amount = 0.002,
            smoothen = True,
            )

        frequency_plot.make_from_signal(
            signal=self.signal_mono,
            filename=filename,
            )

    def plot_matcheq(self, filename='', smoothen=True):
        self.make_mono()

        if filename == '':
            f = self.name_ext(self.filename)
            filename = f'{f[0]}_frequency_plot.png'

        frequency_plot = FrequencyPlot(
            sample_rate = self.sample_rate,
            num_fft = self.meq.fft_size,
            smoothen = smoothen,
            )

        self.make_mono()
        frequency_plot.make_from_matcheq(
            source = self.meq.source_average_fft,
            target = self.meq.target_average_fft,
            correction = self.meq.match_fft,
            signal = self.signal_mono,
            filename = filename,
            )

    def plot_amplitude(self,
            filename='',
            min_dBFS=None,
            max_dBFS=None,
            min_val=None,
            max_val=None,
            save=True,
            ):
        #self.make_mono()
        if filename == '':
            f = self.name_ext(self.filename)
            filename = f'{f[0]}_amplitude_plot.png'

        self.amplitudePlot = AmplitudePlot(
            sample_rate=self.sample_rate,
            min_dBFS=min_dBFS,
            max_dBFS=max_dBFS,
            min_val=min_val,
            max_val=max_val,
            )

        self.amplitudePlot.make(signal=self.get_mono(), filename=filename)
        if save: self.amplitudePlot.save()







