import yt_dlp
import os
from pathlib import Path
from db_manager import SimpleMusicDB
import concurrent.futures

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
        
        # Basic yt-dlp config
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
        Search YouTube and download a song.
        Returns the file path if successful.
        """
        # Create search query
        query = f"{artist} {title} audio"
        
        # First, search for the video
        search_opts = {
            'quiet': True,
            'extract_flat': True,
            'default_search': 'ytsearch',
        }
        
        try:
            with yt_dlp.YoutubeDL(search_opts) as ydl:
                info = ydl.extract_info(query, download=False)
                if 'entries' in info and info['entries']:
                    video_url = f"https://www.youtube.com/watch?v={info['entries'][0]['id']}"
                    
                    # Now download it
                    self.ydl_opts['outtmpl'] = str(self.download_dir / f'{title} - {artist}.%(ext)s')
                    
                    with yt_dlp.YoutubeDL(self.ydl_opts) as ydl_dl:
                        ydl_dl.download([video_url])
                    
                    # Find the downloaded file
                    for file in self.download_dir.iterdir():
                        if file.suffix == '.mp3' and title in file.stem and artist in file.stem:
                            return str(file)
            
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
    
    def download_all_tracks(self, max_workers: int = 4) -> tuple:
        """
        Download ALL tracks in the database that don't have a path.
        Uses multithreading for faster downloads.
        
        Args:
            max_workers: Number of parallel downloads
            
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
        print("Starting bulk download...")
        
        # Use ThreadPoolExecutor for parallel downloads
        success = 0
        failed = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all download tasks
            future_to_id = {
                executor.submit(self.download_track, track_id): track_id 
                for track_id in track_ids
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_id):
                track_id = future_to_id[future]
                try:
                    if future.result():
                        success += 1
                    else:
                        failed += 1
                except Exception:
                    failed += 1
        
        print(f"\nDownload complete!")
        print(f"✓ Successfully downloaded: {success}")
        print(f"✗ Failed: {failed}")
        
        return success, failed
    
    def download_playlist(self, playlist_id: int, max_workers: int = 4) -> tuple:
        """
        Download all tracks in a specific playlist.
        
        Args:
            playlist_id: The playlist ID
            max_workers: Number of parallel downloads
            
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
        
        # Use the same parallel download logic
        success = 0
        failed = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_id = {
                executor.submit(self.download_track, track_id): track_id 
                for track_id in track_ids
            }
            
            for future in concurrent.futures.as_completed(future_to_id):
                track_id = future_to_id[future]
                try:
                    if future.result():
                        success += 1
                    else:
                        failed += 1
                except Exception:
                    failed += 1
        
        print(f"\nPlaylist '{playlist_name}' download complete!")
        print(f"✓ Successfully downloaded: {success}")
        print(f"✗ Failed: {failed}")
        
        return success, failed

# Simple test
if __name__ == "__main__":
    # Initialize
    db = SimpleMusicDB()
    downloader = SimpleDownloader(db)
    
    print("=== Simple YouTube Downloader ===\n")
    
    # # Test 1: Download a single track (assuming track ID 1 exists)
    # print("1. Testing single track download...")
    # downloader.download_track(1)
    #
    # print("\n" + "="*50 + "\n")
    #
    # Test 2: Bulk download all tracks
    print("2. Testing bulk download of all tracks...")
    success, failed = downloader.download_all_tracks(max_workers=2)
    
    print("\n" + "="*50 + "\n")
    
    # Test 3: Download a playlist (assuming playlist ID 1 exists)
    print("3. Testing playlist download...")
    downloader.download_playlist(1, max_workers=2)
