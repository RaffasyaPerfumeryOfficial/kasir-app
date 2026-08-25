from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

old = '''import os
import shutil
'''

new = '''import os
import shutil
from pathlib import Path
'''

if old not in s:
    raise Exception("blok import tidak ditemukan")

s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")

print("OK tambah import Path")
