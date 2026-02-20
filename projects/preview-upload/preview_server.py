#!/usr/bin/env python3
"""
Simple video preview server for Tailscale network.
Serves the latest video from output dir for mobile review.

Container-aware: reads OUTPUT_DIR and TRAINING_DIR from env vars.
"""

import os
import html
import json
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", Path.home() / "output"))
TRAINING_DIR = Path(os.environ.get("TRAINING_DIR", Path.home() / ".sharingan" / "training"))


def safe_resolve(filename: str, base_dir: Path = OUTPUT_DIR) -> Path | None:
    """Resolve filename within base_dir, preventing path traversal."""
    resolved = (base_dir / filename).resolve()
    if not resolved.is_relative_to(base_dir.resolve()):
        return None
    return resolved


def get_training_podcasts():
    """Get all training podcasts from the Sharingan training directory."""
    if not TRAINING_DIR.exists():
        return []
    podcasts = []
    for mp3 in sorted(TRAINING_DIR.glob("*/podcast.mp3"), key=lambda f: f.stat().st_mtime, reverse=True):
        scroll_name = mp3.parent.name
        meta_path = mp3.parent / "metadata.json"
        meta = {}
        if meta_path.exists():
            with open(meta_path) as f:
                meta = json.load(f)
        size_mb = mp3.stat().st_size / (1024 * 1024)
        podcasts.append({
            "scroll": scroll_name,
            "path": mp3,
            "size_mb": size_mb,
            "level": meta.get("level", "unknown"),
            "domain": meta.get("domain", ""),
            "generated_at": meta.get("generated_at", ""),
        })
    return podcasts


def get_latest_video():
    """Get the most recently created MP4 file in output directory."""
    mp4_files = list(OUTPUT_DIR.glob("*.mp4"))
    if not mp4_files:
        return None
    mp4_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return mp4_files[0]


def get_thumbnail_for_video(video_path):
    """Find a matching thumbnail for the video."""
    if not video_path:
        return None
    stem = video_path.stem
    parent = video_path.parent
    for pattern in [
        f"{stem}.thumb.png", f"{stem}.thumb.jpg",
        f"{stem}_thumb.png", f"{stem}_thumb.jpg",
        f"{stem}_thumb_v2.png", f"{stem}_thumb_v2.jpg",
    ]:
        thumb = parent / pattern
        if thumb.exists():
            return thumb
    base = stem.rsplit("_", 2)[0] if "_" in stem else stem
    for ext in ("png", "jpg"):
        for thumb in parent.glob(f"{base}*thumb*.{ext}"):
            return thumb
    return None


class PreviewHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {format % args}")

    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == "/" or path == "/preview":
            self.serve_preview()
        elif path.startswith("/video/"):
            filename = path.replace("/video/", "")
            self.serve_video(filename)
        elif path.startswith("/thumb/"):
            filename = path.replace("/thumb/", "")
            self.serve_image(filename)
        elif path.startswith("/download/"):
            filename = path.replace("/download/", "")
            self.serve_download(filename)
        elif path == "/training":
            self.serve_training()
        elif path.startswith("/audio/"):
            scroll_name = path.replace("/audio/", "")
            self.serve_audio(scroll_name)
        elif path == "/list":
            self.serve_list()
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        if self.path == "/action/approve":
            self.handle_approve()
        elif self.path == "/action/reject":
            self.handle_reject()
        else:
            self.send_error(404, "Not Found")

    def serve_preview(self):
        latest = get_latest_video()

        if not latest:
            page = """
            <html>
                <head><title>No Video Found</title></head>
                <body style="font-family: sans-serif; padding: 20px;">
                    <h1>No videos found</h1>
                    <p>No .mp4 files in output directory.</p>
                </body>
            </html>
            """
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(page.encode())
            return

        video_name = html.escape(latest.name)
        file_size_mb = latest.stat().st_size / (1024 * 1024)

        thumb = get_thumbnail_for_video(latest)
        thumb_html = ""
        if thumb:
            safe_thumb = html.escape(thumb.name)
            thumb_html = f"""
                <div class="section-label">Thumbnail</div>
                <img src="/thumb/{safe_thumb}" class="thumbnail" alt="Thumbnail">
            """

        page = f"""
        <html>
            <head>
                <title>Preview: {video_name}</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                        margin: 0; padding: 20px; background: #1a1a1a; color: #fff;
                    }}
                    h1 {{ font-size: 24px; margin-bottom: 10px; }}
                    .info {{ color: #888; font-size: 14px; margin-bottom: 20px; }}
                    video {{ width: 100%; max-width: 100%; border-radius: 8px; background: #000; }}
                    .thumbnail {{ width: 100%; max-width: 100%; border-radius: 8px; margin-top: 8px; border: 1px solid #333; }}
                    .section-label {{ color: #00c8ff; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-top: 24px; margin-bottom: 4px; }}
                    .buttons {{ display: flex; gap: 10px; margin-top: 20px; }}
                    button, .btn {{ flex: 1; padding: 15px; font-size: 18px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; text-align: center; text-decoration: none; display: inline-block; }}
                    .save {{ background: #3498db; color: white; }}
                    .approve {{ background: #2ecc71; color: white; }}
                    .reject {{ background: #e74c3c; color: white; }}
                    .status {{ margin-top: 20px; padding: 15px; border-radius: 8px; display: none; }}
                    .status.show {{ display: block; }}
                    .status.approved {{ background: #27ae60; }}
                    .status.rejected {{ background: #c0392b; }}
                </style>
            </head>
            <body>
                <h1>Latest Preview</h1>
                <div class="info">
                    <strong>{video_name}</strong><br>
                    Size: {file_size_mb:.1f} MB
                </div>

                <div class="section-label">Video</div>
                <video controls autoplay playsinline>
                    <source src="/video/{video_name}?t={int(latest.stat().st_mtime)}" type="video/mp4">
                    Your browser doesn't support video playback.
                </video>

                {thumb_html}

                <div class="buttons">
                    <a href="/download/{video_name}" class="btn save">Save Video</a>
                    <button class="approve" onclick="handleAction('approve')">Approve</button>
                    <button class="reject" onclick="handleAction('reject')">Reject</button>
                </div>

                <div id="status" class="status"></div>

                <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #333;">
                    <a href="/training" style="color: #a78bfa; text-decoration: none; font-size: 14px;">Training Dojo Podcasts</a>
                </div>

                <script>
                    function handleAction(action) {{
                        const status = document.getElementById('status');
                        if (action === 'approve') {{
                            status.className = 'status show approved';
                            status.textContent = 'Approved! Ready to post.';
                            fetch('/action/approve', {{method: 'POST'}});
                        }} else {{
                            status.className = 'status show rejected';
                            status.textContent = 'Rejected. Will not post.';
                            fetch('/action/reject', {{method: 'POST'}});
                        }}
                    }}
                </script>
            </body>
        </html>
        """

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(page.encode())

    def serve_video(self, filename):
        video_path = safe_resolve(filename)
        if not video_path or not video_path.exists() or not video_path.is_file():
            self.send_error(404, "Video not found")
            return

        file_size = video_path.stat().st_size
        range_header = self.headers.get('Range')
        if range_header:
            byte_range = range_header.replace('bytes=', '').split('-')
            start = int(byte_range[0]) if byte_range[0] else 0
            end = int(byte_range[1]) if len(byte_range) > 1 and byte_range[1] else file_size - 1

            self.send_response(206)
            self.send_header('Content-type', 'video/mp4')
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
            self.send_header('Content-Length', str(end - start + 1))
            self.end_headers()

            with open(video_path, 'rb') as f:
                f.seek(start)
                self.wfile.write(f.read(end - start + 1))
        else:
            self.send_response(200)
            self.send_header('Content-type', 'video/mp4')
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Content-Length', str(file_size))
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()

            with open(video_path, 'rb') as f:
                self.wfile.write(f.read())

    def serve_image(self, filename):
        image_path = safe_resolve(filename)
        if not image_path or not image_path.exists() or not image_path.is_file():
            self.send_error(404, "Image not found")
            return

        ext = image_path.suffix.lower()
        mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}.get(ext, "image/png")
        file_size = image_path.stat().st_size

        self.send_response(200)
        self.send_header('Content-type', mime)
        self.send_header('Content-Length', str(file_size))
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()

        with open(image_path, 'rb') as f:
            self.wfile.write(f.read())

    def serve_download(self, filename):
        video_path = safe_resolve(filename)
        if not video_path or not video_path.exists() or not video_path.is_file():
            self.send_error(404, "Video not found")
            return

        file_size = video_path.stat().st_size
        self.send_response(200)
        self.send_header('Content-Type', 'video/mp4')
        safe_dl_name = filename.replace('"', '_').replace('\\', '_')
        self.send_header('Content-Disposition', f'attachment; filename="{safe_dl_name}"')
        self.send_header('Content-Length', str(file_size))
        self.end_headers()

        with open(video_path, 'rb') as f:
            self.wfile.write(f.read())

    def serve_list(self):
        mp4_files = sorted(OUTPUT_DIR.glob("*.mp4"), key=lambda f: f.stat().st_mtime, reverse=True)

        if not mp4_files:
            page = "<html><body><h1>No videos found</h1></body></html>"
        else:
            video_list = ""
            for video in mp4_files[:20]:
                size_mb = video.stat().st_size / (1024 * 1024)
                safe_name = html.escape(video.name)
                video_list += f'<li><a href="/video/{safe_name}">{safe_name}</a> ({size_mb:.1f} MB)</li>'

            page = f"""
            <html>
                <head><title>Video List</title></head>
                <body style="font-family: sans-serif; padding: 20px;">
                    <h1>Available Videos</h1>
                    <ul>{video_list}</ul>
                </body>
            </html>
            """

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(page.encode())

    def serve_training(self):
        podcasts = get_training_podcasts()

        if not podcasts:
            items_html = "<p style='color: #888;'>No podcasts yet.</p>"
        else:
            items_html = ""
            for p in podcasts:
                safe_scroll = html.escape(p["scroll"])
                level = html.escape(p["level"])
                domain = html.escape(p["domain"])
                items_html += f"""
                <div style="background: #16161e; border: 1px solid #333; border-radius: 10px; padding: 16px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 18px; font-weight: 600;">{safe_scroll}</span>
                        <span style="color: #a78bfa; font-size: 12px; text-transform: uppercase;">{level}</span>
                    </div>
                    <div style="color: #888; font-size: 13px; margin-bottom: 12px;">{domain} - {p['size_mb']:.1f} MB</div>
                    <audio controls preload="none" style="width: 100%;">
                        <source src="/audio/{safe_scroll}" type="audio/mpeg">
                    </audio>
                </div>
                """

        page = f"""
        <html>
            <head>
                <title>Training Dojo</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #1a1a1a; color: #fff; }}
                    h1 {{ font-size: 24px; margin-bottom: 4px; }}
                    .subtitle {{ color: #888; font-size: 14px; margin-bottom: 24px; }}
                    a {{ color: #00c8ff; text-decoration: none; }}
                </style>
            </head>
            <body>
                <h1>Training Dojo</h1>
                <div class="subtitle">Sharingan scroll podcasts</div>
                {items_html}
                <div style="margin-top: 24px;">
                    <a href="/preview">Back to Preview</a>
                </div>
            </body>
        </html>
        """
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(page.encode())

    def serve_audio(self, scroll_name):
        audio_path = safe_resolve("podcast.mp3", TRAINING_DIR / scroll_name)
        if not audio_path or not audio_path.exists() or not audio_path.is_file():
            self.send_error(404, "Podcast not found")
            return

        file_size = audio_path.stat().st_size
        range_header = self.headers.get('Range')
        if range_header:
            byte_range = range_header.replace('bytes=', '').split('-')
            start = int(byte_range[0]) if byte_range[0] else 0
            end = int(byte_range[1]) if len(byte_range) > 1 and byte_range[1] else file_size - 1

            self.send_response(206)
            self.send_header('Content-type', 'audio/mpeg')
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
            self.send_header('Content-Length', str(end - start + 1))
            self.end_headers()

            with open(audio_path, 'rb') as f:
                f.seek(start)
                self.wfile.write(f.read(end - start + 1))
        else:
            self.send_response(200)
            self.send_header('Content-type', 'audio/mpeg')
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Content-Length', str(file_size))
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()

            with open(audio_path, 'rb') as f:
                self.wfile.write(f.read())

    def handle_approve(self):
        latest = get_latest_video()
        if latest:
            marker = latest.parent / f"{latest.stem}.approved"
            marker.touch()
            print(f"Video approved: {latest.name}")

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "approved"}).encode())

    def handle_reject(self):
        latest = get_latest_video()
        if latest:
            marker = latest.parent / f"{latest.stem}.rejected"
            marker.touch()
            print(f"Video rejected: {latest.name}")

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "rejected"}).encode())


def run_server(port=8081):
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, PreviewHandler)

    print(f"Preview server running on http://0.0.0.0:{port}/preview")
    print(f"Output dir: {OUTPUT_DIR}")
    print(f"Training dir: {TRAINING_DIR}")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Server stopped")
        httpd.server_close()


if __name__ == "__main__":
    run_server()
