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

        # Regex for standard markdown checklist: "- [ ] " or "* [x] "
        # Group 1: Leading whitespace
        # Group 2: Marker (- or *)
        # Group 3: Status (x or space)
        # Group 4: Text
        pattern = re.compile(r'^(\s*)([-*])\s+\[([xX ])\]\s+(.*)')

        for line in lines:
            if not line.strip():
                continue
                
            match = pattern.match(line)
            if match:
                indent_str, marker, status_char, text = match.groups()
                
                # Calculate level (assuming 2 spaces per level, or 4)
                # Let's normalize tabs to 4 spaces first if needed, but simple len check is usually okay for consistent files
                indent_len = len(indent_str.replace('\t', '    '))
                level = indent_len // 2 # Rough heuristic: 2 spaces = 1 level
                
                is_completed = status_char.lower() == 'x'
                
                node = {
                    "text": text.strip(),
                    "status": "done" if is_completed else "todo",
                    "level": level,
                    "children": []
                }

                # Tree building logic
                if not stack:
                    root_nodes.append(node)
                    stack.append(node)
                else:
                    # Pop stack until we find the parent (node with level < current level)
                    while stack and stack[-1]['level'] >= level:
                        stack.pop()
                    
                    if stack:
                        # Parent found
                        stack[-1]['children'].append(node)
                    else:
                        # Top level node
                        root_nodes.append(node)
                    
                    stack.append(node)

        # Calculate stats (Recursive)
        stats = self._calculate_stats(root_nodes)
        
        return {
            "tasks": root_nodes,
            "stats": stats
        }

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
