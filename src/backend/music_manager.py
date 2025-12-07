from .db_manager import SimpleMusicDB
from .spotify_service import SpotifyService
from .track_download import SimpleDownloader
from .playlist_model import PlaylistModel
from .track_model import TrackModel
from . import config

"""
    - import_from_spotify()         Import all playlists from Spotify
    - download_all_tracks()         Download all tracks from YouTube
    - sync_all()                    Full Spotify import + YouTube download
    - get_all_playlists()           Get all playlists as models
    - update_playlist_name()        Rename a playlist
    - delete_playlist()             Delete a playlist
    - add_playlist()                Create new playlist
    - add_track_to_playlist()       Add & download track to playlist
    - remove_track_from_playlist()  Remove track from playlist
"""

class MusicManager:
    """Main interface for Spotify import, YouTube download, and playlist management."""

    def __init__(self, db_path: str = "playlists_songs.db"):
        self.db = SimpleMusicDB()
        self.spotify_service = SpotifyService(
            client_id=config.CLIENT_ID, redirect_uri=config.REDIRECT_URI, db=self.db
        )
        self.downloader = SimpleDownloader(self.db)

    def import_from_spotify(self) -> list[PlaylistModel]:
        """Authenticate and import playlists from Spotify."""
        print("🔗 Authenticating with Spotify...")
        self.spotify_service.authenticate()

        print("📥 Importing playlists...")
        stats = self.spotify_service.import_all_playlists()
        print(
            f"✅ Imported {stats['tracks_imported']} tracks from {stats['playlists_imported']} playlists"
        )

        return self._get_all_playlists()

    def download_all_tracks(self) -> list[PlaylistModel]:
        """Download all tracks from YouTube to local files."""
        print("⬇️  Downloading all tracks from YouTube...")
        success, failed = self.downloader.download_all_tracks()
        print(f"✅ Downloaded {success} tracks, {failed} failed")

        return self._get_all_playlists()

    def update_playlist_name(self, playlist_id: str, new_name: str) -> bool:
        """Update playlist name. Returns True if successful."""
        try:
            playlist_id_int = int(playlist_id)
            return self.db.update_playlist_name(playlist_id_int, new_name)
        except ValueError:
            print(f"Invalid playlist ID: {playlist_id}")
            return False

    def sync_all(self) -> list[PlaylistModel]:
        """Complete sync: import from Spotify then download from YouTube."""
        print("🚀 Starting complete sync...")
        self.import_from_spotify()
        self.download_all_tracks()
        return self._get_all_playlists()

    def get_all_playlists(self) -> list[PlaylistModel]:
        """Get all playlists from database as model objects."""
        return self._get_all_playlists()

    def delete_playlist(self, playlist_id: str) -> bool:
        """Delete a playlist from the database."""
        try:
            playlist_id_int = int(playlist_id)
            # remove_playlist already exists in SimpleMusicDB
            self.db.remove_playlist(playlist_id_int)
            print(f"✓ Deleted playlist ID {playlist_id}")
            return True
        except ValueError:
            print(f"Invalid playlist ID: {playlist_id}")
            return False
        except Exception as e:
            print(f"Error deleting playlist: {e}")
            return False

    def remove_track_from_playlist(self, playlist_id: str, track_id: str) -> bool:
        """Remove a track from a specific playlist."""
        try:
            playlist_id_int = int(playlist_id)
            track_id_int = int(track_id)
            
            # Use the existing database method
            self.db.remove_track_from_playlist(playlist_id_int, track_id_int)
            print(f"✓ Removed track ID {track_id} from playlist ID {playlist_id}")
            return True
            
        except ValueError:
            print(f"Invalid ID format")
            return False
        except Exception as e:
            print(f"Error removing track from playlist: {e}")
            return False

    def add_track_to_playlist(self, playlist_id: str, artist: str, title: str, 
                              album: str = "", icon: str = None) -> str:
        try:
            playlist_id_int = int(playlist_id)
            
            track_id = self.db.add_track_to_playlist(
                playlist_id=playlist_id_int,
                title=title,
                artist=artist,
                album=album,
                duration=0,
                icon=icon
            )
            
            print(f"✓ Added '{title}' by '{artist}' to database")
            
            success = self.downloader.download_track(track_id)
            
            if success:
                return str(track_id)
            else:
                return ""
                
        except Exception as e:
            print(f"Error adding track: {e}")
            return ""

    def add_playlist(self, name: str, icon: str = None) -> str:
        """Create a new playlist in the database."""
        try:
            playlist_id = self.db.add_playlist(name, icon)
            return str(playlist_id)
        except Exception as e:
            print(f"Error creating playlist: {e}")
            return ""

    def _get_all_playlists(self) -> list[PlaylistModel]:
        """Convert database playlists and tracks to model objects."""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, name FROM playlists")
        playlists = cursor.fetchall()

        playlist_models = []

        for playlist_id, playlist_name in playlists:
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

            playlist_model = PlaylistModel(
                playlist_id=str(playlist_id), name=playlist_name, tracks=track_models
            )
            playlist_models.append(playlist_model)

        return playlist_models
