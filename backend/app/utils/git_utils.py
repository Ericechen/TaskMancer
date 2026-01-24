import subprocess
import os
from typing import Dict, Any, Optional

class GitHelper:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def _run_git(self, args: list) -> Optional[str]:
        try:
            result = subprocess.run(
                ["git", "-C", self.repo_path] + args,
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8',
                errors='ignore'
            )
            return result.stdout.strip()
        except Exception:
            return None

    def get_repo_snapshot(self) -> Dict[str, Any]:
        """獲取基本的 Git 狀態快照"""
        if not os.path.exists(os.path.join(self.repo_path, ".git")):
            return {"is_git": False, "branch": "", "uncommitted": 0, "sync_status": "Not a Git repo"}

        branch = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"]) or "Unknown"
        
        # 統計未提交的變動
        status_raw = self._run_git(["status", "--porcelain"])
        uncommitted_count = len(status_raw.splitlines()) if status_raw else 0
        
        # 檢查 Ahead/Behind
        sync_status = "Synced"
        try:
            sync_info = self._run_git(["rev-list", "--left-right", "--count", "HEAD...@{u}"])
            if sync_info:
                ahead, behind = map(int, sync_info.split())
                if ahead > 0 and behind > 0:
                    sync_status = f"Diverged (+{ahead}/-{behind})"
                elif ahead > 0:
                    sync_status = f"Ahead (+{ahead})"
                elif behind > 0:
                    sync_status = f"Behind (-{behind})"
            else:
                sync_status = "No upstream"
        except:
            sync_status = "Not checked"

        return {
            "is_git": True,
            "branch": branch,
            "uncommitted": uncommitted_count,
            "sync_status": sync_status
        }

    def get_momentum_score(self, days: int = 7) -> int:
        """獲取最近幾天的 Commit 數量作為動能分數"""
        if not os.path.exists(os.path.join(self.repo_path, ".git")):
            return 0
            
        count_str = self._run_git(["rev-list", "--count", f"--since={days} days ago", "HEAD"])
        try:
            return int(count_str) if count_str else 0
        except:
            return 0
