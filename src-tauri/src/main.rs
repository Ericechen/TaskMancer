use std::process::Command;
use std::os::windows::process::CommandExt;
use tauri::{
    menu::{Menu, MenuItem},
    tray::{TrayIconBuilder, TrayIconEvent},
    Manager,
};

fn run_bat(name: &str) {
    let _ = Command::new("cmd")
        .args(["/c", name])
        .current_dir("..")
        .creation_flags(0x08000000)
        .spawn();
}

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            // 啟動時執行 start.bat
            run_bat("start.bat");

            let quit_i = MenuItem::with_id(app, "quit", "Exit", true, None::<&str>)?;
            let show_i = MenuItem::with_id(app, "show", "Open Dashboard", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&show_i, &quit_i])?;

            let _tray = TrayIconBuilder::new()
                .icon(app.default_window_icon().unwrap().clone())
                .menu(&menu)
                .show_menu_on_left_click(false)
                .on_menu_event(|app, event| match event.id.as_ref() {
                    "quit" => {
                        run_bat("StopTaskMancer.bat");
                        app.exit(0);
                    }
                    "show" => {
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.focus();
                        }
                    }
                    _ => {}
                })
                .on_tray_icon_event(|app, event| {
                    if let TrayIconEvent::Click { .. } = event {
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.focus();
                        }
                    }
                })
                .build(app)?;

            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                let _ = window.hide();
                api.prevent_close();
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
