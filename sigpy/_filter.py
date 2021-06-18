import numpy as np
from _matcheq import MatchEQ

class Filter:
    """ For use in class FFmpeg """
    def add_filter(self, _filter):
        """ functon to make multiple filter actions in one go of fpeg
        """
        corresponding = ['normalize', 'compress', 'limit', 'denoise', 'declip']

    def overload_protection(self):
        _max = np.abs(self.signal.max())
        if _max > self.db_to_linear(-2):
            print('Signal overload protection activating.')
            print(f'    Signal max was at: {self.linear_to_db(_max)} dBFS')
            self.normalize(headroom_db=2)
            print(f'Now at: {self.linear_to_db(np.abs(self.signal.max()))} dBFS')

    def normalize(self, type_='peak', headroom_db=2, target_max_value=None):
        if type_ == 'peak':
            headroom_linear = self.db_to_linear(-headroom_db)
            target_max_value = target_max_value or headroom_linear
            current_max = np.abs(self.signal).max()
            self.signal /= (current_max / target_max_value)
        else:
            raise Exception(f'normalize type: {type_} unrecognised')

    def limit(self, max_dbfs=-2, attack=5, release=50):
        roof = f'{self.db_to_linear(max_dbfs):.8}'
        if self.num_channels == 1:
            # Ffmpeg writes mono 3 dB louder than stereo it seems...
            filters = f'volume=volume=-3dB,'\
                      f'alimiter=level_in=1:level_out=1:'\
                      f'limit={roof}:attack={attack}:release={release}'\
                      f':level=disabled'
        else:
            filters = f'alimiter=level_in=1:level_out=1:'\
                      f'limit={roof}:attack={attack}:release={release}'\
                      f':level=disabled'

        cmd = [
            self.ffmpeg_path,
            *self.I(),
            '-af', filters,
            *self.O()
            ]

        latency = round(attack * (self.sample_rate / 1000))
        self.process_with_latency_compensation(cmd, latency)

    def compress(self, threshold=-18, ratio=2, attack=5, release=50):

        threshold = f'{self.db_to_linear(threshold):.8}'

        filters= f'acompressor=threshold={threshold}:ratio={ratio}:'\
                 f'attack={attack}:release={release}'

        cmd = [
            self.ffmpeg_path,
            *self.I(),
            '-af', filters,
            *self.O()
            ]

        self.signal = self.get_stdout_as_signal(*cmd, signal=signal)

    def denoise(self, mix=1.):
        if self.num_channels == 1:
            filters = [
                '-filter_complex',
                f'lv2=p={self.denoise_plugin}'
                ]
        elif self.num_channels == 2:
            filters = [
                '-filter_complex',
                f'channelsplit[l][r]'\
                f',[l]lv2=p={self.denoise_plugin}[left]'\
                f',[r]lv2=p={self.denoise_plugin}[right]'\
                f',[left][right]amerge[out]',
                '-map', '[out]'
                ]

        cmd = [
            self.ffmpeg_path_lv2,
            *self.I(),
            *filters,
            *self.O()
            ]

        signal_pre_denoise = self.signal[:]
        latency = int(0.02 * self.sample_rate)
        self.process_with_latency_compensation(cmd, latency)

        if mix > 0 and mix < 1:
            self.signal = (
                self.signal * mix + (signal_pre_denoise * (1-mix))
                )

    def denoise_stream(self, mix=1.):
        if self.num_channels == 1:
            filters = [
                '-filter_complex',
                f'lv2=p={self.denoise_plugin_stream}'
                ]
        elif self.num_channels == 2:
            filters = [
                '-filter_complex',
                f'channelsplit[l][r]'\
                f',[l]lv2=p={self.denoise_plugin_stream}[left]'\
                f',[r]lv2=p={self.denoise_plugin_stream}[right]'\
                f',[left][right]amerge[out]',
                '-map', '[out]'
                ]

        latency = int(0.02 * self.sample_rate)
        return filters, latency

    def denoise_stream_with_mix(self, mix=1.):
        if self.num_channels == 1:
            filters = [
                '-filter_complex',
                f'lv2=p={self.denoise_plugin_stream}'
                ]
        elif self.num_channels == 2:
            print(mix)
            filters = [
                '-filter_complex',
                f'channelsplit[l][r]'\
                f',[l]volume={mix},lv2=p={self.denoise_plugin_stream}[left]'
                f',[r]adelay=960S,volume={1-mix}[right]'\
                f',[left][right]amerge[out]',
                #f',[out]adelay=0|{20*self.sample_rate}[output]',
                #f'[out]adelay=0|{20*self.sample_rate}[o]'
                '-map', '[out]',

                ]
                #f',[r]adelay={20*self.sample_rate}[right]'\
                # f',[r]lv2=p={self.denoise_plugin_stream}[right]'\

        latency = int(0.02 * self.sample_rate)
        return filters, latency

    def declip(
            self,
            windowSize = 55,
            windowOverlap = 75,
            autoRegressionOrder = 8,
            threshold = 10,
            histogramSize = 1000,
            overlapMethod = 'add',
            ):
        """
        Remove clipped samples from input audio.
        Samples detected as clipped are replaced by interpolated samples using autoregressive modelling.
        w : Set window size, in milliseconds. Allowed range is from 10 to 100. Default value is 55 milliseconds. This sets size of window which will be processed at once.
        o : Set window overlap, in percentage of window size. Allowed range is from 50 to 95. Default value is 75 percent.
        a : Set autoregression order, in percentage of window size. Allowed range is from 0 to 25. Default value is 8 percent. This option also controls quality of interpolated samples using neighbour good samples.
        t : Set threshold value. Allowed range is from 1 to 100. Default value is 10. Higher values make clip detection less aggressive.
        n : Set size of histogram used to detect clips. Allowed range is from 100 to 9999. Default value is 1000. Higher values make clip detection less aggressive.
        m : Set overlap method.
            It accepts the following values:
            a : Select overlap-add method. Even not interpolated samples are slightly changed with this method.
            s : Select overlap-save method. Not interpolated samples remain unchanged. Default value is a.
        """
        overlapMethods = {'add' : 'a', 'save' : 's'}
        latency = 0

        filters = \
            f'adeclip'\
            f'=w={windowSize}'\
            f':o={windowOverlap}'\
            f':a={autoRegressionOrder}'\
            f':t={threshold}'\
            f':n={histogramSize}'\
            f':m={overlapMethods.get(overlapMethod)}'\

        cmd = [
            self.ffmpeg_path,
            *self.I(),
            '-af', filters,
            *self.O()
            ]

        self.process_with_latency_compensation(cmd, latency)

    def declick(
            self,
            windowSize = 55,
            windowOverlap = 75,
            autoRegressionOrder = 2,
            threshold = 2,
            burstFusion = 2,
            overlapMethod = 'add',
            ):
        """
        Remove impulsive noise from input audio.
        Samples detected as impulsive noise are replaced by interpolated samples using autoregressive modelling.
        w -> Set window size, in milliseconds. Allowed range is from 10 to 100. Default value is 55 milliseconds. This sets size of window which will be processed at once.
        o -> Set window overlap, in percentage of window size. Allowed range is from 50 to 95. Default value is 75 percent. Setting this to a very high value increases impulsive noise removal but makes whole process much slower.
        a -> Set autoregression order, in percentage of window size. Allowed range is from 0 to 25. Default value is 2 percent. This option also controls quality of interpolated samples using neighbour good samples.
        t -> Set threshold value. Allowed range is from 1 to 100. Default value is 2. This controls the strength of impulsive noise which is going to be removed. The lower value, the more samples will be detected as impulsive noise.
        b -> Set burst fusion, in percentage of window size. Allowed range is 0 to 10. Default value is 2. If any two samples detected as noise are spaced less than this value then any sample between those two samples will be also detected as noise.
        m -> Set overlap method. It accepts the following values:
            a -> Select overlap-add method. Even not interpolated samples are slightly changed with this method.
            s -> Select overlap-save method. Not interpolated samples remain unchanged.
            Default value is a.
        """
        overlapMethods = {'add' : 'a', 'save' : 's'}
        latency = 0

        filters = \
            f'adeclick'\
            f'=w={windowSize}'\
            f':o={windowOverlap}'\
            f':a={autoRegressionOrder}'\
            f':t={threshold}'\
            f':b={burstFusion}'\
            f':m={overlapMethods.get(overlapMethod)}'\

        cmd = [
            self.ffmpeg_path,
            *self.I(),
            '-af', filters,
            *self.O()
            ]

        self.process_with_latency_compensation(cmd, latency)

    def contrast(self, contrast=33):
        """
        Simple audio dynamic range compression/expansion filter.
        The filter accepts the following options:
        contrast
            Set contrast. Default is 33. Allowed range is between 0 and 100.
        """
        latency = 0
        filters = \
            f'acontrast'\
            f'=contrast={contrast}'\

        cmd = [
            self.ffmpeg_path,
            *self.I(),
            '-af', filters,
            *self.O()
            ]

        self.process_with_latency_compensation(cmd, latency)

    def mcompand(self, preset='K-Weighting'):
        """
        Multiband Compress or expand the audio’s dynamic range.
        The input audio is divided into bands using 4th order Linkwitz-Riley IIRs.
            This is akin to the crossover of a loudspeaker,
            and results in flat frequency response when absent compander action.
        It accepts the following parameters:
            args
            This option syntax is:
             attack,decay,[attack,decay..] soft-knee points crossover_frequency [delay [initial_volume [gain]]] | attack,decay ...
             For explanation of each item refer to compand filter documentation.
        """
        latency = 0

        expander_floor = -100
        compress_ratio = 2
        expander_ratio = 1
        attack = 0.005
        release = 0.01
        attack = 0.001
        release = 0.1
        soft_knee = 6
        reference_db = -23

        if preset == 'A-Weighting':
            frequencies = [    64,   125,   250,   500, 1000, 2000, 4000, 8000, 16000 ]
            a_weighting = [ -26.2, -16.1,  -8.6,  -3.2,    0,  1.2,    1, -1.1,  -6.6 ]
            compression_thresholds  = [weight + reference_db for weight in a_weighting]
            expander_thresholds = [-70 for f in frequencies]

        elif preset == 'C-Weighting':
            frequencies = [    64,   125,   250,   500, 1000, 2000, 4000, 8000, 16000 ]
            c_weighting = [  -0.8,  -0.2,     0,     0,    0, -0.2, -0.8, -3.0,  -8.5 ]
            compression_thresholds  = [weight + reference_db for weight in c_weighting]
            expander_thresholds = [-70 for f in frequencies]

        elif preset == 'Z-Weighting':
            frequencies = [    64,   125,   250,   500, 1000, 2000, 4000, 8000, 16000 ]
            z_weighting = [     0,     0,     0,     0,    0,    0,    0,    0,     0 ]
            compression_thresholds  = [weight + reference_db for weight in z_weighting]
            expander_thresholds = [-70 for f in frequencies]

        elif preset == 'K-Weighting':
            frequencies = [    64,   125,   250,   500, 1000, 2000, 4000, 8000, 16000 ]
            k_weighting = [    -4,   -2,      0,     0,    +1,  +3,    +4,  +4,  +4 ]
            compression_thresholds  = [weight + reference_db for weight in k_weighting]
            expander_thresholds = [-70 for f in frequencies]

        elif preset == 'ITU-R468':
            frequencies = [    64,   125,   250,   500, 1000, 2000, 4000, 8000, 16000 ]
            itur468_weighting = [    -25,  -18,    -12,   -6,    0,   +6,  +11,  +11,   -25 ]
            compression_thresholds  = [weight + reference_db for weight in itur468_weighting]
            expander_thresholds = [-70 for f in frequencies]

        if preset == 'default':
            bands = '0.005,0.1 6 -47/-40,-34/-34,-17/-33 100 | 0.003,0.05 6 -47/-40,-34/-34,-17/-33 400 | 0.000625,0.0125 6 -47/-40,-34/-34,-15/-33 1600 | 0.0001,0.025 6 -47/-40,-34/-34,-31/-31,-0/-30 6400 | 0,0.025 6 -38/-31,-28/-28,-0/-25 22000'
            filters = \
                f'mcompand'\
                f"='[{bands}]'"
        else:
            # Make Points
            expanders_at_floor = []
            compressions_at_zero = []
            compressions_at_twenty = []
            for compress_threshold, expander_threshold in zip(
                    compression_thresholds, expander_thresholds):
                expanders_at_floor.append(
                    (expander_threshold
                    - ((expander_threshold
                    - expander_floor)
                    * expander_ratio)
                    ).__round__(1))
                compressions_at_zero.append(
                    (compress_threshold
                    - ((compress_threshold
                    - 0)
                    / compress_ratio)
                    ).__round__(1))
                compressions_at_twenty.append(
                    (compress_threshold
                    - ((compress_threshold
                    - 20)
                    / compress_ratio)
                    ).__round__(1))

            points_all_bands = []
            for(
                expander_at_floor,
                expander_threshold,
                compress_threshold,
                compress_at_zero,
                compress_at_twenty
                ) in zip(
                        expanders_at_floor,
                        expander_thresholds,
                        compression_thresholds,
                        compressions_at_zero,
                        compressions_at_twenty
                        ):
                points = \
                    f'{expander_floor}/{expander_at_floor}' \
                    f',{expander_threshold}/{expander_threshold}' \
                    f',{compress_threshold}/{compress_threshold}' \
                    f',0/{compress_at_zero}' \
                    f',20/{compress_at_twenty}'

                points_all_bands.append(points)

            # make bands
            bands = []
            for points, freq in zip(points_all_bands, frequencies):
                band = \
                    f'{attack},{release} '\
                    f'{soft_knee} '\
                    f'{points} '\
                    f'{freq}'\

                bands.append(band)

            bands = ' | '.join(bands)

        filters = \
            f'mcompand'\
            f"='[{bands}]'"\

        cmd = [
            self.ffmpeg_path,
            *self.I(),
            '-af', filters,
            *self.O()
            ]

        self.process_with_latency_compensation(cmd, latency)

    def mcompand_stream(self, preset='K-Weighting'):
        _filt = ['-af', "mcompand='[0.001,0.1 6 -100/-100,-70/-70,-27/-27,0/-13.5,20/-3.5 64 | 0.001,0.1 6 -100/-100,-70/-70,-25/-25,0/-12.5,20/-2.5 125 | 0.001,0.1 6 -100/-100,-70/-70,-23/-23,0/-11.5,20/-1.5 250 | 0.001,0.1 6 -100/-100,-70/-70,-23/-23,0/-11.5,20/-1.5 500 | 0.001,0.1 6 -100/-100,-70/-70,-22/-22,0/-11.0,20/-1.0 1000 | 0.001,0.1 6 -100/-100,-70/-70,-20/-20,0/-10.0,20/0.0 2000 | 0.001,0.1 6 -100/-100,-70/-70,-19/-19,0/-9.5,20/0.5 4000 | 0.001,0.1 6 -100/-100,-70/-70,-19/-19,0/-9.5,20/0.5 8000 | 0.001,0.1 6 -100/-100,-70/-70,-19/-19,0/-9.5,20/0.5 16000]'"]
        cmd = self.make_stream_cmd(options=_filt)
        self.run_in_shell(*cmd)

    def compand(
            self,
            attack = 0.005,
            decay = 0.01,
            soft_knee = 0.01,
            expander_threshold = -70,
            compress_threshold = -18,
            expander_ratio = 3,
            compress_ratio = 2,
            gain = 0,
            volume = 0,
            ):
        """
        Compress or expand the audio’s dynamic range.
        It accepts the following parameters:
        attacks
        decays
            A list of times in seconds for each channel over which the instantaneous level of the input signal is averaged to determine its volume. attacks refers to increase of volume and decays refers to decrease of volume. For most situations, the attack time (response to the audio getting louder) should be shorter than the decay time, because the human ear is more sensitive to sudden loud audio than sudden soft audio.
            A typical value for attack is 0.3 seconds and a typical value for decay is 0.8 seconds.
            If specified number of attacks & decays is lower than number of channels, the last set attack/decay will be used for all remaining channels.
        points
            A list of points for the transfer function,
            specified in dB relative to the maximum possible signal amplitude.
            Each key points list must be defined using the following syntax: x0/y0|x1/y1|x2/y2|.... or x0/y0 x1/y1 x2/y2 ....
            The input values must be in strictly increasing order but the transfer function does not have to be monotonically rising. The point 0/0 is assumed but may be overridden (by 0/out-dBn). Typical values for the transfer function are -70/-70|-60/-20|1/0.
        soft-knee
            Set the curve radius in dB for all joints. It defaults to 0.01.
        gain
            Set the additional gain in dB to be applied at all points on the transfer function.
            This allows for easy adjustment of the overall gain. It defaults to 0.
        volume
            Set an initial volume, in dB, to be assumed for each channel when filtering starts. This permits the user to supply a nominal level initially, so that, for example,
            a very large gain is not applied to initial signal levels before the companding has begun to operate.
            A typical value for audio which is initially quiet is -90 dB. It defaults to 0.
        delay
            Set a delay, in seconds. The input audio is analyzed immediately, but audio is delayed before being fed to the volume adjuster.
            Specifying a delay approximately equal to the attack/decay times allows the filter to effectively operate in predictive rather than reactive mode. It defaults to 0.
        """
        delay = attack
        latency = 0 #int((delay * self.sample_rate).__round__(0))

        # Points
        expander_floor = -100
        expander_at_floor = (expander_threshold - (
            (expander_threshold - expander_floor
            ) * expander_ratio)
            ).__round__(1)
        compress_at_zero  = (compress_threshold - (
            (compress_threshold - 0
            ) / compress_ratio)
            ).__round__(1)
        compress_at_twenty = (compress_threshold - (
            (compress_threshold - 20
            ) / compress_ratio)
            ).__round__(1)

        points = \
            f'{expander_floor}/{expander_at_floor}' \
            f'|{expander_threshold}/{expander_threshold}' \
            f'|{compress_threshold}/{compress_threshold}' \
            f'|0/{compress_at_zero}' \
            f'|20/{compress_at_twenty}' \

        compander = \
            f'compand='\
            f'attacks={attack}'\
            f':decays={decay}'\
            f':points={points}'\
            f':soft-knee={soft_knee}'\
            f':gain={gain}'\
            f':volume={volume}'\
            f':delay={delay}'\

        filters = ['-af', compander]

        cmd = [
            self.ffmpeg_path,
            *self.I(),
            *filters,
            *self.O()
            ]

        self.process_with_latency_compensation(cmd, latency)
        print(filters)
        print(cmd)

    def deess(
            self,
            sensitivity=0.6,
            treble_amount=0.6,
            original_frequency_content=0.6,
            output_mode='filtered',
            ):
        """
        Apply de-essing to the audio samples.
        i -> Set intensity for triggering de-essing. Allowed range is from 0 to 1. Default is 0.
        m -> Set amount of ducking on treble part of sound. Allowed range is from 0 to 1. Default is 0.5.
        f -> How much of original frequency content to keep when de-essing. Allowed range is from 0 to 1. Default is 0.5.
        s -> Set the output mode.
            It accepts the following values:
                i -> Pass input unchanged.
                o -> Pass ess filtered out.
                e -> Pass only ess.
                Default value is o.
        """
        output_modes = {
            'unchanged' : 'i', 'i' : 'i',
            'filtered' : 'o', 'o' : 'o',
            'ess' : 'e', 'e' : 'e',
            }

        output_mode_ = output_modes.get(output_mode)

        latency = 0
        filters = f'deesser='\
            f'i={sensitivity}'\
            f':m={treble_amount}'\
            f':f={original_frequency_content}'\
            f':s={output_mode_}'

        cmd = [
            self.ffmpeg_path,
            *self.I(),
            '-af', filters,
            *self.O()
            ]

        self.process_with_latency_compensation(cmd, latency)

    def matcheq(self, target, smoothing=0.0375, fft_size=4096, min_freq=100, max_freq=8000, mix=1):
        self.meq = MatchEQ(
            sample_rate=self.sample_rate,
            smoothing=smoothing,
            fft_size=fft_size,
            min_freq = min_freq,
            max_freq = max_freq,
            mix = mix,
            )
        if isinstance(target, str):
            if target.endswith('.npy'):
                pass
            elif isinstance(target, str):
                target = self.load_mono(target)

        for ch in range(self.channels):
            self.signal[ch,:] = self.meq(source=self.signal[ch,:], target=target)


if __name__ == '__main__':
    x = Filter()
    print(x.__dict__.items())
