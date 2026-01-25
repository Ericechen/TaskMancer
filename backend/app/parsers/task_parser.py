import re
import asyncio
import aiofiles
from typing import List, Dict, Any, AsyncGenerator

class TaskParser:
    def __init__(self):
        # [v13.1] 記憶體優化：新增統計快取，避免重複計算
        self._stats_cache = {}
        self._cache_size_limit = 1000

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        同步解析方法，保持向後相容性
        """
        import asyncio
        return asyncio.run(self.parse_file_async(file_path))

    async def parse_file_async(self, file_path: str, max_lines: int = 10000) -> Dict[str, Any]:
        """
        非同步串流解析大檔案，支援記憶體優化
        Args:
            file_path: 檔案路徑
            max_lines: 最大讀取行數，防止記憶體溢出
        """
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                lines = []
                line_count = 0
                
                # 串流讀取檔案，限制最大行數
                async for line in f:
                    if line_count >= max_lines:
                        print(f"Warning: File {file_path} exceeds max_lines ({max_lines}), truncating...")
                        break
                    lines.append(line)
                    line_count += 1
                    
            result = self.parse_lines(lines)
            
            # 為統計結果生成快取鍵
            stats_hash = self._generate_stats_hash(result['tasks'])
            result['_stats_hash'] = stats_hash
            
            return result
        except Exception as e:
            return {"error": str(e), "tasks": [], "stats": {}}

    def _generate_stats_hash(self, nodes: List[Dict]) -> str:
        """生成任務樹的雜湊值，用於快取統計結果"""
        import hashlib
        
        def node_to_string(node, level=0):
            indent = '  ' * level
            status = node.get('status', 'unknown')
            text = node.get('text', '').strip()
            result = f"{indent}[{status}] {text}"
            
            for child in node.get('children', []):
                result += '\n' + node_to_string(child, level + 1)
            return result
        
        tree_string = '\n'.join(node_to_string(node) for node in nodes)
        return hashlib.md5(tree_string.encode('utf-8')).hexdigest()[:16]

    def parse_lines(self, lines: List[str]) -> Dict[str, Any]:
        tasks = []
        root_nodes = []
        stack = [] # Stack of (level, node_dict)

        # Regex for standard markdown checklist
        pattern = re.compile(r'^(\s*)([-*])\s+\[([xX ])\]\s+(.*)')
        # Regex for [Link]: https://...
        link_pattern = re.compile(r'^\[Link\]:\s*(https?://[^\s]+)')
        # Regex for Headers: ## Title
        header_pattern = re.compile(r'^(#+)\s+(.*)')

        links = []
        for line in lines:
            line_strip = line.strip()
            if not line_strip:
                continue
                
            # Check for links
            link_match = link_pattern.match(line_strip)
            if link_match:
                links.append(link_match.group(1))
                continue
            
            # Check for headers
            header_match = header_pattern.match(line_strip)
            if header_match:
                hashes, text = header_match.groups()
                num_hashes = len(hashes)
                if num_hashes == 1:
                    continue # Ignore H1
                
                # H2 = level 0, H3 = level 1...
                level = num_hashes - 2
                node = {
                    "text": text.strip(),
                    "status": "done",
                    "level": max(0, level),
                    "children": [],
                    "isHeader": True
                }
                self._add_to_tree(root_nodes, stack, node)
                continue

            match = pattern.match(line)
            if match:
                indent_str, marker, status_char, text = match.groups()
                
                # Calculate level: (indent / 2) + 1 
                # This ensures even unindented items (level 1) sit under H2 (level 0)
                indent_len = len(indent_str.replace('\t', '    '))
                level = (indent_len // 2) + 1
                
                is_completed = status_char.lower() == 'x'
                
                node = {
                    "text": text.strip(),
                    "status": "done" if is_completed else "todo",
                    "level": level,
                    "children": []
                }
                self._add_to_tree(root_nodes, stack, node)

        # Calculate stats (Recursive)
        stats = self._calculate_stats(root_nodes)
        
        return {
            "tasks": root_nodes,
            "stats": stats,
            "links": links
        }

    def _add_to_tree(self, root_nodes: List[Dict], stack: List[Dict], node: Dict):
        level = node['level']
        if not stack:
            root_nodes.append(node)
            stack.append(node)
        else:
            # Pop stack until we find the parent (node with level < current level)
            while stack and stack[-1]['level'] >= level:
                stack.pop()
            
            if stack:
                stack[-1]['children'].append(node)
            else:
                root_nodes.append(node)
            
            stack.append(node)

    def _calculate_stats(self, nodes: List[Dict], use_cache: bool = True) -> Dict[str, Any]:
        """計算任務統計，支援記憶體優化"""
        # [v13.1] 檢查快取
        if use_cache:
            stats_hash = self._generate_stats_hash(nodes)
            if stats_hash in self._stats_cache:
                return self._stats_cache[stats_hash]
        
        total = 0
        completed = 0
        
        # 優化的遞迴遍歷，避免深度過深造成的效能問題
        def traverse_iterative(nodes):
            nonlocal total, completed
            stack = list(nodes)
            
            while stack:
                node = stack.pop()
                if not node.get('children'):
                    # Leaf node: count it
                    total += 1
                    if node.get('status') == 'done':
                        completed += 1
                else:
                    # Add children to stack for processing
                    stack.extend(node.get('children', []))
        
        traverse_iterative(nodes)
        
        percentage = int((completed / total * 100)) if total > 0 else 0
        
        stats = {
            "total": total,
            "completed": completed,
            "percentage": percentage
        }
        
        # [v13.1] 快取結果
        if use_cache:
            stats_hash = self._generate_stats_hash(nodes)
            self._stats_cache[stats_hash] = stats
            
            # 限制快取大小，防止記憶體洩漏
            if len(self._stats_cache) > self._cache_size_limit:
                # 刪除最舊的 20% 快取項目
                items_to_remove = int(self._cache_size_limit * 0.2)
                keys_to_remove = list(self._stats_cache.keys())[:items_to_remove]
                for key in keys_to_remove:
                    del self._stats_cache[key]
        
        return stats

    def clear_stats_cache(self):
        """清除統計快取"""
        self._stats_cache.clear()

if __name__ == "__main__":
    # Test
    sample = [
        "- [ ] Task 1",
        "  - [x] Subtask 1.1",
        "  - [ ] Subtask 1.2",
        "- [x] Task 2"
    ]
    parser = TaskParser()
    result = parser.parse_lines(sample)
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))
