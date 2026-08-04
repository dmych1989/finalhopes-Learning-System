# -*- coding: utf-8 -*-
"""从 文章分类.txt(EXE真实目录) 反向构建 nhxlwj.ID -> 栏目 映射, 输出 article_cat_map.json。"""
import re, json, os, pyodbc

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "Data", "LILUN.mdb"); PWD = "JiSkS92A30"

def conn():
    return pyodbc.connect("Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=%s;PWD=%s;" % (DB, PWD))

c = conn(); cur = c.cursor()
cur.execute("SELECT [ID] FROM [nhxlwj]")
ids = [r[0] for r in cur.fetchall() if r[0]]
c.close()
print("nhxlwj 总文章:", len(ids))

raw = open(os.path.join(BASE, "文章分类.txt"), encoding="utf-8").read()

def norm(s):
    s = s.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    s = s.replace("又唐", "汉唐")          # 目录写'又唐' 实际库为'汉唐'
    return s

ntxt = norm(raw)
# 栏目标题位置 (在归一化文本中)
hdr_re = re.compile(r'^\s*\d+\s*[.．。·]\s*《(.+?)》', re.M)
headers = [(m.start(), m.group(1)) for m in hdr_re.finditer(ntxt)]
print("解析到栏目数:", len(headers))

def cat_of(pos):
    name = None
    for p, n in headers:
        if p <= pos:
            name = n
        else:
            break
    return name

BOUND = set("\n 《》(）)、；：！？/　 \"'")  # 标题分隔符
def clean_match(nid):
    """返回首个'边界干净'的匹配位置, 否则 -1。边界: 匹配前后为分隔符/起止。"""
    start = 0
    L = len(nid)
    while True:
        p = ntxt.find(nid, start)
        if p == -1:
            return -1
        prev_ok = (p == 0) or (ntxt[p-1] in BOUND)
        nxt_ok = (p+L == len(ntxt)) or (ntxt[p+L] in BOUND)
        if prev_ok or nxt_ok:
            return p
        start = p + 1

cat_map = {}        # id -> 栏目名
counts = {}
short_rejected = [] # 短ID因非边界被拒(供审查)
for idv in ids:
    nid = norm(idv)
    if len(nid) < 2:
        continue
    if len(nid) <= 6:
        p = clean_match(nid)
    else:
        p = ntxt.find(nid)
    if p == -1:
        if len(nid) <= 6:
            short_rejected.append(idv)
        continue
    name = cat_of(p)
    if name is None:
        continue
    cat_map[idv] = name
    counts[name] = counts.get(name, 0) + 1

print("\n=== 各栏目命中文章数 (EXE目录->文章库) ===")
for p, n in headers:
    print(f"  {n}: {counts.get(n,0)}")
print("总计命中:", len(cat_map))

print("\n=== 短ID(<=6字)因非边界被拒(防止片段误匹配), 供人工核查 ===")
for s in short_rejected:
    print("  ", repr(s))

# 第7栏 汉唐方剂: 目录原文用 '........' 缩写 01-100, 文章库有 汉唐-XX号, 整组归入
cat7 = next((n for _, n in headers if "汉唐" in n), None)
aug = 0
if cat7:
    for idv in ids:
        if re.match(r'^汉唐-\d+号$', idv) and idv not in cat_map:
            cat_map[idv] = cat7
            counts[cat7] = counts.get(cat7, 0) + 1
            aug += 1
    print(f"\n第7栏补录 汉唐-XX号 文章: +{aug} (现 {counts.get(cat7,0)})")

out = {
    "cats": [n for _, n in headers],
    "map": cat_map,
}
with open(os.path.join(BASE, "article_cat_map.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=0)
print("\n已写出 article_cat_map.json  映射条目:", len(cat_map))
