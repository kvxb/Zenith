import requests
from pathlib import Path
import sqlite3
from typing import Optional, Dict
import hashlib


class IconDownloader:
    def __init__(self, db_path: str = "playlists_songs.db", icons_dir: str = "src/assets/icons"):
        self.icons_dir = Path(icons_dir)
        self.icons_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        
    def download_icon(self, url: str) -> Optional[str]:
        """Download icon from URL and return local path."""
        if not url:
            return None
        
        # If already a local path (assets/icons/...), return it
        if url.startswith("assets/icons/"):
            return url
            
        if not url.startswith("http"):
            return None
            
        try:
            # Create filename from URL hash
            filename = hashlib.md5(url.encode()).hexdigest() + ".jpg"
            local_path = self.icons_dir / filename
            
            # Download if not exists
            if not local_path.exists():
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                print(f"✓ Downloaded icon: {filename}")
            else:
                print(f"⏭️  Icon already exists: {filename}")
            
            # Return relative path for database
            return f"assets/icons/{filename}"
            
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
            print("✅ All icons are already downloaded locally")
            return {"success": 0, "failed": 0, "already_local": "all"}
        
        results = {"success": 0, "failed": 0}
        
        for url in all_urls:
            local_path = self.download_icon(url)
            if local_path:
                results["success"] += 1
                # Update database with local path
                cursor.execute(
                    "UPDATE tracks SET icon = ? WHERE icon = ?",
                    (local_path, url)
                )
                cursor.execute(
                    "UPDATE playlists SET icon = ? WHERE icon = ?",
                    (local_path, url)
                )
            else:
                results["failed"] += 1
        
        conn.commit()
        print(f"✅ Downloaded {results['success']} icons, {results['failed']} failed")
        return results        
