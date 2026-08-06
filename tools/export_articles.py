# -*- coding: utf-8 -*-
"""把 EXE 内的文章按 web 系统(EXE 派生)的模块/栏目结构导出为 txt 文件树。

模块(顶层文件夹):
  倪海厦论文/    -> 按 article_cat_map 13 栏目分子文件夹
  病症研究/      -> 按 BZ 栏目分子文件夹
  时事评论/      -> 按 SSPL 栏目分子文件夹
  黄帝外经/      -> 78 篇(扁平)
  临床医案/      -> 按 伤寒六经/脏腑 证型 分子文件夹
  未归类文章/    -> nhxlwj 中未被任何板块收录的文章(扁平, 保证不漏)

每篇文章一个 txt: 文件名=标题(脱敏), 内容=标题+正文。
各模块互不重叠(优先序: 黄帝外经 > 倪海厦论文 > 病症研究 > 时事评论)。
"""
import os, sys, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "web_app"))
import server as S

OUT_ROOT = r"E:/Soft/倪海夏三套学习系统/QQ频道号talktyph0id/医学论文医案查询系统"
DRY = "--write" not in sys.argv

ARTICLES = S.ARTICLES
N = len(ARTICLES)

# HDWJ 行身份集合(用 (ID,MZ) 标识)
hdwj_id = set((str(r.get("ID", "")), str(r.get("MZ", ""))) for r in S.HDWJ)
hdwj_idx = set(i for i, r in enumerate(ARTICLES)
               if (str(r.get("ID", "")), str(r.get("MZ", ""))) in hdwj_id)

paper_idx = set(S.ARTICLE_ALL) - hdwj_idx
bz_idx = set(S.BZ_ALL) - hdwj_idx - paper_idx
sspl_idx = set(S.SSPL_ALL) - hdwj_idx - paper_idx - bz_idx
assigned = hdwj_idx | paper_idx | bz_idx | sspl_idx
other_idx = set(range(N)) - assigned

bz_label = {c["key"]: c["name"] for c in S.BZ_CATS}
sspl_label = {c["key"]: c["name"] for c in S.SSPL_CATS}
case_label = {k: lbl for k, lbl, _ in S.CASE_CATS}

def first_cat(idx, cat_sets):
    for k in cat_sets:
        if idx in cat_sets[k]:
            return k
    return None

def safe_name(title, used):
    t = str(title).strip()
    for ch in '\\/:*?"<>|\t\n\r':
        t = t.replace(ch, "_")
    t = t.strip(" ._")
    if not t:
        t = "未命名"
    if len(t) > 80:
        t = t[:80]
    base = t
    i = 1
    while t in used:
        i += 1
        t = f"{base}_{i}"
    used.add(t)
    return t

used_by_folder = {}
def write_txt(folder, title, body):
    os.makedirs(folder, exist_ok=True)
    used = used_by_folder.setdefault(folder, set())
    fn = safe_name(title, used) + ".txt"
    path = os.path.join(folder, fn)
    with open(path, "w", encoding="utf-8") as f:
        f.write(str(title) + "\n\n")
        f.write(str(body).strip() + "\n")
    return path

if DRY:
    print("nhxlwj 总数:", N)
    print("黄帝外经:", len(hdwj_idx), " 倪海厦论文:", len(paper_idx),
          " 病症研究:", len(bz_idx), " 时事评论:", len(sspl_idx),
          " 未归类:", len(other_idx))
    print("\n[DRY RUN] 仅打印结构样例，不写文件\n")
    for label, idxset, getter in [
        ("倪海厦论文", paper_idx, lambda i: ARTICLES[i]),
        ("病症研究", bz_idx, lambda i: ARTICLES[i]),
        ("时事评论", sspl_idx, lambda i: ARTICLES[i]),
        ("黄帝外经", hdwj_idx, lambda i: ARTICLES[i]),
        ("未归类", other_idx, lambda i: ARTICLES[i]),
    ]:
        print(f"== {label} (样例) ==")
        for i in list(idxset)[:3]:
            r = getter(i)
            print("   ", r.get("MZ", "")[:40])
    cases = S.get_cases()
    print(f"\n== 临床医案 (共 {len(cases)}) 样例 ==")
    for c in cases[:3]:
        print("   ", c.get("_title", "")[:40])
    sys.exit(0)

# ---- 正式写入 ----
total = 0
for i in paper_idx:
    r = ARTICLES[i]
    cat = r.get("_art_cat", "") or "未归类"
    write_txt(os.path.join(OUT_ROOT, "倪海厦论文", cat),
              r.get("MZ", ""), r.get("NR", "") or "")
    total += 1
for i in bz_idx:
    r = ARTICLES[i]
    k = first_cat(i, S.BZ_CAT_SETS) or "未归类"
    write_txt(os.path.join(OUT_ROOT, "病症研究", bz_label.get(k, k)),
              r.get("MZ", ""), r.get("NR", "") or "")
    total += 1
for i in sspl_idx:
    r = ARTICLES[i]
    k = first_cat(i, S.SSPL_CAT_SETS) or "未归类"
    write_txt(os.path.join(OUT_ROOT, "时事评论", sspl_label.get(k, k)),
              r.get("MZ", ""), r.get("NR", "") or "")
    total += 1
for r in S.HDWJ:
    write_txt(os.path.join(OUT_ROOT, "黄帝外经"),
              r.get("MZ", ""), r.get("NR", "") or "")
    total += 1
for i in other_idx:
    r = ARTICLES[i]
    mz = str(r.get("MZ", ""))
    # 未被任何板块收录的文章：若标题以《栏目》开头，归入同名子文件夹(EXE 原有专栏)
    mm = re.match(r"^《([^》]{1,20})》", mz)
    sub = mm.group(1) if mm else "其他"
    write_txt(os.path.join(OUT_ROOT, "未归类文章", sub),
              mz, r.get("NR", "") or "")
    total += 1
cases = S.get_cases()
for idx, c in enumerate(cases):
    cats = [k for k in S.CASE_CAT_SETS if idx in S.CASE_CAT_SETS[k]]
    catlabel = case_label.get(cats[0], "未归类") if cats else "未归类"
    lines = []
    for key, val in c.items():
        if key == "_title":
            continue
        if val and str(val).strip():
            lines.append(f"{key}\n{val}")
    write_txt(os.path.join(OUT_ROOT, "临床医案", catlabel),
              c.get("_title", "医案"), "\n\n".join(lines))
    total += 1

print("写入文件总数:", total)
# 汇总各顶层模块文件数
for mod in ["倪海厦论文", "病症研究", "时事评论", "黄帝外经", "临床医案", "未归类文章"]:
    d = os.path.join(OUT_ROOT, mod)
    n = sum(len(f) for _, _, f in os.walk(d)) if os.path.isdir(d) else 0
    print(f"  {mod}: {n} 个 txt")
