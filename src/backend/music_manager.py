from .db_manager import SimpleMusicDB
from .spotify_service import SpotifyService
from .track_download import SimpleDownloader
from .playlist_model import PlaylistModel
from .track_model import TrackModel
from . import config

"""
Public API for frontend:
- import_from_spotify()         Import all playlists from Spotify
- download_all_tracks()         Download all tracks from YouTube
- sync_all()                    Full Spotify import + YouTube download
- get_all_playlists()           Get all playlists as models
- update_playlist_name()        Rename a playlist
- delete_playlist()             Delete a playlist
- add_playlist()                Create new playlist
- add_track_to_playlist()       Add track (existing or download new)
- remove_track_from_playlist()  Remove track from playlist
- get_track_by_id()             Get single track info
- get_playlist_by_id()          Get single playlist info
- get_track_id()                Find track ID by artist/title
- get_playlist_id()             Find playlist ID by name
- get_all_playlist_ids()        Get all playlist names and IDs
- set_library_name()            Set library name
- get_library_name()            Get library name
- set_metadata()                Set any metadata
- get_metadata()                Get any metadata
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

    def set_library_name(self, name: str) -> bool:
        """Set the library name in metadata."""
        return self.db.set_metadata('LIBRARY_NAME', name)
    
    def get_library_name(self) -> str:
        """Get the library name from metadata."""
        return self.db.get_metadata('LIBRARY_NAME', 'My Library')
    
    def set_metadata(self, key: str, value: str) -> bool:
        """Set any metadata key-value pair."""
        return self.db.set_metadata(key, value)
    
    def get_metadata(self, key: str, default: str = "") -> str:
        """Get any metadata value by key."""
        return self.db.get_metadata(key, default)

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
            
            self.db.remove_track_from_playlist(playlist_id_int, track_id_int)
            print(f"✓ Removed track ID {track_id} from playlist ID {playlist_id}")
            return True
            
        except ValueError:
            print(f"Invalid ID format")
            return False
        except Exception as e:
            print(f"Error removing track from playlist: {e}")
            return False

    def add_track_to_playlist(self, playlist_id: str, artist: str = None, title: str = None, 
                          track_id: str = None, album: str = "", icon: str = None) -> str:
        """
        Add track to playlist. Two modes:
        1. Add existing track: pass track_id only
        2. Download new track: pass artist and title (will download from YouTube)
        
        Returns: New track ID if successful, empty string if failed
        """
        try:
            playlist_id_int = int(playlist_id)
            
            # Mode 1: Add existing track
            if track_id:
                track_id_int = int(track_id)
                track_info = self.get_track_by_id(track_id)
                if not track_info:
                    return ""
                
                # Check if file is already downloaded
                file_downloaded = bool(track_info["file_path"])
                
                new_track_id = self.db.add_track_to_playlist(
                    playlist_id=playlist_id_int,
                    title=track_info["title"],
                    artist=track_info["artist"],
                    album=track_info["album"],
                    duration=track_info["duration"],
                    icon=track_info.get("icon")
                )
                
                print(f"✓ Copied track '{track_info['title']}' to playlist")
                return str(new_track_id)
            
            # Mode 2: Download new track
            elif artist and title:
                # Add with 0 duration initially
                new_track_id = self.db.add_track_to_playlist(
                    playlist_id=playlist_id_int,
                    title=title,
                    artist=artist,
                    album=album,
                    duration=0,
                    icon=icon
                )
                
                print(f"✓ Added '{title}' by '{artist}' to database")
                
                # Download from YouTube
                success = self.downloader.download_track(new_track_id)
                
                if success:
                    return str(new_track_id)
                else:
                    return ""
            
            else:
                print("Error: Must provide either track_id OR (artist and title)")
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

    def get_track_by_id(self, track_id: str) -> dict:
        """Get detailed info for a single track."""
        try:
            track_id_int = int(track_id)
            conn = self.db._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, title, artist, album, duration, path_mp3, icon
                FROM tracks WHERE id = ?
            """, (track_id_int,))
            
            track = cursor.fetchone()
            if not track:
                return None
                
            return {
                "track_id": str(track[0]),
                "title": track[1],
                "artist": track[2],
                "album": track[3],
                "duration": track[4],
                "file_path": track[5] or "",
                "icon": track[6] or ""
            }
        except ValueError:
            print(f"Invalid track ID: {track_id}")
            return None
        except Exception as e:
            print(f"Error getting track: {e}")
            return None

    def get_playlist_by_id(self, playlist_id: str) -> PlaylistModel:
        """Get a single playlist with all its tracks."""
        try:
            playlist_id_int = int(playlist_id)
            conn = self.db._get_connection()
            cursor = conn.cursor()
            
            # Get playlist info
            cursor.execute("SELECT id, name FROM playlists WHERE id = ?", (playlist_id_int,))
            playlist = cursor.fetchone()
            if not playlist:
                return None
            
            playlist_id_db, playlist_name = playlist
            
            # Get tracks for this playlist
            cursor.execute("""
                SELECT t.id, t.title, t.artist, t.album, t.duration, t.path_mp3
                FROM tracks t
                JOIN playlist_tracks pt ON t.id = pt.track_id
                WHERE pt.playlist_id = ?
            """, (playlist_id_int,))
            
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

            return PlaylistModel(
                playlist_id=str(playlist_id_db),
                name=playlist_name,
                tracks=track_models
            )
            
        except ValueError:
            print(f"Invalid playlist ID: {playlist_id}")
            return None
        except Exception as e:
            print(f"Error getting playlist: {e}")
            return None

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

    def get_track_id(self, artist: str, title: str, album: str = "") -> Optional[str]:
        """Find track ID by artist, title, and optional album."""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        if album:
            cursor.execute(
                "SELECT id FROM tracks WHERE artist = ? AND title = ? AND album = ?",
                (artist, title, album)
            )
        else:
            cursor.execute(
                "SELECT id FROM tracks WHERE artist = ? AND title = ?",
                (artist, title)
            )
        
        result = cursor.fetchone()
        return str(result[0]) if result else None

    def get_playlist_id(self, name: str) -> Optional[str]:
    """Find playlist ID by name."""
    conn = self.db._get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM playlists WHERE name = ?", (name,))
    result = cursor.fetchone()
    
    return str(result[0]) if result else None

    def get_all_playlist_ids(self) -> dict:
        """Get all playlist names and their IDs."""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name FROM playlists")
        results = cursor.fetchall()
        
        return {name: str(pid) for pid, name in results}
