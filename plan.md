# v2.9 - UI 優化 (SweetAlert2)

## 目標
透過 `sweetalert2` 替換原生的瀏覽器彈窗 (alert/confirm)，並根據 "Void" 深色模式進行美化，提升使用者體驗。

## 變更內容

### 依賴
- 在 `frontend` 安裝 `sweetalert2`。

### 前端
- **`swal.ts`**: 建立全域配置，設定配色為背景 `#121212`、文字 `#F8FAFC`、主色 `#8B5CF6`。
- **`ProjectCard.vue`**:
  - 刪除專案時改用 `Swal.fire` 確認。
  - 上傳成功後顯示 Toast 通知。
- **`App.vue`**:
  - 錯誤與成功訊息全面改用美化彈窗。

## 驗證
- [x] 點擊刪除，彈出深色確認視窗。
- [x] 檔案上傳成功後，右上角顯示 Toast。
- [x] 專案創建失敗時，顯示美化的錯誤彈窗。
