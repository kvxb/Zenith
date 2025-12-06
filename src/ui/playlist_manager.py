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

    def on_play(self, playlist_id: str, track_id: str | None):
        """Handle play button or track click"""
        if len(self.state_manager.playlists) == 0:
            return
        playlist = self.state_manager.get_playlist(playlist_id)
        current_playlist = self.state_manager.get_active_playlist()

        if playlist is None:
            return

        if current_playlist == playlist:
            # Same playlist
            if track_id is not None:
                self.state_manager.update_last_state(
                    playlist, playlist.get_active_track()
                )
                playlist.set_active_track(track_id)
                self.play()
            else:
                self.pause() if self.playback_controller.is_playing else self.play()

        else:
            # Different playlist
            self.pause(update_ui=False)
            self.state_manager.set_active_playlist(playlist_id)

            self.state_manager.update_last_state(
                current_playlist,
                current_playlist.get_active_track() if current_playlist else None,
            )
            playlist.set_active_track(track_id if track_id else "first")

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
        tab_area.on_focus_change = lambda playlist_id: self.tab_area.toggle_play_button(
            playlist_id == self.state_manager.active_playlist_id
            and self.playback_controller.is_playing
        )
        tab_area.on_rename_playlist = lambda playlist_id, new_name: (
            self.state_manager.rename_playlist(
                playlist_id, new_name if new_name != "" else "Untitled Playlist"
            )
        )
        tab_area.on_add_empty_playlist = lambda: self.add_playlist()

        tab_area.on_delete_playlist = self.remove_playlist
        tab_area.on_delete_track = self.on_delete_track
        tab_area.on_copy_track = self.on_copy_track
        tab_area.on_paste_track = self.on_paste_track

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

        track_info = self.state_manager.get_track_from_playlists(track_id)
        if track_info is None:
            print(f"Track {track_id} not found")
            return

        source_playlist, track = track_info
        was_active = self.state_manager.get_active_track() == track

        if source_playlist.id == playlist_id:
            print("Track dropped on the same playlist, no action taken")
            return

        target_playlist = self.state_manager.get_playlist(playlist_id)
        if target_playlist is None:
            print(f"Target playlist {playlist_id} not found")
            return

        self.remove_track(source_playlist.id, track.id)
        self.add_track(playlist_id, track)

        if was_active:
            print("Moved track was active, updating playback state")
            self.state_manager.set_active_playlist(playlist_id)
            target_playlist.set_active_track(track.id)
            self.play()

        self.tab_area.update()

    def remove_track(self, playlist_id: str, track_id: str):
        """Remove a track from a playlist"""
        print(f"Removing track {track_id} from playlist {playlist_id}")

        track_info = self.state_manager.get_plalist_track_tuple(playlist_id, track_id)
        if track_info is None:
            print(f"Track {track_id} not found in playlist {playlist_id}")
            return
        playlist, track = track_info

        if self.state_manager.get_active_track() == track:
            if playlist.move_to_next_track() == track:
                playlist.set_active_track("first")

            self.forget()

        playlist.remove_track(track)
        playlist_ui = self.tab_area.get_playlist(playlist_id)
        if playlist_ui is not None:
            playlist_ui.remove_track_item(track_id)

        self.tab_area.update()

    def add_track(self, playlist_id: str, track: TrackModel):
        """Add a track to a playlist"""
        print(f"Adding track {track.id} to playlist {playlist_id}")

        playlist = self.state_manager.get_playlist(playlist_id)
        if playlist is None:
            print(f"Playlist {playlist_id} not found")
            return

        playlist.add_track(track)
        playlit_ui = self.tab_area.get_playlist(playlist_id)
        if playlit_ui is not None:
            item_ui = UiMapper.play_list_item_from_track_model(track, 0)
            playlit_ui.add_track_item(item_ui)

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

    def forget(self):
        """Clear playback state and hide now playing UI"""
        if self.playback_controller.is_playing:
            self.pause(update_ui=False)

        self.state_manager.update_last_state(None, None)
        self.tab_area.now_playing.toggle_show_hide(False)

        # Unhighlight all playlist cards
        for playlist in self.state_manager.playlists:
            card_ui = self.tab_area.get_playslist_card(playlist.id)
            if card_ui is not None:
                card_ui.highlight(False)

    def remove_playlist(self, playlist_id: str):
        """Remove a playlist from the manager"""
        print(f"Removing playlist {playlist_id}")

        playlist = self.state_manager.get_playlist(playlist_id)
        if playlist is None:
            print(f"Playlist {playlist_id} not found")
            return

        def on_confirm():
            active_playlist = self.state_manager.get_active_playlist()

            if active_playlist == playlist:
                self.forget()

            self.tab_area.remove_playlist(playlist_id)
            self.state_manager.remove_playlist(playlist_id)

        self.tab_area.confirm_delete_playlist(playlist, on_confirm)

    def add_playlist(self, playlist: PlaylistModel | None = None):
        """Add a new playlist to the manager"""
        if playlist is None:
            playlist = self.state_manager.create_empty_playlist()
            if playlist is None:
                return

        print(f"Adding new playlist {playlist.name}")

        self.state_manager.add_playlist(playlist)
        card_ui = UiMapper.playlist_card_from_model(playlist)
        playlist_ui = UiMapper.playlist_from_model(playlist)

        self.tab_area.add_playlist(card_ui, playlist_ui)
        self.tab_area.toggle_body_header(True)

    def on_delete_track(self, playlist_id: str, track_id: str):
        """Delete a track from a playlist"""
        print(f"Deleting track {track_id} from playlist {playlist_id}")
        track_info = self.state_manager.get_plalist_track_tuple(playlist_id, track_id)
        if track_info is None:
            return

        playlist, track = track_info

        def on_confirm():
            # Remove from backend
            playlist.remove_track(track)

            # Remove from UI
            playlist_ui = self.tab_area.get_playlist(playlist_id)
            if playlist_ui is not None:
                playlist_ui.remove_track_item(track_id)

        self.tab_area.confirm_delete_track(track, on_confirm)

    def on_copy_track(self, playlist_id: str, track_id: str):
        """Copy a track to clipboard"""
        print(f"Copying track {track_id} from playlist {playlist_id}")

        track_info = self.state_manager.get_plalist_track_tuple(playlist_id, track_id)
        if track_info is None:
            return

        playlist, track = track_info
        self.state_manager.copied_track = track
        self.tab_area.enable_paste_track(True)
        self.tab_area.update()

    def on_paste_track(self, playlist_id: str):
        """Paste copied track to playlist"""
        print(f"Pasting track to playlist {playlist_id}")

        track_copy = self.state_manager.get_copied_track_copy()
        if track_copy is None:
            print("No track to paste")
            return

        self.add_track(playlist_id, track_copy)

        self.tab_area.update()
