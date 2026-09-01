import os

with open('static/app_v4.js', 'rb') as f:
    raw = f.read()

# Remove null bytes or decode utf-16 if needed
if b'\x00' in raw:
    print("Found null bytes! Cleaning...")
    # Decode utf-16 le
    try:
        text = raw.decode('utf-16')
    except Exception:
        text = raw.replace(b'\x00', b'').decode('utf-8', errors='ignore')
else:
    text = raw.decode('utf-8', errors='ignore')

# Clean emojis to pure standard chars or clean unicode
text = text.replace('\ufeff', '')

with open('static/app_v4.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)

print("Saved clean UTF-8 file successfully!")
