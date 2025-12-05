import flet as ft
import flet_audio as fa
from enum import Enum


class AudioManager:
    def __init__(self):
        self.audio = ft.Audio(
            src="Saika.mp3",
            autoplay=False,
            volume=1.0,
            on_state_changed=self._on_state_change,
            on_loaded=self._on_loaded,
        )
        self.state = ft.AudioState.STOPPED
        self.on_sound_change = lambda e: None

        self._seek_position = 0
        self.added_to_page = False
        self.should_play = False

    def clear_audio(self):
        self.audio.release()
        self.state = ft.AudioState.STOPPED

    def play_track(self, track_url: str, seek: int = 0):
        self._seek_position = seek

        self.should_play = True

        if self.audio.src != track_url:
            self.audio.src = track_url
        else:
            print(f"Resuming audio for {track_url} at {seek} ms")
            self.audio.seek(seek)
            self.audio.resume()

        self.audio.update()

    def pause(self):
        self.audio.pause()

    def play(self):
        self.audio.play()

    def next_step(self):
        match self.state:
            case ft.AudioState.PLAYING:
                self.audio.pause()
            case ft.AudioState.PAUSED:
                self.audio.play()
            case _:
                pass

    def _on_state_change(self, e: ft.AudioStateChangeEvent):
        print(f"Audio state changed to: {e.state}")
        self.state = e.state
        self.on_sound_change(e)

    def _on_loaded(self, e: ft.ControlEvent):
        if self._seek_position > 0:
            self.audio.seek(self._seek_position)

        if self.added_to_page and self.should_play:
            print(f"Audio loaded {self.audio.src} seeking to {self._seek_position} ms")
            self.audio.resume()
            self.audio.update()
