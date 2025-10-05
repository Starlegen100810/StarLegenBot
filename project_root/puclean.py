import pathlib, re, shutil
base = pathlib.Path("src/core/pu")
fixed = 0
PATTERN = re.compile(r"def init\(.*\):\s*pass\s*$", re.M)
for f in base.glob("pu*.py"):
    text = f.read_text(encoding="utf-8")
    if PATTERN.search(text):
        backup = f.with_suffix(f.suffix + ".bak")
        shutil.copy(f, backup)
        f.write_text(PATTERN.sub("", text), encoding="utf-8")
        print(f"[FIXED] {f.name}  (backup: {backup.name})")
        fixed += 1
print("Done. Fixed files:", fixed)
