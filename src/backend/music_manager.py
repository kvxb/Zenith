from .db_manager import SimpleMusicDB
from .spotify_service import SpotifyService
from .track_download import SimpleDownloader
from .playlist_model import PlaylistModel
from .track_model import TrackModel
from . import config


class MusicManager:
    """High-level interface for the entire music system."""

    def __init__(self, db_path: str = "playlists_songs.db"):
        self.db = SimpleMusicDB()
        self.spotify_service = SpotifyService(
            client_id=config.CLIENT_ID, redirect_uri=config.REDIRECT_URI, db=self.db
        )
        self.downloader = SimpleDownloader(self.db)

    def import_from_spotify(self) -> list[PlaylistModel]:
        """
        Import from Spotify and return PlaylistModel objects.
        Returns: List of PlaylistModel objects (without file paths yet)
        """
        print("🔗 Authenticating with Spotify...")
        self.spotify_service.authenticate()

        print("📥 Importing playlists...")
        stats = self.spotify_service.import_all_playlists()
        print(
            f"✅ Imported {stats['tracks_imported']} tracks from {stats['playlists_imported']} playlists"
        )

        return self._get_all_playlists()  # ← Returns models!

    def download_all_tracks(self) -> list[PlaylistModel]:
        """
        Download all tracks and return updated PlaylistModel objects.
        Returns: List of PlaylistModel objects (with file paths)
        """
        print("⬇️  Downloading all tracks from YouTube...")
        success, failed = self.downloader.download_all_tracks()
        print(f"✅ Downloaded {success} tracks, {failed} failed")

        return self._get_all_playlists()  # ← Returns models!

    def sync_all(self) -> list[PlaylistModel]:
        """
        Complete sync: Spotify import → YouTube download.
        Returns: List of PlaylistModel objects (ready to play)
        """
        print("🚀 Starting complete sync...")
        self.import_from_spotify()
        self.download_all_tracks()
        return self._get_all_playlists()  # ← Returns models!

    def get_all_playlists(self) -> list[PlaylistModel]:
        """
        Get current database content as PlaylistModel objects.
        Returns: List of PlaylistModel objects
        """
        return self._get_all_playlists()

    def _get_all_playlists(self) -> list[PlaylistModel]:
        """
        Internal method to convert database to PlaylistModel objects.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        # Get all playlists
        cursor.execute("SELECT id, name FROM playlists")
        playlists = cursor.fetchall()

        playlist_models = []

        for playlist_id, playlist_name in playlists:
            # Get all tracks for this playlist
            cursor.execute(
                """
                SELECT t.id, t.title, t.artist, t.album, t.duration, t.path_mp3
                FROM tracks t
                JOIN playlist_tracks pt ON t.id = pt.track_id
                WHERE pt.playlist_id = ?
            """,
                (playlist_id,),
            )

            tracks = cursor.fetchall()

            # Convert to TrackModel objects
            track_models = []
            for track_id, title, artist, album, duration, path_mp3 in tracks:
                track_model = TrackModel(
                    track_id=str(track_id),
                    title=title,
                    artist=artist,
                    album=album or "",
                    duration=duration,
                    file_path=path_mp3 or "",
                )
                track_models.append(track_model)

            # Create PlaylistModel
            playlist_model = PlaylistModel(
                playlist_id=str(playlist_id), name=playlist_name, tracks=track_models
            )
            playlist_models.append(playlist_model)

        return playlist_models
