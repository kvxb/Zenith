import sqlite3
import threading


class SimpleMusicDB:
    """Thread-safe SQLite database for music tracks and playlists."""
    
    def __init__(self):
        self.local = threading.local()
        self._ensure_tables_exist()

    def _ensure_tables_exist(self):
        """Create database tables if they don't exist."""
        conn = sqlite3.connect("playlists_songs.db")
        self._create_tables(conn)
        conn.close()

    def _create_tables(self, conn):
        """Create tracks, playlists, and junction tables."""
        cursor = conn.cursor()

        cursor.execute("""
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
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                song_count INTEGER DEFAULT 0,
                total_duration INTEGER DEFAULT 0,
                icon TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS playlist_tracks (
                playlist_id INTEGER,
                track_id INTEGER,
                FOREIGN KEY (playlist_id) REFERENCES playlists(id),
                FOREIGN KEY (track_id) REFERENCES tracks(id),
                PRIMARY KEY (playlist_id, track_id)
        )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        cursor.execute("""
            INSERT OR IGNORE INTO metadata (key, value) 
            VALUES ('LIBRARY_NAME', 'My Library')
        """)

        conn.commit()
        print("✅ Database tables created!")

    def set_metadata(self, key: str, value: str) -> bool:
        """Set a metadata key-value pair."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO metadata (key, value) 
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = ?
            """,
            (key, value, value)
        )
        
        conn.commit()
        return True

    def get_metadata(self, key: str, default: str = "") -> str:
        """Get a metadata value by key."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM metadata WHERE key = ?", (key,))
        result = cursor.fetchone()
        
        return result[0] if result else default

    def get_all_metadata(self) -> Dict[str, str]:
        """Get all metadata key-value pairs."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT key, value FROM metadata")
        results = cursor.fetchall()
        
        return dict(results)

    def delete_metadata(self, key: str) -> bool:
        """Delete a metadata key-value pair."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM metadata WHERE key = ?", (key,))
        conn.commit()
        
        return cursor.rowcount > 0

    def _get_connection(self):
        """Get thread-local SQLite connection for safe concurrent access."""
        if not hasattr(self.local, 'conn'):
            self.local.conn = sqlite3.connect("playlists_songs.db")
        return self.local.conn

    def get_all_tracks(self):
        """Retrieve all tracks from database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tracks")
        return cursor.fetchall()

    def remove_track_from_playlist(self, playlist_id, track_id):
        """Remove track from playlist and update statistics."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT duration FROM tracks WHERE id = ?", (track_id,))
        duration = cursor.fetchone()[0]

        cursor.execute(
            "DELETE FROM playlist_tracks WHERE playlist_id = ? AND track_id = ?",
            (playlist_id, track_id),
        )

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

    def update_playlist_name(self, playlist_id: int, new_name: str) -> bool:
        """Update playlist name. Returns True if successful."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE playlists SET name = ? WHERE id = ?",
            (new_name, playlist_id)
        )
        
        updated = cursor.rowcount > 0
        conn.commit()
        
        if updated:
            print(f"✓ Playlist ID {playlist_id} renamed to '{new_name}'")
        else:
            print(f"✗ Playlist ID {playlist_id} not found")
        
        return updated

    def add_track_to_playlist(self, playlist_id, title, artist, album, duration, icon):
        """Add track to playlist, reusing existing tracks when possible."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM tracks WHERE title = ? AND artist = ? AND album = ?",
            (title, artist, album)
        )
        existing_track = cursor.fetchone()

        if existing_track:
            track_id = existing_track[0]
            cursor.execute(
                "SELECT 1 FROM playlist_tracks WHERE playlist_id = ? AND track_id = ?",
                (playlist_id, track_id),
            )
            if cursor.fetchone():
                print(f"Track '{title}' by '{artist}' is already in playlist")
                return track_id
        else:
            cursor.execute(
                "INSERT INTO tracks (title, artist, album, duration, icon, reference_count) VALUES (?, ?, ?, ?, ?, ?)",
                (title, artist, album, duration, icon, 1),
            )
            track_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO playlist_tracks (playlist_id, track_id) VALUES (?, ?)",
            (playlist_id, track_id),
        )

        cursor.execute(
            "UPDATE playlists SET song_count = song_count + 1 WHERE id = ?",
            (playlist_id,),
        )

        cursor.execute(
            "UPDATE playlists SET total_duration = total_duration + ? WHERE id = ?",
            (duration, playlist_id),
        )

        conn.commit()
        return track_id

    def add_playlist(self, name, icon=None):
        """Create a new playlist if it doesn't already exist."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Check if playlist already exists
        cursor.execute("SELECT id FROM playlists WHERE name = ?", (name,))
        existing = cursor.fetchone()
        
        if existing:
            print(f"⚠️ Playlist '{name}' already exists (ID: {existing[0]})")
            return existing[0]  # Return existing ID
        
        # Create new playlist
        cursor.execute(
            "INSERT INTO playlists (name, song_count, total_duration, icon) VALUES (?, 0, 0, ?)",
            (name, icon),
        )
        conn.commit()
        
        new_id = cursor.lastrowid
        print(f"✅ Created new playlist '{name}' (ID: {new_id})")
        return new_id

    def remove_playlist(self, playlist_id):
        """Delete playlist and update track reference counts."""
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
        print(f"Playlist {playlist_id} removed successfully")

    def delete_unused_tracks(self):
        """Remove tracks with zero references (not in any playlist)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, title, artist FROM tracks WHERE reference_count <= 0"
        )
        unused_tracks = cursor.fetchall()

        if not unused_tracks:
            print("No unused tracks to delete")
            return 0

        track_ids = [track[0] for track in unused_tracks]
        placeholders = ",".join("?" for _ in track_ids)

        cursor.execute(f"DELETE FROM tracks WHERE id IN ({placeholders})", track_ids)

        deleted_count = cursor.rowcount
        conn.commit()

        print(f"Deleted {deleted_count} unused tracks:")
        for track_id, title, artist in unused_tracks:
            print(f"  - '{title}' by '{artist}'")

        return deleted_count
