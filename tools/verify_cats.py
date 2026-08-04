# -*- coding: utf-8 -*-
"""比对 文章分类.txt(EXE目录) 与 nhxlwj.ID(文章库真实标题)。"""
import re, os, pyodbc, sys

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "Data", "LILUN.mdb")
PWD = "JiSkS92A30"

def conn():
    return pyodbc.connect("Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=%s;PWD=%s;" % (DB, PWD))

# ---- 1. 读取文章库所有 ID ----
c = conn(); cur = c.cursor()
cur.execute("SELECT [ID] FROM [nhxlwj]")
ids = [r[0] for r in cur.fetchall() if r[0]]
c.close()
id_set = set(ids)
print("nhxlwj 总文章数:", len(ids))

# ---- 2. 解析 文章分类.txt ----
txt = open(os.path.join(BASE, "文章分类.txt"), encoding="utf-8").read()
lines = txt.splitlines()

cat_re = re.compile(r'^\s*\d+\s*[.．。·]\s*《(.+?)》')   # 例如 1.《精彩...》
subcat_re = re.compile(r'^《(.+?)》\s*$')          # 子栏目

cats = []  # list of dict(name, titles=[])
cur_cat = None
cur_sub = None  # 用于第13栏子栏目归属(仅统计)

def add_title(t):
    t = t.strip()
    if t and cur_cat is not None:
        cur_cat["titles"].append(t)

i = 0
for ln in lines:
    m = cat_re.match(ln)
    if m:
        cur_cat = {"name": m.group(1), "titles": []}
        cats.append(cur_cat)
        cur_sub = None
        continue
    ms = subcat_re.match(ln)
    if ms and cur_cat is not None:
        # 第13栏内的子栏目标题(如《倪师论癌症》), 本身不是文章; 记录以便跳过
        # 但其下文章行仍归入当前 cat
        continue
    if cur_cat is None:
        continue
    s = ln.strip()
    if not s:
        continue
    # 处理连写: 跟诊倪师心得第X篇 重复
    if "跟诊倪师心得" in s:
        for t in re.findall(r'跟诊倪师心得第\d+篇', s):
            add_title(t)
        continue
    # 倪海厦讲案例之... 重复 -> 以 倪海厦讲案例之 为分隔还原
    if "倪海厦讲案例之" in s:
        parts = s.split("倪海厦讲案例之")
        for p in parts[1:]:
            p = p.strip()
            if p:
                add_title("倪海厦讲案例之" + p)
        continue
    # 又唐 / 汉唐 方剂号
    if ("又唐-" in s or "汉唐-" in s) and re.search(r'\d+号', s):
        for t in re.findall(r'(?:又唐|汉唐)-\d+号', s):
            add_title(t)
        continue
    # 其余: 一行可能含 1~3 个标题, 用 / ／ 分割尝试
    pieces = re.split(r'[／/]', s)
    if len(pieces) > 1:
        for p in pieces:
            add_title(p)
    else:
        add_title(s)

# ---- 3. 去重并精确匹配 ----
total_cand = 0
matched = 0
report = []
for cat in cats:
    seen = set()
    uniq = []
    for t in cat["titles"]:
        if t not in seen:
            seen.add(t); uniq.append(t)
    cat["titles"] = uniq
    total_cand += len(uniq)
    ok = [t for t in uniq if t in id_set]
    bad = [t for t in uniq if t not in id_set]
    matched += len(ok)
    report.append((cat["name"], len(uniq), len(ok), len(bad), bad[:6]))

print("\n=== 各栏目: 候选数 / 精确匹配 / 未匹配 / 未匹配样例 ===")
for name, n, o, b, samp in report:
    print(f"[{name}] 候选{n} 匹配{o} 未匹配{b}  样例:{samp}")
print(f"\n候选总计={total_cand}  精确匹配={matched}  覆盖率={matched/total_cand*100:.1f}%")

# 反向: 文章库里有多少 ID 出现在目录文本中(子串)
ss = txt
infile = sum(1 for x in ids if x in ss)
print(f"文章库ID中作为子串出现在目录文本: {infile}/{len(ids)}")

# 列出目录里有但未匹配的(可能有又唐/汉唐差异)
print("\n--- 未匹配样例(前30, 去重) ---")
allbad = []
for _,_,_,_,samp in report:
    allbad += samp
seen=set(); cnt=0
for b in allbad:
    if b not in seen:
        seen.add(b); print("  ", b); cnt+=1
        if cnt>=30: break
