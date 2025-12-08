from typing import List, Optional, Dict
import sqlite3
import threading
import os
from pathlib import Path


class SimpleMusicDB:
    """Thread-safe SQLite database for music tracks and playlists."""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to the SQLite database file. 
                    If None, uses "playlists_songs.db" in current directory.
        """
        if db_path is None:
            self.db_path = "playlists_songs.db"
        else:
            self.db_path = db_path
            
        # Lock pentru a preveni accesul concurent la database
        self.db_lock = threading.Lock()
        self._ensure_tables_exist()
        
        print(f"🗃️  Database initialized: {self.db_path}")

    def _ensure_tables_exist(self):
        """Create database tables if they don't exist."""
        with self.db_lock:
            conn = sqlite3.connect(self.db_path)
            self._create_tables(conn)
            conn.close()

    def _create_tables(self, conn):
        """Create tracks, playlists, and junction tables."""
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                artist TEXT NOT NULL,
                duration INTEGER,
                album TEXT,
                icon TEXT,
                path_mp3 TEXT,
                reference_count INT DEFAULT 1
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                song_count INTEGER DEFAULT 0,
                total_duration INTEGER DEFAULT 0,
                icon TEXT
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS playlist_tracks (
                playlist_id INTEGER,
                track_id INTEGER,
                position INTEGER DEFAULT 0,
                FOREIGN KEY (playlist_id) REFERENCES playlists(id),
                FOREIGN KEY (track_id) REFERENCES tracks(id),
                PRIMARY KEY (playlist_id, track_id)
            )
        """
        )

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_position ON playlist_tracks(playlist_id, position)")

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """
        )

        cursor.execute(
            """
            INSERT OR IGNORE INTO metadata (key, value) 
            VALUES ('LIBRARY_NAME', 'My Library')
        """
        )

        conn.commit()
        print("✅ Database tables created!")

    def set_metadata(self, key: str, value: str) -> bool:
        """Set a metadata key-value pair."""
        with self.db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO metadata (key, value) 
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = ?
                """,
                (key, value, value),
            )

            conn.commit()
            conn.close()
            return True

    def get_metadata(self, key: str, default: str = "") -> str:
        """Get a metadata value by key."""
        with self.db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT value FROM metadata WHERE key = ?", (key,))
            result = cursor.fetchone()
            conn.close()

            return result[0] if result else default

    def get_all_metadata(self) -> Dict[str, str]:
        """Get all metadata key-value pairs."""
        with self.db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT key, value FROM metadata")
            results = cursor.fetchall()
            conn.close()

            return dict(results)

    def delete_metadata(self, key: str) -> bool:
        """Delete a metadata key-value pair."""
        with self.db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM metadata WHERE key = ?", (key,))
            conn.commit()
            conn.close()

            return cursor.rowcount > 0

    def _get_connection(self):
        """Get a database connection."""
        return sqlite3.connect(self.db_path)

    def execute_query(self, query: str, params: tuple = ()) -> List[tuple]:
        """Execute a read query with locking."""
        with self.db_lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            conn.close()
            return results

    def execute_update(self, query: str, params: tuple = ()) -> bool:
        """Execute an update query with locking."""
        with self.db_lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            conn.close()
            return True

    def get_all_tracks(self) -> List[tuple]:
        """Retrieve all tracks from database."""
        with self.db_lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tracks")
            results = cursor.fetchall()
            conn.close()
            return results

    def remove_track_from_playlist(self, playlist_id: int, track_id: int) -> bool:
        """Remove a track from a playlist."""
        with self.db_lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get track duration and position
            cursor.execute("SELECT duration FROM tracks WHERE id = ?", (track_id,))
            duration_result = cursor.fetchone()
            duration = duration_result[0] if duration_result else 0
            
            cursor.execute("SELECT position FROM playlist_tracks WHERE playlist_id = ? AND track_id = ?", 
                           (playlist_id, track_id))
            position_result = cursor.fetchone()
            old_position = position_result[0] if position_result else 0

            # Remove track from playlist
            cursor.execute(
                "DELETE FROM playlist_tracks WHERE playlist_id = ? AND track_id = ?",
                (playlist_id, track_id),
            )

            # Reorder remaining tracks (shift positions up)
            cursor.execute("""
                UPDATE playlist_tracks 
                SET position = position - 1 
                WHERE playlist_id = ? AND position > ?
            """, (playlist_id, old_position))

            # Update playlist stats
            cursor.execute(
                "UPDATE playlists SET song_count = song_count - 1 WHERE id = ?",
                (playlist_id,),
            )

            cursor.execute(
                "UPDATE playlists SET total_duration = total_duration - ? WHERE id = ?",
                (duration, playlist_id),
            )

            cursor.execute(
                "UPDATE tracks SET reference_count = reference_count - 1 WHERE id = ?",
                (track_id,),
            )

            conn.commit()
            conn.close()
            return True

    def reorder_playlist_tracks(self, playlist_id: int, new_order: List[int]) -> bool:
        """Reorder tracks in a playlist. new_order is list of track IDs."""
        with self.db_lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            try:
                for position, track_id in enumerate(new_order, 1):
                    cursor.execute(
                        "UPDATE playlist_tracks SET position = ? WHERE playlist_id = ? AND track_id = ?",
                        (position, playlist_id, track_id)
                    )
                
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                conn.rollback()
                conn.close()
                print(f"Error reordering: {e}")
                return False

    def update_playlist_name(self, playlist_id: int, new_name: str) -> bool:
        """Update playlist name. Returns True if successful."""
        with self.db_lock:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE playlists SET name = ? WHERE id = ?", (new_name, playlist_id)
            )

            updated = cursor.rowcount > 0
            conn.commit()
            conn.close()

            if updated:
                print(f"✓ Playlist ID {playlist_id} renamed to '{new_name}'")
            else:
                print(f"✗ Playlist ID {playlist_id} not found")

            return updated

    def add_track_to_playlist(self, playlist_id: int, title: str, artist: str, 
                             album: str, duration: int, icon: Optional[str]) -> int:
        """Add a track to a playlist."""
        with self.db_lock:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Check if track exists in tracks table
            cursor.execute(
                "SELECT id FROM tracks WHERE title = ? AND artist = ? AND album = ?",
                (title, artist, album)
            )
            existing_track = cursor.fetchone()

            if existing_track:
                track_id = existing_track[0]
                # Check if track is already in THIS specific playlist
                cursor.execute(
                    "SELECT 1 FROM playlist_tracks WHERE playlist_id = ? AND track_id = ?",
                    (playlist_id, track_id),
                )
                if cursor.fetchone():
                    print(f"Track '{title}' by '{artist}' is already in playlist {playlist_id}")
                    conn.close()
                    return track_id
                
                # Track exists in database but NOT in this playlist
                cursor.execute(
                    "UPDATE tracks SET reference_count = reference_count + 1 WHERE id = ?",
                    (track_id,)
                )
                print(f"Track '{title}' exists, added to another playlist (ref count++)")
            else:
                # Track doesn't exist in database at all
                cursor.execute(
                    "INSERT INTO tracks (title, artist, album, duration, icon, reference_count) VALUES (?, ?, ?, ?, ?, ?)",
                    (title, artist, album, duration, icon, 1),
                )
                track_id = cursor.lastrowid
                print(f"Created new track '{title}' (ref count = 1)")

            # Get current song count BEFORE updating (for position)
            cursor.execute("SELECT song_count FROM playlists WHERE id = ?", (playlist_id,))
            result = cursor.fetchone()
            current_count = result[0] if result else 0

            # Insert track into playlist at the end
            cursor.execute(
                "INSERT INTO playlist_tracks (playlist_id, track_id, position) VALUES (?, ?, ?)",
                (playlist_id, track_id, current_count + 1),
            )

            # Update playlist stats
            cursor.execute(
                "UPDATE playlists SET song_count = song_count + 1 WHERE id = ?",
                (playlist_id,),
            )

            # Only add duration if we have actual duration
            if duration > 0:
                cursor.execute(
                    "UPDATE playlists SET total_duration = total_duration + ? WHERE id = ?",
                    (duration, playlist_id),
                )

            conn.commit()
            conn.close()
            return track_id

    def add_playlist(self, name: str, icon: Optional[str] = None) -> int:
        """Create a new playlist if it doesn't already exist."""
        with self.db_lock:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Check if playlist already exists
            cursor.execute("SELECT id FROM playlists WHERE name = ?", (name,))
            existing = cursor.fetchone()

            if existing:
                print(f"⚠️ Playlist '{name}' already exists (ID: {existing[0]})")
                conn.close()
                return existing[0]  # Return existing ID

            # Create new playlist
            cursor.execute(
                "INSERT INTO playlists (name, song_count, total_duration, icon) VALUES (?, 0, 0, ?)",
                (name, icon),
            )
            conn.commit()

            new_id = cursor.lastrowid
            conn.close()
            print(f"✅ Created new playlist '{name}' (ID: {new_id})")
            return new_id

    def remove_playlist(self, playlist_id: int) -> bool:
        """Delete playlist and update track reference counts."""
        with self.db_lock:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT track_id FROM playlist_tracks WHERE playlist_id = ?", (playlist_id,)
            )
            track_ids = [row[0] for row in cursor.fetchall()]

            cursor.execute(
                "DELETE FROM playlist_tracks WHERE playlist_id = ?", (playlist_id,)
            )

            for track_id in track_ids:
                cursor.execute(
                    "UPDATE tracks SET reference_count = reference_count - 1 WHERE id = ?",
                    (track_id,),
                )

            cursor.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))

            conn.commit()
            conn.close()
            print(f"Playlist {playlist_id} removed successfully")
            return True

    def delete_unused_tracks(self) -> int:
        """Remove tracks with zero references (not in any playlist)."""
        with self.db_lock:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id, title, artist FROM tracks WHERE reference_count <= 0"
            )
            unused_tracks = cursor.fetchall()

            if not unused_tracks:
                print("No unused tracks to delete")
                conn.close()
                return 0

            track_ids = [track[0] for track in unused_tracks]
            placeholders = ",".join("?" for _ in track_ids)

            cursor.execute(f"DELETE FROM tracks WHERE id IN ({placeholders})", track_ids)

            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            print(f"Deleted {deleted_count} unused tracks:")
            for track_id, title, artist in unused_tracks:
                print(f"  - '{title}' by '{artist}'")

            return deleted_count

    def get_database_info(self) -> Dict[str, any]:
        """Get information about the database."""
        with self.db_lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM tracks")
            track_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM playlists")
            playlist_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM metadata")
            metadata_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "db_path": self.db_path,
                "track_count": track_count,
                "playlist_count": playlist_count,
                "metadata_count": metadata_count
            }

    # Additional helper methods for IconDownloader and other components

    def get_remote_icons(self) -> List[str]:
        """Get all remote icon URLs from database."""
        with self.db_lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT icon 
                FROM tracks 
                WHERE icon IS NOT NULL 
                AND icon != '' 
                AND icon LIKE 'http%'
            """)
            track_icons = [row[0] for row in cursor.fetchall()]
            
            cursor.execute("""
                SELECT DISTINCT icon 
                FROM playlists 
                WHERE icon IS NOT NULL 
                AND icon != '' 
                AND icon LIKE 'http%'
            """)
            playlist_icons = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            return list(set(track_icons + playlist_icons))

    def update_icon_path(self, old_url: str, new_path: str) -> bool:
        """Update icon path in database."""
        with self.db_lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Update tracks
            cursor.execute(
                "UPDATE tracks SET icon = ? WHERE icon = ?",
                (new_path, old_url)
            )
            
            # Update playlists
            cursor.execute(
                "UPDATE playlists SET icon = ? WHERE icon = ?",
                (new_path, old_url)
            )
            
            conn.commit()
            conn.close()
            return True

    def get_track_info(self, track_id: int) -> Optional[tuple]:
        """Get track information by ID."""
        with self.db_lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, title, artist, album, duration, path_mp3, icon
                FROM tracks WHERE id = ?
            """, (track_id,))
            
            result = cursor.fetchone()
            conn.close()
            return result

    def get_undownloaded_tracks(self) -> List[tuple]:
        """Get all tracks without downloaded files."""
        with self.db_lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, title, artist 
                FROM tracks 
                WHERE path_mp3 IS NULL OR path_mp3 = ''
            """)
            
            results = cursor.fetchall()
            conn.close()
            return results

    def update_track_path(self, track_id: int, full_file_path: str, duration: int) -> bool:
        """Update track file path and duration."""
        with self.db_lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Extract just the filename for display purposes if needed
            # But store the full path in database
            file_name = Path(full_file_path).name
            
            cursor.execute(
                "UPDATE tracks SET path_mp3 = ?, duration = ? WHERE id = ?", 
                (full_file_path, duration, track_id)  # Store FULL path
            )
            
            cursor.execute("""
                UPDATE playlists 
                SET total_duration = total_duration + ? 
                WHERE id IN (
                    SELECT playlist_id 
                    FROM playlist_tracks 
                    WHERE track_id = ?
                )
            """, (duration, track_id))
            
            conn.commit()
            conn.close()
            return True
