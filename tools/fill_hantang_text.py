#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fill the empty `text` fields of web_app/hantang_quxue.json (renji 汉唐取穴)
with the body text extracted from 汉唐取穴_导出.html, following renji's
existing directory structure (4 methods categories -> leaves).

Mapping rule:
  renji leaf.name  ==  HTML <h3>● TOPIC</h3>  (within the matching category)
  leaf.text        =  concatenation of all <div class="entry"> (nm + bd)
                     found under that topic (including any .fine subgroups).

Category name correspondence (renji method key -> HTML 《category》):
  jingluo  -> 经络辩证取穴
  zangfu   -> 脏腑辩证取穴
  duizheng -> 汉唐对症取穴
  bianzheng-> 汉唐辩病取穴法
"""
import re, json, os, shutil, sys

ROOT = r"E:\Soft\倪海夏三套学习系统\QQ频道号talktyph0id"
HTML = os.path.join(ROOT, r"人纪学习系统\汉唐取穴\导出\汉唐取穴_导出.html")
JSON = os.path.join(ROOT, r"finalhopes-Learning-System\web_app\hantang_quxue.json")

CAT_MAP = {
    "jingluo":   "经络辩证取穴",
    "zangfu":    "脏腑辩证取穴",
    "duizheng":  "汉唐对症取穴",
    "bianzheng": "汉唐辩病取穴法",
}

# ---------- 1. parse HTML ----------
html = open(HTML, encoding="utf-8").read()

def clean_bd(s):
    s = s.strip()
    s = re.sub(r"[ \t]+", " ", s)        # collapse runs of spaces/tabs
    s = re.sub(r"\n[ \t]*\n", "\n", s)   # drop blank lines
    return s.strip()

cats = {}
sec_re = re.compile(r'<section class="cat"><h2>《([^》]+)》</h2>(.*?)</section>', re.S)
for m in sec_re.finditer(html):
    cat = m.group(1).strip()
    body = m.group(2)
    topics = {}
    # split by <h3>● NAME</h3>; parts alternate [preamble, name, content, name, content, ...]
    parts = re.split(r'<h3>●\s*([^<]+?)\s*</h3>', body)
    for i in range(1, len(parts), 2):
        tname = parts[i].strip()
        tcontent = parts[i + 1]
        entries = []
        for em in re.finditer(
            r'<div class="entry"><span class="nm">([^<]*)</span>\s*'
            r'<div class="bd">(.*?)</div>\s*</div>', tcontent, re.S):
            nm = em.group(1).strip()
            bd = clean_bd(em.group(2))
            if nm or bd:
                entries.append((nm, bd))
        topics[tname] = entries
    cats[cat] = topics

# ---------- 2. load JSON ----------
data = json.load(open(JSON, encoding="utf-8"))

def build_text(entries):
    blocks = []
    for nm, bd in entries:
        if nm and bd:
            blocks.append(f"{nm}\n{bd}")
        elif bd:
            blocks.append(bd)
        elif nm:
            blocks.append(nm)
    return "\n\n".join(blocks)

# ---------- 3. fill ----------
report = []
total_filled = 0
total_empty = 0
html_only = []   # topics in HTML but not in renji (renji missing leaf)

for method_key, html_cat in CAT_MAP.items():
    m = data["methods"].get(method_key)
    if not m:
        report.append(f"[SKIP] method '{method_key}' not found in JSON")
        continue
    html_topics = cats.get(html_cat, {})
    matched_topics = set()
    for leaf in m["leaves"]:
        name = leaf["name"]
        if name in html_topics:
            entries = html_topics[name]
            leaf["text"] = build_text(entries)
            matched_topics.add(name)
            if leaf["text"].strip():
                total_filled += 1
            else:
                total_empty += 1
        else:
            # keep existing (likely empty) text
            if leaf.get("text", "").strip():
                total_filled += 1
            else:
                total_empty += 1
            report.append(f"  [NO HTML TOPIC] {method_key}/{name}")
    # detect HTML topics not present in renji leaf list
    renji_names = {lf["name"] for lf in m["leaves"]}
    for t in html_topics:
        if t not in renji_names:
            html_only.append((method_key, html_cat, t, len(html_topics[t])))

# ---------- 3b. append HTML-only topics as new leaves (complete the directory) ----------
added = []
for mk, hc, t, n in html_only:
    m = data["methods"].get(mk)
    if not m:
        continue
    entries = cats[hc][t]
    m["leaves"].append({
        "name": t,
        "charts": [],
        "text": build_text(entries),
    })
    added.append((mk, t, len(entries)))

# ---------- 4. backup + write ----------
bak = JSON + ".bak_" + str(os.path.getmtime(JSON)).replace(".", "_")
shutil.copy2(JSON, bak)
json.dump(data, open(JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ---------- 5. report ----------
print("=== FILL REPORT ===")
print(f"filled leaves (non-empty text): {total_filled}")
print(f"empty leaves (no text):         {total_empty}")
print(f"backup: {bak}")
print()
for r in report:
    print(r)
print()
print("=== HTML topics NOT in renji leaf list (renji missing these) ===")
for mk, hc, t, n in html_only:
    print(f"  [{mk}/{hc}] {t}  ({n} entries)")
print()
print(f"total HTML-only topics: {len(html_only)}")
print()
print("=== appended HTML-only topics as new renji leaves ===")
for mk, t, n in added:
    print(f"  [+{mk}] {t}  ({n} entries)")
print()
print("=== NOTE: 2 renji leaves remain empty (source export has no body) ===")
print("   bianzheng/运动系统辩证选穴  (EXE empty container; content under 腰椎、颈椎病症)")
print("   bianzheng/传染性疾病辩病选穴 (export did not capture the 8 infectious-disease bodies)")
