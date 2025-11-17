import sqlite3

class SimpleMusicDB:
    def __init__(self):
        self.conn = sqlite3.connect("playlists_songs.db")
        self._create_tables()
    
    def _create_tables(self):
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                artist TEXT NOT NULL,
                duration INTEGER,
                icon TEXT,
                path_mp3 TEXT,
                reference_count INT DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                song_count INTEGER DEFAULT 0,
                total_duration INTEGER DEFAULT 0,
                icon TEXT
            )
        ''')
        
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
    

    # when we have to download the files from youtube
    def get_all_tracks(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tracks")
        return cursor.fetchall()
 
    def remove_track_from_playlist(self, playlist_id, track_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT duration FROM tracks WHERE id = ?", (track_id,))
        track = cursor.fetchone()
        duration = track[0]

        cursor.execute(
            "DELETE FROM playlist_tracks WHERE playlist_id = ? AND track_id = ?",
            (playlist_id, track_id)
        )

        cursor.execute(
            "UPDATE playlists SET song_count = song_count - 1 WHERE id = ?",
            (playlist_id,)
        )

        cursor.execute(
            "UPDATE playlists SET total_duration = total_duration - ? WHERE id = ?",
            (duration, playlist_id)
        )

        cursor.execute(
            "UPDATE tracks SET reference_count = reference_count - 1 WHERE id = ?",
            (track_id,)
        )

        self.conn.commit()
        
    # the main operation done after the user chooses his playlists
    def add_track_to_playlist(self, playlist_id, title, artist, duration, icon):
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT id FROM tracks WHERE title = ? AND artist = ?", (title, artist))
        existing_track = cursor.fetchone()
        
        if existing_track:
            track_id = existing_track[0]

            cursor.execute(
                "SELECT 1 FROM playlist_tracks WHERE playlist_id = ? AND track_id = ?", 
                (playlist_id, track_id)
            )
            if cursor.fetchone():
                print(f"Track '{title}' by '{artist}' is already in playlist")
                return track_id
            else:
                cursor.execute(
                    "INSERT INTO tracks (title, artist, duration, icon, reference_count) VALUES (?, ?, ?, ?, ?)",
                    (title, artist, duration, icon, 1)
                )
                track_id = cursor.lastrowid
        
        cursor.execute(
            "INSERT INTO playlist_tracks (playlist_id, track_id) VALUES (?, ?)",
            (playlist_id, track_id)
        )

        cursor.execute(
            "UPDATE playlists SET song_count = song_count + 1 WHERE id = ?",
            (playlist_id,)
        )

        cursor.execute(
            "UPDATE playlists SET total_duration = total_duration + ? WHERE id = ?",
            (duration, playlist_id)
        )

        self.conn.commit()
        return track_id


    # before adding the tracks to the playlists we add the playlists themselves
    def add_playlist(self, name, icon=None):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO playlists (name, song_count, total_duration, icon) VALUES (?, 0, 0, ?)",
            (name, icon)
        )
        self.conn.commit()
        return cursor.lastrowid

    # removes playlists removes the tracks from playlist_tracks db and decreases the track counter from tracks db
    def remove_playlist(self, playlist_id):
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT track_id FROM playlist_tracks WHERE playlist_id = ?", (playlist_id,))
        track_ids = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("DELETE FROM playlist_tracks WHERE playlist_id = ?", (playlist_id,))
        
        for track_id in track_ids:
            cursor.execute(
                "UPDATE tracks SET reference_count = reference_count - 1 WHERE id = ?",
                (track_id,)
            )
        
        cursor.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
        
        self.conn.commit()
        print(f"Playlist {playlist_id} removed successfully")   


    # keep a counter on every track and when the counter reaches 0 and the user wants to free useless mem delete all files with 0 uses
    def delete_unused_tracks(self):
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT id, title, artist FROM tracks WHERE reference_count <= 0")
        unused_tracks = cursor.fetchall()
        
        if not unused_tracks:
            print("No unused tracks to delete")
            return 0
        
        track_ids = [track[0] for track in unused_tracks]
        placeholders = ','.join('?' for _ in track_ids)
        
        cursor.execute(f"DELETE FROM tracks WHERE id IN ({placeholders})", track_ids)
        
        deleted_count = cursor.rowcount
        self.conn.commit()
        
        print(f"Deleted {deleted_count} unused tracks:")
        for track_id, title, artist in unused_tracks:
            print(f"  - '{title}' by '{artist}'")
        
        return deleted_count



if __name__ == "__main__":
    db = SimpleMusicDB()
    
    test_tracks = [
        ("Bohemian Rhapsody", "Queen", 354, "/home/tudor/Music/song1.mp3"),
        ("Sweet Child O'Mine", "Guns N' Roses", 356, "/home/tudor/Music/song2.mp3"),
    ]
