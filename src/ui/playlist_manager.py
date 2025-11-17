import flet as ft

from src.ui.components import PlaylistTabArea
from src.ui import AudioManager
from src.backend import PlaylistModel, TrackModel
from src.ui.ui_mapper import UiMapper

class PlaylistManager:
	def get_track(self, track_id: str) -> tuple[PlaylistModel, TrackModel] | None:
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

	def play_track_by_id(self, track_id: str):
		result = self.get_track(track_id)
		if result is None:
			return
		
		playlist, track = result
		self.set_active_playlist(playlist.id)
		playlist.set_active_track(playlist.tracks.index(track))
		self.audio_manager.play_track(track.file_path)	

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

	def on_play(self, id: str):
		if id is None:
			self.handle_play_button()
		else:
			self.play_track_by_id(id)

	def event_bindings(self):
		ui = self.playlist_tab_area
		ui.on_play = self.on_play



  
		