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
- [x] 實作上傳成功 Toast 通知

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


[Link]: https://github.com/Ericechen/TaskMancer
