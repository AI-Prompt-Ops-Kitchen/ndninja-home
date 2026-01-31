#!/usr/bin/env python3
"""
youtube_channel_branding.py — Update YouTube channel branding (banner, profile pic)

Usage:
    python youtube_channel_branding.py --banner banner.png
    python youtube_channel_branding.py --profile profile.png
    python youtube_channel_branding.py --banner banner.png --profile profile.png
"""

import argparse
import base64
import os
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Need broader scope for channel updates
SCOPES = [
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/youtube.upload'
]
TOKEN_DIR = Path.home() / '.config' / 'youtube_uploader'
TOKEN_FILE = TOKEN_DIR / 'branding_token.json'  # Separate token for branding
CLIENT_SECRETS = Path(__file__).parent / 'client_secrets.json'


def get_branding_credentials():
    """Get credentials with channel management scope."""
    creds = None
    
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing access token...")
            creds.refresh(Request())
        else:
            if not CLIENT_SECRETS.exists():
                print(f"❌ Missing {CLIENT_SECRETS}")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS), SCOPES)
            
            # Generate auth URL for manual flow
            auth_url, _ = flow.authorization_url(prompt='consent')
            print("\n🔐 YouTube Channel Branding Authorization Required")
            print("=" * 50)
            print("\n1. Open this URL in your browser:\n")
            print(auth_url)
            print("\n2. Authorize the app")
            print("3. Copy the authorization code from the redirect URL")
            print("   (the 'code' parameter after ?code=)")
            print("\n4. Paste the code here:\n")
            
            code = input("Authorization code: ").strip()
            flow.fetch_token(code=code)
            creds = flow.credentials
        
        TOKEN_DIR.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
        print(f"✅ Token saved to {TOKEN_FILE}")
    
    return creds


def update_channel_banner(banner_path: str):
    """Update the channel banner image."""
    print(f"🎬 Updating channel banner: {banner_path}")
    
    creds = get_branding_credentials()
    if not creds:
        return False
    
    youtube = build('youtube', 'v3', credentials=creds)
    
    # Read and encode image
    with open(banner_path, 'rb') as f:
        banner_data = base64.b64encode(f.read()).decode('utf-8')
    
    # Get current channel
    channels = youtube.channels().list(part='brandingSettings', mine=True).execute()
    
    if not channels['items']:
        print("❌ No channel found")
        return False
    
    channel = channels['items'][0]
    channel_id = channel['id']
    print(f"📺 Channel ID: {channel_id}")
    
    # Update banner
    # YouTube requires the image to be uploaded via channels.update with the bannerExternalUrl
    # OR using the channelBanners.insert endpoint
    
    # Method: Use channelBanners.insert to upload, then channels.update to set
    print("📤 Uploading banner image...")
    
    # Insert banner
    banner_resource = youtube.channelBanners().insert(
        media_body=banner_path
    ).execute()
    
    banner_url = banner_resource['url']
    print(f"✅ Banner uploaded: {banner_url}")
    
    # Update channel branding settings
    print("🔄 Applying banner to channel...")
    
    channel['brandingSettings']['image'] = {
        'bannerExternalUrl': banner_url
    }
    
    youtube.channels().update(
        part='brandingSettings',
        body={
            'id': channel_id,
            'brandingSettings': channel['brandingSettings']
        }
    ).execute()
    
    print("✅ Channel banner updated successfully!")
    return True


def main():
    parser = argparse.ArgumentParser(description="Update YouTube channel branding")
    parser.add_argument("--banner", help="Path to banner image (2560x1440 recommended)")
    parser.add_argument("--auth-only", action="store_true", help="Only run authentication")
    
    args = parser.parse_args()
    
    if args.auth_only:
        creds = get_branding_credentials()
        if creds:
            print("✅ Authentication successful!")
        return
    
    if not args.banner:
        parser.print_help()
        return
    
    if args.banner:
        if not Path(args.banner).exists():
            print(f"❌ Banner file not found: {args.banner}")
            return
        update_channel_banner(args.banner)


if __name__ == "__main__":
    main()
