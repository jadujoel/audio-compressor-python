import atexit
import os
import time
import pickle
from FFmpeg import FFmpeg
from SwedishRadioAudioFile import SwedishRadioAudioFile
#from utils import *

class File:
    def __init__(self, path):
        self.processed = False

        self.path = path
        (self.directory,
            self.basename,
            self.path_extless,
            self.basename_extless,
            self.ext) = self.names(self.path)

        self.path_exists = os.path.exists(self.path)

        if self.path_exists:
            self.size = self.size(self.path)
            self.file_info = os.stat(path)
            self.inode = self.file_info.st_ino # almost unique number
            self.modification_date = time.ctime(self.file_info[8])

    def names(self, path):
        directory, basename = os.path.split(path)
        path_extless, ext = os.path.splitext(path)
        basename_extless, ext = os.path.splitext(basename)
        return directory, basename, path_extless, basename_extless, ext

    def target(self, path):
        self.target_path = path
        (self.target_directory,
            self.target_basename,
            self.target_path_extless,
            self.target_basename_extless,
            self.target_ext) = self.names(self.target_path)

    def convert_bytes(self, num):
        for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
            if num < 1024.0:
                return "%3.1f %s" % (num, x)
            num /= 1024.0

    def size(self, path):
        if os.path.isfile(path):
            file_info = os.stat(path)
            return self.convert_bytes(file_info.st_size)
        else:
            return "Null"

class NewFiles:
    """ This class looks in a folder for files containing accepted extensions.
    it creates File objects and yields them.
    If a new file is added to the folder during runtime,
    the class will yield the added file.
    On kill signal, the class saves the current state to a pickle file.
    On init it will look for the file and continue where it left off.

    Example use below:

    newfiles = NewFiles()
    while True:
        for file in newfiles():
            do_thing(file)
            newfiles.set_processed(file)

    """
    def __init__(
            self,
            infolder=None,
            picklepath=None,
            out_extend=None,
            can_not_include=None,
            accepted_formats=None,
            ):

        self.infolder = infolder or self.default_infolder()
        self.picklepath = picklepath or self.default_picklepath()
        self.out_extend = out_extend or self.default_out_extend()
        self.can_not_include = can_not_include or self.default_can_not_include()
        self.accepted_formats = accepted_formats or self.default_accepted_formats()

        #self.print_looking_for_new_files = True
        self.times_called = 0
        self.files = []

        self.load_progress_from_pickle()
        self.print_progress()

        atexit.register(self.save_to_pickle)

    def __call__(self):
        self.times_called += 1
        # if self.print_looking_for_new_files:
            #print("\nLooking for new files...")
        self.get_accepted()
        self.return_early_maybe()
        self.make_file_objects()
        for file in self.files:
            if file.processed == False:
                yield file

    def default_infolder(self):
        return os.path.join(os.getcwd(), 'input')

    def default_out_extend(self):
        return r"_autovol"

    def default_accepted_formats(self):
        return (
            '.WAV', '.wav',
            'AIFF', 'AIF', 'aif', 'aiff',
            '.mp3', '.MP3')

    def default_can_not_include(self):
        return "autovol"

    def default_picklepath(self):
        return os.path.join(
            self.infolder, "NewFiles.pickle")

    def get_path(self, name):
        return os.path.join(self.infolder, name[:])

    def get_accepted(self):
        names = os.listdir(self.infolder)
        self.accepted = []
        for name in names:
            if not self.can_not_include in name:
                if not self.out_extend in name:
                    if name.endswith(self.accepted_formats):
                        if not any(file.basename == name for file in self.files):
                            self.accepted.append(name)

    def set_processed(self, file_to_set):
        for i, file in enumerate(self.files):
            if file.path == file_to_set.path:
                self.files[i].processed = True
                break

    def make_file_objects(self):
        for name in self.accepted:
            file = File(self.get_path(name))
            file.target(self.make_target_path(file))
            self.files.append(file)
            print(f'File Accepted: {file.basename}  >  {file.target_basename}')

    def save_to_pickle(self):
        if os.path.isfile(self.picklepath):
            os.remove(self.picklepath)
        with open(self.picklepath, 'wb') as f:
            pickle.dump({'files':self.files}, f)

    def make_target_path(self, file):
        new_name = file.basename
        name_from_comment = False
        if file.basename[0:2] == "SR" and file.ext == ".WAV":
            comment = SwedishRadioAudioFile().get_comment(file.path)
            if len(comment) > 0:
                name_from_comment = True
                new_name = f'{comment}{self.out_extend}{file.ext}'

        if not name_from_comment:
            new_name = f'{file.basename_extless}{self.out_extend}{file.ext}'

        path = self.get_path(name=new_name)
        return path

    def load_progress_from_pickle(self):
        if os.path.isfile(self.picklepath):
            with open(self.picklepath, 'rb') as f:
                self.files = pickle.load(f)['files']

    def reset(self):
        print('resetting progress')
        if os.path.isfile(self.picklepath):
            os.remove(self.picklepath)
        self.files = []
        #self.load_progress_from_pickle()

    def return_early_maybe(self):
        if len(self.accepted) == 0:
            #time.sleep(4)
            # self.print_looking_for_new_files = False
            return None
        # self.print_looking_for_new_files = True

    def print_progress(self):
        for file in self.files:
            if file.processed:
                print(f'Already processed: {file.basename_extless} '\
                      f'> {file.target_basename_extless}')
            else:
                print(f'Accepted to be processed: {file.basename_extless} '\
                     f'> {file.target_basename_extless}')


if __name__ == '__main__':
    path = r"/Users/admin/Dropbox/workspace/levelbox/input/SR170245_31545C5FC20E45AE918BE2A26D67FD85.WAV"
    #f = File(path)
    #quit()
    nf = NewFiles()
    while True:
        for file in nf():
            nf.set_processed(file)
