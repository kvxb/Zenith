import yt_dlp
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from .db_manager import SimpleMusicDB
from threading import Lock


class SimpleDownloader:
    def __init__(self, db: SimpleMusicDB, download_dir: str = "./src/assets/tracks", max_workers: int = 4):
        """
        Multi-threaded YouTube downloader.
        
        Args:
            db: SimpleMusicDB instance
            download_dir: Where to save mp3 files
            max_workers: Number of concurrent download threads
        """
        self.db = db
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        self.max_workers = max_workers
        self.lock = Lock()  # For thread-safe database updates

        # yt-dlp config
        self.ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "quiet": True,
            "no_warnings": True,
        }

    def _search_and_download(self, title: str, artist: str) -> str:
        """Search YouTube and download track, returns file path."""
        query = f"{artist} {title}"

        try:
            download_opts = self.ydl_opts.copy()
            download_opts["outtmpl"] = str(
                self.download_dir / f"{artist} - {title}.%(ext)s"
            )

            with yt_dlp.YoutubeDL(download_opts) as ydl:
                ydl.extract_info(f"ytsearch:{query}", download=True)

                # Find downloaded file
                expected_filename = f"{artist} - {title}.mp3"
                for file in self.download_dir.iterdir():
                    if file.name == expected_filename:
                        return str(file)

                # Fallback: get latest mp3
                mp3_files = list(self.download_dir.glob("*.mp3"))
                if mp3_files:
                    latest_file = max(mp3_files, key=lambda f: f.stat().st_mtime)
                    return str(latest_file)

                return None

        except Exception as e:
            print(f"Error downloading {artist} - {title}: {e}")
            return None

    def _download_single_track(self, track_data: tuple) -> tuple:
        """Thread worker: download single track and return result."""
        track_id, title, artist = track_data
        
        file_path = self._search_and_download(title, artist)
        
        if file_path:
            file_name = "tracks/" + Path(file_path).name
            
            # Get duration from the downloaded file
            duration = self._get_duration_from_file(file_path)
            
            with self.lock:
                cursor = self.db._get_connection().cursor()
                # Update both path AND duration
                cursor.execute(
                    "UPDATE tracks SET path_mp3 = ?, duration = ? WHERE id = ?", 
                    (file_name, duration, track_id)
                )
                
                # Update playlist total duration with the actual duration
                cursor.execute("""
                    UPDATE playlists 
                    SET total_duration = total_duration + ? 
                    WHERE id IN (
                        SELECT playlist_id 
                        FROM playlist_tracks 
                        WHERE track_id = ?
                    )
                """, (duration, track_id))
                
                self.db._get_connection().commit()
                
            return track_id, True, f"✓ Downloaded: {artist} - {title} ({duration}s)"
        else:
            return track_id, False, f"✗ Failed: {artist} - {title}"

    def _get_duration_from_file(self, file_path: str) -> int:
        """Get duration of MP3 file in seconds."""
        try:
            from mutagen.mp3 import MP3
            
            audio = MP3(file_path)
            return int(audio.info.length)
            
        except Exception as e:
            print(f"Error getting duration for {file_path}: {e}")
            # Try with mutagen.File as fallback
            try:
                from mutagen import File
                audio = File(file_path)
                if audio and audio.info:
                    return int(audio.info.length)
            except:
                pass
                
            return 0  # Return 0 if we can't get duration

    def download_track(self, track_id: int) -> bool:
        """Download single track by ID."""
        cursor = self.db._get_connection().cursor()
        cursor.execute("SELECT title, artist FROM tracks WHERE id = ?", (track_id,))
        track = cursor.fetchone()

        if not track:
            print(f"Track ID {track_id} not found")
            return False

        title, artist = track
        print(f"Downloading: {artist} - {title}")

        result = self._download_single_track((track_id, title, artist))
        _, success, message = result
        print(message)
        return success

    def download_all_tracks(self) -> tuple:
        """Multi-threaded download of all tracks without paths."""
        cursor = self.db._get_connection().cursor()
        cursor.execute("""
            SELECT id, title, artist 
            FROM tracks 
            WHERE path_mp3 IS NULL OR path_mp3 = ''
        """)
        tracks = cursor.fetchall()

        if not tracks:
            print("All tracks already downloaded!")
            return 0, 0

        print(f"Downloading {len(tracks)} tracks with {self.max_workers} workers...")
        
        success = 0
        failed = 0
        completed = 0
        total = len(tracks)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all download tasks
            future_to_track = {
                executor.submit(self._download_single_track, track): track[0]
                for track in tracks
            }

            # Process results as they complete
            for future in as_completed(future_to_track):
                completed += 1
                track_id, success_flag, message = future.result()
                
                print(f"[{completed}/{total}] {message}")
                
                if success_flag:
                    success += 1
                else:
                    failed += 1

        print(f"\n" + "=" * 50)
        print(f"DOWNLOAD COMPLETE!")
        print(f"✓ Successfully downloaded: {success}")
        print(f"✗ Failed: {failed}")

        return success, failed

    def download_playlist(self, playlist_id: int) -> tuple:
        """Multi-threaded download of all tracks in a playlist."""
        cursor = self.db._get_connection().cursor()
        
        # Get playlist name
        cursor.execute("SELECT name FROM playlists WHERE id = ?", (playlist_id,))
        playlist_name = cursor.fetchone()[0]
        
        # Get undownloaded tracks in playlist
        cursor.execute("""
            SELECT t.id, t.title, t.artist 
            FROM tracks t
            JOIN playlist_tracks pt ON t.id = pt.track_id
            WHERE pt.playlist_id = ? 
            AND (t.path_mp3 IS NULL OR t.path_mp3 = '')
        """, (playlist_id,))
        
        tracks = cursor.fetchall()

        if not tracks:
            print(f"All tracks in '{playlist_name}' already downloaded!")
            return 0, 0

        print(f"Downloading playlist '{playlist_name}' ({len(tracks)} tracks)...")
        
        success = 0
        failed = 0
        completed = 0
        total = len(tracks)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_track = {
                executor.submit(self._download_single_track, track): track[0]
                for track in tracks
            }

            for future in as_completed(future_to_track):
                completed += 1
                track_id, success_flag, message = future.result()
                
                print(f"[{completed}/{total}] {message}")
                
                if success_flag:
                    success += 1
                else:
                    failed += 1

        print(f"\nPlaylist '{playlist_name}' download complete!")
        print(f"✓ Successfully downloaded: {success}")
        print(f"✗ Failed: {failed}")

        return success, failed
