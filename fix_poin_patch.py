import io
p = "fix_poin.py"
s = io.open(p, encoding="utf-8").read()
old = 'id="modalBayar"['
new = 'id="modal"['
if old in s:
    s = s.replace(old, new)
    io.open(p, "w", encoding="utf-8").write(s)
    print("patched")
else:
    print("sudah patched")
