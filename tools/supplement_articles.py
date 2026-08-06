# -*- coding: utf-8 -*-
"""补全文章：对 web 数据库中的每一篇文章，算出它"应落"的现有文件夹，
若磁盘上尚无对应 txt，则补建（绝不移动已有文件、绝不新建文件夹）。
用法:
  python supplement_articles.py          # 仅报告缺口, 不写文件
  python supplement_articles.py --write  # 实际补建缺失的 txt
"""
import os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "web_app"))
import server as S

OUT_ROOT = r"E:/Soft/倪海夏三套学习系统/QQ频道号talktyph0id/医学论文医案查询系统"
DRY = "--write" not in sys.argv

ARTICLES = S.ARTICLES
N = len(ARTICLES)
hdwj_id = set((str(r.get("ID", "")), str(r.get("MZ", ""))) for r in S.HDWJ)
bz_label = {c["key"]: c["name"] for c in S.BZ_CATS}
sspl_label = {c["key"]: c["name"] for c in S.SSPL_CATS}
case_label = {k: lbl for k, lbl, _ in S.CASE_CATS}

def first_cat(idx, cat_sets):
    for k in cat_sets:
        if idx in cat_sets[k]:
            return k
    return None

def base_name(title):
    t = str(title).strip()
    for ch in '\\/:*?"<>|\t\n\r':
        t = t.replace(ch, "_")
    t = t.strip(" ._")
    if not t:
        t = "未命名"
    if len(t) > 80:
        t = t[:80]
    return t

def target_of(i, r):
    """返回 (文件夹绝对路径, 基准标题)。与 export_articles.py 的分类一致。"""
    key = (str(r.get("ID", "")), str(r.get("MZ", "")))
    if key in hdwj_id:
        return os.path.join(OUT_ROOT, "黄帝外经"), base_name(r.get("MZ", ""))
    if i in S.ARTICLE_ALL:
        cat = r.get("_art_cat", "") or "未归类"
        return os.path.join(OUT_ROOT, "倪海厦论文", cat), base_name(r.get("MZ", ""))
    if i in S.BZ_ALL:
        k = first_cat(i, S.BZ_CAT_SETS) or "未归类"
        return os.path.join(OUT_ROOT, "病症研究", bz_label.get(k, k)), base_name(r.get("MZ", ""))
    if i in S.SSPL_ALL:
        k = first_cat(i, S.SSPL_CAT_SETS) or "未归类"
        return os.path.join(OUT_ROOT, "时事评论", sspl_label.get(k, k)), base_name(r.get("MZ", ""))
    # 未归类
    mz = str(r.get("MZ", ""))
    mm = re.match(r"^《([^》]{1,20})》", mz)
    sub = mm.group(1) if mm else "其他"
    return os.path.join(OUT_ROOT, "未归类文章", sub), base_name(mz)

# 预扫描各文件夹已有文件名(基准匹配)
existing = {}
def has_txt(folder, base):
    files = existing.get(folder)
    if files is None:
        files = set(f[:-4] for f in os.listdir(folder)) if os.path.isdir(folder) else set()
        existing[folder] = files
    return base in files or any(f.startswith(base + "_") for f in files)

# 收集缺口
missing = []  # (folder, base, title, body)
for i, r in enumerate(ARTICLES):
    folder, base = target_of(i, r)
    if not has_txt(folder, base):
        missing.append((folder, base, r.get("MZ", ""), r.get("NR", "") or ""))

# 临床医案
cases = S.get_cases()
for idx, c in enumerate(cases):
    cats = [k for k in S.CASE_CAT_SETS if idx in S.CASE_CAT_SETS[k]]
    catlabel = case_label.get(cats[0], "未归类") if cats else "未归类"
    folder = os.path.join(OUT_ROOT, "临床医案", catlabel)
    base = base_name(c.get("_title", "医案"))
    if not has_txt(folder, base):
        lines = []
        for key, val in c.items():
            if key == "_title":
                continue
            if val and str(val).strip():
                lines.append(f"{key}\n{val}")
        missing.append((folder, base, c.get("_title", "医案"), "\n\n".join(lines)))

print(f"数据库文章总数: nhxlwj={N} + cases={len(cases)} = {N+len(cases)}")
print(f"缺失(应落文件夹但无 txt): {len(missing)}")
if missing:
    print("\n=== 缺口明细 ===")
    for f, b, t, _ in missing:
        print(f"  {os.path.relpath(f, OUT_ROOT)} / {b}   << {str(t)[:30]}")

if DRY:
    print("\n[DRY] 未写入。加 --write 实际补建。")
    sys.exit(0)

# 实际补建
added = 0
used = {}
for folder, base, title, body in missing:
    os.makedirs(folder, exist_ok=True)
    u = used.setdefault(folder, set())
    fn = base
    i = 1
    while fn in u:
        i += 1
        fn = f"{base}_{i}"
    u.add(fn)
    path = os.path.join(folder, fn + ".txt")
    with open(path, "w", encoding="utf-8") as fp:
        fp.write(str(title) + "\n\n")
        fp.write(str(body).strip() + "\n")
    added += 1
print(f"\n✅ 已补建 {added} 个 txt 到现有文件夹（未移动/未新建任何文件夹）。")
