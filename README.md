<div align="center">
  <h1>TaskMancer</h1>

  <p>
    <strong>A powerful, zero-distraction multi-project task management dashboard designed for developers.</strong>
  </p>

  <p>
    <!-- Add standard badges here -->
    <img alt="Vue 3" src="https://img.shields.io/badge/Vue.js-3.0-4FC08D?logo=vue.js&logoColor=white" />
    <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" />
    <img alt="Tauri" src="https://img.shields.io/badge/Tauri-FFC131?logo=tauri&logoColor=white" />
  </p>
</div>

<img width="2046" height="1222" alt="image" src="https://github.com/user-attachments/assets/4cd5e710-1443-42f6-ab1e-96657ddeb6f9" />
<img width="2150" height="1162" alt="image" src="https://github.com/user-attachments/assets/1ebd0a69-4a65-403c-881e-c099ae586922" />
<img width="1836" height="1033" alt="image" src="https://github.com/user-attachments/assets/229cf9c1-3a41-4069-a574-a705c655401c" />
<img width="1967" height="1041" alt="image" src="https://github.com/user-attachments/assets/cb47db0f-2e2c-4b76-b17f-2a3ea1024943" />




TaskMancer 是一個強大的多專案任務管理儀表板，專為常常在不同專案間切換的開發者設計。它能遞迴掃描資料夾中的 `task.md`，並透過現代化的 Web 介面 (Vue 3 + Tailwind CSS v4) 即時視覺化各個專案的開發進度與狀態，幫助你專注在程式碼本身，而非繁瑣的專案管理工具。

## ✨ 核心特色

- **自動探索 (Auto-Discovery)**：指定工作目錄後，自動搜尋深層目錄中的 `task.md` 文件並納入監管。
- **巢狀任務解析 (Nested Parsing)**：完美理解 Markdown 中的縮排任務清單結構，正確計算真實的進度百分比。
- **即時同步 (Real-time Sync)**：內建 Debounced File Watcher，完美相容現代編輯器的原子存檔特性，毫秒級透過 WebSocket 刷新介面。
- **現代化設計 (Modern UI)**：搭載玻璃擬物化 (Glassmorphism) 設計、暗色模式、瀑布流佈局，以及重新設計的 Markdown 閱讀面板。
- **效能與診斷中心**：內建全域進程監控 (CPU/RAM)、專案診斷中心 (量化代碼指標、檔案大小)、智能日誌終端與連線埠口檢測。
- **桌面級整合**：原生 Tauri 桌面應用程式整合了 Windows 系統托盤，提供一鍵啟動/停止後端服務的便捷控制。

## � 快速開始

### 系統環境要求

- Node.js (v18+)
- Python (3.9+)
- (可選) Tauri 開發前置套件 (Rust, Build Tools) 若需編譯桌面端應用程式

### 啟動後端服務 (FastAPI)

> [!NOTE]
> 後端服務負責監聽本地檔案的變動，並透過 WebSocket 將狀態即時廣播給前端。

```bash
cd backend
python -m venv .venv
# 啟動虛擬環境 (Windows)
.\.venv\Scripts\Activate
# 啟動虛擬環境 (macOS/Linux)
# source .venv/bin/activate

pip install -r requirements.txt
python main.py --root "D:\Your\Project\Path"
```

### 啟動前端介面 (Vue 3)

```bash
cd frontend
npm install
npm run dev
```

啟動後，開啟瀏覽器瀏覽 `http://localhost:5173` 即可看見管理儀表板。

## 📥 桌面應用程式 (Tauri)

TaskMancer 提供了基於 Tauri 的原生桌面用戶端，能深層整合至作業系統中，讓管理更加順手。

1. **開發模式啟動**：在 `frontend` 目錄下執行 `npm run tauri dev`。
2. **系統托盤整合**：啟動後會在 Windows 右下角駐留系統綠色托盤圖示。
3. **快捷操作**：右鍵點選托盤選單，可快速實現「開啟儀表板」、「啟動/停止後端服務」、「開機自啟」等高頻操作。

## 🗂️ 專案結構

```text
TaskMancer/
├── backend/          # Python FastAPI 專案核心
│   ├── scanner.py    # 資料夾遞迴掃描引擎
│   ├── watcher_service.py # Watchdog 檔案變動監聽器
│   └── task_parser.py     # Markdown 巢狀樹狀結構解析器
├── frontend/         # Vue 3 前端專案
│   ├── src/
│   │   ├── components/    # 介面元件 (瀑布流卡片、Markdown 預覽)
│   │   └── stores/        # Pinia 狀態管理
└── task.md           # 任務追蹤文件範例
```

## 🛠️ 開發架構與設計邏輯

> [!TIP]
> TaskMancer 的核心哲學是「無侵入性」。你只需要在專案內維護單一的 `task.md`，即可將開發流程統一集中到儀表板上。

後端透過 `Watchdog` 遞迴監聽工作區（支援 `ignore_directories` 避免掃描 `node_modules` 等龐大目錄）。當檔案發生變動，會觸發 `Debouncer` 以過濾編輯器的寫入雜訊，並使用進度解析器重新建構樹狀任務 JSON。隨後，資料會經由 WebSocket 推送至前端 Pinia Store，最後交給 Vue 重新渲染。
