import zlib

with open('f.txt', 'rb') as f:
    text = f.read()
lc = 0
decompressed = zlib.decompress(text)
timeline = 0
for line in decompressed.splietlines():
    lc+=1
    timeline = line.decode('utf-8').split(' ')[0]
    print(line.decode('utf-8'))
