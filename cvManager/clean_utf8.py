with open('static/app_v4.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace corrupted chars
text = text.replace("??", "⚡").replace("", "✓")

with open('static/app_v4.js', 'w', encoding='utf-8') as f:
    f.write(text)
print("UTF-8 clean!")
