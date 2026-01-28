import os

path = "backend/app/core/project_manager.py"
with open(path, "rb") as f:
    content = f.read()

# Try to decode as UTF-8 with BOM first, then UTF-8, then cp950 (Big5)
try:
    text = content.decode("utf-8-sig")
    print("Decoded as UTF-8")
except:
    try:
        text = content.decode("cp950")
        print("Decoded as CP950")
    except:
        text = content.decode("utf-8", errors="replace")
        print("Decoded as UTF-8 (with replacement)")

with open(path, "w", encoding="utf-8", newline="\n") as f:
    f.write(text)
print("File rewritten as clean UTF-8")
