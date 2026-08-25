from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

s = s.replace(
'''@app.on_event("startup")
def auto_backup_database("auto"):
    backup_database()
''',
'''@app.on_event("startup")
def auto_backup_database():
    backup_database("auto")
'''
)

p.write_text(s, encoding="utf-8")

print("OK fix startup backup")
