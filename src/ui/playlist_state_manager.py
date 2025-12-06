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
        if self.playlists is None:
            return None

        if playlist_id == "first" and len(self.playlists) > 0:
            self.active_playlist_id = self.playlists[0].id
            return self.get_active_playlist()

        if playlist_id == "last" and len(self.playlists) > 0:
            self.active_playlist_id = self.playlists[-1].id
            return self.get_active_playlist()

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

    def get_plalist_track_tuple(
        self, playlist_id: str, track_id: str
    ) -> Optional[tuple[PlaylistModel, TrackModel]]:
        """Get a (playlist, track) tuple by their IDs"""
        playlist = self.get_playlist(playlist_id)
        if playlist is None:
            return None

        track = playlist.get_track(track_id)
        if track is None:
            return None

        return (playlist, track)

    def move_track_to_playlist(self, track_id: str, target_playlist_id: str) -> bool:
        """Move a track to a different playlist"""
        source = self.get_track_from_playlists(track_id)
        target_playlist = self.get_playlist(target_playlist_id)

        if source is None:
            return False

        source_playlist, track = source
        if target_playlist is None:
            source_playlist.remove_track(track)
            return True

        if source_playlist.id == target_playlist.id:
            return False

        source_playlist.remove_track(track)
        target_playlist.add_track(track)
        return True

    def add_playlist(self, playlist: PlaylistModel):
        """Add a new playlist to the manager"""
        self.playlists.append(playlist)

    def remove_playlist(self, playlist_id: str):
        """Remove a playlist from the manager by ID"""
        self.playlists = [pl for pl in self.playlists if pl.id != playlist_id]

    def rename_playlist(self, playlist_id: str, new_name: str) -> None:
        """Rename a playlist by ID"""
        print(f"Renaming playlist {playlist_id} to {new_name}")
        playlist = self.get_playlist(playlist_id)
        if playlist is None:
            return
        playlist.name = new_name

    def create_empty_playlist(self) -> PlaylistModel:
        """Create and return a new empty playlist"""
        import uuid

        new_id = str(uuid.uuid4())
        new_playlist = PlaylistModel(playlist_id=new_id, name="New Playlist", tracks=[])
        return new_playlist
