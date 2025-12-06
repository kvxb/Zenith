# test_simple.py
import os
import sqlite3

# Delete database to start fresh
if os.path.exists("playlists_songs.db"):
    os.remove("playlists_songs.db")
    print("🗑️  Deleted old database")

# Import everything (they're in same directory)
from db_manager import SimpleMusicDB
from spotify_service import SpotifyService
from track_download import SimpleDownloader
import config

print("🎵 TEST STARTING")

# 1. Create database
db = SimpleMusicDB()
print("✅ Database created")

# 2. Import from Spotify
print("\n🔗 IMPORTING FROM SPOTIFY...")
spotify = SpotifyService(config.CLIENT_ID, config.REDIRECT_URI, db)
spotify.authenticate()
stats = spotify.import_all_playlists()
print(f"✅ Imported {stats['tracks_imported']} tracks")

# 3. Download from YouTube
print("\n⬇️  DOWNLOADING FROM YOUTUBE...")
downloader = SimpleDownloader(db)
success, failed = downloader.download_all_tracks()
print(f"✅ Downloaded {success} tracks, {failed} failed")

# 4. Show results
print("\n📊 FINAL RESULTS:")
conn = sqlite3.connect("playlists_songs.db")
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM playlists")
playlists = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM tracks")
total_tracks = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM tracks WHERE path_mp3 IS NOT NULL")
downloaded_tracks = cursor.fetchone()[0]

print(f"Playlists: {playlists}")
print(f"Total tracks: {total_tracks}")
print(f"Downloaded: {downloaded_tracks}")

if total_tracks > 0:
    print(f"Success rate: {downloaded_tracks/total_tracks*100:.1f}%")

# Show some downloaded files
print("\n📁 Downloaded files:")
for file in os.listdir("downloads"):
    if file.endswith(".mp3"):
        size = os.path.getsize(f"downloads/{file}") / 1024 / 1024
        print(f"  {file} ({size:.1f} MB)")
        break  # Just show first one

print("\n🎉 TEST COMPLETE!")
