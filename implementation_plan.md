# TaskMancer 實作計畫 (Implementation Plan) - v1.1

本階段將 TaskMancer 升級為「多專案戰情室」，支援遞迴掃描、巢狀任務解析與原子存檔容錯。

## User Review Required

> [!IMPORTANT]
> **v1.1 架構變更**:
> - **Backend**: 改為掃描 Root Path，支援多個 `task.md`。
> - **Watcher**: 實作 Debounce 機制以處理 Atomic Save。
> - **Frontend**: 改為 Card Grid 佈局，並使用遞迴組件渲染任務樹。

## Proposed Changes

### Backend (Python/FastAPI)

#### [MODIFY] [main.py](file:///d:/Dev/TaskMancer/backend/main.py)
- 新增 CLI 參數解析 (`argparse`) 接收 `--root`。
- 初始化 `ProjectManager` 與 `RecursiveWatcher`。
- WebSocket Payload 結構變更為 `{ projects: [...] }`。

#### [NEW] [scanner.py](file:///d:/Dev/TaskMancer/backend/scanner.py)
- 實作 `DirectoryScanner`。
- 遞迴掃描目錄 (max_depth=2)。
- 回傳包含 `task.md` 的專案路徑列表。

#### [NEW] [watcher_service.py](file:///d:/Dev/TaskMancer/backend/watcher_service.py)
- 取代舊的 `watcher.py`。
- 實作 `DebouncedEventHandler` (繼承自 `FileSystemEventHandler`)。
- 處理 `on_any` 事件，過濾雜訊，延遲 500ms 後觸發重讀。

#### [MODIFY] [parser.py](file:///d:/Dev/TaskMancer/backend/parser.py)
- 重寫解析邏輯，支援縮排 (Indentation) 偵測。
- 建立樹狀結構 (Tree Structure)。
- 計算邏輯：僅計算 Leaf Node 的完成度。

### Frontend (Vue.js 3 + Pinia)

#### [NEW] [stores/projectStore.js](file:///d:/Dev/TaskMancer/frontend/src/stores/projectStore.js)
- 使用 Pinia 管理 `projects` 陣列。
- 處理 WebSocket 接收到的全域狀態更新。

#### [MODIFY] [Dashboard.vue](file:///d:/Dev/TaskMancer/frontend/src/components/Dashboard.vue)
- 改為 Grid Layout 顯示 Project Cards。
- 點擊 Card 彈出 Project Detail Modal。

#### [NEW] [components/ProjectCard.vue](file:///d:/Dev/TaskMancer/frontend/src/components/ProjectCard.vue)
- 顯示專案名稱、總進度條。

#### [NEW] [components/TaskTree.vue](file:///d:/Dev/TaskMancer/frontend/src/components/TaskTree.vue)
- 遞迴組件，渲染巢狀任務清單。
- 根據 `level` 處理縮排樣式。

## Verification Plan

### Automated Tests
- **Tree Parser Test**: 測試多層縮排 Markdown 的解析正確性 (`test_parser_tree.py`)。
- **Debounce Test**: 模擬快速連續的 File Create/Delete 事件，驗證是否只觸發一次解析。

### Manual Verification
1. **多專案測試**: 準備一個測試目錄，包含 3 個子專案資料夾，各有 `task.md`。
2. **啟動測試**: `python main.py --root /path/to/test_projects`。
3. **Atomic Save 測試**: 使用 VS Code 編輯其中一個 `task.md` 並存檔，確認不會崩潰且 UI 正確更新。
4. **巢狀渲染驗證**: 確認前端能正確顯示父子任務階層，且進度條計算正確。
