---
name: tauri-v2-overlay
domain: Desktop/Glitch
level: 2-tomoe
description: Tauri v2 for transparent always-on-top Linux desktop overlay windows — config, system tray, Rust commands, Python sidecar, WebSocket IPC, and Linux X11/Wayland gotchas.
sources:
  - type: docs
    title: "Tauri v2 Getting Started"
    url: "https://v2.tauri.app/start/"
    date: "2026-02-19"
    confidence: high
  - type: docs
    title: "Tauri v2 Configuration Reference"
    url: "https://v2.tauri.app/reference/config/"
    date: "2026-02-19"
    confidence: high
  - type: docs
    title: "Tauri v2 Window Customization"
    url: "https://v2.tauri.app/learn/window-customization/"
    date: "2026-02-19"
    confidence: high
  - type: docs
    title: "Tauri v2 Shell Plugin / Sidecar"
    url: "https://v2.tauri.app/plugin/shell/"
    date: "2026-02-19"
    confidence: high
  - type: docs
    title: "Tauri v2 WebSocket Plugin"
    url: "https://v2.tauri.app/plugin/websocket/"
    date: "2026-02-19"
    confidence: high
  - type: docs
    title: "Tauri v2 System Tray"
    url: "https://v2.tauri.app/learn/system-tray/"
    date: "2026-02-19"
    confidence: high
  - type: github
    title: "Transparent Window Bug (v2)"
    url: "https://github.com/tauri-apps/tauri/issues/8308"
    date: "2026-02-19"
    confidence: medium
  - type: github
    title: "setIgnoreCursorEvents Wayland Bug"
    url: "https://github.com/tauri-apps/tauri/issues/11461"
    date: "2026-02-19"
    confidence: high
last_updated: 2026-02-19
can_do_from_cli: partial
---

# Tauri v2 — Desktop Overlay Window

## Mental Model
Tauri wraps your web frontend (HTML/CSS/JS) in a native desktop window using the system's built-in webview (WebKitGTK on Linux). It's not Electron — no bundled Chromium, apps can be under 600KB. Rust handles the native layer; JS/frontend talks to Rust via `invoke` commands and events. For an overlay, you combine `transparent + decorations:false + alwaysOnTop + skipTaskbar` and spawn the Python AI brain as a sidecar subprocess.

## Prerequisites
- Rust 1.77.2+
- Node.js/Bun
- Linux: `webkit2gtk-4.1` dev package (`sudo apt install libwebkit2gtk-4.1-dev`)
- `create-tauri-app` to scaffold

## Core Workflows

### Workflow 1: Overlay Window Config
**When to use:** Setting up the transparent always-on-top Glitch window

`tauri.conf.json`:
```json
{
  "app": {
    "windows": [{
      "label": "glitch-overlay",
      "url": "index.html",
      "width": 250,
      "height": 370,
      "decorations": false,
      "transparent": true,
      "alwaysOnTop": true,
      "skipTaskbar": true,
      "resizable": false,
      "closable": false,
      "visible": false
    }]
  }
}
```

Start hidden (`visible: false`) → restore state → show. Prevents position flicker on startup.

**Enable dragging without titlebar:**
```html
<div data-tauri-drag-region class="drag-handle"><!-- moves window --></div>
```
Or in JS: `await getCurrentWindow().startDragging()`
Permission needed: `"core:window:allow-start-dragging"`

**Anchor to corner at runtime:**
```bash
npm run tauri add positioner
```
```javascript
import { moveWindow, Position } from '@tauri-apps/plugin-positioner';
await moveWindow(Position.BottomRight);
```

**Gotchas:**
- `transparent` has a known v2 bug on Windows — may need workaround for Win users
- `macOS` requires `macos-private-api` feature flag for transparency
- On Linux, some window properties are ignored by certain window managers (KDE/GNOME)
- `visible: false` on startup + window-state plugin prevents position flicker

---

### Workflow 2: Show / Hide / Toggle
**When to use:** Super+G keybind toggling Glitch on/off

```javascript
import { getCurrentWindow } from '@tauri-apps/api/window';
const win = getCurrentWindow();

// Toggle
if (await win.isVisible()) {
  await win.hide();
} else {
  await win.show();
}

// Modes
await win.setSize(new PhysicalSize(100, 185));   // compact
await win.setSize(new PhysicalSize(250, 370));   // full
await win.setPosition(new PhysicalPosition(x, y));
```

**Gotchas:**
- `isVisible()` is async — always `await` it
- Global hotkeys need a separate plugin (not built-in) — search `tauri-plugin-global-shortcut`

---

### Workflow 3: System Tray
**When to use:** Always-on tray icon for show/hide/quit

`Cargo.toml`:
```toml
tauri = { version = "2", features = ["tray-icon"] }
```

`src-tauri/src/lib.rs`:
```rust
use tauri::menu::{Menu, MenuItem};
use tauri::tray::TrayIconBuilder;

TrayIconBuilder::new()
  .icon(app.default_window_icon().unwrap().clone())
  .menu(&Menu::with_items(app, &[
    &MenuItem::with_id(app, "show", "Show Glitch", true, None::<&str>)?,
    &MenuItem::with_id(app, "hide", "Hide Glitch", true, None::<&str>)?,
    &MenuItem::with_id(app, "quit", "Quit",        true, None::<&str>)?,
  ])?)
  .on_menu_event(|app, event| match event.id.as_ref() {
    "show" => { app.get_webview_window("glitch-overlay").unwrap().show().unwrap(); }
    "hide" => { app.get_webview_window("glitch-overlay").unwrap().hide().unwrap(); }
    "quit" => { app.exit(0); }
    _ => {}
  })
  .build(app)?;
```

**Gotchas:**
- On Linux, the tray icon may be invisible unless a menu is set — always attach a menu
- Cursor events (hover enter/leave on tray) are NOT supported on Linux

---

### Workflow 4: Rust Commands (JS → Rust)
**When to use:** JS frontend triggers a Rust action (spawn process, read file, etc.)

`src-tauri/src/lib.rs`:
```rust
#[tauri::command]
fn set_mode(mode: String) -> String {
  format!("Mode set to {}", mode)
}

#[tauri::command]
async fn get_screen_info() -> Result<String, String> {
  // async ok
  Ok("screen data".into())
}

// Register in builder:
.invoke_handler(tauri::generate_handler![set_mode, get_screen_info])
```

Frontend JS:
```javascript
import { invoke } from '@tauri-apps/api/core';

const result = await invoke('set_mode', { mode: 'compact' });
const info   = await invoke('get_screen_info');
```

**Gotchas:**
- Command args use camelCase in JS, snake_case in Rust — Tauri maps automatically
- Commands can't be `pub` in `lib.rs` root — put in a module if needed
- All types must impl `serde::Serialize`/`Deserialize`

---

### Workflow 5: Events (Rust → JS)
**When to use:** Rust pushes state changes to the frontend (sidecar message received, screen changed)

Rust emit:
```rust
app.emit("avatar-state", serde_json::json!({"state": "talking"}))?;
// or target specific window:
app.emit_to("glitch-overlay", "avatar-state", payload)?;
```

JS listen:
```javascript
import { listen } from '@tauri-apps/api/event';

const unlisten = await listen('avatar-state', (event) => {
  setState(event.payload.state);   // update data-state attribute
});
// Call unlisten() to remove when done
```

---

### Workflow 6: Python Sidecar (AI Brain)
**When to use:** Spawning the Python AI brain as a bundled subprocess

`tauri.conf.json`:
```json
{
  "bundle": {
    "externalBin": ["binaries/glitch-brain"]
  }
}
```

Binary naming (REQUIRED — must match target triple):
```
binaries/glitch-brain-x86_64-unknown-linux-gnu   ← Linux
binaries/glitch-brain-x86_64-pc-windows-msvc.exe ← Windows
binaries/glitch-brain-aarch64-apple-darwin        ← macOS Apple Silicon
```

Get your triple: `rustc --print host-tuple`

Rust spawn:
```rust
use tauri_plugin_shell::ShellExt;

let (mut rx, child) = app.shell()
  .sidecar("binaries/glitch-brain")?
  .spawn()?;

tokio::spawn(async move {
  while let Some(event) = rx.recv().await {
    match event {
      CommandEvent::Stdout(line) => { /* parse JSON messages */ }
      CommandEvent::Terminated(_) => break,
      _ => {}
    }
  }
});
```

**Simpler approach for Glitch:** Don't bundle Python. Start Python brain separately, connect via localhost WebSocket. Bundling requires PyInstaller compilation — complex. For dev/home use, just `subprocess` or systemd service.

**Gotchas:**
- Bundled sidecars need platform-specific binaries — one per OS
- Python scripts can't be bundled directly — must be compiled with PyInstaller first
- For local-only use (Glitch on your machine), running Python separately is simpler

---

### Workflow 7: WebSocket to Python Brain
**When to use:** Real-time bidirectional communication between overlay and Python AI

```bash
npm run tauri add websocket
```

```javascript
import { WebSocket } from '@tauri-apps/plugin-websocket';

const ws = await WebSocket.connect('ws://127.0.0.1:8765');

ws.addListener((msg) => {
  const data = JSON.parse(msg.data);
  if (data.action === 'setState')  setState(data.state);
  if (data.action === 'setMouth')  setMouth(data.viseme);
  if (data.action === 'setEyes')   setEyes(data.eyes);
});

// Send to brain
await ws.send(JSON.stringify({ action: 'speak', text: 'Hello!' }));
```

Permissions (`capabilities/default.json`):
```json
{
  "permissions": [
    "websocket:allow-connect",
    "websocket:allow-send"
  ]
}
```

**Gotchas:**
- The Python brain must be running before the WS connect — add retry logic or wait for sidecar stdout "ready" signal
- Tauri WS plugin behaves differently from browser `WebSocket` — use the plugin import, not native WS

---

## Command Reference

| Action | How | Notes |
|--------|-----|-------|
| Scaffold project | `npm create tauri-app@latest` | Pick Rust + your frontend |
| Add plugin | `npm run tauri add <plugin>` | e.g. `websocket`, `positioner`, `window-state` |
| Build | `npm run tauri build` | Produces native binary |
| Dev mode | `npm run tauri dev` | Hot reload |
| List windows | `getAll()` from `@tauri-apps/api/window` | Returns all WebviewWindows |
| Emit to frontend | `app.emit("event", payload)?` in Rust | JSON payload |
| Invoke Rust | `invoke('command_name', args)` in JS | Awaitable |
| Position to corner | `moveWindow(Position.BottomRight)` | Needs positioner plugin |
| Persist position | `npm run tauri add window-state` | Auto save/restore |

## Integration Points — Glitch
- **Python AI brain:** Start as systemd service or sidecar → connect via `ws://127.0.0.1:8765`
- **Sprite animation:** Tauri webview renders the HTML/CSS sprite overlay (`css-sprite-animation` scroll)
- **Screen awareness:** AT-SPI called from Python brain (separate process) → sends window info over WebSocket
- **ElevenLabs TTS:** Python brain generates audio + viseme timestamps → sends to JS → drives mouth sprites
- **Keybinds:** `tauri-plugin-global-shortcut` for Super+G and Super+Shift+G

## Limitations & Gaps — CRITICAL FOR LINUX

| Issue | Severity | Workaround |
|-------|----------|-----------|
| `setIgnoreCursorEvents` **broken on Wayland** | HIGH | Target X11 only for MVP. Wayland users: use tray as primary interface |
| Transparent window bug (v2 Windows) | MEDIUM | Mostly affects Windows users, Linux fine |
| CSS animation performance on WebKitGTK | MEDIUM | Use transform/opacity only. Avoid filter, box-shadow, backdrop-filter |
| Tray icon invisible on Linux without menu | LOW | Always attach a Menu |
| Global hotkeys need extra plugin | LOW | Add `tauri-plugin-global-shortcut` |
| AT-SPI "could not determine accessibility bus" error | LOW | Graceful degrade, not Tauri's responsibility |
| Python sidecar bundling requires PyInstaller | MEDIUM | Run Python brain separately for local/dev use |

**Click-through on Linux:** Overlay windows that let mouse events pass through to applications underneath are only reliable on X11. On Wayland this is unsupported. For Glitch MVP: use X11, make the window small enough to not be in the way, rather than relying on click-through.

## Tips & Best Practices
- **Start hidden, then show** — `visible: false` + window-state plugin = no startup flicker
- **All capabilities denied by default** — if something doesn't work, check `capabilities/default.json` first
- **Target X11 for MVP** — Wayland has too many overlay limitations. Add Wayland support later.
- **Don't bundle Python for home use** — start the AI brain separately. Bundling (PyInstaller) is a whole project in itself.
- **WebSocket is the right IPC for Glitch** — low latency, bidirectional, works perfectly for avatar state commands from Python brain
- **Use `visible: false` at startup** — always. Avoids window flashing in wrong position before state restores.
- **Rust commands are sync or async** — if your command does I/O, mark it `async` and return `Result<T, String>`
- **Log to stdout from sidecar** — Rust reads it via `CommandEvent::Stdout`. Simple JSON messages work great as a protocol.
