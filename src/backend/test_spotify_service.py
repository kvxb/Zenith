#!/usr/bin/env python3
from spotify_service import SpotifyAuthenticator
import config

def test_pkce_authentication():
    print("🎵 Testing Spotify PKCE Authentication...")
    print("=" * 50)
    
    try:
        # Initialize with just client_id - no secret!
        auth = SpotifyAuthenticator(
            client_id=config.CLIENT_ID,
            redirect_uri=config.REDIRECT_URI
        )
        
        print("✅ PKCE Authenticator created successfully")
        print("🔐 Using secure PKCE flow (no client secret needed!)")
        
        # This will open browser for authentication
        print("\n🔄 Starting PKCE flow...")
        sp_client = auth.authenticate()
        
        # Test API access
        print("\n🧪 Testing API access...")
        user_info = auth.get_current_user()
        print(f"✅ Logged in as: {user_info['display_name']}")
        
        # Test playlist access
        playlists = sp_client.current_user_playlists()
        print(f"📁 Number of playlists: {len(playlists['items'])}")
        
        print("\n🎉 PKCE authentication working perfectly!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_pkce_authentication()
