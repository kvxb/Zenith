"""Orchestrates playlist management - simplified version using components"""

import flet as ft
from src.ui.components import PlaylistTabArea
from src.ui import AudioManager
from src.ui.playback_controller import PlaybackController
from src.ui.playlist_state_manager import PlaylistStateManager
from src.backend import PlaylistModel, TrackModel
from src.ui.ui_mapper import UiMapper


class PlaylistManager:
    def __init__(self, playlists: list[PlaylistModel]):
        # Initialize components
        self.state_manager = PlaylistStateManager(playlists)
        self.audio_manager = AudioManager()
        self.playback_controller = PlaybackController(self.audio_manager)
        self.tab_area = UiMapper.playlist_tab_area_from_models(playlists)

        self.event_bindings()

    def add_to_page(self, page: ft.Page):
        self.audio_manager.added_to_page = True
        self.page = page
        page.overlay.append(self.audio_manager.audio)
        page.add(self.tab_area)

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
            self.tab_area.update_ui_on_play(
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
        active_playlist_ui = self.tab_area.get_active_playlist()
        focused_playlist_id = active_playlist_ui.id if active_playlist_ui else None
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

        if current_playlist is None:
            return

        current_track = self.state_manager.get_active_track()

        # If no active track, try to activate the first one
        if current_track is None:
            current_track = current_playlist.set_active_track("first")
            if current_track is None:
                # Playlist is empty
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

        playlist_ui = self.tab_area.get_playlist(id)
        if playlist_ui is not None:
            playlist.track_order_list = playlist_ui.get_uuid_list()
        self.tab_area.update()

    def event_bindings(self):
        """Bind all UI events to handlers"""
        tab_area = self.tab_area
        now_playing = tab_area.now_playing
        audio = self.audio_manager.audio

        tab_area.on_play = self.on_play
        tab_area.on_reorder = self.on_reorder
        tab_area.on_drop = self.on_track_drop

        self.audio_manager.on_sound_change = self.on_sound_change
        audio.on_position_changed = lambda e: now_playing.update_playback_position(
            int(e.position)
        )
        audio.on_seek_complete = lambda e: now_playing.seek_complete()

        now_playing.on_slider_end = self._on_slider_seek
        now_playing.play_pause_btn.on_click = lambda e: (
            self.pause() if self.playback_controller.is_playing else self.play()
        )

        now_playing.next_btn.on_click = lambda e: self.play_next_track()
        now_playing.previous_btn.on_click = lambda e: self.play_previous_track()

    def on_track_drop(self, playlist_id: str, track_id: str):
        """Handle track drop on playlist card"""
        print(f"Track {track_id} dropped on playlist {playlist_id}")

        # Get track info before moving
        track_info = self.state_manager.get_track_from_playlists(track_id)
        if track_info is None:
            print(f"Track {track_id} not found")
            return

        source_playlist, track = track_info

        # Check if the moved track is currently playing
        is_active_track = self.state_manager.get_active_track() == track

        res = self.state_manager.move_track_to_playlist(track_id, playlist_id)

        if not res:
            print(f"Failed to move track {track_id} to playlist {playlist_id}")
            return

        # Update UI: remove from source, add to target
        source_ui = self.tab_area.get_playlist(source_playlist.id)
        if source_ui is not None:
            source_ui.remove_track_item(track_id)

        target_ui = self.tab_area.get_playlist(playlist_id)
        if target_ui is not None:
            target_ui.add_track_item(UiMapper.play_list_item_from_track_model(track, 0))

        # Handle active track being moved
        if is_active_track:
            self.pause(update_ui=False)
            target_playlist = self.state_manager.set_active_playlist(playlist_id)

            if target_playlist is not None:
                target_playlist.set_active_track(track_id)
                self.tab_area.update_ui_on_play(
                    None, None, target_playlist, self.playback_controller.is_playing
                )

        self.tab_area.update()

    def remove_track(self, playlist_id: str, track_id: str):
        # """Remove a track from a playlist"""
        # print(f"Removing track {track_id} from playlist {playlist_id}")

        # playlist = self.state_manager.get_playlist(playlist_id)
        # if playlist is None:
        #     print(f"Playlist {playlist_id} not found")
        #     return

        # track = playlist.get_track(track_id)
        # if track is None:
        #     print(f"Track {track_id} not found in playlist")
        #     return

        # is_active_track = self.state_manager.get_active_track() == track

        # # Handle active track being removed - move to next track first
        # if is_active_track:
        #     self.pause(update_ui=False)
        #     next_track = self.state_manager.move_to_next_track()

        #     if next_track == track:

        # # Remove from backend
        # playlist.remove_track(track)

        # # Update UI
        # playlist_ui = self.tab_area.get_playlist(playlist_id)
        # if playlist_ui is not None:
        #     playlist_ui.remove_track_item(track_id)

        # # Update playback state after removal
        # if is_active_track:
        #     if next_track is None:
        #         # No next track, clear the now playing UI
        #         self.tab_area.update_ui_on_play(
        #             None, None, playlist, False
        #         )
        #     else:
        #         # Play next track
        #         self.play()

        self.tab_area.update()

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
            self.tab_area.update_ui_on_play(
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

        self.tab_area.update_ui_on_play(
            previous_playlist,
            previous_track,
            current_playlist,
            self.playback_controller.is_playing,
        )

    def on_search(self, query: str):
        """Handle search queries"""
        result = self.state_manager.get_track_of_name(query)
