# **產品規格書 (Product Requirement Document)**

**專案名稱**: TaskMancer

**版本**: v1.1 (Major Refactor)

**狀態**: Approved

**日期**: 2024-05-23

**類型**: 個人作品 / 技術學習

## **1\. 專案概況 (Project Overview)**

### **1.1 背景與動機 (Background & Motivation)**

開發者通常同時管理多個專案，且常在編輯器與專案管理工具（如 Jira, Trello）之間切換，造成心流中斷。雖然 Markdown (task.md) 是一種輕量級的替代方案，但缺乏直觀的視覺反饋，且難以一次概覽所有專案的狀態。

### **1.2 核心價值 (Value Proposition)**

**TaskMancer** 是一個「多專案戰情室」與「零干擾」的開發輔助工具。

* **全域視角**：掃描工作區，自動將散落在各資料夾的 task.md 匯總至單一儀表板。  
* **即時反饋**：解決編輯器「原子存檔」造成的延遲問題，提供穩定的即時更新。  
* **結構感知**：理解 Markdown 的巢狀任務結構，而非單純計算勾選框。

### **1.3 成功指標 (Success Metrics)**

* **多專案負載**：能同時監聽並渲染至少 10 個專案的狀態。  
* **原子存檔容錯**：在 VS Code / JetBrains 等編輯器儲存時，不發生崩潰或漏讀。  
* **準確度**：能正確解析至少 3 層巢狀結構的 Markdown 任務清單。

## **2\. 用戶故事 (User Stories)**

| ID | 角色 | 行為 | 期望結果 | 優先級 |
| :---- | :---- | :---- | :---- | :---- |
| **US-1** | 使用者 | 啟動程式並指定工作區路徑 (如 \~/MyProjects) | Dashboard 顯示該路徑下所有包含 task.md 的子專案卡片總表。 | P0 |
| **US-2** | 開發者 | 在編輯器中按下 Ctrl+S (觸發原子存檔) | 系統過濾掉刪除/移動等雜訊事件，在 500ms 內正確刷新 Dashboard。 | P0 |
| **US-3** | 使用者 | 定義巢狀任務 (父任務 \> 子任務) | Dashboard 能夠以縮排或樹狀結構顯示任務，且進度條計算能反映真實完成度。 | P0 |
| **US-4** | 使用者 | 查看總表 | 能一目了然哪些專案是「進行中 (Active)」、「卡關 (Stuck)」或「已完成」。 | P1 |
| **US-5** | 使用者 | 新增專案路徑 | 在前端輸入路徑後，後端自動掃描該路徑並納入監控，無需重啟程式。 | P1 |

## **3\. 功能需求 (Functional Requirements)**

### **3.1 核心邏輯 (Backend \- Python)**

*   **動態專案管理 (Dynamic Project Manager)**
    *   **狀態保存**：維護一個 `watched_roots` 列表 (在記憶體中，或 MVP 不需持久化)。
    *   **API**:
        *   `POST /api/roots`: 接收 `{ path: str }`。
        *   驗證路徑存在。
        *   觸發 `DirectoryScanner` 掃描新路徑。
        *   為新路徑註冊 Watcher。
        *   廣播更新後的專案列表。

* **工作區掃描器 (Workspace Scanner)**  
  * **輸入**：啟動參數 \--root \<path\>。  
  * **行為**：遞迴掃描目標路徑（限深 2 層以優化效能），尋找 task.md。  
  * **輸出**：專案列表 \[Project\_A, Project\_B, ...\]。  
* **強健檔案監聽 (Robust File Watcher)**  
  * **機制**：監聽 Root 目錄下的遞迴事件 (recursive=True)。  
  * **去雜訊 (Debounce)**：實作 Debouncer 類別。當收到 FileMoved, FileCreated, FileDeleted 或 FileModified 事件時，先等待 500ms。若 500ms 內無新事件，且目標路徑存在 task.md，才觸發解析。  
  * **目的**：完美處理現代編輯器的 "Atomic Save" (Write \-\> Rename \-\> Delete) 流程。  
* **結構化解析引擎 (Indentation-Aware Parser)**  
  * **邏輯**：讀取每一行，計算行首空白符 (Space/Tab) 來決定層級 (Level)。  
  * **資料結構轉換**：  
    \# 從扁平列表轉換為樹狀結構  
    \[  
        {"text": "父任務", "level": 0, "children": \[  
            {"text": "子任務 A", "level": 1, "status": "done"},  
            {"text": "子任務 B", "level": 1, "status": "todo"}  
        \]}  
    \]

  * **進度計算策略**：採用「葉節點計算法 (Leaf Node Count)」。只有最底層的子任務納入總進度計算，父任務狀態僅作視覺展示。

### **3.2 介面需求 (Frontend \- Vue.js)**

* **總表視圖 (Master Dashboard \- Grid View)**  
  * 展示所有偵測到的專案卡片。  
  * 每張卡片顯示：專案名稱 (資料夾名)、總進度條、剩餘任務數。  
  * 點擊卡片可展開查看詳細任務樹 (Task Tree)。  
* **專案詳情 (Project Detail \- Modal/Expand)**  
  * **樹狀渲染**：使用遞迴組件 (Recursive Component) 渲染巢狀任務。  
  * **視覺引導**：父任務若未完成但子任務有進展，顯示「部分完成」樣式。

## **4\. 技術架構 (Technical Architecture)**

### **4.1 技術棧 (Tech Stack) \- Path A (Enhanced)**

* **Backend**: Python 3.9+  
  * 框架: **FastAPI**  
  * 監控: **Watchdog** (需實作 Custom Event Handler)  
  * 工具: pathlib (處理路徑), asyncio (處理 Debounce)  
* **Frontend**: Vue.js 3  
  * 狀態管理: **Pinia** (管理多專案狀態)  
  * UI 組件: **Headless UI** 或 **Naive UI** (支援 Tree Component)  
  * 樣式: **Tailwind CSS**

### **4.2 系統架構圖 (System Context)**

graph TD  
    Root\[工作區根目錄\] \--\>|Scan| ProjA\[專案 A\]  
    Root \--\>|Scan| ProjB\[專案 B\]  
    ProjA \--\> TaskA\[task.md\]  
    ProjB \--\> TaskB\[task.md\]

    Watcher\[Watchdog Observer\] \-- "Recursive Events (Debounced)" \--\> EventFilter  
    EventFilter \-- "Valid Change" \--\> Parser\[Tree Parser\]  
    Parser \-- "Projects List JSON" \--\> WS\[WebSocket\]  
    WS \-- "Broadcast" \--\> Dashboard\[Vue Master View\]

## **5\. 限制與風險 (Constraints & Risks)**

### **5.1 硬性邊界 (Anti-Scope)**

* **不支援跨檔案關聯**：每個專案僅限一個 task.md，不支援 include 其他檔案。  
* **不支援複雜 Markdown**：僅支援列表 (-) 與核取方塊 (\[ \])，不支援表格或程式碼區塊內的任務解析。

### **5.2 風險評估 (Risk Assessment)**

* **效能瓶頸**：若工作區包含 node\_modules 或 .git 等巨大資料夾，Watchdog 效能會驟降。  
  * *對策*：Watcher 必須設定 ignore\_directories，明確排除常見的開發依賴目錄。

## **6\. 開發路線圖 (Roadmap Refined)**

* **Phase 1: Robust Core (Day 1\)**  
  * 實作 DebouncedFileSystemEventHandler 解決原子存檔問題。  
  * 開發 DirectoryScanner 支援多專案發現。  
* **Phase 2: Tree Parser & API (Day 2\)**  
  * 實作巢狀 Markdown 解析邏輯。  
  * 設計 WebSocket 資料結構：Payload \= { projects: \[...\] }。  
* **Phase 3: Master Dashboard (Day 3-4)**  
  * 前端改為 Card Grid 佈局。  
  * 實作遞迴組件顯示巢狀任務。