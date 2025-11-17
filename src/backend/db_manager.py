import sqlite3

class SimpleMusicDB:
    def __init__(self):
        self.conn = sqlite3.connect("simple_music.db")
        self._create_tables()
    
    def _create_tables(self):
        cursor = self.conn.cursor()
        
        # Create tracks table (simplified)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                artist TEXT NOT NULL,
                duration INTEGER,
                icon TEXT
            )
        ''')
        
        # Create playlists table  
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                song_count INTEGER,
                total_duration INTEGER,
                icon TEXT
            )
        ''')
        
        # Create the "pointing" table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlist_tracks (
                playlist_id INTEGER,
                track_id INTEGER,
                FOREIGN KEY (playlist_id) REFERENCES playlists(id),
                FOREIGN KEY (track_id) REFERENCES tracks(id),
                PRIMARY KEY (playlist_id, track_id)
            )
        ''')
        
        self.conn.commit()
        print("✅ Database tables created!")
    
    def add_track(self, title, artist, duration, icon):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO tracks (title, artist, duration, icon) VALUES (?, ?, ?, ?)",
            (title, artist, duration, icon)
        )
        self.conn.commit()
        return cursor.lastrowid  # Returns the new track ID
    
    def get_all_tracks(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tracks")
        return cursor.fetchall()

    def _update_playlist_stats(self, playlist_id):
        """Recalculate and update playlist counts"""
        cursor = self.conn.cursor()
        
        # Calculate current stats
        cursor.execute('''
            SELECT 
                COUNT(pt.track_id),
                COALESCE(SUM(t.duration), 0)
            FROM playlist_tracks pt
            JOIN tracks t ON pt.track_id = t.id
            WHERE pt.playlist_id = ?
        ''', (playlist_id,))
        
        count, duration = cursor.fetchone()
        
        # Update playlist
        cursor.execute(
            "UPDATE playlists SET song_count = ?, total_duration = ? WHERE id = ?",
            (count, duration, playlist_id)
        )
        self.conn.commit()

    def add_track_to_playlist(self, playlist_id, track_id):
        """Add track"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO playlist_tracks (playlist_id, track_id) VALUES (?, ?)",
            (playlist_id, track_id)
        )
        self.conn.commit()

    def remove_track_from_playlist(self, playlist_id, track_id):
        """Remove track"""
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM playlist_tracks WHERE playlist_id = ? AND track_id = ?",
            (playlist_id, track_id)
        )
        self.conn.commit()
        
    def add_playlist(self, name, icon=None):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO playlists (name, song_count, total_duration, icon) VALUES (?, 0, 0, ?)",
            (name, icon)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_track_by_title_artist(self, title, artist):
        """Check if track already exists by title and artist"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id FROM tracks WHERE title = ? AND artist = ?", 
            (title, artist)
        )
        result = cursor.fetchone()
        return result[0] if result else None

if __name__ == "__main__":
    db = SimpleMusicDB()
    
    test_tracks = [
        ("Bohemian Rhapsody", "Queen", 354, "/home/tudor/Music/song1.mp3"),
        ("Sweet Child O'Mine", "Guns N' Roses", 356, "/home/tudor/Music/song2.mp3"),
    ]
    
    for title, artist, duration, file_path in test_tracks:
        existing_id = db.get_track_by_title_artist(title, artist)
        
        if existing_id:
            print(f"🚫 SKIPPING: '{title}' by {artist} already exists (ID: {existing_id})")
        else:
            # Add to database
            track_id = db.add_track(title, artist, duration, file_path)
            print(f"✅ ADDED: '{title}' by {artist} (ID: {track_id})")
    
    # Show final database
    tracks = db.get_all_tracks()
    print("\n📀 Final tracks in database:", tracks)
