import flet_audio as fa
from enum import Enum


class AudioManager:
	def __init__(self):
		self.audio = fa.Audio()
		self.state = fa.AudioState.DISPOSED
		self.on_sound_change = lambda e: None
  
		self.audio.on_state_changed = self.on_sound_change

	def clear_audio(self):
		self.audio.release()
		self.state = fa.AudioState.DISPOSED

	def play_track(self, track_url: str):
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
  
	def _on_state_change(self, e: fa.AudioStateChangeEvent):
		self.state = e.state
		self.on_sound_change(e)