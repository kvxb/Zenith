import requests
import os
from pathlib import Path
from typing import Optional, Dict
import hashlib
from .db_manager import SimpleMusicDB


class IconDownloader:
    def __init__(self, db: SimpleMusicDB, icons_dir: str):
        """
        Initialize IconDownloader for the new storage system.
        
        Args:
            db: SimpleMusicDB instance
            icons_dir: Full path to the icons directory
        """
        self.db = db
        self.icons_dir = Path(icons_dir)
        
        # Create icons directory if it doesn't exist
        self.icons_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"🖼️  Icon downloader initialized:")
        print(f"   Icons dir: {self.icons_dir}")
    
    def download_icon(self, url: str) -> Optional[str]:
        """Download icon and return FULL filesystem path for database."""
        if not url:
            return None
        
        # If already a local path, return it as-is
        if url.startswith("icons/") or os.path.exists(url):
            return url
            
        if not url.startswith("http"):
            return None
            
        try:
            # Create filename from URL hash
            filename = hashlib.md5(url.encode()).hexdigest() + ".jpg"
            local_file_path = self.icons_dir / filename
            
            # Download if not exists
            if not local_file_path.exists():
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                with open(local_file_path, 'wb') as f:
                    f.write(response.content)
                print(f"✓ Downloaded icon: {filename}")
            else:
                print(f"⏭️  Icon already exists: {filename}")
            
            # Return FULL filesystem path for database
            return str(local_file_path)
            
        except Exception as e:
            print(f"✗ Failed to download {url}: {e}")
            return None
    
    def download_all_icons(self) -> Dict[str, int]:
        """Download all remote icons from database."""
        all_urls = self.db.get_remote_icons()
        print(f"🔍 Found {len(all_urls)} remote icons to download")
        
        if not all_urls:
            print(f"✅ No remote icons found - all icons are local")
            return {"success": 0, "failed": 0, "total": 0}
        
        results = {"success": 0, "failed": 0, "total": len(all_urls)}
        
        for url in all_urls:
            full_path = self.download_icon(url)  # Returns FULL path
            if full_path:
                results["success"] += 1
                # Update database with FULL path
                self.db.update_icon_path(url, full_path)
            else:
                results["failed"] += 1
        
        print(f"✅ Downloaded {results['success']} icons, {results['failed']} failed")
        return results    

    def get_icon_filepath(self, db_icon_path: str) -> Optional[Path]:
        """
        Convert database icon path to filesystem path.
        
        Args:
            db_icon_path: Path from database (e.g., "icons/filename.jpg")
            
        Returns:
            Full filesystem path to the icon file, or None if invalid
        """
        if not db_icon_path or not db_icon_path.startswith("icons/"):
            return None
        
        # Extract filename from database path
        filename = db_icon_path.split("/")[-1]
        return self.icons_dir / filename
    
    def check_icon_status(self) -> Dict[str, Dict[str, int]]:
        """
        Check the status of icons in the database.
        
        Returns: Dictionary with counts of remote vs local icons
        """
        # We'll implement this using SimpleMusicDB methods
        # For now, use direct query as before but wrap it in a new method
        # We'll need to add this method to SimpleMusicDB
        
        # Temporary: use direct query (will be replaced)
        import sqlite3
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # Count tracks icons
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN icon LIKE 'http%' THEN 1 END) as remote,
                COUNT(CASE WHEN icon LIKE 'icons/%' THEN 1 END) as local,
                COUNT(CASE WHEN icon IS NULL OR icon = '' THEN 1 END) as missing
            FROM tracks
        """)
        track_counts = cursor.fetchone()
        
        # Count playlist icons
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN icon LIKE 'http%' THEN 1 END) as remote,
                COUNT(CASE WHEN icon LIKE 'icons/%' THEN 1 END) as local,
                COUNT(CASE WHEN icon IS NULL OR icon = '' THEN 1 END) as missing
            FROM playlists
        """)
        playlist_counts = cursor.fetchone()
        
        conn.close()
        
        return {
            "tracks": {
                "remote": track_counts[0],
                "local": track_counts[1],
                "missing": track_counts[2],
                "total": sum(track_counts[:3])
            },
            "playlists": {
                "remote": playlist_counts[0],
                "local": playlist_counts[1],
                "missing": playlist_counts[2],
                "total": sum(playlist_counts[:3])
            }
        }
    
    def verify_icon_files(self) -> Dict[str, int]:
        """
        Verify that all local icon references have corresponding files.
        
        Returns: Statistics about missing files
        """
        # Get all icon paths from database using SimpleMusicDB
        # We'll need to add a method to get all icon paths
        # For now, use direct query
        
        import sqlite3
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # Get all local icon paths from database
        cursor.execute("SELECT DISTINCT icon FROM tracks WHERE icon LIKE 'icons/%'")
        track_icons = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT DISTINCT icon FROM playlists WHERE icon LIKE 'icons/%'")
        playlist_icons = [row[0] for row in cursor.fetchall()]
        
        all_db_icons = set(track_icons + playlist_icons)
        
        # Check which files exist
        missing_files = []
        existing_files = []
        
        for db_path in all_db_icons:
            filepath = self.get_icon_filepath(db_path)
            if filepath and filepath.exists():
                existing_files.append(db_path)
            else:
                missing_files.append(db_path)
        
        conn.close()
        
        print(f"📊 Icon verification:")
        print(f"   Total references: {len(all_db_icons)}")
        print(f"   Files found: {len(existing_files)}")
        print(f"   Files missing: {len(missing_files)}")
        
        if missing_files:
            print(f"   Missing files: {missing_files[:5]}...")  # Show first 5
        
        return {
            "total_references": len(all_db_icons),
            "files_found": len(existing_files),
            "files_missing": len(missing_files),
            "missing_list": missing_files[:10]  # First 10 for debugging
        }
