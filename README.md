# TaskMancer

**TaskMancer** 是一個強大的多專案任務管理儀表板，專為開發者設計。它能遞迴掃描資料夾中的 `task.md`，並透過現代化的 Web 介面 (Vue 3 + Tailwind CSS v4) 呈現即時進度。

![Dashboard Preview](https://via.placeholder.com/800x400?text=TaskMancer+Dashboard)

## Features

- **🔎 自動掃描 (Auto-Discovery)**: 遞迴搜尋指定路徑下的 `task.md` 文件。
- **🌲 巢狀任務解析 (Nested Parsing)**: 支援無限層級的縮排任務清單。
- **⚡ 即時更新 (Real-time)**: 檔案變更後 (Debounced)，Web 介面毫秒級自動刷新。
- **🎨 現代化介面 (Modern UI)**: 深色模式、瀑布流 (Masonry) 排版、Markdown 渲染支援。
- **💾 持久化 (Persistence)**: 自動記住您加入的專案路徑 (`projects.json`)。

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
