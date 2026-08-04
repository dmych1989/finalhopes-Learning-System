# -*- coding: utf-8 -*-
"""Generate web_app/hantang_enrich.json from the user's Obsidian 倪师100方剂 notes.

Mapping rule (verified against the source DB): Obsidian filename number N
corresponds to 汉唐-N in the hantang table. The 15 "name mismatches" found in
cross-referencing are the same formula written under a different commercial
codename in the source zygn (e.g. 女子白带过多 = 玉洁一号), so number-based
mapping is authoritative.
"""
import os, re, json

OBS_DIR = "E:/Soft/GitHub/Obsidian/人事/方剂整理/倪师100方剂"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hantang_enrich.json")

def clean(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def extract(lines, keywords):
    """Return the full sentence(s) of the first line containing any keyword,
    bounded by Chinese/Latin sentence terminators, so the highlight captures a
    clean clause instead of bleeding into the next section."""
    for ln in lines:
        for kw in keywords:
            i = ln.find(kw)
            if i >= 0:
                left = ln.rfind("。", 0, i)
                left = left + 1 if left >= 0 else 0
                right = len(ln)
                for sep in ("。", "."):
                    j = ln.find(sep, i + len(kw))
                    if j >= 0 and j < right:
                        right = j + 1
                return ln[left:right].strip()
    return ""

def parse_file(path, num):
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    # name from filename already known; body = cleaned content
    body = clean(raw)
    lines = [l.strip() for l in raw.split("\n")]
    # remove a possible leading "# title" markdown header to avoid dup
    composition = extract(lines, ["主要成份", "组成", "成份", "方中用", "方中"])
    usage = extract(lines, ["服用方法", "服用方式", "服法", "用法", "三餐", "每次", "饭前", "饭后", "早晚"])
    caution = extract(lines, ["注意", "禁忌", "须候", "停药", "中医师", "有毒", "毒性", "孕妇"])
    return {
        "num": num,
        "body": body,
        "composition": composition,
        "usage": usage,
        "caution": caution,
    }

data = {}
for fn in os.listdir(OBS_DIR):
    if not fn.endswith(".md"):
        continue
    m = re.match(r"^(\d+)\s*(.+)\.md$", fn)
    if not m:
        continue
    num = int(m.group(1))
    name = m.group(2).strip()
    rec = parse_file(os.path.join(OBS_DIR, fn), num)
    rec["name"] = name
    data[str(num)] = rec

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)

print("wrote", OUT, "records:", len(data))
# quick sanity
for n in ("1", "10", "83"):
    if n in data:
        r = data[n]
        print(f"  N{n} name={r['name']} | comp={r['composition'][:24]!r} | usage={r['usage'][:24]!r} | caution={r['caution'][:24]!r} | body_len={len(r['body'])}")
