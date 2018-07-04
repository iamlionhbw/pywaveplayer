# -*- coding:utf-8 -*-

import os
import wave
import pyaudio
import functools
import time
import threading


def _singleton(cls):
    ins = {}

    @functools.wraps(cls)
    def get_inst(*args, **kwargs):
        if cls not in ins:
            ins[cls] = cls(*args, **kwargs)
        return ins[cls]
    return get_inst


@_singleton
class _AudioMgr(object):

    def __init__(self):
        super().__init__()

        self.audio = pyaudio.PyAudio()

    def make_stream(self, params):
        if self.audio is None:
            raise RuntimeError("Cannot hold a PyAudio instance")
        if isinstance(params, wave._wave_params):
            return self.audio.open(
                format=self.audio.get_format_from_width(params.sampwidth),
                channels=params.nchannels,
                rate=params.framerate,
                output=True
            )
        else:
            raise ValueError("Need wave._wave_params, but get type:%s" % type(params))

    def __del__(self):
        if self.audio is not None:
            self.audio.terminate()


class Sound(object):

    def __init__(self, file_path):
        super().__init__()

        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            raise RuntimeError("File not exists")

        self.fp = file_path

        self.wave_file = wave.open(self.fp, "rb")

        self.wave_params = self.wave_file.getparams()

        self.stream = _AudioMgr().make_stream(self.wave_params)

        self._stop_play_flag = True
        self._is_stopped = True

    def __del__(self):
        self.stop()
        while not self.stopped():
            time.sleep(0.5)

        self.stream.close()

    def get_file_path(self):
        return self.fp

    def play(self, loops=1, chunk_size=1024, delay=0):
        if delay:
            time.sleep(delay)
        self._stop_play_flag = False
        self._is_stopped = False
        while loops and not self._stop_play_flag:
            loops -= 1
            data = self.wave_file.readframes(chunk_size)
            while len(data) > 0 and not self._stop_play_flag:
                self.stream.write(data)
                data = self.wave_file.readframes(chunk_size)
            self.wave_file.rewind()
        self._is_stopped = True

    def play_background(self, loops=1, chunk_size=1024, delay=0):
        threading.Thread(
            target=Sound._background_thread,
            args=(self, loops, chunk_size, delay)
        ).start()

    @staticmethod
    def _background_thread(self, loops, chunk_size, delay):
        self.play(loops, chunk_size, delay)

    def stop(self):
        self._stop_play_flag = True
        while not self.stopped():
            time.sleep(0.5)
        self.stream.stop_stream()

    def stopped(self):
        return self._is_stopped


if __name__ == '__main__':
    sound1 = Sound("./exc.wav")
    sound1.play_background()
    sound2 = Sound("./fcm.wav")
    sound2.play()
