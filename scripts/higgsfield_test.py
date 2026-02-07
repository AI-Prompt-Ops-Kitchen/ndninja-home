#!/usr/bin/env python3
"""
Test script for Higgsfield Kling Avatar API
Usage: python higgsfield_test.py --image path/to/image.jpg --audio path/to/audio.wav
"""

import argparse
import os
import sys

try:
    import higgsfield_client
except ImportError:
    print("Install: pip install higgsfield-client")
    sys.exit(1)


def test_kling_avatar(image_path: str, audio_path: str, output_dir: str = "output"):
    """Test Kling Avatar with image + audio -> lip-synced video"""
    
    # Check credentials
    if not os.environ.get("HF_KEY") and not (os.environ.get("HF_API_KEY") and os.environ.get("HF_API_SECRET")):
        print("Set HF_KEY='api-key:api-secret' or HF_API_KEY + HF_API_SECRET")
        sys.exit(1)
    
    print(f"Uploading image: {image_path}")
    image_url = higgsfield_client.upload_file(image_path)
    print(f"  -> {image_url}")
    
    print(f"Uploading audio: {audio_path}")
    audio_url = higgsfield_client.upload_file(audio_path)
    print(f"  -> {audio_url}")
    
    # Try Kling Avatar model
    # Note: Model name may vary - check docs.higgsfield.ai for exact name
    model_candidates = [
        "kling/avatar/v2",
        "kling/avatar",
        "kuaishou/kling/avatar/v2",
        "kling-avatar-2.0",
    ]
    
    print("\nTrying Kling Avatar models...")
    
    for model in model_candidates:
        print(f"\nTrying model: {model}")
        try:
            result = higgsfield_client.subscribe(
                model,
                arguments={
                    "image": image_url,
                    "audio": audio_url,
                    # These params may vary by model
                    "aspect_ratio": "9:16",
                    "prompt": "Static camera, stable framing. Professional presenter speaking to camera. No camera movement or zoom.",
                },
                on_queue_update=lambda s: print(f"  Status: {s}")
            )
            
            if result and "video" in result:
                video_url = result["video"]["url"] if isinstance(result["video"], dict) else result["video"]
                print(f"\n✅ Success with model: {model}")
                print(f"Video URL: {video_url}")
                
                # Download
                os.makedirs(output_dir, exist_ok=True)
                out_path = os.path.join(output_dir, "higgsfield_test.mp4")
                
                import requests
                resp = requests.get(video_url)
                with open(out_path, "wb") as f:
                    f.write(resp.content)
                print(f"Saved to: {out_path}")
                return out_path
                
            elif result:
                print(f"Result keys: {result.keys()}")
                print(f"Full result: {result}")
                
        except Exception as e:
            print(f"  Error: {e}")
            continue
    
    print("\n❌ No working model found. Check docs.higgsfield.ai for correct model name.")
    return None


def list_available_models():
    """Try to list available models (if API supports it)"""
    print("Attempting to list models...")
    # This may or may not work depending on API
    try:
        # Check if there's a list endpoint
        import requests
        key = os.environ.get("HF_KEY", "")
        if ":" in key:
            api_key, api_secret = key.split(":", 1)
        else:
            api_key = os.environ.get("HF_API_KEY", "")
            api_secret = os.environ.get("HF_API_SECRET", "")
        
        # Try common endpoints
        for endpoint in ["https://api.higgsfield.ai/v1/models", "https://cloud.higgsfield.ai/api/models"]:
            try:
                resp = requests.get(endpoint, headers={"Authorization": f"Bearer {api_key}:{api_secret}"}, timeout=10)
                if resp.ok:
                    print(f"Models from {endpoint}:")
                    print(resp.json())
                    return
            except:
                pass
        print("Could not list models. Check docs.higgsfield.ai")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Higgsfield Kling Avatar")
    parser.add_argument("--image", required=True, help="Path to reference image")
    parser.add_argument("--audio", required=True, help="Path to audio file")
    parser.add_argument("--output", default="output", help="Output directory")
    parser.add_argument("--list-models", action="store_true", help="Try to list available models")
    
    args = parser.parse_args()
    
    if args.list_models:
        list_available_models()
    else:
        test_kling_avatar(args.image, args.audio, args.output)
