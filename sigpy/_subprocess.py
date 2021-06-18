import numpy as np
import asyncio
class Subprocess:
    """ For use in class FFmpeg """
    ################## Interface with shell #########################
    async def execute_command(self, *cmd, input=None, loop=None):
        p = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            loop=loop)
        stdout, stderr = await p.communicate(input=input)
        self.log_stdout = stdout[:]
        self.log_stderr = stderr[:]
        return stdout, stderr

    async def execute_shell(self, *cmd):
        cmd = ' '.join(cmd)
        p = await asyncio.create_subprocess_shell(
            cmd,
            #stdin=asyncio.subprocess.PIPE,
            #stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            )#loop=loop)
        stderr = await p.communicate()
        #self.log_stdout = stdout[:]
        self.log_stderr = stderr[:]
        return stderr

    def run_in_shell(self, *cmd):
        asyncio.run(self.execute_shell(*cmd))

    def get_stdout(self, *cmd, input=None, signal=None):
        if input is None and signal is not None:
            signal = self.signal_to_stdin(signal=signal)
            input = signal

        stdout, stderr = asyncio.run(self.execute_command(*cmd,
                                    input=input))
        return stdout

    def get_stderr(self, *cmd, input=None, signal=None):
        if signal is not None and input is None:
            signal = self.signal_to_stdin(signal=signal)
            input = signal

        stdout, stderr = asyncio.run(self.execute_command(*cmd,
                                    input=input))
        return stderr

    def get_stdout_and_stderr(self, *cmd, input=None, signal=None):
        if signal is not None and input is None:
            signal = self.signal_to_stdin(signal=signal)
            input = signal

        stdout, stderr = asyncio.run(self.execute_command(*cmd,
                                    input=input))
        return stdout, stderr

    def get_stdout_as_signal(self, *cmd, input=None, signal=None):
        if signal is not None and input is None:
            input = self.signal_to_stdin(signal=signal)

        stdout = self.get_stdout(*cmd, input=input)
        signal = np.frombuffer(stdout, dtype=np.float32)[:]

        signal_reshaped = np.array(
            [signal[c::self.num_channels] for c in range(self.num_channels)],
            dtype=np.float32)

        return signal_reshaped

    def get_stdout_as_iso(self, *cmd, input=None):
        stdout = self.get_stdout(*cmd, input=input)
        return stdout.decode('iso-8859-1')

    def get_stdout_as_ascii(self, *cmd, input=None):
        stdout = self.get_stdout(*cmd, input=input)
        return stdout.decode('ascii')

    def signal_to_stdin(self, signal):
        signal_reshaped = np.zeros(signal.shape[0]*signal.shape[1])
        for ch in range(signal.shape[0]):
            signal_reshaped[ch::signal.shape[0]] = signal[ch,:]
        return signal_reshaped.astype(np.float32).tobytes()

    def I(self):
        return [
            '-f', 'f32le',
            '-ar', f'{self.sample_rate}',
            '-ac', f'{self.num_channels}',
            '-i', '-'
            ]

    def O(self):
        return [
            '-ar', f'{self.sample_rate}',
            '-ac', f'{self.num_channels}',
            '-f', 'f32le',
            '-acodec', 'pcm_f32le',
            '-'
            ]
        #return cmd


    # def I_mono(self):
    #     return [
    #         '-f', 'f32le',
    #         '-ar', f'{self.sample_rate}',
    #         '-ac', '1',
    #         '-i', '-'
    #         ]

    # def O_mono(self):
    #     return [
    #         '-ar', f'{self.sample_rate}',
    #         '-ac', '1',
    #         '-f', 'f32le',
    #         '-acodec', 'pcm_f32le',
    #         '-'
    #         ]
        #return cmd
