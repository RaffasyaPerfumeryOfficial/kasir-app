import io
p = "app/main.py"
s = io.open(p, encoding="utf-8").read()

old_a = '''    for p in produk_list:
        if p.nama.lower() in ql:
            return p
    toks = [w for w in re.split("[^a-z0-9]+", ql) if len(w) >= 3 and w not in STOP_WORDS]'''
new_a = '''    for p in produk_list:
        if p.nama.lower() in ql:
            return p
    for p in produk_list:
        for w in re.split("[^a-z0-9]+", p.nama.lower()):
            if len(w) >= 7 and w in ql:
                return p
    toks = [w for w in re.split("[^a-z0-9]+", ql) if len(w) >= 3 and w not in STOP_WORDS]'''
assert old_a in s, "old_a"
s = s.replace(old_a, new_a, 1)

old_b = '''        if "stok" in ql or "sisa" in ql or "tersisa" in ql:'''
new_b = '''        if "ada" in ql or "mengandung" in ql or "pakai" in ql or "pake" in ql:
            nts_low = (N.get(target.nama) or "").lower()
            bad = STOP_WORDS + ["apakah", "ada", "nya", "mengandung", "pakai", "pake", "tidak", "gak", "apa", "notes", "aroma", "wangi"]
            sisa = [w for w in re.split("[^a-z0-9]+", ql) if len(w) >= 3 and w not in bad]
            ntoks_t = set(re.split("[^a-z0-9]+", target.nama.lower()))
            sisa = [w for w in sisa if w not in ntoks_t]
            if sisa:
                ing = sisa[0]
                terms = NOTE_SYNONYMS.get(ing, [ing])
                for tm in terms:
                    if tm in nts_low:
                        return "Ya, " + target.nama + " mengandung " + ing + ".\\n" + format_notes(N.get(target.nama))
                return "Tidak ada " + ing + " di " + target.nama + ".\\nNotesnya:\\n" + format_notes(N.get(target.nama))
        if "stok" in ql or "sisa" in ql or "tersisa" in ql:'''
assert old_b in s, "old_b"
s = s.replace(old_b, new_b, 1)

old_c = '            out += "\\nNotes: " + nts'
new_c = '            out += "\\n" + format_notes(nts)'
assert old_c in s, "old_c"
s = s.replace(old_c, new_c, 1)

old_d = '            return tgt.nama + ":\\nNotes: " + (N.get(tgt.nama) or "-") + "\\n\\nMau saya carikan parfum dengan notes menyerupai " + short + "? Jawab: ya"'
new_d = '            return tgt.nama + ":\\n" + format_notes(N.get(tgt.nama)) + "\\n\\nMau saya carikan parfum dengan notes menyerupai " + short + "? Jawab: ya"'
assert old_d in s, "old_d"
s = s.replace(old_d, new_d, 1)

old_e = '            return t2.nama + ":\\n" + (N.get(t2.nama) or "Data notes belum ada untuk produk ini.") + "\\n\\nMau saya carikan parfum dengan notes menyerupai " + short2 + "? Jawab: ya"'
new_e = '            return t2.nama + ":\\n" + format_notes(N.get(t2.nama) or "Data notes belum ada untuk produk ini.") + "\\n\\nMau saya carikan parfum dengan notes menyerupai " + short2 + "? Jawab: ya"'
assert old_e in s, "old_e"
s = s.replace(old_e, new_e, 1)

io.open(p, "w", encoding="utf-8").write(s)
print("otak notes ok")
