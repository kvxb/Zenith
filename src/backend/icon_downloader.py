import requests
from pathlib import Path
import sqlite3
from typing import Optional, Dict, Tuple
import hashlib


class IconDownloader:
    def __init__(self, db_path: str = "playlists_songs.db", icons_dir: str = "src/assets/icons"):
        self.icons_dir = Path(icons_dir)
        self.icons_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        
    def _get_db_path(self, local_file: Path) -> str:
        """Convert absolute/local path to database path format."""
        # Convert to relative path from assets directory
        try:
            # Find the 'assets' directory in the path
            parts = local_file.parts
            if 'assets' in parts:
                # Get everything from 'assets' onward
                assets_index = parts.index('assets')
                db_path = '/'.join(parts[assets_index:])
                return db_path
            else:
                # Fallback: use just the filename in 'icons/' directory
                return f"icons/{local_file.name}"
        except:
            # If anything fails, return the relative path from current directory
            return str(local_file.relative_to(Path.cwd()))
    
    def download_icon(self, url: str) -> Optional[str]:
        """Download icon from URL and return local path for database."""
        if not url:
            return None
        
        # If already a local path in correct format (icons/...), return it
        if url.startswith("icons/") or url.startswith("assets/icons/"):
            # Convert to database format if needed
            if url.startswith("assets/icons/"):
                return url.replace("assets/", "", 1)  # Remove 'assets/' prefix
            return url  # Already in icons/... format
            
        if not url.startswith("http"):
            return None
            
        try:
            # Create filename from URL hash
            filename = hashlib.md5(url.encode()).hexdigest() + ".jpg"
            local_file_path = self.icons_dir / filename
            db_path = f"icons/{filename}"  # Database entry format
            
            # Download if not exists
            if not local_file_path.exists():
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                with open(local_file_path, 'wb') as f:
                    f.write(response.content)
                print(f"✓ Downloaded icon: {filename}")
            else:
                print(f"⏭️  Icon already exists: {filename}")
            
            # Return database path (not filesystem path)
            return db_path
            
        except Exception as e:
            print(f"✗ Failed to download {url}: {e}")
            return None

    def download_all_icons(self) -> Dict[str, int]:
        """Download all Spotify icons from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get only REMOTE URLs (not local paths)
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
        
        all_urls = list(set(track_icons + playlist_icons))
        print(f"Found {len(all_urls)} remote icons to download")
        
        if not all_urls:
            # Check if any icons already exist locally
            cursor.execute("""
                SELECT COUNT(*) FROM tracks WHERE icon LIKE 'icons/%'
                UNION ALL
                SELECT COUNT(*) FROM playlists WHERE icon LIKE 'icons/%'
            """)
            local_counts = cursor.fetchall()
            total_local = sum(count[0] for count in local_counts)
            print(f"✅ All icons are already downloaded locally ({total_local} icons)")
            return {"success": 0, "failed": 0, "already_local": total_local}
        
        results = {"success": 0, "failed": 0}
        
        for url in all_urls:
            db_path = self.download_icon(url)  # Returns 'icons/filename.jpg'
            if db_path:
                results["success"] += 1
                # Update database with local path in 'icons/...' format
                cursor.execute(
                    "UPDATE tracks SET icon = ? WHERE icon = ?",
                    (db_path, url)
                )
                cursor.execute(
                    "UPDATE playlists SET icon = ? WHERE icon = ?",
                    (db_path, url)
                )
            else:
                results["failed"] += 1
        
        conn.commit()
        conn.close()
        print(f"✅ Downloaded {results['success']} icons, {results['failed']} failed")
        return results

    def check_existing_icons(self) -> Dict[str, int]:
        """Check and count existing icons in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Count tracks and playlists with different icon types
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN icon LIKE 'http%' THEN 1 END) as remote_icons,
                COUNT(CASE WHEN icon LIKE 'icons/%' THEN 1 END) as local_icons,
                COUNT(CASE WHEN icon LIKE 'assets/icons/%' THEN 1 END) as old_local_icons
            FROM tracks
            WHERE icon IS NOT NULL AND icon != ''
        """)
        track_counts = cursor.fetchone()
        
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN icon LIKE 'http%' THEN 1 END) as remote_icons,
                COUNT(CASE WHEN icon LIKE 'icons/%' THEN 1 END) as local_icons,
                COUNT(CASE WHEN icon LIKE 'assets/icons/%' THEN 1 END) as old_local_icons
            FROM playlists
            WHERE icon IS NOT NULL AND icon != ''
        """)
        playlist_counts = cursor.fetchone()
        
        conn.close()
        
        return {
            "tracks": {
                "remote": track_counts[0],
                "local": track_counts[1],
                "old_local": track_counts[2]
            },
            "playlists": {
                "remote": playlist_counts[0],
                "local": playlist_counts[1],
                "old_local": playlist_counts[2]
            }
        }
