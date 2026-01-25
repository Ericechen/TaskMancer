import os
import re
import asyncio
import aiofiles
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Dict, Any

class DirectoryScanner:
    def __init__(self, root_path: str, max_depth: int = 2):
        self.root_path = Path(root_path).resolve()
        self.max_depth = max_depth
        self.ignored_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv'}
        self.executor = ThreadPoolExecutor(max_workers=4)

    def _extract_tags(self, project_path: Path, files: List[str]) -> List[str]:
        tags = []
        # 1. Tech Stack Detection
        if 'package.json' in files:
            tags.append('NodeJS')
            try:
                with open(project_path / 'package.json', 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'vite' in content.lower(): tags.append('Vite')
                    if 'react' in content.lower(): tags.append('React')
                    if 'vue' in content.lower(): tags.append('Vue')
                    if 'next' in content.lower(): tags.append('NextJS')
            except: pass
            
        if 'requirements.txt' in files or 'pyproject.toml' in files:
            tags.append('Python')

        if 'docker-compose.yml' in files or 'Dockerfile' in files:
            tags.append('Docker')

        # 2. task.md Custom Tags (e.g. #personal #work)
        task_file = next((f for f in files if f.lower() == 'task.md'), None)
        if task_file:
            try:
                with open(project_path / task_file, 'r', encoding='utf-8') as f:
                    # Scan first 50 lines for hashtags
                    for _ in range(50):
                        line = f.readline()
                        if not line: break
                        found = re.findall(r'#(\w+)', line)
                        for tag in found:
                            if tag.lower() not in [t.lower() for t in tags]:
                                tags.append(tag)
            except: pass
            
        return tags

    async def _extract_tags_async(self, project_path: Path, files: List[str]) -> List[str]:
        """非同步版本的標籤提取，支援並行處理多個檔案"""
        tags = []
        
        # 並行處理多個檔案檢測任務
        async def check_package_json():
            if 'package.json' not in files:
                return []
            detected_tags = ['NodeJS']
            try:
                async with aiofiles.open(project_path / 'package.json', 'r', encoding='utf-8') as f:
                    content = await f.read()
                    content_lower = content.lower()
                    if 'vite' in content_lower: detected_tags.append('Vite')
                    if 'react' in content_lower: detected_tags.append('React')
                    if 'vue' in content_lower: detected_tags.append('Vue')
                    if 'next' in content_lower: detected_tags.append('NextJS')
            except:
                pass
            return detected_tags
        
        async def check_python():
            if not ('requirements.txt' in files or 'pyproject.toml' in files):
                return []
            return ['Python']
        
        async def check_docker():
            if not ('docker-compose.yml' in files or 'Dockerfile' in files):
                return []
            return ['Docker']
        
        async def scan_task_tags():
            task_file = next((f for f in files if f.lower() == 'task.md'), None)
            if not task_file:
                return []
            
            found_tags = []
            try:
                async with aiofiles.open(project_path / task_file, 'r', encoding='utf-8') as f:
                    # 只讀取前50行，限制記憶體使用
                    for _ in range(50):
                        line = await f.readline()
                        if not line: break
                        hashtag_matches = re.findall(r'#(\w+)', line)
                        for tag in hashtag_matches:
                            if tag.lower() not in [t.lower() for t in found_tags]:
                                found_tags.append(tag)
            except:
                pass
            return found_tags
        
        # 並行執行所有檢測任務
        try:
            results = await asyncio.gather(
                check_package_json(),
                check_python(),
                check_docker(),
                scan_task_tags(),
                return_exceptions=True
            )
            
            # 合併結果
            for result in results:
                if isinstance(result, list):
                    tags.extend(result)
        except Exception as e:
            print(f"Error in tag extraction: {e}")
        
        return tags

    def scan(self) -> List[Dict[str, Any]]:
        """
        同步掃描方法，保持向後相容性
        """
        import asyncio
        return asyncio.run(self.scan_async())

    async def scan_async(self, batch_size: int = 50) -> List[Dict[str, Any]]:
        """
        非同步掃描專案，支援大批量處理和記憶體優化
        Args:
            batch_size: 每批處理的專案數量，避免記憶體過載
        Returns:
            專案列表
        """
        projects = []
        
        async def walk_directory_async():
            """非同步目錄遍歷，使用執行緒池避免阻塞事件循環"""
            loop = asyncio.get_event_loop()
            
            def _blocking_walk():
                found_projects = []
                for root, dirs, files in os.walk(self.root_path):
                    current_path = Path(root)
                    
                    try:
                        relative_path = current_path.relative_to(self.root_path)
                        depth = len(relative_path.parts)
                    except ValueError:
                        depth = 0

                    if depth > self.max_depth:
                        dirs[:] = []
                        continue

                    # 提前過濾忽略的目錄，避免深度遍歷
                    dirs[:] = [d for d in dirs if d not in self.ignored_dirs]

                    task_files = [f for f in files if f.lower() == 'task.md']
                    if task_files:
                        found_projects.append({
                            'current_path': current_path,
                            'files': files,
                            'task_file': task_files[0]
                        })
                return found_projects
            
            # 將阻塞操作移到執行緒池
            return await loop.run_in_executor(self.executor, _blocking_walk)
        
        # 執行非同步目錄遍歷
        raw_projects = await walk_directory_async()
        
        # 分批處理專案標籤提取，避免記憶體過載
        for i in range(0, len(raw_projects), batch_size):
            batch = raw_projects[i:i + batch_size]
            
            # 並行處理每批專案的標籤提取
            batch_tasks = []
            for project_data in batch:
                current_path = project_data['current_path']
                files = project_data['files']
                task_file = project_data['task_file']
                
                task = self._extract_tags_async(current_path, files)
                batch_tasks.append(task)
            
            # 等待批次完成
            batch_tags = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # 組合最終結果
            for j, project_data in enumerate(batch):
                if isinstance(batch_tags[j], list):
                    projects.append({
                        'name': project_data['current_path'].name if project_data['current_path'] != self.root_path else self.root_path.name,
                        'path': str(project_data['current_path']),
                        'task_file': str(project_data['current_path'] / project_data['task_file']),
                        'tags': batch_tags[j]
                    })
                else:
                    # 錯誤處理：使用空標籤列表
                    projects.append({
                        'name': project_data['current_path'].name if project_data['current_path'] != self.root_path else self.root_path.name,
                        'path': str(project_data['current_path']),
                        'task_file': str(project_data['current_path'] / project_data['task_file']),
                        'tags': []
                    })
        
        return projects

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    
    scanner = DirectoryScanner(args.root)
    results = scanner.scan()
    print(f"Found {len(results)} projects:")
    for p in results:
        print(f" - {p['name']} {p.get('tags', [])}")
