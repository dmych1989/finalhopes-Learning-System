#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依据 server.py 的时事评论分类（来自 sspl_map.json + EXE 目录.txt）重建
医学论文医案查询系统/时事评论 下的子文件夹与文章 txt。

- 保留 时事评论\目录.txt（权威来源，不删除）。
- 删除旧的错误子文件夹（倪师论中药/忧郁/抗生素/牛奶/肝病/肾脏/血液/未归类评论 等），
  按 EXE 真实 18 个栏目重建。
- 每篇文章：文件名=<标题>.txt，内容=标题 + 空行 + 正文(NR，已解密)。
"""
import sys, os, json, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web_app")
sys.path.insert(0, WEB)
import server as S

BASE = os.path.join(
    "E:\\Soft\\倪海夏三套学习系统\\QQ频道号talktyph0id\\医学论文医案查询系统",
    "时事评论"
)
CAT_NAME = {
    "ai": "倪师论癌症", "ganbing": "倪师论肝病", "liugan": "倪师论流感",
    "shenzang": "倪师论肾脏", "niunai": "倪师论牛奶", "tangniao": "倪师论糖尿",
    "xinbing": "倪师论心病", "xueye": "倪师论血液", "zhongyao": "倪师论中药",
    "kangshengsu": "倪师论抗生素", "zuixin": "最新研究成果时事评论",
    "ruanai": "倪师论乳癌", "youyu": "倪师论忧郁", "fuke": "倪师论妇科",
    "baojian": "保健锦囊", "fkmenzhen": "妇科门诊", "weifanlei": "未归类评论",
    "foodinc": "食品帝国FoodInc.",
}

# 1) 清掉旧子文件夹（保留 目录.txt）
for entry in os.listdir(BASE):
    p = os.path.join(BASE, entry)
    if os.path.isdir(p):
        shutil.rmtree(p)
        print("删除旧文件夹:", entry)

# 2) 加载映射
with open(os.path.join(WEB, "sspl_map.json"), encoding="utf-8") as f:
    _MAP = json.load(f)
_id_to_idx = {str(r.get("ID", "")): i for i, r in enumerate(S.ARTICLES)}

ILLEGAL = '\\/:*?"<>|'

def safe(fn):
    for ch in ILLEGAL:
        fn = fn.replace(ch, " ")
    return fn.strip()[:120] or "未命名"

# 3) 写入
written = 0
used = {}  # (folder, base) -> count
for aid, key in _MAP.items():
    idx = _id_to_idx.get(str(aid))
    if idx is None:
        continue
    r = S.ARTICLES[idx]
    title = str(r.get("MZ", "") or "").strip() or "未命名"
    body = str(r.get("NR", "") or "")
    folder = CAT_NAME.get(key, "未归类评论")
    fdir = os.path.join(BASE, folder)
    os.makedirs(fdir, exist_ok=True)
    base = safe(title)
    fp = os.path.join(fdir, base + ".txt")
    n = 1
    while os.path.exists(fp):
        n += 1
        fp = os.path.join(fdir, "%s_%d.txt" % (base, n))
    content = title + "\n\n" + body
    with open(fp, "w", encoding="utf-8") as wf:
        wf.write(content)
    written += 1

print("写入文章 txt 总数:", written)
print("=== 各栏目文件数 ===")
for key, name in CAT_NAME.items():
    d = os.path.join(BASE, name)
    if os.path.isdir(d):
        print("  %-22s %d" % (name, len([x for x in os.listdir(d) if x.endswith(".txt")])))
