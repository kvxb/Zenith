import flet as ft
import flet_audio as fa
from enum import Enum


class AudioManager:
	def __init__(self):
		self.audio = ft.Audio(
      		src="gorosei.mp3", 
        	autoplay=False, 
         	volume=1.0,
          	on_state_changed=self._on_state_change,
           	on_loaded= self._on_loaded,
        )
		self.state = ft.AudioState.STOPPED
		self.on_sound_change = lambda e: None
  
		self._seek_position = 0
  
	def clear_audio(self):
		self.audio.release()
		self.state = ft.AudioState.STOPPED

	def play_track(self, track_url: str, seek: int = 0):
		self.audio.src = track_url
		self._seek_position = seek
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
		print(f"Audio loaded {self.audio.src} playing at {self.audio.get_current_position()} seconds")
		self.audio.seek(self._seek_position)
		self.audio.resume()
		

