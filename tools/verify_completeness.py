# -*- coding: utf-8 -*-
"""校验 医学论文医案查询系统 下的 txt 树是否 100% 覆盖了 web 数据库的文章。
不做任何写入，仅报告：缺哪些、哪个文件夹有缺口。
复用 export_articles.py 的分类逻辑（与导出时一致）。
"""
import os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "web_app"))
import server as S

OUT_ROOT = r"E:/Soft/倪海夏三套学习系统/QQ频道号talktyph0id/医学论文医案查询系统"

ARTICLES = S.ARTICLES
N = len(ARTICLES)
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

# 构建 (目标文件夹, 基准标题) 列表
plan = []
for i in paper_idx:
    r = ARTICLES[i]
    cat = r.get("_art_cat", "") or "未归类"
    plan.append((os.path.join(OUT_ROOT, "倪海厦论文", cat), base_name(r.get("MZ", ""))))
for i in bz_idx:
    r = ARTICLES[i]
    k = first_cat(i, S.BZ_CAT_SETS) or "未归类"
    plan.append((os.path.join(OUT_ROOT, "病症研究", bz_label.get(k, k)), base_name(r.get("MZ", ""))))
for i in sspl_idx:
    r = ARTICLES[i]
    k = first_cat(i, S.SSPL_CAT_SETS) or "未归类"
    plan.append((os.path.join(OUT_ROOT, "时事评论", sspl_label.get(k, k)), base_name(r.get("MZ", ""))))
for r in S.HDWJ:
    plan.append((os.path.join(OUT_ROOT, "黄帝外经"), base_name(r.get("MZ", ""))))
for i in other_idx:
    r = ARTICLES[i]
    mz = str(r.get("MZ", ""))
    mm = re.match(r"^《([^》]{1,20})》", mz)
    sub = mm.group(1) if mm else "其他"
    plan.append((os.path.join(OUT_ROOT, "未归类文章", sub), base_name(mz)))
cases = S.get_cases()
for c in cases:
    cats = [k for k in S.CASE_CAT_SETS if False]  # cases 用下面的索引集合
# cases 分类：复制 export 逻辑
case_cat_sets = getattr(S, "CASE_CAT_SETS", None)
for idx, c in enumerate(cases):
    if case_cat_sets:
        cats = [k for k in case_cat_sets if idx in case_cat_sets[k]]
        catlabel = case_label.get(cats[0], "未归类") if cats else "未归类"
    else:
        catlabel = "未归类"
    plan.append((os.path.join(OUT_ROOT, "临床医案", catlabel), base_name(c.get("_title", "医案"))))

# 校验
missing = []
existing_files = {}
for folder, base in plan:
    d = folder
    if not os.path.isdir(d):
        missing.append((folder, base, "文件夹不存在"))
        continue
    # 该文件夹下所有 txt 的文件名(去 .txt)
    files = existing_files.get(d)
    if files is None:
        files = set(f[:-4] for f in os.listdir(d) if f.endswith(".txt"))
        existing_files[d] = files
    # 命中：文件名 == base 或以 base + "_<数字>" 开头
    hit = base in files or any(f.startswith(base + "_") for f in files)
    if not hit:
        missing.append((folder, base, "txt 缺失"))

print("数据库文章总数(计划导出):", len(plan))
print("  倪海厦论文:", len(paper_idx), " 病症研究:", len(bz_idx),
      " 时事评论:", len(sspl_idx), " 黄帝外经:", len(hdwj_idx),
      " 未归类:", len(other_idx), " 临床医案:", len(cases))
print("缺失 txt 数量:", len(missing))
if missing:
    print("\n=== 缺失样例(前40) ===")
    for f, b, why in missing[:40]:
        print(f"  [{why}] {os.path.relpath(f, OUT_ROOT)} / {b}")
    # 按文件夹汇总缺口
    from collections import Counter
    cc = Counter(os.path.relpath(f, OUT_ROOT) for f, b, why in missing)
    print("\n=== 各文件夹缺口数 ===")
    for k, v in cc.items():
        print(f"  {k}: {v}")
else:
    print("✅ 全部文章均已存在对应 txt，无缺口。")
