
import os

try:
    with open('requirements.txt', 'rb') as f:
        content = f.read()

    # Try decoding as utf-16
    try:
        text = content.decode('utf-16')
    except:
        text = content.decode('utf-8')

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    new_lines = []
    has_whitenoise = False
    for line in lines:
        # Remove null bytes if any remain (though decode should handle it)
        clean_line = line.replace('\x00', '')
        if 'whitenoise' in clean_line.lower():
            has_whitenoise = True
        new_lines.append(clean_line)

    if not has_whitenoise:
        print("Adding whitenoise to requirements.txt")
        new_lines.append('whitenoise==6.6.0') # stable version

    with open('requirements.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines) + '\n')

    print("Successfully converted requirements.txt to UTF-8 and checked for whitenoise.")

except Exception as e:
    print(f"Error: {e}")
