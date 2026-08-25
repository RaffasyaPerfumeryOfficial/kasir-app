from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

old = '''    elif t.metode == "SPLIT":
        t.p_tunai = float(payload.get("tunai") or 0)
        t.p_nontunai = total - t.p_tunai
'''

new = '''    elif t.metode == "SPLIT" or "NON-TUNAI" in t.metode.upper():
        t.p_tunai = float(payload.get("tunai") or 0)
        t.p_nontunai = total - t.p_tunai
'''

if old not in s:
    raise Exception("Blok SPLIT tidak ditemukan")

s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")

print("OK patch split non-tunai")
