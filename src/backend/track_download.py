import yt_dlp
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from .db_manager import SimpleMusicDB
from threading import Lock
import mutagen
from typing import Optional, Dict, Tuple, List
from mutagen.mp3 import MP3


class SimpleDownloader:
    def __init__(self, db: SimpleMusicDB, download_dir: str, max_workers: int = 4):
        """
        Multi-threaded YouTube downloader for the new storage system.
        
        Args:
            db: SimpleMusicDB instance
            download_dir: Full path where to save mp3 files (e.g., "/path/to/storage/tracks")
            max_workers: Number of concurrent download threads
        """
        self.db = db
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
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
            "extract_flat": False,
        }

        print(f"🎵 Downloader initialized:")
        print(f"   Tracks dir: {self.download_dir}")
        print(f"   Max workers: {self.max_workers}")

    def _sanitize_filename(self, filename: str) -> str:
        """Remove invalid characters from filename."""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '')
        filename = filename.strip('. ')
        return filename

    def _search_and_download(self, title: str, artist: str) -> Optional[str]:
        """Search YouTube and download track, returns file path."""
        query = f"{artist} {title}"
        
        safe_artist = self._sanitize_filename(artist)
        safe_title = self._sanitize_filename(title)
        
        try:
            download_opts = self.ydl_opts.copy()
            download_opts["outtmpl"] = str(
                self.download_dir / f"{safe_artist} - {safe_title}.%(ext)s"
            )

            with yt_dlp.YoutubeDL(download_opts) as ydl:
                ydl.extract_info(f"ytsearch:{query}", download=True)
                
                expected_filename = f"{safe_artist} - {safe_title}.mp3"
                expected_path = self.download_dir / expected_filename
                
                if expected_path.exists():
                    return str(expected_path)
                
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
        
        if file_path and Path(file_path).exists():
            # Store FULL filesystem path in database
            full_file_path = str(file_path)
            
            # Get duration from the downloaded file
            duration = self._get_duration_from_file(file_path)
            
            with self.lock:
                # Update database with FULL path
                self.db.update_track_path(track_id, full_file_path, duration)
                
            return track_id, True, f"✓ Downloaded: {artist} - {title} ({duration}s)"
        else:
            return track_id, False, f"✗ Failed: {artist} - {title}"

    def download_track(self, track_id: int) -> bool:
        """Download single track by ID."""
        track_info = self.db.get_track_info(track_id)
        if not track_info:
            print(f"Track ID {track_id} not found")
            return False

        _, title, artist, _, _, _, _ = track_info
        print(f"🎵 Downloading: {artist} - {title}")

        result = self._download_single_track((track_id, title, artist))
        _, success, message = result
        print(message)
        return success

    def _get_duration_from_file(self, file_path: str) -> int:
        """Get duration of MP3 file in seconds."""
        try:
            audio = MP3(file_path)
            return int(audio.info.length)
        except Exception as e:
            print(f"Error getting duration for {file_path}: {e}")
            try:
                audio = mutagen.File(file_path)
                if audio and audio.info:
                    return int(audio.info.length)
            except:
                pass
            return 0

    def download_all_tracks(self) -> Tuple[int, int]:
        """Multi-threaded download of all tracks without paths."""
        tracks = self.db.get_undownloaded_tracks()

        if not tracks:
            print("✅ All tracks already downloaded!")
            return 0, 0

        print(f"⬇️  Downloading {len(tracks)} tracks with {self.max_workers} workers...")
        
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

        print(f"\n" + "=" * 50)
        print(f"✅ DOWNLOAD COMPLETE!")
        print(f"✓ Successfully downloaded: {success}")
        print(f"✗ Failed: {failed}")
        print(f"📁 Tracks saved to: {self.download_dir}")

        return success, failed

    def download_playlist(self, playlist_id: int) -> Tuple[int, int]:
        """Multi-threaded download of all tracks in a playlist."""
        # We'll need to add a method to SimpleMusicDB for this
        # For now, use existing logic but adapt it
        
        # Get playlist name
        import sqlite3
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM playlists WHERE id = ?", (playlist_id,))
        playlist_result = cursor.fetchone()
        playlist_name = playlist_result[0] if playlist_result else f"Playlist {playlist_id}"
        
        # Get undownloaded tracks in playlist
        cursor.execute("""
            SELECT t.id, t.title, t.artist 
            FROM tracks t
            JOIN playlist_tracks pt ON t.id = pt.track_id
            WHERE pt.playlist_id = ? 
            AND (t.path_mp3 IS NULL OR t.path_mp3 = '')
        """, (playlist_id,))
        
        tracks = cursor.fetchall()
        conn.close()

        if not tracks:
            print(f"✅ All tracks in '{playlist_name}' already downloaded!")
            return 0, 0

        print(f"📚 Downloading playlist '{playlist_name}' ({len(tracks)} tracks)...")
        
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

        print(f"\n✅ Playlist '{playlist_name}' download complete!")
        print(f"✓ Successfully downloaded: {success}")
        print(f"✗ Failed: {failed}")

        return success, failed

    def get_track_filepath(self, db_track_path: str) -> Optional[Path]:
        """
        Convert database track path to filesystem path.
        
        Args:
            db_track_path: Path from database (e.g., "filename.mp3")
            
        Returns:
            Full filesystem path to the track file, or None if invalid
        """
        if not db_track_path:
            return None
        
        return self.download_dir / db_track_path

    def check_track_files(self) -> Dict[str, int]:
        """
        Verify that all track references have corresponding files.
        
        Returns: Statistics about missing files
        """
        # We'll need to add a method to SimpleMusicDB for this
        # For now, use direct query
        
        import sqlite3
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT path_mp3 FROM tracks WHERE path_mp3 IS NOT NULL AND path_mp3 != ''")
        track_paths = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        missing_files = []
        existing_files = []
        
        for track_path in track_paths:
            filepath = self.get_track_filepath(track_path)
            if filepath and filepath.exists():
                existing_files.append(track_path)
            else:
                missing_files.append(track_path)
        
        print(f"📊 Track files verification:")
        print(f"   Total references: {len(track_paths)}")
        print(f"   Files found: {len(existing_files)}")
        print(f"   Files missing: {len(missing_files)}")
        
        return {
            "total_references": len(track_paths),
            "files_found": len(existing_files),
            "files_missing": len(missing_files),
            "missing_list": missing_files[:10]
        }

    def cleanup_orphaned_tracks(self) -> Dict[str, int]:
        """
        Remove track files that are no longer referenced in the database.
        
        Returns: Dictionary with cleanup statistics
        """
        # Get all track paths from database
        import sqlite3
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT path_mp3 FROM tracks WHERE path_mp3 IS NOT NULL AND path_mp3 != ''")
        db_tracks = set(row[0] for row in cursor.fetchall())
        
        conn.close()
        
        track_files = list(self.download_dir.glob("*.mp3"))
        orphaned_files = []
        
        for track_file in track_files:
            if track_file.name not in db_tracks:
                orphaned_files.append(track_file)
        
        removed_count = 0
        for orphaned_file in orphaned_files:
            try:
                orphaned_file.unlink()
                removed_count += 1
                print(f"🗑️  Removed orphaned track: {orphaned_file.name}")
            except Exception as e:
                print(f"✗ Failed to remove {orphaned_file}: {e}")
        
        print(f"🧹 Cleanup removed {removed_count} orphaned tracks")
        
        return {
            "total_tracks_in_db": len(db_tracks),
            "total_files_in_dir": len(track_files),
            "orphaned_removed": removed_count
        }
