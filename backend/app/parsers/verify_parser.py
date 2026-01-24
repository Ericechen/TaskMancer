import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_parser import ConfigParser

# Mock content based on user's config.md
mock_content = """# TaskMancer Configuration

[Link]: https://github.com/Ericechen/TaskMancer
Port : Frontend : 5173
Port : Backend : 8000

> 這是專案的元數據定義，用於 TaskMancer 監控。
"""

# Create a dummy file
with open("test_config.md", "w", encoding="utf-8") as f:
    f.write(mock_content)

config = ConfigParser.parse_file("test_config.md")
print(f"Parsed Config: {config}")

# Clean up
try:
    os.remove("test_config.md")
except:
    pass
