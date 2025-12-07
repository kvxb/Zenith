"""Manages playlist and track state"""

from typing import Optional
from backend import PlaylistModel, TrackModel
from backend.music_manager import MusicManager


class PlaylistStateManager:
    def __init__(self, music_manager: MusicManager):
        self.music_manager = music_manager

        self.playlists = self.music_manager.get_all_playlists()

        self.active_playlist_id = self.playlists[0].id if self.playlists else ""
        self.last_playlist: Optional[PlaylistModel] = None
        self.last_track: Optional[TrackModel] = None
        self.copied_track: Optional[TrackModel] = None

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

    def move_track_to_playlist(
        self, source_playlist_id: str, track: TrackModel, target_playlist_id: str = ""
    ) -> bool:
        """Move a track to a different playlist"""
        source_playlist = (
            self.get_playlist(source_playlist_id) if source_playlist_id else None
        )
        target_playlist = (
            self.get_playlist(target_playlist_id) if target_playlist_id else None
        )

        if source_playlist_id and source_playlist is None:
            return False

        if target_playlist_id and target_playlist is None:
            return False

        # Remove from source playlist if it exists
        if source_playlist:
            source_playlist.remove_track(track)
            self.music_manager.remove_track_from_playlist(source_playlist.id, track.id)

        # Add to target playlist if it exists
        if target_playlist:
            if source_playlist and source_playlist.id == target_playlist.id:
                return False

            target_playlist.add_track(track)
            self.music_manager.add_track_to_playlist(
                target_playlist.id,
                track.artist,
                track.title,
                track.album,
                track.image_path,
            )

        return True

    def add_playlist(self, playlist: PlaylistModel):
        """Add a new playlist to the manager"""
        self.playlists.append(playlist)
        self.music_manager.add_playlist(playlist.name)

    def remove_playlist(self, playlist_id: str):
        """Remove a playlist from the manager by ID"""
        self.playlists = [pl for pl in self.playlists if pl.id != playlist_id]
        success = self.music_manager.delete_playlist(playlist_id)
        print(f"Removed playlist {playlist_id}: {success}")

    def rename_playlist(self, playlist_id: str, new_name: str) -> None:
        """Rename a playlist by ID"""
        print(f"Renaming playlist {playlist_id} to {new_name}")
        playlist = self.get_playlist(playlist_id)
        if playlist is None:
            return
        playlist.name = new_name

        self.music_manager.update_playlist_name(playlist_id, new_name)

    def create_empty_playlist(self) -> PlaylistModel | None:
        """Create and return a new empty playlist"""
        # import uuid

        # new_id = str(uuid.uuid4())
        # new_playlist = PlaylistModel(playlist_id=new_id, name="New Playlist", tracks=[])
        new_name = "New Playlist"
        id = self.music_manager.add_playlist(new_name)
        if id is None:
            raise Exception("Failed to create new playlist")
            return

        return PlaylistModel(playlist_id=id, name=new_name, tracks=[])

    def get_copied_track_copy(self) -> TrackModel | None:
        if self.copied_track is None:
            return None
        return self.copied_track.clone(self.copied_track)

    def toggle_loop(self, playlist_id: str) -> bool:
        """Toggle loop state for a playlist"""
        playlist = self.get_playlist(playlist_id)
        if playlist:
            playlist.is_looping = not playlist.is_looping
            return playlist.is_looping
        return False

    def toggle_track_loop(self, playlist_id: str, track_id: str) -> bool:
        """Toggle loop state for a track in a specific playlist"""
        playlist = self.get_playlist(playlist_id)
        if playlist is None:
            return False
            
        track = playlist.get_track(track_id)
        if track:
            track.is_looping = not track.is_looping
            return track.is_looping
        return False
