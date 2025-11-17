import flet as ft

from src.ui.components import PlaylistTabArea
from src.ui import AudioManager
from src.backend import PlaylistModel, TrackModel
from src.ui.ui_mapper import UiMapper

class PlaylistManager:
	def get_pressed_track(self, track_id: str) -> tuple[PlaylistModel, TrackModel] | None:
		for playlist in self.playlists:
			track = playlist.get_track(track_id)
			if track is not None:
				return (playlist, track)
		return None

	def get_playlist(self, playlist_id: str) -> PlaylistModel | None:
		for playlist in self.playlists:
			if playlist.id == playlist_id:
				return playlist
		return None

	def get_active_track(self) -> TrackModel | None:
		active_playlist = self.get_active_playlist()
		if active_playlist is None:
			return None

		return active_playlist.get_active_track()

	def set_active_playlist(self, playlist_uuid: str):
		self.active_playlist_id = playlist_uuid
  
	def get_active_playlist(self) -> PlaylistModel | None:
		return self.get_playlist(self.active_playlist_id)

	def __init__(self, playlists: list[PlaylistModel]):
		self.playlists = playlists
		self.playlist_tab_area = UiMapper.playlist_tab_area_from_models(playlists)
		
		self.active_playlist_id = playlists[0].id  
  
		self.audio_manager = AudioManager()
		self.event_bindings()
	
	def add_to_page(self, page: ft.Page):
		page.overlay.append(self.audio_manager.audio)
		page.add(self.playlist_tab_area)

	def play_next_track(self):
		active_playlist = self.get_active_playlist()
		if active_playlist is None:
			return
		
		next_track = active_playlist.move_to_next_track()
		if next_track is None:
			return
		
		self.audio_manager.play_track(next_track.file_path)

	def play_previous_track(self):
		active_playlist = self.get_active_playlist()
		if active_playlist is None:
			return
		
		prev_track = active_playlist.move_to_previous_track()
		if prev_track is None:
			return
		
		self.audio_manager.play_track(prev_track.file_path)
  
	def moved_to_diffrent_playlist(self):
		focused_playlist = self.playlist_tab_area.get_active_playlist()
		
		if focused_playlist is None:
			return False
		return focused_playlist.id != self.active_playlist_id

	def get_focused_playlist(self) -> PlaylistModel | None:
		playlist_ui = self.playlist_tab_area.get_active_playlist()
		if playlist_ui is None:
			return None

		return self.get_playlist(playlist_ui.id)

	def pause_current_playlist(self):
		active_playlist = self.get_active_playlist()
		if active_playlist is None:
			return

		self.audio_manager.pause()
		active_playlist.pause(self.audio_manager.audio.get_current_position() or 0)

	def on_play(self, id: str):
		if len(self.playlists) == 0:
			return
		current_playlist = self.get_active_playlist()
		focused_playlist = self.get_focused_playlist()
		next_track = None
		if focused_playlist is None:
			return

		if current_playlist is None:
			current_playlist = focused_playlist
			self.set_active_playlist(focused_playlist.id)
  
		if current_playlist.id != focused_playlist.id:
			self.pause_current_playlist()
			self.set_active_playlist(focused_playlist.id)
			current_playlist = focused_playlist
		
		if id is not None:
			next_track = current_playlist.get_track(id)
		else:
			next_track = current_playlist.resume()
   
		if next_track is not None:
			seek = next_track.played_time
			print(f"Seeking to {seek} seconds")
			self.audio_manager.play_track(next_track.file_path, seek)
			

	def event_bindings(self):
		ui = self.playlist_tab_area
		ui.on_play = self.on_play



  
		