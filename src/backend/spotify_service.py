import spotipy
from spotipy.oauth2 import SpotifyPKCE
import config

class SpotifyAuthenticator:
    """
    Handles Spotify PKCE authentication - NO CLIENT SECRET NEEDED!
    """
    
    SCOPE = "playlist-read-private playlist-read-collaborative user-library-read"
    
    def __init__(self, client_id: str, redirect_uri: str):
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self._spotify_client = None
    
    def authenticate(self) -> spotipy.Spotify:
        """
        Performs PKCE OAuth flow - opens browser for user login.
        """
        try:
            self._spotify_client = spotipy.Spotify(auth_manager=SpotifyPKCE(
                client_id=self.client_id,
                redirect_uri=self.redirect_uri,
                scope=self.SCOPE,
                cache_path=".spotify_pkce_cache"
            ))
            
            self._spotify_client.current_user()
            print("✅ Spotify PKCE authentication successful!")
            return self._spotify_client
            
        except Exception as e:
            print(f"❌ PKCE authentication failed: {e}")
            raise
    
    # def get_client(self) -> spotipy.Spotify:
    #     """Returns authenticated client"""
    #     if self._spotify_client is None:
    #         raise RuntimeError("Not authenticated. Call authenticate() first.")
    #     return self._spotify_client
    
    def get_current_user(self) -> dict:
        """Returns current user profile"""
        client = self.get_client()
        user_data = client.current_user()
        return {
            'display_name': user_data.get('display_name', 'Unknown'),
            'id': user_data.get('id', 'Unknown'),
            'email': user_data.get('email', 'Not provided'),
        }
