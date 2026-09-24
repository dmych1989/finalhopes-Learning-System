// 发布版不显示控制台窗口
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{WebviewUrl, WebviewWindowBuilder};

/// 壳加载的目标站点
const HOME_URL: &str = "https://finalhopes.dynv6.net/";

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            let url = WebviewUrl::External(
                HOME_URL.parse().expect("HOME_URL 不是合法的绝对 URL"),
            );

            WebviewWindowBuilder::new(app, "main", url)
                .title("FinalHopes 学习系统")
                .inner_size(1280.0, 820.0)
                .min_inner_size(720.0, 480.0)
                .center()
                .resizable(true)
                .build()?;

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("FinalHopes 壳启动失败");
}
