# TaskMancer 開發任務清單

## v1.1 - 後端與前端重構 (已完成)
- [x] 規劃
- [x] 後端重構 (Scanner, Watcher, Parser)
- [x] 前端重構 (Vue 3, Pinia, Tailwind v4)

## v2.0 - 數據儀表板 (已完成)
- [x] App.vue 路由重構 (Dashboard vs Projects)
- [x] 統計組件與圓環圖實作

## v2.5 - 設計語言更新 (Premium Minimalist) (已完成)
- [x] 引進 Outfit & Plus Jakarta Sans 字體
- [x] Void & Light 主題配色與動畫

## v2.6 - 專案列表分類 (已完成)
- [x] 根據進度自動分類 (草稿、進行中、已完成)

## v2.7 - 專案創建功能 (已完成)
- [x] 後端創建資料夾與自動生成 task.md API
- [x] 前端創建視窗與表單

## v2.8 - 文件上傳功能 (已完成)
- [x] 後端 `/api/projects/upload` API
- [x] 前端上傳按鈕與 Store Action

## v2.9 - UI 優化 (SweetAlert2) (已完成)
- [x] 安裝 `sweetalert2`
- [x] 全域 SweetAlert2 深色主題配置 (`swal.ts`)
- [x] 替換原生 `confirm` 與 `alert` 為美化彈窗
- [x] 實實作上傳成功 Toast 通知

## v3.0 - 雙重刪除模式 (已完成)
- [x] Backend: `DELETE /api/roots` 支援 `delete_files` 參數
- [x] Frontend: `removeProject` store action 支援刪除文件

## v3.1 - UI 優化 (獨立刪除按鈕) (已完成)
- [x] Frontend: `ProjectCard.vue` 拆分「移除追蹤」與「刪除資料夾」按鈕

## v3.2 - UI 優化 (彈窗內容美化) (已完成)
- [x] Frontend: 文字階層化與 HTML 內容重構

## v4.0 - 交互增強 (連結與指令) (已完成)
- [x] Backend: 支援 `[Link]:` 自動掃描連結
- [x] Backend: 一鍵執行 `code .` 與 `npm run dev`
- [x] Frontend: 專案卡片新增「快捷行動」功能區

## v4.2 - UI 細節調整 (已完成)
- [x] Frontend: 將 Link 標籤改名為 GitHub 並移至路徑下方
- [x] Frontend: 將快捷按鈕 Focus 改名為 Antigravity

## v4.3 - 邏輯修正 (開啟正確編輯器) (已完成)
- [x] Backend: 將 `open` 指令修改為 `antigravity .`

## v4.5 - 自定義啟動指令 (.bat 支援) (已完成)
- [x] Backend: 實作 `start.bat` 自動偵測與優先執行邏輯
- [x] DevOps: 為 TaskMancer 專案本身建立 `start.bat` 達成自我啟動

## v4.6 - 解析器修復 (標題支援) (已完成)
- [x] Backend: 支援 `#` Markdown 標題解析與顯示

## v4.7 - 解析器優化 (層級調整) (已完成)
- [x] Backend: 忽略 H1 (#) 標題
- [x] Backend: H2 (##) 作為任務容器，並修正列表項嵌套縮排

## v5.0 - 工作站強化 (條件操作與資訊面板) (已完成)
- [x] Backend: 自動偵測 `start.bat` 與 `README.md`
- [x] Backend: 實作 README 內容讀取 API
- [x] Frontend: 專案卡片條件顯示「Dev/Info」按鈕
- [x] Frontend: 實作 README Markdown 彈窗介面

## v6.0 - 進階監控 (Git 與活動中心) (已完成)
- [x] Backend: 實作 Git 資料獲取模組 (Branch, Status, Commits)
- [x] Frontend: Dashboard 新增 Git 同步快照與活動動能 (Momentum)

## v6.1 - 專案診斷 (環境與規模指標) (已完成)
- [x] Backend: 自動偵測環境健康度 (Dependencies, Engines)
- [x] Backend: 實作代碼規模量化 (LOC, Size, Languages)
- [x] Frontend: Dashboard 新增診斷結果與規模分布

## v6.2 - UI 精緻化與穩定性 (已完成)
- [x] Backend: 優化檔案監視器，加入忽略清單過濾雜訊
- [x] Backend: 修正 GitHelper 命名不一致導致的 Attribute Error
- [x] Frontend: 重新設計專案卡片佈局，將技術指標移至 Footer
- [x] Frontend: 精細調校診斷列與進度條之間的垂直間距

## v7.0 - Live Detection: 虛擬與現實的橋樑 (已完成)
- [x] Backend: 實作 `PortScanner` 偵測本機埠口佔用
- [x] Backend: 實作 `DependencyAuditor` 分析依賴健康度
- [x] Frontend: 專案卡片顯示活動 Port 標籤並支援點擊跳轉

## v7.3 - Hotfix: 恢復遺失的前端邏輯與修復渲染崩潰 (已完成)
- [x] Frontend: 恢復 `projectStore` 中遺失的 `fetchConfig`, `discoverProjects`執 等方法
- [x] Frontend: 修復 `ProjectCard.vue` 中的 `isUnlinking.ref` 語法錯誤

## v7.5 - Explicit Config: 精確埠口定義 (已完成)
- [x] Backend: 實作 `config.md` 解析器並支援語義標籤 (`Port : Frontend : 5173`)
- [x] Backend: 升級 `live_utils` 支援精確埠口探測 (Explicit Port Scan)
- [x] Frontend: `ProjectCard.vue` 顯示對應的埠口標籤 (Label)

## v8.0 - Dynamic Orchestration: 動態編排 (已完成)
- [x] Backend: 啟動專案時自動注入 `TM_PORT_[LABEL]` 環境變數
- [x] Backend: `main.py` 支援 `--port` 參數接收動態埠口
- [x] DevOps: 更新專案 `start.bat` 示範環璄變數動態接軌

## v8.5 - Service Monitoring: 服務狀態燈號 (已完成)
- [x] Backend: `PortScanner` 返回包含 `online/offline` 狀態的完整列表
- [x] Frontend: `ProjectCard.vue` 實作狀態燈號 (綠色呼吸燈 = Online, 灰色 = Offline)

## v8.6 - Hotfix: 修復偵測失效與 UI 條件渲染 (已完成)
- [x] Backend: 修復 `live_utils.py` 中的 `reader/writer` 解析錯誤（解決 Vue 偵測不到的問題）
- [x] Backend: 導出 `hasConfig` 標記至前端
- [x] Frontend: 僅在具備 `config.md` 的專案顯示服務狀態區塊

## v9.0 - UI 精緻化 (README 面板美化) (已完成)
- [x] 重新設計 README 彈窗介面 (Glassmorphism & Better Typography)
- [x] 優化 Markdown 渲染樣式 (tm-readme-content)
- [x] 新增彈窗動畫與佈局調整

## v9.2 - UI 修正 (埠口顯示邏輯優化) (已完成)
- [x] 移除前端顯示 Port 的 `hasConfig` 限制
- [x] 調整後端 PortScanner 確保沒配置時也能正確顯示常用埠口
- [x] 優化燈號顯示邏輯

## v9.3 - UI 修正 (更正埠口顯示邏輯) (已完成)
- [x] 恢復前端 `hasConfig` 顯示限制，避免無配置專案誤報
- [x] 關閉後端 `PortScanner` 的全域備用掃描 (COMMON_DEV_PORTS)
- [x] 確保精確顯示已定義的埠口狀態

[Link]: https://github.com/Ericechen/TaskMancer

## v9.4 - Bug Fix (配置解析與掃描增強) (已完成)
- [x] 優化 `config_parser` 正則表達式，支援更寬鬆的語法
- [x] 增強 `PortScanner` 連線能力 (Localhost 優先 + Timeout 放寬)
- [x] 後端掃描加入錯誤防護 (Safe Mode Scan)

## v9.5 - Hotfix (恢復 127.0.0.1 掃描) (已完成)
- [x] 修正 `live_utils.py`: 恢復使用 IP 直連，解決 Windows Localhost 解析導致的 API 卡死問題
- [x] 確保前端能正確獲取後端資料
 
 ## v9.6 - Stability (全域異常防護) (已完成)
 - [x] `main.py`: 實作 `scan_root` 層級的異常隔離，防止單一專案解析失敗導致 WebSocket 斷線
 - [x] `asyncio.gather`: 啟用 `return_exceptions=True` 避免 Root 掃描崩潰

## v9.7 - Protocol Support (IPv6 支援) (已完成)
- [x] `PortScanner` 支援雙協議掃描 (IPv4 First, IPv6 Fallback)
- [x] 解決 Vite 預設綁定 `::1` 導致的偵測失效問題

## v9.8 - Persistence Fix (自動載入修復) (已完成)
- [x] `main.py`: 加入 Startup Event，確保伺服器啟動時自動讀取 `projects.json`
- [x] 解決重啟後專案列表清空的問題

## v9.9 - UI Layout (狀態列分層優化) (已完成)
- [x] 將 ProjectCard 狀態指示器重構為雙層結構
- [x] Row 1: Git Info (Branch, Sync, Changes, Momentum)
- [x] Row 2: Live Ports (Frontend, Backend)


## v9.10 - UI Layout Optimization (已完成)
- [x] 修正 Git 資訊列寬度，移除多餘邊距使其與內容容器等寬
- [x] 重構 Header 佈局，將防撞邊距 (pr-16) 精確套用於標題區域


## v9.11 - UI Readability Optimization (已完成)
- [x] 調亮專案指標 (LOC, Size, Files) 的文字顏色 (opacity 40% -> 60%)
- [x] 全面提升低對比度次要文字的亮度 (包含任務進度標籤、已完成任務文字等)

## v9.12 - Extreme Readability & High Contrast (已完成)
- [x] 二次大幅調亮所有次要文字透明度 (opacity 60% -> 80% / 80% -> 90%)
- [x] 全面掃描並移除所有低於 70% 透明度的關鍵資訊文字


## v10.0.0 - The Convergence (已完成)
- [x] 彙整 v9.x 系列所有 Bug Fix 與 UI 優化
- [x] 全站配色與亮度二次調校完成
- [x] 正式同步 package.json 與 UI 版本號


## v10.0.1 - Git Watcher Fix (已完成)
- [x] 修正 `watcher_service.py` 排除 `.git` 資料夾導致 commit 後不刷新的問題
- [x] 允許 Git `index` 與 `HEAD` 變更觸發 UI 即時刷新

[Link]: https://github.com/Ericechen/TaskMancer
