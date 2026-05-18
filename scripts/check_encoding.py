# Read the original file and check encoding
with open('output/test_thesis.md', 'r', encoding='utf-8') as f:
    content = f.read()

chinese_chars = [c for c in content if '\u4e00' <= c <= '\u9fff']
print('Chinese chars found:', len(chinese_chars))
print('First 50 Chinese chars:', ''.join(chinese_chars[:50]))

# Check if file has actual Chinese
print('\nIs Chinese present:', any('\u4e00' <= c <= '\u9fff' for c in content))

# Check the raw bytes
with open('output/test_thesis.md', 'rb') as f:
    raw = f.read(300)
print('\nRaw bytes (hex):', raw[:100].hex())
print('Raw bytes (decoded attempt):', raw.decode('utf-8', errors='replace')[:100])