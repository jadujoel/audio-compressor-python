# Author: joel.lof@icloud.com
import sys
import numpy as np
from compressor import Compressor
from plot import AmplitudePlot
from generators import sine, chirp
sys.path.append('sigpy')
from Audio import Audio

def example_one():

    # Set compressor parameters
    sample_rate = 48000
    input_gain = 0
    makeup_gain = 0
    attack = 0.025
    release = 0.05
    ratio = 5
    threshold = -15
    sidechain_lowcut = 20
    sidechain_highcut = 20000

    # Generate two sine waves, one loud, one silent
    above_threshold_sine = sine(
        sample_rate=sample_rate, frequency=1000, dBFS=-5, duration=0.5
        )

    below_threshold_sine = sine(
        sample_rate=sample_rate, frequency=1000, dBFS=-25, duration=0.5
        )

    # Combine the sine waves into one signal
    original = np.hstack([above_threshold_sine, below_threshold_sine])

    # Save as wavfile
    audio = Audio(original, filename_target=f'ex1_sine_original.wav', sample_rate=sample_rate)

    # Apply compression
    compressor = Compressor(
        input_gain = input_gain,
        threshold=threshold,
        ratio=ratio,
        attack=attack,
        release=release,
        makeup_gain=makeup_gain,
        sample_rate=sample_rate,
        sidechain_lowcut=sidechain_lowcut,
        sidechain_highcut=sidechain_highcut,
        )

    compressed = compressor.update(original)

    # Save compressed signal to wavfile
    audio.set_signal(compressed)
    audio.write(path='ex1_sine_compressed.wav')

    # Plot amplitude before and after compression
    ap = AmplitudePlot(
        signals = [original, compressed],
        legends = ['original', 'compressed'],
        sample_rate = sample_rate,
        fname = 'ex1_sine_compression.png',
        yscale = 'dBFS',
        ymax = 0,
        ymin = -40,
        envelope_type='peak',
        )

    ap.plot()
    ap.save()

def example_two():

    # Set compressor parameters
    sample_rate = 48000
    input_gain = 0
    makeup_gain = 0
    attack = 0.1
    release = 0.005
    ratio = 10
    threshold = -25
    sidechain_lowcut = 20
    sidechain_highcut = 20000

    # Generate two sine waves, one loud, one silent
    above_threshold_sine = sine(
        sample_rate=sample_rate, frequency=1000, dBFS=-5, duration=0.5
        )

    below_threshold_sine = sine(
        sample_rate=sample_rate, frequency=1000, dBFS=-25, duration=0.5
        )

    # Combine the sine waves into one signal
    original = np.hstack([above_threshold_sine, below_threshold_sine])

    # Save as wavfile
    audio = Audio(original, filename_target='ex2_sine_originalwav', sample_rate=sample_rate)

    # Apply compression
    compressor = Compressor(
        input_gain = input_gain,
        threshold=threshold,
        ratio=ratio,
        attack=attack,
        release=release,
        makeup_gain=makeup_gain,
        sample_rate=sample_rate,
        sidechain_lowcut=sidechain_lowcut,
        sidechain_highcut=sidechain_highcut,
        )

    compressed = compressor.update(original)

    # Save compressed signal to wavfile
    audio.set_signal(compressed)
    audio.write(path='ex2_sine_compressed.wav')

    # Plot amplitude before and after compression
    ap = AmplitudePlot(
        signals = [original, compressed],
        legends = ['original', 'compressed'],
        sample_rate = sample_rate,
        fname = 'ex2_sine_compression.png',
        #yscale = 'dBFS',
        yscale = 'dBFS',
        ymax = 0,
        ymin = -40,
        envelope_type='peak',
        )

    ap.plot()
    ap.save()

    # Plot the amplitude again but with settings
    # closer to the compressor abplitude calculation
    ap = AmplitudePlot(
        signals = [original, compressed],
        legends = ['original', 'compressed'],
        sample_rate = sample_rate,
        fname = 'ex2_sine_compression_new_plot_settings.png',
        yscale = 'dBFS',
        ymax = 0,
        ymin = -40,
        envelope_type='ppm',
        frame_time = 0.002,
        hop_time = 0.002,
        )

    ap.plot()
    ap.save()

def example_three():

    # Set compressor parameters
    sample_rate = 48000
    input_gain = 0
    makeup_gain = 0
    attack = 0.03
    release = attack
    ratio = 10
    threshold = -25
    sidechain_lowcut = 20
    sidechain_highcut = 20000
    lookahead = attack

    # Generate two sine waves, one loud, one silent
    above_threshold_sine = sine(
        sample_rate=sample_rate, frequency=1000, dBFS=-5, duration=0.5
        )

    below_threshold_sine = sine(
        sample_rate=sample_rate, frequency=1000, dBFS=-25, duration=0.5
        )

    # Combine the sine waves into one signal
    original = np.hstack([below_threshold_sine, above_threshold_sine, below_threshold_sine])

    # Save as wavfile
    audio = Audio(original, filename_target='ex3_original.wav', sample_rate=sample_rate)

    # Apply compression
    compressor = Compressor(
        input_gain = input_gain,
        threshold=threshold,
        ratio=ratio,
        attack=attack,
        release=release,
        makeup_gain=makeup_gain,
        sample_rate=sample_rate,
        sidechain_lowcut=sidechain_lowcut,
        sidechain_highcut=sidechain_highcut,
        lookahead_time = lookahead,
        )

    compressed = compressor.update(original)

    # Save compressed signal to wavfile
    audio.set_signal(compressed)
    audio.write(path='ex3_compressed.wav')

    # Plot amplitude before and after compression
    ap = AmplitudePlot(
        signals = [original, compressed],
        legends = ['original', 'compressed'],
        sample_rate = sample_rate,
        fname = 'ex3_lookahead.png',
        #yscale = 'dBFS',
        yscale = 'dBFS',
        ymax = 0,
        ymin = -40,
        envelope_type='peak',
        )

    ap.plot()
    ap.save()

def example_four():

    # Set compressor parameters
    sample_rate = 48000
    input_gain = 0
    makeup_gain = 0
    attack = 0.005
    release = attack
    ratio = 10
    threshold = -25
    sidechain_lowcut = 20
    sidechain_highcut = 20000
    lookahead = 0

    # Generate two sine waves, one loud, one silent
    above_threshold_sine = sine(
        sample_rate=sample_rate, frequency=1000, dBFS=-5, duration=0.5
        )

    below_threshold_sine = sine(
        sample_rate=sample_rate, frequency=1000, dBFS=-25, duration=0.5
        )

    # Load Signal (synth.wav and kick.wav)
    synth_audio = Audio(r'synth.wav', sample_rate=sample_rate)
    synth_audio.write(path='ex4_original.wav')
    synth_signal = synth_audio.get_mono()

    kick_audio = Audio(r'kick.wav', sample_rate=sample_rate)
    kick_audio.write(path='ex4_sidechain.wav')
    kick_signal = kick_audio.get_mono()

    # Apply compression
    compressor = Compressor(
        input_gain = input_gain,
        threshold=threshold,
        ratio=ratio,
        attack=attack,
        release=release,
        makeup_gain=makeup_gain,
        sample_rate=sample_rate,
        sidechain_lowcut=sidechain_lowcut,
        sidechain_highcut=sidechain_highcut,
        lookahead_time = lookahead,
        )

    compressed = compressor.update(signal=synth_signal, sidechain_signal=kick_signal)

    # Save compressed signal to wavfile
    Audio(compressed, sample_rate=sample_rate, filename_target='ex4_compressed.wav')

    # Plot amplitude before and after compression
    ap = AmplitudePlot(
        signals = [synth_signal, kick_signal, compressed],
        legends = ['Synth (Original)', 'Kick (Sidechain)', 'Synth (Compressed)'],
        sample_rate = sample_rate,
        fname = 'ex4_sidechain.png',
        yscale = 'dBFS',
        ymax = 0,
        ymin = -40,
        envelope_type='rms',
        frame_time = 0.025,
        )

    ap.plot()
    ap.save()

def example_five():

    # Set compressor parameters
    sample_rate = 48000
    input_gain = 0
    makeup_gain = 0
    attack = 0.005
    release = attack
    ratio = 10
    threshold = -25
    sidechain_lowcut = 5000
    sidechain_highcut = 10000
    lookahead = 0

    # Generate a sine wave swepp
    original = chirp(
        start_freq=20,
        stop_freq=20000,
        duration=4,
        sample_rate=sample_rate
        )

    audio = Audio(original, filename_target='chirp.wav', sample_rate=sample_rate)
    audio.plot_freq()

    ap = AmplitudePlot(
        signals = [original],
        legends = ['chirp'],
        sample_rate = sample_rate,
        fname = 'ex5_chirp.png',
        yscale = 'dBFS',
        ymax = 0,
        ymin = -40,
        envelope_type='peak',
        frame_time = 0.01,
        ylabel ='Amplitude in dBFS',
        )
    ap.plot()
    ap.save()

    from pretty_spectrogram import prettyspec
    prettyspec(
        original,
        rate=sample_rate,
        path='ex5_orig_spec',name='',
        fft_size = 1024,
        step_size = 512
        )

    # Apply compression
    compressor = Compressor(
        input_gain = input_gain,
        threshold=threshold,
        ratio=ratio,
        attack=attack,
        release=release,
        makeup_gain=makeup_gain,
        sample_rate=sample_rate,
        sidechain_lowcut=sidechain_lowcut,
        sidechain_highcut=sidechain_highcut,
        lookahead_time = lookahead,
        )

    compressed = compressor.update(signal=original)

    # Save compressed signal to wavfile
    ca = Audio(compressed, sample_rate=sample_rate, filename_target='ex5_compressed.wav')
    ca.plot_freq()
    # Plot amplitude before and after compression
    ap = AmplitudePlot(
        signals = [original, compressed],
        legends = ['original', 'compressed'],
        sample_rate = sample_rate,
        fname = 'ex5_scfilter.png',
        yscale = 'dBFS',
        ymax = 0,
        ymin = -40,
        envelope_type='peak',
        frame_time = 0.01,
        ylabel ='Amplitude in dBFS',
        )

    ap.plot()
    ap.save()

    prettyspec(original,
        rate=sample_rate,
        path='ex5_compressed_spec',name='',
        fft_size = 1024,
        step_size = 512,
        )

def example_six():
    from _plot_frequency import FrequencyPlot
    fp = FrequencyPlot(
        sample_rate = 48000,
        num_fft = 8192,
        smoothing_amount = 0.04,#0.002,
        smoothen = True,
        ymin=-80,
        )

    # Set compressor parameters
    sample_rate = 48000
    input_gain = 0
    makeup_gain = 0
    attack = 0.002
    release = attack
    ratio = 100
    threshold = -25
    sidechain_lowcut = 4000
    sidechain_highcut = 20000
    lookahead = 0

    audio = Audio(r'ex6_original.wav', sample_rate=sample_rate)
    #audio.plot_freq()
    original = audio.get_mono()

    #fp.make_from_signal(), filename='original_fp.png')

    # Apply compression
    compressor = Compressor(
        input_gain = input_gain,
        threshold=threshold,
        ratio=ratio,
        attack=attack,
        release=release,
        makeup_gain=makeup_gain,
        sample_rate=sample_rate,
        sidechain_lowcut=sidechain_lowcut,
        sidechain_highcut=sidechain_highcut,
        lookahead_time = lookahead,
        )

    compressed = compressor.update(signal=original)

    # Save compressed signal to wavfile
    ca = Audio(compressed, sample_rate=sample_rate, filename_target='ex6_compressed.wav')
    #ca.plot_freq()

    # Plot amplitude before and after compression
    ap = AmplitudePlot(
        signals = [original, compressed],
        legends = ['original', 'compressed'],
        sample_rate = sample_rate,
        fname = 'ex6_scfilter.png',
        yscale = 'dBFS',
        ymax = 0,
        ymin = -40,
        envelope_type='peak',
        frame_time = 0.01,
        ylabel ='Amplitude in dBFS',
        ).plotAndSave()

    #ap.plot()
    #ap.save()

    fp.make_from_signal(np.array([original, compressed]), filename='compressed_fp.png')

if __name__ == '__main__':
    example_one()
    example_two()
    example_three()
    example_four()
    example_five()
    example_six()


