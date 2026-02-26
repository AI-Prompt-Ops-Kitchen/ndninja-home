#!/usr/bin/env python3
"""
youtube_auth.py — Handle YouTube OAuth 2.0 authentication

First-time setup:
1. Place client_secrets.json in this directory
2. Run: python youtube_auth.py
3. Complete browser auth flow
4. Token saved to ~/.config/youtube_uploader/token.json
"""

import os
import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
TOKEN_DIR = Path.home() / '.config' / 'youtube_uploader'
TOKEN_FILE = TOKEN_DIR / 'token.json'
CLIENT_SECRETS = Path(__file__).parent / 'client_secrets.json'


def get_credentials(manual_code=None):
    """Get valid credentials, refreshing or re-authenticating as needed."""
    creds = None
    
    # Load existing token
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    
    # Refresh or get new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing access token...")
            creds.refresh(Request())
        else:
            if not CLIENT_SECRETS.exists():
                print(f"❌ Missing {CLIENT_SECRETS}")
                print("   Download OAuth 2.0 Client ID JSON from Google Cloud Console")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS), SCOPES)
            
            if manual_code:
                # Complete flow with provided code
                flow.redirect_uri = 'http://localhost:8080/'
                flow.fetch_token(code=manual_code)
                creds = flow.credentials
            else:
                # Try local server first, fall back to manual code entry
                try:
                    print("🔐 Starting OAuth flow (browser will open)...")
                    creds = flow.run_local_server(port=9090, open_browser=False)
                except Exception as e:
                    print("🔐 Starting manual OAuth flow...")
                    # Set redirect URI for manual flow
                    flow.redirect_uri = 'http://localhost'
                    print("\n" + "="*60)
                    auth_url, _ = flow.authorization_url()
                    print(f"\n1. Open this URL in your browser:\n\n{auth_url}\n")
                    print("2. Authorize the application")
                    print("3. You'll be redirected to localhost (won't load)")
                    print("4. Copy the FULL URL from your browser")
                    print("="*60 + "\n")
                    redirect_response = input("Paste the full redirect URL: ").strip()
                    flow.fetch_token(authorization_response=redirect_response)
                    creds = flow.credentials
        
        # Save credentials
        TOKEN_DIR.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
        print(f"✅ Token saved to {TOKEN_FILE}")
    
    return creds


def main():
    """Run authentication flow."""
    print("🎬 YouTube Uploader Authentication")
    print("=" * 40)
    
    creds = get_credentials()
    if creds:
        print("✅ Authentication successful!")
        print(f"   Token: {TOKEN_FILE}")
    else:
        print("❌ Authentication failed")


if __name__ == "__main__":
    main()
