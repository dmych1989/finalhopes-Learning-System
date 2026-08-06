#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依据 server.py 的病症研究分类（来自 bz_map.json + EXE 目录.txt）重建
医学论文医案查询系统/病症研究 下的子文件夹与文章 txt。

- 保留 病症研究\目录.txt（权威来源，不删除）。
- 删除旧的关键词子文件夹，按 EXE 真实 22 个栏目重建。
- 每篇文章：文件名=<标题>.txt，内容=标题 + 空行 + 正文(NR，已解密)。
"""
import sys, os, json, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web_app")
sys.path.insert(0, WEB)
import server as S

BASE = os.path.join(
    "E:\\Soft\\倪海夏三套学习系统\\QQ频道号talktyph0id\\医学论文医案查询系统",
    "病症研究"
)
CAT_NAME = {
    "aizibing": "艾滋病专论", "feibing": "肺病专论", "ganai": "肝癌专论",
    "guzhishu": "骨质疏松症", "laonianchidai": "老年痴呆症", "rubing": "乳癌专论",
    "shenzangbing": "肾脏病专论", "weitaming": "维他命专论", "xinzangbing": "心脏病专论",
    "yizangai": "胰脏癌专论", "zisha": "自杀案例", "dachangai": "大肠癌专论",
    "fuke": "妇科专论", "ganmao": "感冒与疫苗", "hongbanlangchuang": "红斑狼疮",
    "naobing": "脑病专论", "shenprostate": "摄护腺癌", "tangniaobing": "糖尿病专论",
    "weibing": "胃病区专论", "xueai": "血癌专论", "zhongfeng": "中风专论",
    "aizheng": "癌症专论",
}

# 1) 清掉旧子文件夹（保留 目录.txt）
for entry in os.listdir(BASE):
    p = os.path.join(BASE, entry)
    if os.path.isdir(p):
        shutil.rmtree(p)
        print("删除旧文件夹:", entry)

# 2) 加载映射
with open(os.path.join(WEB, "bz_map.json"), encoding="utf-8") as f:
    _MAP = json.load(f)
_id_to_idx = {str(r.get("ID", "")): i for i, r in enumerate(S.ARTICLES)}

ILLEGAL = '\\/:*?"<>|'

def safe(fn):
    for ch in ILLEGAL:
        fn = fn.replace(ch, " ")
    return fn.strip()[:120] or "未命名"

# 3) 写入
written = 0
for aid, key in _MAP.items():
    idx = _id_to_idx.get(str(aid))
    if idx is None:
        continue
    r = S.ARTICLES[idx]
    title = str(r.get("MZ", "") or "").strip() or "未命名"
    body = str(r.get("NR", "") or "")
    folder = CAT_NAME.get(key, "癌症专论")
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
        print("  %-14s %d" % (name, len([x for x in os.listdir(d) if x.endswith(".txt")])))
