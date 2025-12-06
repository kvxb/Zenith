import yt_dlp
import os
from pathlib import Path
from db_manager import SimpleMusicDB

class SimpleDownloader:
    def __init__(self, db: SimpleMusicDB, download_dir: str = "downloads"):
        """
        Simple YouTube downloader.
        
        Args:
            db: SimpleMusicDB instance
            download_dir: Where to save mp3 files
        """
        self.db = db
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        
        # Simple yt-dlp config - no duration matching
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
        }
    
    def _search_and_download(self, title: str, artist: str) -> str:
        """
        Search YouTube using just song name and artist.
        Returns the file path if successful.
        """
        # Simple search query - just artist and title
        query = f"{artist} {title}"
        
        try:
            # Set output template
            download_opts = self.ydl_opts.copy()
            download_opts['outtmpl'] = str(self.download_dir / f'{artist} - {title}.%(ext)s')
            
            # Search and download in one go
            with yt_dlp.YoutubeDL(download_opts) as ydl:
                # Use ytsearch to find the song
                info = ydl.extract_info(f"ytsearch:{query}", download=True)
                
                # Find the downloaded file
                expected_filename = f"{artist} - {title}.mp3"
                for file in self.download_dir.iterdir():
                    if file.name == expected_filename:
                        return str(file)
                
                # If not found by exact name, get any new mp3 file
                mp3_files = list(self.download_dir.glob("*.mp3"))
                if mp3_files:
                    # Get most recently modified
                    latest_file = max(mp3_files, key=lambda f: f.stat().st_mtime)
                    return str(latest_file)
                
                return None
                
        except Exception as e:
            print(f"Error downloading {artist} - {title}: {e}")
            return None
    
    def download_track(self, track_id: int) -> bool:
        """
        Download a single track by ID.
        Returns True if successful.
        """
        # Get track info from database
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT title, artist FROM tracks WHERE id = ?", (track_id,))
        track = cursor.fetchone()
        
        if not track:
            print(f"Track ID {track_id} not found")
            return False
        
        title, artist = track
        
        print(f"Downloading: {artist} - {title}")
        
        # Download the track
        file_path = self._search_and_download(title, artist)
        
        if file_path:
            # Update database with file path
            cursor.execute(
                "UPDATE tracks SET path_mp3 = ? WHERE id = ?",
                (file_path, track_id)
            )
            self.db.conn.commit()
            print(f"✓ Downloaded: {artist} - {title}")
            return True
        else:
            print(f"✗ Failed to download: {artist} - {title}")
            return False
    
    def download_all_tracks(self) -> tuple:
        """
        Download ALL tracks in the database that don't have a path.
        Simple sequential download.
        
        Returns:
            (success_count, failed_count)
        """
        # Get all track IDs without a path
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id FROM tracks WHERE path_mp3 IS NULL OR path_mp3 = ''")
        track_ids = [row[0] for row in cursor.fetchall()]
        
        if not track_ids:
            print("All tracks already downloaded!")
            return 0, 0
        
        print(f"Found {len(track_ids)} tracks to download")
        print("Starting sequential download...")
        
        success = 0
        failed = 0
        
        for i, track_id in enumerate(track_ids, 1):
            print(f"\n[{i}/{len(track_ids)}] ", end="")
            if self.download_track(track_id):
                success += 1
            else:
                failed += 1
        
        print(f"\n" + "="*50)
        print(f"DOWNLOAD COMPLETE!")
        print(f"✓ Successfully downloaded: {success}")
        print(f"✗ Failed: {failed}")
        
        return success, failed
    
    def download_playlist(self, playlist_id: int) -> tuple:
        """
        Download all tracks in a specific playlist.
        
        Args:
            playlist_id: The playlist ID
            
        Returns:
            (success_count, failed_count)
        """
        # Get track IDs for this playlist that aren't downloaded yet
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT t.id 
            FROM tracks t
            JOIN playlist_tracks pt ON t.id = pt.track_id
            WHERE pt.playlist_id = ? 
            AND (t.path_mp3 IS NULL OR t.path_mp3 = '')
        """, (playlist_id,))
        
        track_ids = [row[0] for row in cursor.fetchall()]
        
        if not track_ids:
            print("All tracks in this playlist are already downloaded!")
            return 0, 0
        
        # Get playlist name for display
        cursor.execute("SELECT name FROM playlists WHERE id = ?", (playlist_id,))
        playlist_name = cursor.fetchone()[0]
        
        print(f"Downloading playlist: {playlist_name}")
        print(f"Found {len(track_ids)} tracks to download")
        
        success = 0
        failed = 0
        
        for i, track_id in enumerate(track_ids, 1):
            print(f"\n[{i}/{len(track_ids)}] ", end="")
            if self.download_track(track_id):
                success += 1
            else:
                failed += 1
        
        print(f"\nPlaylist '{playlist_name}' download complete!")
        print(f"✓ Successfully downloaded: {success}")
        print(f"✗ Failed: {failed}")
        
        return success, failed

# Simple test
# if __name__ == "__main__":
#     # Initialize
#     db = SimpleMusicDB()
#     downloader = SimpleDownloader(db)
#
#     print("=== Simple YouTube Downloader Test ===\n")
#
#     # Clear old test data
#     print("Clearing old test data...")
#     cursor = db.conn.cursor()
#     cursor.execute("DELETE FROM playlist_tracks")
#     cursor.execute("DELETE FROM tracks")
#     cursor.execute("DELETE FROM playlists")
#     db.conn.commit()
#     print("Database cleared\n")
#
#     # Create a test playlist
#     playlist_id = db.add_playlist("Test Playlist")
#     print(f"Created playlist ID: {playlist_id}")
#
#     # Add test songs
#     test_songs = [
#         ("Heavener", "Invent Animate"),
#         ("Icarus", "fromjoy")
#     ]
#
#     added_tracks = []
#     for title, artist in test_songs:
#         track_id = db.add_track_to_playlist(
#             playlist_id=playlist_id,
#             title=title,
#             artist=artist,
#             duration=0,  # Duration doesn't matter for download
#             icon=None
#         )
#         added_tracks.append(track_id)
#         print(f"Added: {artist} - {title} (ID: {track_id})")
#
#     print(f"\nAdded {len(added_tracks)} tracks to the database")
#     print("\n" + "="*50)
#
#     # Test bulk download
#     print("\nStarting bulk download...")
#     success, failed = downloader.download_all_tracks()
#
#     print("\n" + "="*50)
#
#     # Show final status
#     print("\nFinal status:")
#     cursor = db.conn.cursor()
#     cursor.execute("SELECT id, title, artist, path_mp3 FROM tracks")
#     all_tracks = cursor.fetchall()
#
#     for track_id, title, artist, path_mp3 in all_tracks:
#         if path_mp3 and os.path.exists(path_mp3):
#             file_size = os.path.getsize(path_mp3) / 1024 / 1024
#             print(f"✓ {artist} - {title} ({file_size:.1f} MB)")
#         else:
#             print(f"✗ {artist} - {title}: Not downloaded")
#
#     print(f"\n✅ Test completed!")
