"""Handles UI events and updates"""

import flet as ft
from src.ui.components import PlaylistTabArea
from src.backend import PlaylistModel, TrackModel


class UIEventHandler:
    def __init__(self, playlist_tab_area: PlaylistTabArea):
        self.playlist_tab_area = playlist_tab_area

    def update_ui_on_play(
        self,
        previous_playlist: PlaylistModel | None,
        previous_track: TrackModel | None,
        active_playlist: PlaylistModel,
        is_playing: bool,
    ):
        """Update UI when playback state changes"""
        self.playlist_tab_area.update_ui_on_play(
            previous_playlist, previous_track, active_playlist, is_playing
        )

    def update_play_button(self, is_playing: bool):
        """Update the play/pause button icon"""
        self.playlist_tab_area.update_play_button_state(is_playing)

    def update_playback_position(self, position_ms: int):
        """Update the playback position slider"""
        self.playlist_tab_area.now_playing.update_playback_position(position_ms)

    def load_track_info(self, track: TrackModel):
        """Load track info into the now playing UI"""
        self.playlist_tab_area.now_playing.load_track_info(track)

    def on_reorder(self, playlist_id: str, old_idx: int | None, new_idx: int | None):
        """Handle playlist reorder"""
        playlist_ui = self.playlist_tab_area.get_playlist(playlist_id)
        if playlist_ui is not None:
            return playlist_ui.get_uuid_list()
        return []

    def get_focused_playlist_id(self) -> str | None:
        """Get the ID of the currently focused playlist in the UI"""
        playlist_ui = self.playlist_tab_area.get_active_playlist()
        if playlist_ui is None:
            return None
        return playlist_ui.id
