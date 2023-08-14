import zlib

with open('f.txt', 'rb') as f:
    text = f.read()
lc = 0
decompressed = zlib.decompress(text)
for line in decompressed.splitlines():
    lc+=1
    print(line.decode('utf-8'))
