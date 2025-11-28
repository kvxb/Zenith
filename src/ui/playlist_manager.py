import flet as ft

from src.ui.components import PlaylistTabArea
from src.ui import AudioManager
from src.backend import PlaylistModel, TrackModel
from src.ui.ui_mapper import UiMapper


class PlaylistManager:
    def get_pressed_track(
        self, track_id: str
    ) -> tuple[PlaylistModel, TrackModel] | None:
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
        self.is_playing = False
        self.event_bindings()

    def add_to_page(self, page: ft.Page):
        self.audio_manager.added_to_page = True
        page.overlay.append(self.audio_manager.audio)
        page.add(self.playlist_tab_area)

    def play_next_track(self):
        active_playlist = self.get_active_playlist()
        if active_playlist is None:
            return

        if active_playlist.move_to_next_track() is None:
            print("No next track to play")
            return

        self.play()

    def play_previous_track(self):
        active_playlist = self.get_active_playlist()
        if active_playlist is None:
            return

        if active_playlist.move_to_previous_track() is None:
            print("No previous track to play")
            return

        self.play()

    def get_focused_playlist(self) -> PlaylistModel | None:
        playlist_ui = self.playlist_tab_area.get_active_playlist()
        if playlist_ui is None:
            return None

        return self.get_playlist(playlist_ui.id)

    def _check_for_playlist_move(self):
        focused_playlist = self.get_focused_playlist()

        if self.get_active_playlist() != focused_playlist:
            self.pause()

            if focused_playlist is not None:
                self.set_active_playlist(focused_playlist.id)

    def on_play(self, id: str):
        if len(self.playlists) == 0:
            return

        self._check_for_playlist_move()
        current_playlist = self.get_active_playlist()
        current_track = self.get_active_track()

        if current_playlist is None or current_track is None:
            return

        if id is None:
            if self.is_playing:
                self.pause()
            else:
                current_track = current_playlist.resume()
                self.play()
            return

        if id == current_track.id:
            if self.is_playing:
                self.pause()
            else:
                self.play()
            return

        track = current_playlist.set_active_track(id)
        if track is not None:
            print(
                f"Playing track: {track.title} from playlist: {current_playlist.name}"
            )
            self.play()

    def on_sound_change(self, e: ft.AudioStateChangeEvent):
        if e.state == ft.AudioState.COMPLETED:
            track = self.get_active_track()
            if track is not None:
                track.played_time = 0

            print("Track completed, moving to next track")
            self.play_next_track()

    def event_bindings(self):
        ui = self.playlist_tab_area
        ui.on_play = self.on_play
        self.audio_manager.on_sound_change = self.on_sound_change

    def pause(self):
        active_playlist = self.get_active_playlist()
        if active_playlist is None:
            return

        self.audio_manager.pause()
        active_playlist.pause(self.audio_manager.audio.get_current_position() or 0)

        self.is_playing = False
        self.playlist_tab_area.update_ui_on_play(active_playlist, self.is_playing)

    def play(self):
        current_playlist = self.get_active_playlist()
        current_track = self.get_active_track()
        if current_track is None or current_playlist is None:
            return

        self.is_playing = True

        seek = current_track.played_time
        self.audio_manager.play_track(current_track.file_path, seek)

        self.playlist_tab_area.update_ui_on_play(current_playlist, self.is_playing)
