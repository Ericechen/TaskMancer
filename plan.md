# v6.1 - Dashboard 進階監控與診斷 (已完成)

## 目標
將 TaskMancer 儀表板轉型為全能專案指揮中心，整合 Git 快照、開發動能、環境健康檢查與代碼指標量化。

## 變更內容

### 後端 (Python)
- **`git_utils.py`**: 新增 Git 輔助工具類，提取分支、同步狀態、未提交數量與過去 7 天動能得分。
- **`health_utils.py`**: 新增健康檢查與指標統計，掃描環境標記 (NM, PY) 並遞迴計算代碼行數 (LOC) 與檔案體積。
- **`main.py`**: 匯入上述工具，在 `get_current_state` 中注入豐富的專案狀態數據。

### 前端 (Vue 3 + Pinia)
- **`projectStore.ts`**: 擴展 `Project` 介面與相關 Sub-interfaces (GitSnapshot, ProjectHealth, CodebaseMetrics)。
- **`ProjectCard.vue`**:
  - 路徑下方新增 **Git 狀態條** (Branch, Sync, Changes)。
  - 右上方顯示 **Momentum** 活動分數。
  - 底部新增 **環境健康指標** (NM, PY 標籤) 與 **代碼規模統計** (LOC, Size, Files)。
  - 實作 `formatNumber` 與 `formatSize` 格式化工具。

## 驗證
- [x] 專案卡片顯示正確的 Git 分支與未提交狀態。
- [x] 卡片下方顯示 NM/PY 健康標籤（綠色代表存在，灰色/紅色代表缺失）。
- [x] 精確顯示 LOC 與專案體積（已排除 node_modules）。
- [x] 當 Git 遠端領先或落後時，狀態標籤正確切換顏色。
