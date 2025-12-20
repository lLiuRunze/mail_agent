with open('mailer.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Keep only the first 1097 lines (index 0-1096)
with open('mailer.py', 'w', encoding='utf-8') as f:
    f.writelines(lines[:1097])

print(f"File truncated to {1097} lines")
