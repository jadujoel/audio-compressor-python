from utils import *
import json
import copy
import pathlib
import ntpath
import os

from _repr import Repr
#from Filter import Filter
from _subprocess import Subprocess
from _filter import Filter
from _plot import Plot
from _matcheq import MatchEQ


class FFmpeg(Repr, Subprocess, Filter, Plot):
    # A class made to help with interfacing with ffmpeg / ffprobe
    # Intended to be used with Audio Class
    def __init__(self, audio_device=':0'):
        Repr.__init__(self)
        Subprocess.__init__(self)
        Filter.__init__(self)
        Plot.__init__(self)

        this_dir = os.path.dirname(os.path.realpath(__file__))
        self.ffmpeg_path = os.path.join(this_dir, 'ffmpeg')
        self.ffprobe_path = os.path.join(this_dir, 'ffprobe')
        self.ffplay_path = os.path.join(this_dir, 'ffplay')
        self.ffmpeg_path_lv2 = os.path.join(this_dir, 'ffmpeg_lv2')

        self.codecs_incorrect_length = ['mp3', 'mp2']
        self.lufs_gotten = False

        self.denoise_plugin = "https\\\\://github.com/lucianodato/speech-denoiser"
        self.denoise_plugin_stream = r"https\\\\://github.com/lucianodato/speech-denoiser"

        self.sample_rate = 48000
        self.num_channels = 2
        self.acceptable_codec_names = ['wav', 'mp2']
        self.audio_device = audio_device

    def make_stream_cmd(self, options=[], lv2=False, nodisplay=True):
        if lv2:
            ffmpeg_path = self.ffmpeg_path_lv2
        cmd = [
            ffmpeg_path,
            '-f', 'avfoundation',
            '-i', self.audio_device,
            *options,
            '-f', 'wav',
            #'-ar', f'96000'
            '-',
            '|',
            self.ffplay_path,
            '-f', 'wav',
            #'-ar', f'{48000}',
            #'-ac', f'{2}',
            '-sync', 'ext',
            '-fflags', 'nobuffer',
            '-i', '-'
            ]
        if nodisplay:
            cmd = [*cmd, '-nodisp']
        """
        By default, ffplay introduces a small latency of its own,
        Also useful is mplayer with its -nocache for testing latency (
        or -benchmark).
        Using the SDL out is also said to view frames with minimal latency:
            ffmpeg ... -f sdl -
        -probesize 32 -analyzeduration 0

        """
        return cmd

    def process_with_latency_compensation(self, cmd, latency):
        self.signal = np.pad(self.signal, ((0, 0), (0, latency)), 'constant')
        self.signal = self.get_stdout_as_signal(*cmd, signal=self.signal)
        self.signal = self.signal[:,latency:]

    #################### Load and Write to disk #####################
    def load(self, path=None):
        if path is None: path = self.filename

        cmd = [
            self.ffmpeg_path,
            '-i', f'{path}',
            *self.O()
            ]

        signal = self.get_stdout_as_signal(*cmd)
        return signal

    def load_mono(self, path=None):
        if path is None: path = self.filename
        signal = self.load(path=path)
        return np.mean(signal, axis=0)

    def write(
            self,
            signal=None,
            path='',
            num_channels=None,
            sample_rate=None,
            codec_name=None,
            ):
        if not self.is_audio(signal): signal = self.signal
        if num_channels is None: num_channels = signal.shape[0]
        if path == '': path = self.filename_target
        if sample_rate is None: sample_rate = self.sample_rate
        if codec_name is None: codec_name = self.target_codec
        if not codec_name in self.acceptable_codec_names:
            codec_name='wav'

        self.overload_protection()

        cmd = [
            self.ffmpeg_path,
            *self.I(),
            '-ac', f'{num_channels}',
            '-ar', f'{sample_rate}',
            '-f', f'{codec_name}',
            '-y',
            path
            ]
        stdout, stderr = self.get_stdout_and_stderr(*cmd, signal=signal)
        return True

    def copy_file(self, path_source, path_target):
        cmd = [self.ffmpeg_path,
            '-i',  path_source,
            '-ar', f'{self.sample_rate}',
            '-y',
            path_target]
        stdout, self.get_stdout(*cmd)

    ########################## Interactives ########################
    def play(self, input=None):
        if input is None:
            self.play_signal(self.signal)
        elif self.is_audio(input):
            self.play_signal(signal=input)
        elif self.is_filepath(input):
            self.play_file(filename=input)

    def play_signal(self, signal):
        cmd = [self.ffmpeg_path,
            *self.I(),
            '-f', 'wav',
            '-',
            # ffplay
            r'|',
            self.ffplay_path,
            '-'
            ]
        cmd = ' '.join(cmd)
        signal = self.signal_to_stdin(signal)
        p = sp.Popen(cmd, stdin=sp.PIPE, stderr=sp.PIPE, shell=True)
        p.communicate(input=signal)

    def play_file(self, filename):
        cmd = [
                self.ffplay_path,
                f'{filename}'
                ]
        p = sp.Popen(cmd)
        p.wait()

    ################## Metadata and such ##################
    def probe(self, filename=''):
        if filename == '': filename = self.filename
        probe = self.probe_file(filename)

        _stream = probe['streams'][0]
        self.index = _stream.get('index')
        self.codec_name = _stream.get('codec_name')
        self.codec_type = _stream.get('codec_type')
        self.codec_time_base = _stream.get('codec_time_base')
        self.codec_tag_string = _stream.get('codec_tag_string')
        self.codec_tag = _stream.get('codec_tag')
        self.sample_fmt = _stream.get('sample_fmt')
        self.sample_rate = int(_stream.get('sample_rate'))
        self.channels = _stream.get('channels')
        self.num_channels = self.channels
        self.channel_layout = _stream.get('channel_layout')
        self.bits_per_sample = _stream.get('bits_per_sample')
        self.r_frame_rate = _stream.get('r_frame_rate')
        self.avg_frame_rate = _stream.get('avg_frame_rate')
        self.time_base = _stream.get('time_base')
        self.duration_ts = int(_stream.get('duration_ts'))
        self.duration = _stream.get('duration')
        #self.bit_rate = int(_stream.get('bit_rate']) # Is set elsewhere
        self.nb_read_frames = int(_stream.get('nb_read_frames'))
        self.nb_read_packets = int(_stream.get('nb_read_packets'))
        self.disposition = _stream.get('disposition')

        _format = probe['format']
        self.filename = _format["filename"]
        self.nb_streams = _format["nb_streams"]
        self.nb_programs = _format["nb_programs"]
        self.format_name = _format["format_name"]
        self.duration = _format["duration"]
        self.size = int(_format["size"])
        self.bit_rate = int(_format["bit_rate"])
        self.probe_score = _format["probe_score"]

        if "tags" in _format:
            self.tags = _format["tags"]
            self.time_reference = self.tags.get("time_reference")
            self.coding_history = self.tags.get("coding_history")
            self.creation_time = self.tags.get("creation_time")
            self.encoded_by = self.tags.get("encoded_by")
            self.comment = self.tags.get("comment")
            self.date = self.tags.get("date")
            self.umid = self.tags.get("umid")

    def probe_file(self, path=''):
        if path == '': path = self.filename

        cmd = [self.ffprobe_path,
            "-i", f'{path}',
            "-show_streams", "-select_streams", "a:0",
            "-show_format",
            "-show_packets",
            "-show_frames",
            #"-show_chapters",
            "-bitexact",
            "-print_format", "json"
            ]
        stdout = self.get_stdout(*cmd)
        return json.loads(stdout)

    def get_comment(self, filename):
        # Will also set object metadata to metadata in <filename>
        self.probe(filename)
        return self.comment

    def get_lufs(self, signal=None):
        self.lufs_gotten = True
        if signal is None:
            signal = self.signal

        cmd = [
            self.ffmpeg_path,
            '-hide_banner',
            '-nostats',
            *self.I(),
            '-filter_complex',
            'ebur128',
            '-f', 'null',
            '-']

        self.lufs_stderr = self.get_stderr(*cmd, signal=signal)
        self.parse_lufs()

    def parse_lufs(self):
        text = self.lufs_stderr.decode("ascii")
        text = " ".join(text.split())

        start, end = self.find_next_substring(string=text, beginning="] t:", ending="LU ")
        text = text[end+30:]
        frames = []
        time = 0
        pts = 0
        self.LUFS = {}
        for i in range(len(text)):
            start, end = self.find_next_substring(string=text, beginning="] t:", ending="LU ")
            if start == -1:
                # Has reached end of thing to read
                break
            else:
                frame = text[start+2:end]
                s, e = self.find_next_substring(frame, "M:", " S")
                LUFS_M = float(self.parse_spaces(frame[s+2:e-2]))
                s, e = self.find_next_substring(frame, "S:", " I")
                LUFS_S = float(self.parse_spaces(frame[s+2:e-2]))
                s, e = self.find_next_substring(frame, "I:", " LUFS LRA")
                LUFS_I = float(self.parse_spaces(frame[s+2:e-9]))
                s, e = self.find_next_substring(frame, "LRA:", " LU")
                LRA = float(self.parse_spaces(frame[s+5:-3]))

                time += 0.1
                pts = int(time*self.sample_rate)

                self.LUFS[f'frame {i}'] = {
                    "Time": time,
                    "pts" : pts,
                    "M" : LUFS_M,
                    "S" : LUFS_S,
                    "I" : LUFS_I,
                    "LRA" : LRA
                    }

                text = text[end+30:]

        # Save in arrays for easy access
        self.loudness_time = np.array([], dtype=np.float32)
        self.loudness_pts = np.array([], dtype=np.int32)
        self.loudness_momentary = np.array([], dtype=np.float32)
        self.loudness_integrated = np.array([], dtype=np.float32)
        self.loudness_short_term = np.array([], dtype=np.float32)
        self.LRA = np.array([], dtype=np.float32)
        for key, frame in self.LUFS.items():
            self.loudness_time = np.append(self.loudness_time, frame['Time'])
            self.loudness_pts = np.append(self.loudness_pts, frame['pts'])
            self.loudness_momentary = np.append(self.loudness_momentary, frame['M'])
            self.loudness_integrated = np.append(self.loudness_integrated, frame['I'])
            self.loudness_short_term = np.append(self.loudness_short_term, frame['S'])
            self.LRA = np.append(self.LRA, frame['LRA'])

        self.loudness_summary = {
            "Integrated" : self.loudness_integrated[-1],
            "LRA" : self.LRA[-1]
            }

    ###################### HELPERS ############################
    def db_to_linear(self, dB):
        return 10**(dB/20)

    def linear_to_db(self, lin):
        return 20*np.log10(lin)

    def find_next_substring(self, string, beginning, ending):
        start = string.find(beginning)
        end = string.find(ending) + len(ending)
        return start, end

    def is_audio(self, x):
        if type(x) is np.ndarray: return True
        else: return False

    def is_filepath(self, x):
        return os.path.exists(x)

    def sigmoid(self, x, derivative=False):
        sigm = 1. / (1. + np.exp(-x))
        if derivative:
            return sigm * (1. - sigm)
        return sigm

    def path_leaf(self, path):
        ## Get basename for file regardless of OS
        head, tail = ntpath.split(path)
        return tail or ntpath.basename(head)

    def name_ext(self, path):
        basename = self.path_leaf(path)
        extless, ext = ntpath.splitext(basename)
        return extless, ext

    def parse_spaces(self, string):
        # Remove spaces in string
        return ''.join(string).split()[0]

    def grouped(self, iterable, n):
        # for iterating over every n elements
        "s -> (s0,s1,s2,...sn-1), (sn,sn+1,sn+2,...s2n-1), (s2n,s2n+1,s2n+2,...s3n-1), ..."
        return zip(*[iter(iterable)]*n)


if __name__ == '__main__':
    ff = FFmpeg()
    print(ff.__dict__.items())
    ff.mcompand()
    """
    highpass
    asr?
    anequalizer
    superequalizer as match eq?
    """



