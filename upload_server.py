#!/usr/bin/env python3
"""Quick upload server for receiving files from mobile devices."""
import os
import re
import html as html_mod
from http.server import HTTPServer, BaseHTTPRequestHandler

UPLOAD_DIR = "/home/ndninja/uploads"

HTML = """<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ninja Upload</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0f0f13;color:#eee;font-family:system-ui,-apple-system,sans-serif;min-height:100vh;display:flex;justify-content:center;align-items:center}
.scene{text-align:center;width:90%;max-width:420px}
.box{background:#1a1a2e;border:2px dashed #6366f1;border-radius:16px;padding:40px}
.box h1{font-size:1.5em;margin-bottom:8px}
.box p{color:#888;font-size:0.9em}
input[type=file]{margin:20px 0;color:#aaa}
.btn{background:#6366f1;color:#fff;border:none;padding:12px 32px;border-radius:8px;font-size:1em;cursor:pointer;font-weight:500}
.btn:hover{background:#818cf8}

.loading{display:none;flex-direction:column;align-items:center;gap:24px}
.loading.show{display:flex}
.load-label{font-size:0.7em;color:#444;text-transform:uppercase;letter-spacing:3px;font-weight:600}
.lcards{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.lcard{background:#16161e;border:1px solid #222;border-radius:10px;padding:12px 16px;display:flex;align-items:center;gap:10px;font-size:0.85em;font-weight:500;color:#555;transition:all 0.5s}
.lcard.active{border-color:#333;color:#eee}
.pxi{flex-shrink:0;width:3px;height:3px;border-radius:1px;margin:8px 6px}
.pxi-xp{background:#4ade80;animation:xp 1.2s ease-in-out infinite}
@keyframes xp{
  0%,100%{box-shadow:-6px -6px 0 #4ade80,6px -6px 0 #4ade80,-6px 6px 0 #4ade80,6px 6px 0 #4ade80}
  50%{box-shadow:0 -8px 0 #22c55e,8px 0 0 #22c55e,0 8px 0 #22c55e,-8px 0 0 #22c55e}
}
.pxi-grid{background:#60a5fa;animation:gfill 1.8s ease-in-out infinite}
@keyframes gfill{
  0%,100%{box-shadow:7px 0 0 #60a5fa,14px 0 0 #60a5fa,0 7px 0 #60a5fa,7px 7px 0 #60a5fa,14px 7px 0 #60a5fa,0 14px 0 #60a5fa,7px 14px 0 #60a5fa,14px 14px 0 #60a5fa}
  50%{box-shadow:7px 0 0 #2563eb,14px 0 0 #1e40af,0 7px 0 #3b82f6,7px 7px 0 #60a5fa,14px 7px 0 #3b82f6,0 14px 0 #1e40af,7px 14px 0 #2563eb,14px 14px 0 #3b82f6}
}
</style></head><body>
<div class="scene">
  <div class="box" id="uploadBox">
    <h1>Ninja File Drop</h1>
    <p>Drop your file here</p>
    <form id="uploadForm" method="POST" enctype="multipart/form-data">
      <input type="file" name="file" id="fileInput" accept="image/*,video/*"><br><br>
      <button type="submit" class="btn">Upload</button>
    </form>
  </div>
  <div class="loading" id="loading">
    <div class="load-label">uploading</div>
    <div class="lcards">
      <div class="lcard active" id="cRecv"><div class="pxi pxi-xp"></div>Receiving</div>
      <div class="lcard" id="cSave"><div class="pxi pxi-grid"></div>Saving</div>
    </div>
  </div>
</div>
<script>
document.getElementById('uploadForm').onsubmit=function(e){
  e.preventDefault();
  var f=document.getElementById('fileInput').files[0];
  if(!f)return;
  document.getElementById('uploadBox').style.display='none';
  document.getElementById('loading').classList.add('show');
  var fd=new FormData();fd.append('file',f);
  fetch('',{method:'POST',body:fd})
    .then(function(r){return r.text()})
    .then(function(h){
      document.getElementById('cRecv').classList.remove('active');
      document.getElementById('cSave').classList.add('active');
      setTimeout(function(){document.open();document.write(h);document.close()},800);
    })
    .catch(function(err){alert('Upload failed: '+err);location.reload()});
};
</script>
</body></html>"""

SUCCESS = """<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Upload Complete</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0f0f13;color:#eee;font-family:system-ui;display:flex;justify-content:center;align-items:center;min-height:100vh}}
.done{{background:#16161e;border:1px solid #4ade80;border-radius:16px;padding:40px;text-align:center;max-width:400px;width:90%}}
.done h1{{color:#4ade80;margin-bottom:12px;font-size:1.4em}}
.done p{{color:#888;font-size:0.9em;margin-top:8px}}
.check{{width:3px;height:3px;border-radius:1px;background:#4ade80;margin:0 auto 20px;
  box-shadow:6px 6px 0 #4ade80,12px 12px 0 #4ade80,-6px 6px 0 #4ade80,-12px 0 0 #4ade80,-18px -6px 0 #4ade80}}
</style></head><body>
<div class="done">
<div class="check"></div>
<h1>Upload Complete!</h1>
<p>File saved: {filename}</p>
<p>You can close this tab.</p>
</div></body></html>"""


def parse_multipart(body: bytes, boundary: bytes):
    """Parse multipart form data without the cgi module."""
    parts = body.split(b"--" + boundary)
    for part in parts:
        if b"Content-Disposition" not in part:
            continue
        header_end = part.find(b"\r\n\r\n")
        if header_end == -1:
            continue
        header = part[:header_end].decode("utf-8", errors="replace")
        data = part[header_end + 4:]
        if data.endswith(b"\r\n"):
            data = data[:-2]
        # Extract filename
        match = re.search(r'filename="([^"]+)"', header)
        if match:
            return match.group(1), data
    return None, None


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(HTML.encode())

    def do_POST(self):
        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self.send_error(400)
            return

        # Extract boundary
        match = re.search(r"boundary=(.+)", content_type)
        if not match:
            self.send_error(400, "No boundary")
            return
        boundary = match.group(1).strip().encode()

        # Read body
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        filename, file_data = parse_multipart(body, boundary)
        if filename and file_data:
            filename = os.path.basename(filename)
            filepath = os.path.join(UPLOAD_DIR, filename)
            if os.path.exists(filepath):
                base, ext = os.path.splitext(filename)
                n = 1
                while os.path.exists(filepath):
                    filename = f"{base}_{n}{ext}"
                    filepath = os.path.join(UPLOAD_DIR, filename)
                    n += 1
            with open(filepath, "wb") as f:
                f.write(file_data)
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(SUCCESS.format(filename=html_mod.escape(filename)).encode())
            print(f"Saved: {filepath} ({len(file_data)} bytes)")
        else:
            self.send_error(400, "No file found in upload")

    def log_message(self, format, *args):
        print(f"[upload] {args[0]}")


os.makedirs(UPLOAD_DIR, exist_ok=True)
print(f"Upload server running on http://100.77.248.9:8082")
HTTPServer(("0.0.0.0", 8082), Handler).serve_forever()
