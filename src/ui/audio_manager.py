import flet_audio as fa
from enum import Enum


class AudioManager:
	def __init__(self):
		self.audio = fa.Audio(src="gorosei.mp3", autoplay=False, volume=1.0, on_state_changed=self._on_state_change)
		self.state = fa.AudioState.STOPPED
		self.on_sound_change = lambda e: None
  
	def clear_audio(self):
		self.audio.release()
		self.state = fa.AudioState.DISPOSED

	def play_track(self, track_url: str):
		print(f"Requested to play track: {track_url} in state {self.state} and src {self.audio.src}")
		if track_url is None:
			self.play()
			return

		if self.state == fa.AudioState.PLAYING:
			if self.audio.src == track_url:
				self.audio.seek(0)
				return
		
		self.audio.src = track_url
		self.audio.play()

	def pause(self):
		self.audio.pause()
	
	def play(self):
		self.audio.play()
	
	def next_step(self):
		match self.state:
			case fa.AudioState.PLAYING:
				self.audio.pause()
			case fa.AudioState.PAUSED:
				self.audio.play()
			case _:
				pass	
	def _on_state_change(self, e: fa.AudioStateChangeEvent):
		print(f"Audio state changed to: {e.state}")
		self.state = e.state
		self.on_sound_change(e)

