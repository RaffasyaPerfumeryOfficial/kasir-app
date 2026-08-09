import io, re
p = "app/main.py"
s = io.open(p, encoding="utf-8").read()
pat = re.compile(r'@app\.post\("/login/masuk"\)[\s\S]*?(?=\n@app\.)')
assert pat.search(s), "route login tidak ketemu"
new = '''LOGIN_FAIL = {}

@app.post("/login/masuk")
def login_masuk(request: Request, username: str = Form(...), password: str = Form(...)):
    import time as _time
    info = LOGIN_FAIL.setdefault(username, {"n": 0, "lock": 0})
    if info["lock"] and _time.time() < info["lock"]:
        sisa = int((info["lock"] - _time.time()) // 60) + 1
        return templates.TemplateResponse(
            request, "login.html",
            {"pesan": "Terlalu banyak percobaan. Coba lagi " + str(sisa) + " menit lagi."})
    if USERS.get(username) == password:
        info["n"] = 0
        info["lock"] = 0
        sid = secrets.token_hex(16)
        dbx = SessionLocal()
        dbx.add(models.Sesi(token=sid))
        dbx.commit()
        dbx.close()
        resp = RedirectResponse("/dashboard", status_code=303)
        resp.set_cookie("session_id", sid, max_age=604800)
        return resp
    info["n"] += 1
    if info["n"] >= 5:
        info["lock"] = _time.time() + 300
        info["n"] = 0
        return templates.TemplateResponse(
            request, "login.html",
            {"pesan": "5x salah! Login dikunci 5 menit."})
    return templates.TemplateResponse(
        request, "login.html",
        {"pesan": "Username atau password salah (percobaan " + str(info["n"]) + "/5)"})


'''
s = pat.sub(lambda m: new, s, count=1)
io.open(p, "w", encoding="utf-8").write(s)
print("kunci login terpasang")
