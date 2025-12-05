"""Orchestrates playlist management - simplified version using components"""

import flet as ft
from src.ui.components import PlaylistTabArea
from src.ui import AudioManager
from src.ui.playback_controller import PlaybackController
from src.ui.playlist_state_manager import PlaylistStateManager
from src.ui.ui_event_handler import UIEventHandler
from src.backend import PlaylistModel, TrackModel
from src.ui.ui_mapper import UiMapper


class PlaylistManager:
    def __init__(self, playlists: list[PlaylistModel]):
        # Initialize components
        self.state_manager = PlaylistStateManager(playlists)
        self.audio_manager = AudioManager()
        self.playback_controller = PlaybackController(self.audio_manager)
        self.playlist_tab_area = UiMapper.playlist_tab_area_from_models(playlists)
        self.ui_handler = UIEventHandler(self.playlist_tab_area)

        self.event_bindings()

    def add_to_page(self, page: ft.Page):
        self.audio_manager.added_to_page = True
        self.page = page
        page.overlay.append(self.audio_manager.audio)
        page.add(self.playlist_tab_area)

        page.on_connect = lambda e: self.reconnect()
        page.on_disconnect = lambda e: self.on_disconnect()

    def on_disconnect(self):
        print("Disconnecting - cleaning up audio")
        if self.playback_controller.is_playing:
            self.pause(update_ui=False)
        self.audio_manager.should_play = False

    def reconnect(self):
        print("Reconnecting - recreating audio manager")
        active_playlist = self.state_manager.get_active_playlist()

        if self.playback_controller.is_playing:
            self.playback_controller.is_playing = False

        # Create new audio manager
        self.audio_manager = AudioManager()
        self.audio_manager.added_to_page = True
        self.audio_manager.should_play = False
        self.playback_controller.audio_manager = self.audio_manager

        # Clear and re-add to overlay
        self.page.overlay.clear()
        self.page.overlay.append(self.audio_manager.audio)

        # Rebind all events
        self.event_bindings()

        # Update UI to reflect stopped state
        if active_playlist is not None:
            self.ui_handler.update_ui_on_play(
                None, None, active_playlist, self.playback_controller.is_playing
            )

        self.page.update()

    def play_next_track(self):
        """Play the next track in the playlist"""
        if self.playback_controller.is_playing:
            self.pause(update_ui=False)

        active_playlist = self.state_manager.get_active_playlist()
        track = self.state_manager.get_active_track()

        if active_playlist is None or track is None:
            return

        track.played_time = 0

        if self.state_manager.move_to_next_track() is None:
            print("No next track to play")
            return

        self.state_manager.update_last_state(active_playlist, track)
        self.play()

    def play_previous_track(self):
        """Play the previous track in the playlist"""
        if self.playback_controller.is_playing:
            self.pause(update_ui=False)

        active_playlist = self.state_manager.get_active_playlist()
        track = self.state_manager.get_active_track()

        if active_playlist is None or track is None:
            return
        track.played_time = 0

        if self.state_manager.move_to_previous_track() is None:
            print("No previous track to play")
            return

        self.state_manager.update_last_state(active_playlist, track)
        self.play()

    def _check_for_playlist_move(self):
        """Check if user switched to a different playlist"""
        focused_playlist_id = self.ui_handler.get_focused_playlist_id()
        current_playlist = self.state_manager.get_active_playlist()

        if current_playlist and focused_playlist_id != current_playlist.id:
            self.pause(update_ui=False)

            self.state_manager.update_last_state(
                current_playlist,
                current_playlist.get_active_track() if current_playlist else None,
            )

            if focused_playlist_id is not None:
                self.state_manager.set_active_playlist(focused_playlist_id)

    def on_play(self, id: str):
        """Handle play button or track click"""
        if len(self.state_manager.playlists) == 0:
            return

        self._check_for_playlist_move()
        current_playlist = self.state_manager.get_active_playlist()
        current_track = self.state_manager.get_active_track()

        if current_playlist is None or current_track is None:
            return

        if id is None:
            # Play button clicked
            if self.playback_controller.is_playing:
                self.pause()
            else:
                current_playlist.resume()
                self.play()
            return

        if id == current_track.id:
            # Same track clicked - toggle play/pause
            if self.playback_controller.is_playing:
                self.pause()
            else:
                self.play()
            return

        # Different track clicked - switch and play
        self.state_manager.update_last_state(current_playlist, current_track)
        track = current_playlist.set_active_track(id)
        if track is not None:
            self.play()

    def on_sound_change(self, e: ft.AudioStateChangeEvent):
        """Handle audio state changes"""
        if e.state == ft.AudioState.COMPLETED:
            track = self.state_manager.get_active_track()
            if track is not None:
                track.played_time = 0

            print("Track completed, moving to next track")
            self.play_next_track()

    def on_reorder(self, id: str, old_idx: int | None, new_idx: int | None):
        """Handle playlist reorder"""
        playlist = self.state_manager.get_playlist(id)
        if playlist is None:
            return

        playlist.track_order_list = self.ui_handler.on_reorder(id, old_idx, new_idx)
        self.playlist_tab_area.update()

    def event_bindings(self):
        """Bind all UI events to handlers"""
        tab_area = self.playlist_tab_area
        now_playing = tab_area.now_playing
        audio = self.audio_manager.audio

        tab_area.on_play = self.on_play
        tab_area.on_reorder = self.on_reorder

        self.audio_manager.on_sound_change = self.on_sound_change
        audio.on_position_changed = lambda e: self.ui_handler.update_playback_position(
            int(e.position)
        )
        audio.on_seek_complete = lambda e: now_playing.seek_complete()

        now_playing.on_slider_end = self._on_slider_seek
        now_playing.play_pause_btn.on_click = lambda e: (
            self.pause() if self.playback_controller.is_playing else self.play()
        )

        now_playing.next_btn.on_click = lambda e: self.play_next_track()
        now_playing.previous_btn.on_click = lambda e: self.play_previous_track()

    def _on_slider_seek(self, position):
        """Handle seek slider changes"""
        self.playback_controller.seek(position)
        track = self.state_manager.get_active_track()
        if track is not None:
            track.played_time = int(position)

    def pause(self, update_ui: bool = True):
        """Pause playback and optionally update UI"""
        active_playlist = self.state_manager.get_active_playlist()
        if active_playlist is None:
            return

        current_pos = self.audio_manager.audio.get_current_position() or 0
        self.playback_controller.pause(current_pos)
        active_playlist.pause(current_pos)

        if update_ui:
            self.ui_handler.update_ui_on_play(
                None, None, active_playlist, self.playback_controller.is_playing
            )

    def play(self):
        """Start playback and update UI"""
        current_playlist = self.state_manager.get_active_playlist()
        current_track = self.state_manager.get_active_track()

        if current_track is None or current_playlist is None:
            return

        previous_playlist = self.state_manager.last_playlist
        previous_track = self.state_manager.last_track

        seek = current_track.played_time
        self.playback_controller.play(current_track, seek)

        self.state_manager.update_last_state(current_playlist, current_track)

        self.ui_handler.update_ui_on_play(
            previous_playlist,
            previous_track,
            current_playlist,
            self.playback_controller.is_playing,
        )
