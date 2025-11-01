import spotipy
import config
import csv
import os
from spotipy.oauth2 import SpotifyOAuth

# Define Spotify API permissions
SCOPE = "playlist-read-private playlist-read-collaborative"

def authenticate_user():
    """
    Opens Spotify login in browser, lets user authenticate, and returns a Spotify object.
    """
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=config.CLIENT_ID,
        client_secret=config.CLIENT_SECRET,
        redirect_uri=config.REDIRECT_URI,
        scope=SCOPE
    ))
    return sp

def get_user_playlists(sp):
    """
    Fetch all playlists for the authenticated user.
    """
    playlists = sp.current_user_playlists()
    results = []
    for playlist in playlists['items']:
        results.append({
            "name": playlist['name'],
            "id": playlist['id'],
            "tracks_total": playlist['tracks']['total']
        })
    return results

def get_tracks_from_playlist(sp, playlist_id):
    """
    Returns all tracks from a given playlist as a list of dicts.
    Each track dict contains: name, artists, album
    """
    tracks_data = sp.playlist_items(playlist_id)
    tracks = []
    for item in tracks_data['items']:
        track = item['track']
        tracks.append({
            "name": track['name'],
            "artists": ", ".join([a['name'] for a in track['artists']]),
            "album": track['album']['name']
        })
    return tracks

def generate_csv(tracks, filename):
    """
    Writes playlist tracks to a CSV file under /exports.
    """
    output_dir = "exports"
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["name", "artists", "album"])
        writer.writeheader()
        writer.writerows(tracks)
    print(f"✅ Saved CSV: {os.path.abspath(path)}")

def export_selected_playlists(sp, playlist_ids):
    """
    Given a list of playlist IDs, exports each one to a CSV.
    """
    playlists = sp.current_user_playlists()["items"]
    id_to_name = {p["id"]: p["name"] for p in playlists}

    for pid in playlist_ids:
        name = id_to_name.get(pid, pid)
        print(f"\nExporting '{name}'...")
        tracks = get_tracks_from_playlist(sp, pid)
        filename = f"{name.replace('/', '_')}.csv"
        generate_csv(tracks, filename)

