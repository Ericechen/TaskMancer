import os
import shutil
import unittest
from scanner import DirectoryScanner
from task_parser import TaskParser

class TestBackend(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_env"
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Project A (Root)
        with open(os.path.join(self.test_dir, "task.md"), "w") as f:
            f.write("- [ ] Root Task\n")
            
        # Project B (Subfolder)
        os.makedirs(os.path.join(self.test_dir, "ProjectB"), exist_ok=True)
        with open(os.path.join(self.test_dir, "ProjectB", "task.md"), "w") as f:
            f.write("- [x] Nested Task\n  - [ ] Child 1\n")
            
        # Ignored Folder
        os.makedirs(os.path.join(self.test_dir, "node_modules"), exist_ok=True)
        with open(os.path.join(self.test_dir, "node_modules", "task.md"), "w") as f:
            f.write("- [ ] Should not be found\n")

    def tearDown(self):
        try:
            shutil.rmtree(self.test_dir)
        except:
            pass

    def test_scanner(self):
        scanner = DirectoryScanner(self.test_dir)
        projects = scanner.scan()
        print(f"DEBUG: Found projects: {[p['name'] for p in projects]}")
        # Should find Root and ProjectB
        self.assertEqual(len(projects), 2)
        names = sorted([p['name'] for p in projects])
        self.assertEqual(names, sorted([self.test_dir, 'ProjectB']))

    def test_parser(self):
        parser = TaskParser()
        # Parse ProjectB
        path = os.path.join(self.test_dir, "ProjectB", "task.md")
        result = parser.parse_file(path)
        
        # Check tasks
        self.assertEqual(len(result['tasks']), 1)
        root_task = result['tasks'][0]
        self.assertEqual(root_task['text'], "Nested Task")
        self.assertEqual(root_task['children'][0]['text'], "Child 1")
        
        # Check stats (Leaf nodes: Nested Task has 1 child, so only Child 1 is leaf?)
        # Logic in parser: 
        # root_task has children, so it recurses.
        # Child 1 has no children, so it counts. Total 1.
        # Check logic again:
        # traverse(root_task) -> has children -> traverse(child1) -> no children -> total+=1, status=todo
        # So total=1, completed=0.
        
        self.assertEqual(result['stats']['total'], 1)
        self.assertEqual(result['stats']['completed'], 0)

if __name__ == '__main__':
    unittest.main()
