import spotipy
import os
from spotipy.oauth2 import SpotifyPKCE
from . import config
from .db_manager import SimpleMusicDB
import threading
from typing import Optional, List, Dict, Any


class SpotifyService:
    """
    Handles Spotify authentication and data import using SimpleMusicDB.
    """

    SCOPE = "playlist-read-private playlist-read-collaborative user-library-read"

    def __init__(self, client_id: str, redirect_uri: str, db: SimpleMusicDB, cache_dir: Optional[str] = None):
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.db = db
        self._spotify_client = None
        self.cache_dir = cache_dir  # Add this
    
    def authenticate(self) -> spotipy.Spotify:
        try:
            # Determine cache path
            if self.cache_dir:
                cache_path = os.path.join(self.cache_dir, ".spotify_pkce_cache")
            else:
                cache_path = ".spotify_pkce_cache"
            
            self._spotify_client = spotipy.Spotify(
                auth_manager=SpotifyPKCE(
                    client_id=self.client_id,
                    redirect_uri=self.redirect_uri,
                    scope=self.SCOPE,
                    cache_path=cache_path,  # Changed here
                )
            )

            self._spotify_client.current_user()
            print("✅ Spotify PKCE authentication successful!")
            return self._spotify_client

        except Exception as e:
            print(f"❌ PKCE authentication failed: {e}")
            raise

    def get_client(self) -> spotipy.Spotify:
        """Returns authenticated client"""
        if self._spotify_client is None:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        return self._spotify_client

    def get_current_user(self) -> dict:
        """Returns current user profile"""
        client = self.get_client()
        user_data = client.current_user()
        return {
            "display_name": user_data.get("display_name", "Unknown"),
            "id": user_data.get("id", "Unknown"),
            "email": user_data.get("email", "Not provided"),
        }

    def import_all_playlists(self) -> dict:
        """
        Import all user's playlists and their tracks to database.

        Returns:
            Dictionary with import statistics
        """
        client = self.get_client()

        print("📥 Fetching playlists from Spotify...")

        # Get all playlists
        playlists = []
        results = client.current_user_playlists(limit=50)

        while results:
            playlists.extend(results["items"])
            if results["next"]:
                results = client.next(results)
            else:
                results = None

        print(f"📋 Found {len(playlists)} playlists")

        stats = {
            "total_playlists": len(playlists),
            "playlists_imported": 0,
            "tracks_imported": 0,
            "errors": 0,
        }

        # Import each playlist
        for playlist in playlists:
            try:
                playlist_stats = self._import_playlist(playlist)
                stats["playlists_imported"] += 1
                stats["tracks_imported"] += playlist_stats["tracks_imported"]
                stats["errors"] += playlist_stats["errors"]
            except Exception as e:
                print(f"❌ Error importing playlist '{playlist['name']}': {e}")
                stats["errors"] += 1

        return stats

    def _import_playlist(self, playlist: dict) -> dict:
        """
        Import a single playlist and its tracks.
        """
        playlist_name = playlist["name"]
        playlist_id = playlist["id"]

        print(f"\n🎵 Importing playlist: {playlist_name}")

        # Get playlist details
        try:
            playlist_details = self.get_client().playlist(
                playlist_id, fields="name,images,tracks.total"
            )
        except Exception as e:
            print(f"   ❌ Failed to get playlist details: {e}")
            return {"tracks_imported": 0, "errors": 1}

        # Get playlist cover image
        icon_url = None
        if playlist_details.get("images"):
            icon_url = (
                playlist_details["images"][0]["url"]
                if playlist_details["images"][0]["url"]
                else None
            )

        # Add playlist to database using SimpleMusicDB
        db_playlist_id = self.db.add_playlist(name=playlist_name, icon=icon_url)

        print(f"   Created database playlist ID: {db_playlist_id}")

        # Get tracks with manual pagination
        tracks = []
        offset = 0
        limit = 100

        try:
            while True:
                results = self.get_client().playlist_items(
                    playlist_id, limit=limit, offset=offset, additional_types=["track"]
                )

                if not results or not results.get("items"):
                    break

                for item in results["items"]:
                    if item and item.get("track"):
                        tracks.append(item["track"])

                # Check if we got all tracks
                if len(results["items"]) < limit:
                    break

                offset += limit

        except Exception as e:
            print(f"   ❌ Error fetching tracks: {e}")
            import traceback
            traceback.print_exc()
            return {"tracks_imported": 0, "errors": 1}

        print(f"   Found {len(tracks)} tracks")

        stats = {"tracks_imported": 0, "errors": 0}

        for i, track in enumerate(tracks, 1):
            try:
                # Extract track info
                title = track["name"]
                artists = ", ".join([artist["name"] for artist in track["artists"]])
                duration = track["duration_ms"] // 1000
                album = track.get("album", {}).get("name", "") if track.get("album") else ""

                # Get album cover
                icon_url = None
                if track.get("album") and track["album"].get("images"):
                    icon_url = (
                        track["album"]["images"][0]["url"]
                        if track["album"]["images"][0]["url"]
                        else None
                    )

                # Add to database using SimpleMusicDB
                track_id = self.db.add_track_to_playlist(
                    playlist_id=db_playlist_id,
                    title=title,
                    artist=artists,
                    album=album,
                    duration=duration,
                    icon=icon_url,
                )

                stats["tracks_imported"] += 1

                if i % 10 == 0:
                    print(f"   Imported {i}/{len(tracks)} tracks...")

            except Exception as e:
                print(f"   ❌ Error importing track {i}: {e}")
                stats["errors"] += 1

        # Update playlist stats
        self._update_playlist_stats(db_playlist_id)

        print(f"   ✅ Imported {stats['tracks_imported']} tracks")
        return stats

    def _update_playlist_stats(self, db_playlist_id: int):
        """
        Update song count and total duration for a playlist.
        """
        # Use SimpleMusicDB's execute_query method
        results = self.db.execute_query(
            """
            SELECT COUNT(pt.track_id), SUM(t.duration)
            FROM playlist_tracks pt
            JOIN tracks t ON pt.track_id = t.id
            WHERE pt.playlist_id = ?
            """,
            (db_playlist_id,)
        )

        if results and results[0]:
            song_count = results[0][0] or 0
            total_duration = results[0][1] or 0
            
            # Update using SimpleMusicDB
            self.db.execute_update(
                """
                UPDATE playlists 
                SET song_count = ?, total_duration = ?
                WHERE id = ?
                """,
                (song_count, total_duration, db_playlist_id)
            )

    def import_saved_tracks(self) -> dict:
        """
        Import user's saved tracks (liked songs) as a playlist.

        Returns:
            Dictionary with import statistics
        """
        client = self.get_client()

        print("📥 Fetching saved tracks from Spotify...")

        # Create a playlist for saved tracks using SimpleMusicDB
        db_playlist_id = self.db.add_playlist(name="Liked Songs", icon=None)

        # Get all saved tracks
        tracks = []
        results = client.current_user_saved_tracks(limit=50)

        while results:
            for item in results["items"]:
                if item["track"]:
                    tracks.append(item["track"])

            if results["next"]:
                results = client.next(results)
            else:
                results = None

        print(f"📋 Found {len(tracks)} saved tracks")

        stats = {"tracks_imported": 0, "errors": 0}

        # Import each track
        for i, track in enumerate(tracks, 1):
            try:
                # Extract track info
                title = track["name"]
                artists = ", ".join([artist["name"] for artist in track["artists"]])
                duration = track["duration_ms"] // 1000
                album = track.get("album", {}).get("name", "") if track.get("album") else ""

                # Get album cover
                icon_url = None
                if track.get("album") and track["album"].get("images"):
                    icon_url = (
                        track["album"]["images"][0]["url"]
                        if track["album"]["images"][0]["url"]
                        else None
                    )

                # Add to database using SimpleMusicDB
                self.db.add_track_to_playlist(
                    playlist_id=db_playlist_id,
                    title=title,
                    artist=artists,
                    album=album,
                    duration=duration,
                    icon=icon_url,
                )

                stats["tracks_imported"] += 1

                if i % 10 == 0:
                    print(f"   Imported {i}/{len(tracks)} tracks...")

            except Exception as e:
                print(f"   ❌ Error importing track {i}: {e}")
                stats["errors"] += 1

        # Update playlist stats
        self._update_playlist_stats(db_playlist_id)

        print(f"✅ Imported {stats['tracks_imported']} saved tracks")
        return stats

    def get_playlist_tracks_count(self, playlist_id: str) -> int:
        """
        Get the number of tracks in a Spotify playlist.
        """
        try:
            playlist = self.get_client().playlist(
                playlist_id, fields="tracks.total"
            )
            return playlist.get("tracks", {}).get("total", 0)
        except Exception as e:
            print(f"Error getting playlist track count: {e}")
            return 0
