"""Manages playlist and track state"""

from typing import Optional
from src.backend import PlaylistModel, TrackModel


class PlaylistStateManager:
    def __init__(self, playlists: list[PlaylistModel]):
        self.playlists = playlists
        self.active_playlist_id = playlists[0].id if playlists else ""
        self.last_playlist: Optional[PlaylistModel] = None
        self.last_track: Optional[TrackModel] = None

    def get_playlist(self, playlist_id: str) -> Optional[PlaylistModel]:
        """Get playlist by ID"""
        for playlist in self.playlists:
            if playlist.id == playlist_id:
                return playlist
        return None

    def get_active_playlist(self) -> Optional[PlaylistModel]:
        """Get the currently active playlist"""
        return self.get_playlist(self.active_playlist_id)

    def set_active_playlist(self, playlist_id: str):
        """Set the active playlist"""
        self.active_playlist_id = playlist_id
        return self.get_active_playlist()

    def get_active_track(self) -> Optional[TrackModel]:
        """Get the currently active track"""
        active_playlist = self.get_active_playlist()
        if active_playlist is None:
            return None
        return active_playlist.get_active_track()

    def get_track_from_playlists(
        self, track_id: str
    ) -> Optional[tuple[PlaylistModel, TrackModel]]:
        """Find a track across all playlists"""
        for playlist in self.playlists:
            track = playlist.get_track(track_id)
            if track is not None:
                return (playlist, track)
        return None

    def move_to_next_track(self) -> Optional[TrackModel]:
        """Move to next track in active playlist"""
        active_playlist = self.get_active_playlist()
        if active_playlist is None:
            return None
        return active_playlist.move_to_next_track()

    def move_to_previous_track(self) -> Optional[TrackModel]:
        """Move to previous track in active playlist"""
        active_playlist = self.get_active_playlist()
        if active_playlist is None:
            return None
        return active_playlist.move_to_previous_track()

    def update_last_state(
        self, playlist: Optional[PlaylistModel], track: Optional[TrackModel]
    ):
        """Update the last known playlist and track"""
        self.last_playlist = playlist
        self.last_track = track

    def get_track_of_name(
        self, track_name: str
    ) -> Optional[tuple[PlaylistModel, TrackModel]]:
        """Find a track by name across all playlists"""
        for playlist in self.playlists:
            for track in playlist.tracks():
                if track.title == track_name:
                    return (playlist, track)
        return None

    def move_track_to_playlist(self, track_id: str, target_playlist_id: str) -> bool:
        """Move a track to a different playlist"""
        source = self.get_track_from_playlists(track_id)
        target_playlist = self.get_playlist(target_playlist_id)

        if source is None or target_playlist is None:
            return False

        source_playlist, track = source

        if source_playlist.id == target_playlist.id:
            return False

        source_playlist.remove_track(track)
        target_playlist.add_track(track)
        return True
