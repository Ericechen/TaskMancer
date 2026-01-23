import re
from typing import List, Dict, Any

class TaskParser:
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            return self.parse_lines(lines)
        except Exception as e:
            return {"error": str(e), "tasks": [], "stats": {}}

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

    def _calculate_stats(self, nodes: List[Dict]) -> Dict[str, Any]:
        total = 0
        completed = 0
        
        def traverse(node):
            nonlocal total, completed
            if not node['children']:
                # Leaf node: count it
                total += 1
                if node['status'] == 'done':
                    completed += 1
            else:
                # Determine parent status based on children? 
                # PRD says "Progress calculation: Leaf nodes only"
                # So we just traverse down.
                # However, for UI, we might want to know if parent is partially done. 
                # We can compute that on frontend or backend.
                # Let's just traverse children.
                for child in node['children']:
                    traverse(child)

        for node in nodes:
            traverse(node)
            
        percentage = int((completed / total * 100)) if total > 0 else 0
        
        return {
            "total": total,
            "completed": completed,
            "percentage": percentage
        }

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
