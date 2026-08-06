# -*- coding: utf-8 -*-
import re, json, sys
sys.path.insert(0, r"E:\Soft\倪海夏三套学习系统\QQ频道号talktyph0id\finalhopes-Learning-System\web_app")
import common

MD = r"E:\Soft\GitHub\Obsidian\人事\外经微言.md"
text = open(MD, encoding="utf-8").read()
lines = text.split("\n")

# parse chapters: lines starting with "- " are headings
chapters = {}
cur = None
buf = []
for ln in lines:
    m = re.match(r"^\s*-\s+(.+?)\s*$", ln)
    if m:
        if cur is not None:
            chapters[cur] = "\n".join(buf).strip()
        cur = m.group(1).strip()
        buf = []
    else:
        if cur is not None:
            buf.append(ln)
if cur is not None:
    chapters[cur] = "\n".join(buf).strip()

print("parsed chapters:", len(chapters))
print("keys sample:", list(chapters.keys())[:10])

# load MDB HDWJ MZ set
rows = common.load_table("nhxlwj")
EXCLUDE = {"黄帝内经篇","跟诊案例研究篇","醒世篇"}
mz_set = set()
for r in rows:
    mz = str(r.get("MZ",""))
    if mz.endswith("篇") and mz not in EXCLUDE:
        mz_set.add(mz)
print("MDB HDWJ MZ count:", len(mz_set))

# reverse alias
ALIAS = {"热舒肝篇":"寒热舒肝篇","六气异同篇":"四时六气异同篇"}
rev = {v:k for k,v in ALIAS.items()}

missing = []
for mz in sorted(mz_set):
    if mz in chapters:
        continue
    alt = rev.get(mz)
    if alt and alt in chapters:
        continue
    missing.append(mz)
print("MDB chapters WITHOUT md translation:", missing)

# save canonical-name -> text mapping (md names)
out = {k: v for k, v in chapters.items() if k not in ("概述",)}
# also include reverse alias mapping so server can find by MZ directly
for mz, canon in ALIAS.items():
    if canon in chapters:
        out[mz] = chapters[canon]
with open(r"E:\Soft\倪海夏三套学习系统\QQ频道号talktyph0id\finalhopes-Learning-System\web_app\hdwj_yi.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=0)
print("saved hdwj_yi.json with", len(out), "entries")
# dump a sample for inspection
import itertools
for k in list(out.keys())[:2]:
    print("\n---", k, "---")
    print(out[k][:300])
