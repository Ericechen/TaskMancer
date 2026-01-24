# TaskMancer

**TaskMancer** 是一個強大的多專案任務管理儀表板，專為開發者設計。它能遞迴掃描資料夾中的 `task.md`，並透過現代化的 Web 介面 (Vue 3 + Tailwind CSS v4) 呈現即時進度。

## Features

- **🔎 自動掃描 (Auto-Discovery)**: 遞迴搜尋指定路徑下的 `task.md` 文件。
- **🌲 巢狀任務解析 (Nested Parsing)**: 支援無限層級的縮排任務清單。
- **⚡ 即時更新 (Real-time)**: 檔案變更後 (Debounced)，Web 介面毫秒級自動刷新。
- **🎨 現代化介面 (Modern UI)**: 深色模式、瀑布流 (Masonry) 排版、Markdown 渲染支援。
- **💾 專案持久化 (Persistence)**: 自動記住專案路徑 (`projects.json`)。
- **📂 專案管理 (Management)**: 支援直接在 UI 創建專案與上傳文件 (如 PRD, task.md)。
- **✨ SweetAlert2 整合**: 全面替換原生彈窗，提升操作質感。
- **🗑️ 雙重刪除模式**: 支援「移除追蹤」與「刪除資料夾」兩種刪除方式。
- **🚀 快捷行動系統**: 卡片內建「Antigravity」與「Dev」快速鍵，支援自定義 `start.bat` 啟動腳本。
- **🔗 外部連結整合**: 自動解析 `task.md` 中的 `[Link]: url` 語法，顯示為 GitHub 標籤並支援跳轉。
- **📊 進階監視器 (v6.0)**: 整合 Git 快照 (Branch, Sync Status, Uncommitted) 與 7 天開發動能 (Momentum)。
- **🏥 專案診斷中心 (v6.1)**: 自動檢測環境健康度 (NM, PY Venv) 並量化代碼指標 (LOC, 檔案大小, 語言分佈)。
- **📡 服務即時監控 (v8.5)**: 即時檢測埠口佔用狀態，顯示 Online/Offline 燈號。
- **📖 README 預覽面板 (v9.0)**: 重新設計的 Glassmorphism 面板，提供精緻的 Markdown 閱讀體驗。
- **🎨 佈局優化 (v9.10)**: 精細調整資訊列寬度，提升大寬度螢幕下的視覺平衡感。
- **🌗 可讀性提升 (v9.11)**: 調亮所有低對比度文字，確保在深色主題下仍保有優異的閱讀體驗。
- **🕯️ 極致亮度優化 (v9.12)**: 二次提升全站透明度係數，確保關鍵指標 (LOC, Size, Path) 在任何光線下都清晰可見。
- **💎 v10.0.0 正式版**: 系統穩定性與 UI 交互體驗的重大里程碑。
- **🔍 智能搜尋與過濾 (v10.3)**: 即時過濾大規模專案列表。
- **📟 智慧日誌終端 (v10.4)**: 支援 ANSI 顏色、自動捲動鎖定與日誌匯出。
- **📊 全域進程監控 (v10.4)**: 即時追蹤所有專案的 CPU/RAM 資源佔用與報錯檢索。
- **🧭 三向導航系統 (v10.6)**: 支援 List / Grid / Monitor 三種佈局，適配不同的工作流。
- **🤖 智慧標籤與偵測 (v11.0)**: 自動識別專案技術棧並支援 `#Hashtag` 標籤過濾。
- **📈 效能歷史快照 (v11.0)**: 以 SVG Sparklines 呈現進程 CPU/RAM 歷史趨勢圖。
- **🖥️ NOC 專業級監控台 (v11.1)**: 水平分割寬屏視圖，同步顯示終端日誌與全域基礎設施負載。
- **👁️ 真．自我觀察系統 (v11.2)**: 遞迴監控 TaskMancer 本身，並實現後端 Log 直播與專案負載動態彙總。
- **🚀 工業級持久化引擎 (v12.0)**: 基於 SQLite 的歷史還原、WebSocket 增量更新與資源異常智能警報。

## Quick Start

### Backend (Python)

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt
python main.py --root "D:\Your\Project\Path"
```

### Frontend (Vue 3)

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

- `backend/`: FastAPI 伺服器，負責檔案掃描 (`scanner.py`)、監聽 (`watcher_service.py`) 與解析 (`task_parser.py`)。
- `frontend/`: Vue 3 + Pinia + Tailwind CSS 前端。
- `task.md`: 任務追蹤文件範例。

## License

MIT
