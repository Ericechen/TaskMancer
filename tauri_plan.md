# Tauri Tray App Implementation Plan

## Goals
- Create a Tauri 2.0 application that runs in the windows system tray.
- Provide a menu to Start, Stop, and Open the TaskMancer service.
- Implement Rust commands to manage the Python backend life-cycle.

## Steps
1. **Infrastructure**:
   - Create `src-tauri` directory.
   - Create `Cargo.toml` with v2 dependencies.
   - Create `tauri.conf.json` configured for tray and allow-listing backend commands.
2. **Rust Core**:
   - Implement `main.rs` with tray menu setup.
   - Add state management to track if the backend is running.
   - Implement commands: `start_backend`, `stop_backend`, `get_status`.
3. **Frontend Integration**:
   - Add a hidden or mini-window for the tray interface (if a popup is needed).
   - Alternatively, use the native tray menu for simplicity.
4. **Icons**:
   - Create default icons (32x32, 128x128 etc.) using a placeholder or local tool.

## Technical Details
- Backend command: `.venv\Scripts\python.exe backend/main.py`
- Tray items: "Start Service", "Stop Service", "Open Dashboard", "Exit"
