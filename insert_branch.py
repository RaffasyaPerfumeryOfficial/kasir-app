import io
main = io.open("app/main.py", encoding="utf-8").read()
branch = io.open("produk_branch.py", encoding="utf-8").read()
anchor = '    if ("omzet" in ql or "omset" in ql) and ("hari ini" in ql or "sekarang" in ql):'
if anchor not in main:
    print("anchor tidak ditemukan!")
else:
    main = main.replace(anchor, branch + anchor, 1)
    io.open("app/main.py", "w", encoding="utf-8").write(main)
    print("insert selesai")
