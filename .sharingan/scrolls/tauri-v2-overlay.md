---
name: tauri-v2-overlay
domain: Desktop/Glitch
level: 3-tomoe
description: Tauri v2 transparent always-on-top Linux overlay — config, tray, Rust commands + state, Channel API, global shortcuts, Python WS IPC, X11/Wayland gotchas.
sources:
  - { type: docs, title: "Tauri v2 Getting Started", url: "https://v2.tauri.app/start/" }
  - { type: docs, title: "Tauri v2 Config Reference", url: "https://v2.tauri.app/reference/config/" }
  - { type: docs, title: "Tauri v2 Window Customization", url: "https://v2.tauri.app/learn/window-customization/" }
  - { type: docs, title: "Tauri v2 Calling Rust", url: "https://v2.tauri.app/develop/calling-rust/" }
  - { type: docs, title: "Tauri v2 State Management", url: "https://v2.tauri.app/develop/state-management/" }
  - { type: docs, title: "Tauri v2 Global Shortcut", url: "https://v2.tauri.app/plugin/global-shortcut/" }
  - { type: docs, title: "Tauri v2 Window State", url: "https://v2.tauri.app/plugin/window-state/" }
  - { type: docs, title: "Tauri v2 IPC / Channel API", url: "https://v2.tauri.app/concept/inter-process-communication/" }
  - { type: docs, title: "Tauri v2 Shell / Sidecar", url: "https://v2.tauri.app/plugin/shell/" }
  - { type: docs, title: "Tauri v2 WebSocket Plugin", url: "https://v2.tauri.app/plugin/websocket/" }
  - { type: github, title: "setIgnoreCursorEvents Wayland Bug", url: "https://github.com/tauri-apps/tauri/issues/11461" }
  - { type: github, title: "Wayland+NVIDIA Overlay Workaround", url: "https://github.com/overlayeddev/overlayed/issues/263" }
  - { type: github, title: "Window Props Ignored on Linux", url: "https://github.com/tauri-apps/tauri/issues/6162" }
sources_count: 13
last_updated: 2026-02-23
can_do_from_cli: partial
---

# Tauri v2 -- Desktop Overlay Window

## Mental Model
Tauri = system webview (WebKitGTK on Linux) + Rust native layer. Not Electron -- no bundled Chromium, apps under 600KB. JS talks to Rust via `invoke` commands and events. For overlay: `transparent + decorations:false + alwaysOnTop + skipTaskbar`.

**Versions (Feb 2026):** tauri-bundler 2.8.0, wry 0.54.2, tao 0.34.5

## Prerequisites
```bash
# Linux deps
sudo apt install libwebkit2gtk-4.1-dev libappindicator3-dev librsvg2-dev patchelf
# Scaffold
npm create tauri-app@latest
```
Requires Rust 1.77.2+ and Node.js/Bun.

## 1: Overlay Window Config
`tauri.conf.json`:
```json
{ "app": { "windows": [{
  "label": "glitch-overlay", "url": "index.html",
  "width": 250, "height": 370,
  "decorations": false, "transparent": true,
  "alwaysOnTop": true, "skipTaskbar": true,
  "resizable": false, "closable": false, "visible": false
}]}}
```
Start hidden (`visible: false`) -> restore state -> show. No flicker.

**Drag:** `<div data-tauri-drag-region>` or `await getCurrentWindow().startDragging()`
**Anchor:** `npm run tauri add positioner` then `moveWindow(Position.BottomRight)`

## 2: Show / Hide / Toggle
```javascript
import { getCurrentWindow } from '@tauri-apps/api/window';
import { PhysicalSize, PhysicalPosition } from '@tauri-apps/api/dpi';
const win = getCurrentWindow();
if (await win.isVisible()) await win.hide(); else await win.show();
await win.setSize(new PhysicalSize(100, 185));   // compact
await win.setSize(new PhysicalSize(250, 370));   // full
```

## 3: Global Shortcuts (Super+G)
```bash
npm run tauri add global-shortcut
```
```rust
use tauri_plugin_global_shortcut::{Code, GlobalShortcutExt, Modifiers, Shortcut, ShortcutState};

let toggle = Shortcut::new(Some(Modifiers::SUPER), Code::KeyG);
let focus  = Shortcut::new(Some(Modifiers::SUPER | Modifiers::SHIFT), Code::KeyG);

app.plugin(
    tauri_plugin_global_shortcut::Builder::new()
        .with_handler(move |app, shortcut, event| {
            if event.state != ShortcutState::Pressed { return; }
            let win = app.get_webview_window("glitch-overlay").unwrap();
            if shortcut == &toggle {
                if win.is_visible().unwrap() { win.hide().unwrap(); }
                else { win.show().unwrap(); win.set_focus().unwrap(); }
            } else if shortcut == &focus {
                app.emit("focus-mode-toggle", ()).unwrap();
            }
        })
        .build(),
)?;
app.global_shortcut().register(toggle)?;
app.global_shortcut().register(focus)?;
```
Permissions: `"global-shortcut:allow-register"`, `"global-shortcut:allow-unregister"`

## 4: System Tray
`Cargo.toml`: `tauri = { version = "2", features = ["tray-icon"] }`
```rust
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
Gotcha: Linux tray icon invisible unless a menu is attached.

## 5: Rust Commands + State Management
```rust
use std::sync::Mutex;
use tauri::State;

#[derive(Default)]
struct GlitchState { mode: String, is_speaking: bool }
type AppState = Mutex<GlitchState>;

#[tauri::command]
fn set_mode(mode: String, state: State<'_, AppState>) -> Result<String, String> {
    let mut s = state.lock().map_err(|e| e.to_string())?;
    s.mode = mode.clone();
    Ok(format!("Mode set to {}", mode))
}

// Register: .manage(Mutex::new(GlitchState::default()))
//           .invoke_handler(tauri::generate_handler![set_mode])
```
```javascript
const result = await invoke('set_mode', { mode: 'compact' });
```

**Key rules:** camelCase JS args -> snake_case Rust (auto-mapped). No `Arc` needed -- Tauri wraps internally. All types need `serde::Serialize/Deserialize`. `generate_handler!` called ONCE with all commands.

**Error handling (thiserror):**
```rust
#[derive(Debug, thiserror::Error)]
enum GlitchError {
    #[error("Brain not connected: {0}")]
    BrainDisconnected(String),
    #[error(transparent)]
    Io(#[from] std::io::Error),
}
impl serde::Serialize for GlitchError {
    fn serialize<S: serde::Serializer>(&self, s: S) -> Result<S::Ok, S::Error> {
        s.serialize_str(self.to_string().as_ref())
    }
}
```

## 6: Channel API (Rust -> JS Streaming)
Faster than events, ordered. Use for viseme frames, progress, high-throughput data.
```rust
use tauri::ipc::Channel;
#[tauri::command]
async fn stream_visemes(channel: Channel<serde_json::Value>) {
    for v in get_viseme_sequence().await {
        channel.send(serde_json::json!({"mouth": v.shape, "ts": v.time_ms})).unwrap();
    }
}
```
```javascript
import { invoke, Channel } from '@tauri-apps/api/core';
const ch = new Channel();
ch.onmessage = (msg) => setMouthShape(msg.mouth);
await invoke('stream_visemes', { channel: ch });
```
**Channel vs Events:** Channel = ordered streaming within a command. Events = fire-and-forget broadcast from anywhere.

## 7: Events (Rust -> JS Broadcast)
```rust
app.emit("avatar-state", serde_json::json!({"state": "talking"}))?;
```
```javascript
const unlisten = await listen('avatar-state', (e) => setState(e.payload.state));
```

## 8: Python Brain (WebSocket IPC)
Don't bundle Python. Run brain as separate service, connect via localhost WS.
```bash
npm run tauri add websocket
```
```javascript
import { WebSocket } from '@tauri-apps/plugin-websocket';
const ws = await WebSocket.connect('ws://127.0.0.1:8765');
ws.addListener((msg) => {
    const data = JSON.parse(msg.data);
    if (data.action === 'setState') setState(data.state);
    if (data.action === 'setMouth') setMouth(data.viseme);
});
await ws.send(JSON.stringify({ action: 'speak', text: 'Hello!' }));
```
Permissions: `"websocket:allow-connect"`, `"websocket:allow-send"`

Sidecar naming (if bundling later): `binaries/glitch-brain-x86_64-unknown-linux-gnu` (get triple: `rustc --print host-tuple`)

## 9: Window State Persistence
```bash
npm run tauri add window-state
```
```rust
#[cfg(desktop)]
app.handle().plugin(tauri_plugin_window_state::Builder::default().build());
```
Set `visible: false` in config. Plugin restores position then shows. Permission: `"window-state:default"`

## Command Reference
| Action | How |
|--------|-----|
| Scaffold | `npm create tauri-app@latest` |
| Add plugin | `npm run tauri add <name>` |
| Build | `npm run tauri build` |
| Dev mode | `npm run tauri dev` |
| Invoke Rust | `invoke('cmd', {args})` from JS |
| Stream to JS | `Channel<T>` param in command |
| Emit broadcast | `app.emit("evt", payload)?` |
| Global hotkey | `app.global_shortcut().register(shortcut)?` |

## Linux Gotchas -- X11 vs Wayland

| Issue | Sev | Workaround |
|-------|-----|------------|
| `setIgnoreCursorEvents` broken on Wayland | **HIGH** | X11 only for click-through |
| Window position ignored on Wayland | HIGH | No global coords in Wayland protocol |
| `alwaysOnTop` ignored by some WMs | MED | KDE/GNOME may override |
| Wayland+NVIDIA crash | MED | `WEBKIT_DISABLE_DMABUF_RENDERER=1` (causes redraw glitches) |
| CSS perf on WebKitGTK | MED | Only `transform`/`opacity`. No `filter`/`box-shadow`/`backdrop-filter` |
| Tray icon invisible | LOW | Always attach a Menu |
| No wlr-layer-shell | INFO | Tauri uses tao/wry, not wlr protocols |

**Decision: X11 for Glitch MVP.** Force it: `GDK_BACKEND=x11 npm run tauri dev`

## Glitch Integration Map
- **Python brain:** systemd service -> `ws://127.0.0.1:8765`
- **Sprite:** Tauri webview renders HTML/CSS overlay
- **Screen awareness:** AT-SPI from Python -> WS -> Rust -> frontend
- **TTS visemes:** Python generates audio + visemes -> Channel API -> mouth sprites
- **Keybinds:** Super+G toggle, Super+Shift+G focus (global-shortcut plugin)
- **State flow:** Python brain -> WS -> Rust -> Channel/Event -> JS -> CSS sprite

## Tips
- `visible: false` + window-state plugin = zero startup flicker
- All capabilities denied by default -- check `capabilities/default.json`
- No `Arc` for managed state -- Tauri wraps in Arc. Just `Mutex<T>`
- Channel > Events for streaming. Events for broadcasts
- `generate_handler!` called once. Last call wins
- Async commands: `async fn` + `Result<T, String>`. Sync blocks main thread
- Don't bundle Python for home use -- PyInstaller is a whole project
