import re

with open('static/app_v4.js', 'rb') as f:
    raw = f.read()

# Strip all non-ascii / non-standard characters except basic code chars
decoded = raw.decode('utf-8', errors='ignore')
cleaned = decoded.replace('✓', '')

with open('static/app_v4.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(cleaned)

print("Stripped checkmarks successfully!")
