# http://openaudio.blogspot.com/2017/01/basic-dynamic-range-compressor.html made the original c++ code

import os
import sys
import scipy
import numpy as np

class Compressor:
    def __init__(self,
            input_gain=0,
            threshold=-24,
            ratio=2,
            attack=0.005,
            release=0.2,
            makeup_gain=0,
            sample_rate=48000,
            sidechain_lowcut=20,
            sidechain_highcut=20000,
            use_prefilter=True,
            smoothen=True,
            lookahead_time = 0,
            ):
        self.smoothen = smoothen
        self.sample_rate = sample_rate
        self.input_gain = input_gain
        self.nyquist = int(0.5 * sample_rate)
        self.makeup_gain = self.dblin(makeup_gain)
        self.threshold_dBFS = threshold
        self.attack_sec = attack
        self.release_sec = release
        self.ratio = ratio
        self.highpass_frequency = sidechain_lowcut
        self.lowpass_frequency = sidechain_highcut
        self.use_prefilter = use_prefilter
        self.lookahead_time = lookahead_time * 5
        self.lookahead_samples = round(self.sample_rate * self.lookahead_time)
        self.prev_level_lp_pow = 1e-6
        self.prev_gain_dB = 0
        self.min_time_sec = 0.002
        #self.min_time_sec = 1e-6

        self.setThresh_dBFS(self.threshold_dBFS)
        self.setCompressionRatio(self.ratio)
        #self.setThresh_dBFS(self.threshold_dBFS)
        self.setAttack_sec(self.attack_sec)
        self.setRelease_sec(self.release_sec)
        self.first_time = True

    def setThresh_dBFS(self, val):
        self.thresh_dBFS = val# -4 # added because yes.
        self.setThreshPowFS(10**(self.threshold_dBFS/10))
        #self.setThreshPowFS(10*np.log10(10**(self.threshold_dBFS/20)))

    def setThreshPowFS(self, val):
        self.thresh_powFS = val
        self.updateThresholdAndCompRatioConstants()

    def setAttack_sec(self, t_sec):
        self.attack_sec = max(t_sec, 1e-6)
        self.attack_const = np.exp(-1/(self.attack_sec*self.sample_rate)) # added /5
        self.setLevelTimeConst_sec(min(self.attack_sec, self.release_sec)/5)#(2.71828)

    def setRelease_sec(self, t_sec):
        self.release_sec = max(t_sec, 1e-6)
        self.release_const = np.exp(-1/(self.release_sec*self.sample_rate)) # added /16
        self.setLevelTimeConst_sec(min(self.attack_sec, self.release_sec)/5)#(2.71828)

    def setLevelTimeConst_sec(self, t_sec):
        self.level_lp_sec = max(self.min_time_sec, t_sec)
        self.level_lp_const = np.exp(-1/(self.level_lp_sec * self.sample_rate))

    def setCompressionRatio(self, ratio):
        self.ratio = max(0.001, ratio)
        self.updateThresholdAndCompRatioConstants()

    def updateThresholdAndCompRatioConstants(self):
        self.comp_ratio_const = 1-(1/self.ratio)
        self.thresh_powFS_wCR = self.thresh_powFS ** self.comp_ratio_const

    def getAttackTime(self):
        return self.attack_sec

    def getReleaseTime(self):
        return self.attack_sec

    def getSignal(self):
        return self.signal

    def getLevelLPConstant(self):
        return self.level_lp_const

    def getSampleRate(self):
        return self.sample_rate

    def getInstantaneousTargetGain(self):
        return self.inst_targ_gain_dB_block

    def getAttackPhase(self):
        return self.attack_phase

    def getGainAdjustment(self):
        return self.gain_linear_block

    ##########################################################################
    def update(self, signal, sidechain_signal=None):
        self.signal = signal
        self.sidechain_signal = sidechain_signal
        self.use_external_sidechain = type(self.sidechain_signal) != type(None)
        self.use_lookahead = self.lookahead_samples > 0
        self.initSidechainAndLookahead()
        self.applyInputGain()
        self.calcAudioLevel_dB()
        self.calcInstantaneousTargetGain()
        self.calcSmoothedGain_dB()
        self.applyGain()
        return self.signal

    def initSidechainAndLookahead(self):
        if self.use_lookahead:
            self.signal = np.pad(self.signal, (0, self.lookahead_samples))
            if self.use_external_sidechain:
                self.sidechain_signal = np.pad(
                    self.sidechain_signal, (0, self.lookahead_samples))

        if not self.use_external_sidechain:
            self.sidechain_signal = self.getSignal()

        if self.use_lookahead:
            self.signal = np.roll(self.signal, self.lookahead_samples)

        if self.use_prefilter:
            self.sidechain_signal = self.bandpass(self.sidechain_signal)

    def applyGain(self):
        # if self.use_lookahead:
        #     self.signal = np.roll(self.signal, self.lookahead_samples)

        self.signal = self.signal * self.gain_linear_block * self.makeup_gain

        if self.use_lookahead:
            self.signal = self.signal[self.lookahead_samples:]

    def applyInputGain(self):
        if self.input_gain != 0:
            self.sidechain_signal *= 10**(self.input_gain/20)

    # Here's the method that estimates the level of the audio (in dB)
    # It squares the signal and low-pass filters to get a time-averaged
    # signal power.  It then multiplies by 10 to convert to dB.
    # log10(x ** 2)*10 = 20*log10(x)
    def calcAudioLevel_dB(self):
        self.wav_pow = self.sidechain_signal**2
        self.level_dB_block = []
        c1 = self.getLevelLPConstant()
        c2 = 1 - c1
        for i in range(len(self.wav_pow)):
            # Lowpass
            self.wav_pow[i] = c1 * self.prev_level_lp_pow + c2 * self.wav_pow[i]
            self.prev_level_lp_pow = self.wav_pow[i]

        if self.prev_level_lp_pow < 1e-13:
            self.prev_level_lp_pow = 1e-13

        self.level_dB_block = np.log10(self.wav_pow) * 10

    def calcInstantaneousTargetGain(self):
        self.above_tresh_dB_block = self.level_dB_block - self.thresh_dBFS
        self.inst_targ_gain_dB_block = self.above_tresh_dB_block * (1/self.ratio)
        self.inst_targ_gain_dB_block -= self.above_tresh_dB_block

        np.clip(self.inst_targ_gain_dB_block,
            a_min=None,
            a_max=0,
            out=self.inst_targ_gain_dB_block)

    def calcSmoothedGain_dB(self):
        self.one_minus_attack_const = 1 - self.attack_const
        self.one_minus_release_const = 1 - self.release_const
        self.gain_dB_block = np.array([])
        self.attack_phase = []

        for i in range(len(self.inst_targ_gain_dB_block)):
            self.gain_dB = self.inst_targ_gain_dB_block[i]

            if self.gain_dB < self.prev_gain_dB:
                self.attack_phase.append(True)
                self.gain_dB_block = np.append(
                    self.gain_dB_block,
                    (self.attack_const
                    *self.prev_gain_dB
                    +self.one_minus_attack_const
                    *self.gain_dB)
                    )
            else:
                self.attack_phase.append(False)
                self.gain_dB_block = np.append(
                    self.gain_dB_block,
                    (self.release_const
                    *self.prev_gain_dB
                    +self.one_minus_release_const
                    *self.gain_dB)
                    )
            self.prev_gain_dB = self.gain_dB_block[i]

        self.gain_linear_block = 10**(self.gain_dB_block/20)

    def dblin(self, db):
        return 10**(db/20)

    def bandpass(self, data, order=3):
        iir_numerator, iir_denominator = scipy.signal.butter(
            order, [self.highpass_frequency, self.lowpass_frequency],
            btype='bandpass',
            fs=self.sample_rate,
            output='ba',
            analog=False,
            )
        y = scipy.signal.lfilter(iir_numerator, iir_denominator, data)
        return y

