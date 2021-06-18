# Author: joel.lof@icloud.com
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

"""Todo:
    ppm
    Nordic scale etc,
"""

class AmplitudePlot:
    def __init__(
            self,
            signals = [],
            legends = [],
            xlabel = 'Time in Seconds',
            ylabel = None,
            xmin = None,
            xmax = None,
            ymin = None,
            ymax = None,
            sample_rate = 48000,
            envelope_type = 'peak',
            fname = 'peaktest.png',
            yscale = 'linear', #linear, dBFS, log, symlog, logit
            figure_size = (10,5),
            gridlines = 'both',
            linewidth = 1,
            alpha = 1,
            frame_time = 0.001,
            hop_time = None,
            ):

        self.sample_rate = sample_rate
        self.signals = self.setupSignals(signals)
        self.legends = legends
        self.xlabel = xlabel
        self.ylabel = ylabel or yscale
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.envelope_type = envelope_type
        self.fname = fname
        self.yscale = yscale
        self.figure_size = figure_size
        self.gridlines = gridlines
        self.linewidth = linewidth
        self.linewidth = alpha
        self.alpha = alpha
        self.frame_time = frame_time
        self.hop_time = hop_time or frame_time
        self.envelope_type = envelope_type

        self.num_signals = self.signals.shape[0]
        self.envelope = []


    def setupSignals(self, signals):
        signals_lens = [len(sig) for sig in signals]
        max_len = max(signals_lens)

        self.signals = np.zeros((len(signals), max_len))
        for i, n in enumerate(signals_lens):
            self.signals[i,0:n] = signals[i]

        return self.signals

    def plotSaveShow(self):
        self.plot()
        self.save()
        self.show()

    def plotAndSave(self):
        self.plot()
        self.save()

    def plotAndShow(self):
        self.plot()
        self.show()

    def plot(self):
        self.makeFigAx()
        self.plotEnvelope()
        self.formatFigAx()

    def plotEnvelope(self):
        self.makeEnvelope()
        for envelope in self.envelope:
            self.plotData(x=self.envelope_time, y=envelope)

    def plotData(self, x, y):
        self.ax.plot(x, y, linewidth=self.linewidth, alpha=self.alpha)

    def save(self):
        self.fig.savefig(self.fname)

    def show(self):
        plt.show()

    def makeFigAx(self):
        self.fig, self.ax = plt.subplots(nrows=1, ncols=1, figsize=self.figure_size)

    def formatFigAx(self):
        """{"linear", "log", "symlog", "logit", ...}"""
        if not self.yscale == 'dBFS':
            self.ax.set_yscale(self.yscale)
        self.ax.set_xlabel(self.xlabel)
        self.ax.set_ylabel(self.ylabel)
        self.ax.set_xlim(left=self.xmin, right=self.xmax)
        self.ax.set_ylim(bottom=self.ymin, top=self.ymax)
        self.ax.legend(self.legends, loc='best')
        self.ax.xaxis.grid(b=True, which=self.gridlines) # minor major both
        self.ax.yaxis.grid(b=True, which=self.gridlines) # minor major both

    def makeEnvelope(self):
        self.makeAllFrames()

        if self.envelope_type == 'peak':
            self.calcPeakEnvelope()
        if self.envelope_type == 'ppm':
            self.calcPPMEnvelope()
        elif self.envelope_type == 'rms':
            self.calcRmsEnvelope()

        self.calcEnvelopeTime()
        if self.yscale == 'dBFS':
            self.envelope = self.get_dB(lin=self.envelope)

    ### calcs and makes###
    def makeAllFrames(self):
        frame_length = round(self.frame_time * self.sample_rate)
        self.hop_size = round(self.hop_time * self.sample_rate)
        self.frames = np.array([
            self.makeFrames(signal, frame_length, self.hop_size)
            for signal in self.signals
            ])

    def makeFrames(self, x, frame_length, hop_size):
        frames = [
            x[i-hop_size:i]
            for i in range(hop_size, len(x), hop_size)
            ]
        return np.array(frames)

    def calcRmsEnvelope(self):
        self.envelope = np.sqrt(np.mean(np.abs(self.frames**2), axis=2))

    def calcPeakEnvelope(self):
        self.envelope = np.max(np.abs(self.frames), axis=2)

    def calcPPMEnvelope(self):
        self.envelope = np.mean(np.abs(self.frames), axis=2)

    def calcEnvelopeTime(self):
        self.envelope_time = np.linspace(
            start=0,
            stop=self.signals.shape[1],
            num=self.envelope.shape[1],
            ) / self.sample_rate

    #### Gets ###
    def get_dB(self, lin):
        return 20 * np.log10(lin+1e-6)

    def getFigAx(self):
        return self.fig, self.ax

    ### Sets ###
    def setSignals(self, signals):
        """ signals should be (num_signals, samples) arr"""
        self.signals = np.array(signals)
        self.num_signals = self.signals.shape[0]

    def setEnvelopeType(self, s):
        """ hilbert, rms, peak"""
        self.envelope_type = s

    def setXlabel(self, labels:list):
        """ list of strings"""
        self.xlabel = labels

    def setYlabel(self, labels:list):
        """ list of strings"""
        self.ylabel = labels

    def setLegends(self, legends:list):
        """ list of strings"""
        self.legends = legends

    def setLinewidth(self, width:float):
        self.linewidth = width

    def setPlotType(self, pt:str = 'both'):
        """ 'linear', 'dBFS'"""
        self.envelope_type = pt

    def setLineColors(self, colors:list):
        """
        https://en.wikipedia.org/wiki/List_of_colors:_A-F
        black, white, blue, yellow, red, green, orange, magenta, cyan
        hex colors also work, ex: '#eeefff'

        """
        self.lineColors = colors

    def set_min_dBFS(self, val):
        self.min_dBFS = val

    def set_max_dBFS(self, val):
        self.max_dBFS = val

    def set_min_linear(self, val):
        self.min_linear = val

    def set_max_linear(self, val):
        self.max_linear = val

    def setTitle(self, title:str):
        self.title = title

    def setIntegrationTime(self, time:float):
        self.frame_time = time

    def setFrameLength(self, time:float):
        self.frame_length = self.sample_rate * self.frame_time

    def setEnvelopePreset(self, preset_name):
        self.envelope_preset = preset_name

    def setFigureSizePixels(self, px_width, px_height):
        None

    def setFname(self, fname:str):
        self.fname = fname

