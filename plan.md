# TaskMancer 發展規劃

## v7.5 - Explicit Config: 精確埠口定義 (已完成)
- [x] `config.md` 解析與語義化標籤。

## v8.0 - Dynamic Orchestration: 動態編排 (已完成)
- [x] 將 `config.md` 定義的 Port 注入為環境變數 (`TM_PORT_[LABEL]`)。
- [x] 讓 `start.bat` 能動態讀取這些變數。

## v9.0 - README UI Redesign (已完成)
- [x] 提升文件顯示的美觀度與閱讀體驗。

## v9.2 - Port Visibility Fix (已完成)
- [x] 讓 Port 顯示不再依賴於 `config.md`。
- [x] 確保在線埠口能即時反應在 UI 上。
## v9.3 - Accurate Port Detection (已完成)
- [x] 移除全域備用掃描，埠口顯示完全依賴 `config.md`。
## v9.4 - Scanner Robustness (已完成)
- [x] 增強 `config.md` 解析容錯率。
- [x] 確保 `PortScanner` 在 Windows 環境下的穩定性。
## v9.5 - Hotfix (已完成)
- [x] 解決 DNS 解析導致的掛起問題。
## v9.6 - Stability (已完成)
- [x] 防止單一專案錯誤導致後端崩潰。
## v9.7 - Protocol Support (已完成)
- [x] 確保能正確偵測 IPv6 埠口 (Vite default).
## v9.8 - Persistence Fix (已完成)
- [x] 實作 `startup` event handler 自動載入專案。
## v9.9 - UI Layout (已完成)
## v9.10 - UI Layout Optimization (已完成)
- [x] 提升 Git 資訊列的可視寬度，達成視覺統一。
## v9.11 - UI Readability Optimization (已完成)
- [x] 全面提升低對比度文字的亮度，確保在深色背景下依然清晰。
## v9.12 - Extreme Readability & High Contrast (已完成)
- [x] 二次調校全站透明度係數，確保關鍵指標達到最高可讀性。
## v10.0.0 - The Convergence (已完成)
- [x] 正式發表 v10 版本，宣告 UI 與交互邏輯穩定。

## v10.1 - AI Workflow (已完成)
- [x] 引入 `.agent/workflows` 自動化腳本支援。
- [x] 建立快捷 Commit Workflow (`/commit`)。

## v10.2 - Performance (已完成)
- [x] 最佳化掃描效能，移除耗時的 LOC 讀取邏輯。

## v10.3 - Intelligence Hub (已完成)
- [x] 實作 Web Console 支援日誌串流。
- [x] 實作 Metrics 快取與搜尋過濾功能。
