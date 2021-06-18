import asyncio
import numpy as np
import datetime
import copy
import logging

from FFmpeg import FFmpeg
from NewFiles import NewFiles
from utils import *
class AutoVolume:
    # Used by class Audio, uses class FFmpeg
    def __init__(self):
        self.target_LRA = 4

    def autovol(self,
            loudness_type="short",
            mix=0.8,
            max_deviation_gain=20,
            target_lufs=-23
            ):

        self.target_lufs = target_lufs
        self.loudness_max_deviation_gain = max_deviation_gain
        self.loudness_mix = mix
        self.loudness_type = loudness_type
        if self.loudness_type == "integrated":
            self.loudness_block_size = int(3 * self.sample_rate)
        elif self.loudness_type == "short":
            self.loudness_block_size = int(3 * self.sample_rate)
        elif self.loudness_type == "momentary":
            self.loudness_block_size = int(0.4 * self.sample_rate)
        else:
            raise Exception(f'loudness type {loudness_type} not recognised as an option. Please use "integrated", "short" or "momentary"')

        if self.loudness_block_size >= self.signal.shape[1]:
            print(f"Cant autovol this short a signal with loudness type({self.loudness_type}).")
            return None

        if self.loudness_type =='integrated': self.do_integrated()
        else: self.do_short_term_or_momentary()

        self.get_lufs()

    def add_inverse(self):
        self.num_samples = self.signal.shape[1]
        # Reversed audio to beginning and end to help with loudness calculation there.
        inverse_start = self.signal[:,:self.loudness_block_size][:,::-1]
        inverse_end = self.signal[:,-self.loudness_block_size:][:,::-1]
        combined = np.append(inverse_start, self.signal, axis= 1)
        combined = np.append(combined, inverse_end, axis=1)
        self.len_inverse_start = inverse_start.shape[1]
        self.len_inverse_end = inverse_end.shape[1]
        self.signal = combined
        self.num_samples = self.signal.shape[1]

    def do_integrated(self):
        self.get_lufs()
        loudness = self.loudness_integrated[-1]
        multiplier = self.db_to_linear(self.target_lufs - loudness)
        self.signal = self.signal * multiplier

    def do_short_term_or_momentary(self):
        self.add_inverse()
        self.get_lufs()
        self.get_linear_multiplier()
        self.get_volumeride()
        self.volumeride_smoothen()
        self.volumeride_apply()
        self.remove_inverse()
        self.do_integrated()

    def remove_inverse(self):
        self.signal = self.signal[:,
            self.len_inverse_start : - self.len_inverse_end]
        self.num_samples = self.signal.shape[1]

    def get_linear_multiplier(self):
        if self.loudness_type == "momentary":
            loudness = self.loudness_momentary
        elif self.loudness_type == "short":
            loudness = self.loudness_short_term
        elif self.loudness_type == "integrated":
            loudness = self.loudness_integrated

        # Apply a limit to gain increase
        median_loudness = np.median(loudness)
        for i, loud in enumerate(loudness):
            if loud < (median_loudness -
                    self.loudness_max_deviation_gain):
                loudness[i] = loudness[i-1]

        self.linear_multiplier = self.db_to_linear(
            (self.target_lufs - loudness)*self.loudness_mix)

    def get_volumeride(self):
        # Make start/end index arrays
        offset = self.loudness_block_size//2
        self.idx_start = self.loudness_pts - offset
        i = next(x[0] for x in enumerate(self.idx_start) if x[1] > 0)
        self.idx_start = self.idx_start[i:]
        self.linear_multiplier = self.linear_multiplier[i:]
        self.idx_end = self.idx_start[1:]
        self.idx_end = np.append(self.idx_end, self.num_samples-1)

        # Make volumeride
        self.volumeride = np.ones(self.num_samples)
        for start, end, mult in zip(self.idx_start, self.idx_end, self.linear_multiplier):
            self.volumeride[start : end] = mult

    def volumeride_smoothen(self):
        # Apply fades to smoothen transitions
        for start, end in zip(self.idx_start, self.idx_end):
            self.volumeride[start:end] = np.linspace(
                start = self.volumeride[start],
                stop = self.volumeride[end],
                num = end-start)

    def volumeride_apply(self):
        self.signal = self.signal * self.volumeride

class Audio(FFmpeg, AutoVolume):
    def __init__(self,
            arbitrary_input = None,
            filename:str = '',
            filename_target:str = '',
            downloads_dir:str = 'input',
            num_channels:int = None,
            sample_rate:int = None,
            array = None,
            target_codec = None,
            target_lufs = -23
            ):

        FFmpeg.__init__(self)
        AutoVolume.__init__(self)

        self.temp_dir = None

        if arbitrary_input is not None:
            if type(arbitrary_input) is str:
                filename = arbitrary_input
            elif type(arbitrary_input) is np.ndarray:
                array = arbitrary_input
            else:
                raise Exception(f'input of type {type(arbitrary_input)} not recognised. Try str or np.ndarray')

        self.filename = filename
        self.filename_target = filename_target
        self.downloads_dir = downloads_dir
        self.num_channels = num_channels
        self.sample_rate = sample_rate
        self.array = array
        self.target_codec = target_codec
        self.target_lufs = target_lufs

        if self.is_youtube_url():
            self.setup_file_from_youtube_link()

        if self.is_audio_array():
            self.setup_file_from_array()

        ## Check filename
        # def setup_self_from_filename

        # probe will set sample_rate and num_channels from file metadata
        self.probe()

        if sample_rate: self.sample_rate = sample_rate
        if num_channels: self.num_channels = num_channels
        if filename_target != '':
            self.filename_target = filename_target
        else:
            name, ext = self.name_ext(self.filename)
            self.filename_target = f'{name}_output{ext}'
        self.signal = self.load()

    def set_signal(self, signal):
        self.signal = signal
        self.assure_healthy_signal()

    def get_signal(self):
        return self.signal

    def get_mono(self):
        self.make_mono()
        return self.signal_mono

    def getSampleRate(self):
        return self.sample_rate

    def setup_file_from_youtube_link(self):
        """ This function downloads the audio to disk,
        and sets <self.filename> to be the downloaded file.
        If the file already exists in <self.downloads_dir>,
        then it will not redownload.
        """
        if not self.is_downloaded():
            self.download_from_youtube()
            self.Exception_check_youtube_download()
        self.get_filename_of_downloaded_file()
        self.get_youtube_metadata()

    def is_youtube_url(self):
        if r'youtube.com/' in self.filename:
            return True
        else:
            return False

    def is_audio_array(self):
        if type(self.array) == type(np.array([])):
            return True
        else:
            return False

    def setup_file_from_array(self):
        self.signal = self.array
        self.assure_healthy_signal()
        self.sample_rate = self.sample_rate or 48000
        self.num_channels = self.num_channels or self.signal.shape[0]
        if self.filename == '':
            self.create_temporary_filename()
        self.write(path=self.filename)
        logging.info(f'created {self.filename}')

    def assure_correct_signal_shape(self, signal):
        if signal.ndim == 1:
            signal = signal[np.newaxis, :]
        elif signal.ndim == 2:
            shape = signal.shape
            if shape[0] > shape[1]:
                signal = signal.T
        else:
            raise Exception(f'Error: Signal needs to have one or two dimensions. not {signal.ndim}')
        return signal

    def assure_healthy_signal(self):
        self.signal = self.assure_correct_signal_shape(self.signal)
        self.num_channels = self.signal.shape[0]
        if self.signal.dtype is not np.float32:
            self.signal = self.signal.astype(np.float32)
        if self.signal.max() > 1:
            logging.info(f'peak normalizing audio {self.filename} because it exceeds 0 dBFS')
            self.normalize(type_='peak', headroom_db=2)

    def create_temporary_filename(self):
        if self.filename_target != '':
            self.filename = self.filename_target
        else:
            suffix = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
            suffix += '.wav'
            self.filename = os.path.join(os.getcwd(), suffix)
            self.filename_is_temporary = True

    def is_downloaded(self):
        # Todo
        return False

    def Exception_check_youtube_download(self):
        # Todo
        if self.youtube_dl_stderr.startswith('ERROR'):
            raise Exception(
                f'Unable to download "{self.filename}"'
                f' -> {self.youtube_dl_stderr}'
                )

    def download_from_youtube(self):
        # Todo: add check if download succesfull
        cmd = [
            'youtube-dl',
            '-x',
            '--extract-audio',
            '--write-info-json',
            self.filename
            ]

        _stdout, _stderr = self.get_stdout_and_stderr(*cmd)
        self.youtube_dl_stdout = _stdout.decode('iso-8859-1')
        self.youtube_dl_stderr = _stderr.decode('iso-8859-1')

    def get_filename_of_downloaded_file(self):
        # Todo: add check if already downaloaded
        stdout_arr = self.youtube_dl_stdout.split('\n')

        start_of_line_to_find = r'[ffmpeg] Destination: '
        filename_begins = len(start_of_line_to_find)
        downloaded_file = None

        for line in stdout_arr:
            if line.startswith(start_of_line_to_find):
                downloaded_file = line[filename_begins :].strip()
                break

        self.filename = downloaded_file

        start_of_ext = downloaded_file.rfind('.')
        downloaded_file_extless = downloaded_file[:start_of_ext]
        self.youtube_metadata_file = f'{downloaded_file_extless}.info.json'

    def get_youtube_metadata(self):
        with open(self.youtube_metadata_file) as f:
            _metadata_string = f.read()
            self.youtube_metadata = json.loads(_metadata_string)

    def get_signal_as_int16(self):
        return self.signal*32.767

    def copy(self):
        return copy.deepcopy(self)

    def make_mono(self):
        self.signal_mono = np.mean(self.signal, axis=0)

    def __add__(self, y):
        self.signal += y.signal
        return self


def main():
    #audio = Audio(r'/Users/admin/Dropbox/workspace/SigPy/other/test.wav')
    file = r'/Users/admin/Dropbox/workspace/SigPy/other/forevyoungalpha.wav'
    #file = r'/Users/admin/Dropbox/workspace/SigPy/source.wav'
    audio = Audio(file)

    trg = r"/Users/admin/Dropbox/workspace/SigPy/target.wav"
    print(audio)
    #audio.matcheq(target=r'/Users/admin/Dropbox/workspace/SigPy/p1.npy')
    audio.plot_freq(filename='freq.png')
    quit()
    audio.matcheq(target=trg)
    audio.write(path='test2.wav', codec_name="wav")



    quit()
    nf = NewFiles()

    while True:
        for file in nf():
            audio = Audio(filename=file.path, filename_target=file.target_path)
            audio.plot_lufs(filename=f'{file.target_path_extless}_before.png')
            audio.autovol(loudness_type="short", mix=0.8)
            audio.autovol(loudness_type="momentary", mix=0.2)
            audio.limit(max_dbfs=-11)
            audio.plot_lufs(filename=f'{file.target_path_extless}_after.png')
            audio.write(path=self.filename, codec_name="wav")
            #audio.write(path=self.filename)
            # audio.play()

if __name__ == '__main__':
    main()
