# TaskMancer 項目規範 (Rule)

## 語言與文字
- 回話與文件一律使用 **繁體中文** (專有名詞除外)。
- 每次完成 task 或新增 task 時，必須更新 `task.md`, `README.md`, `rule.md` 與 `plan.md`。

## 技術規範
- **Python**: 
  - 使用 `uv` 管理虛擬環境 (venv)。
  - 使用 `python-decouple` 管理 `.env` 配置。
  - Git 操作優先封裝於 `git_utils.py`。
- **Frontend (Vue 3)**:
  - 樣式採用 Tailwind CSS v4，保持 "Void" 深色美學。
  - 專案指標 (LOC, Size) 必須使用格式化 Helper 以保持介面整潔。
- **Git**:
  - 創建新項目時務必初始化 git。
  - 每個 task 完成後，提醒使用者進行 commit。

## 檔案管理
- `task.md` 與 `plan.md` 必須同步備份一份至項目根目錄。
- 嚴禁提供高層級的廢話，必須給出實際的 **代碼** 或 **解釋**。
