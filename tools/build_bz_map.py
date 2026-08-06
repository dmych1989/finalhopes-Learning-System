#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据「医学论文医案查询系统/病症研究/目录.txt」（EXE 病症研究原始栏目结构）
构建 文章ID -> EXE栏目key 的映射，输出为 web_app/bz_map.json，供 server.py 加载。

处理逻辑：
- 按行首《xxx》切分栏目区域；仅认 22 个真实栏目（与现有 txt 文件夹名一致）。
- 内嵌标记「健康警讯 / 解密谣言 / 医药保健 / 肠胃型流感」虽以《》出现，但属于
  某栏目下具体文章的编辑标签，并非独立栏目，故不作为新栏目，其所在行的正文
  归入当前栏目（如 骨质疏松症 / 心脏病专论 / 胰脏癌专论 / 感冒与疫苗）。
- 匹配：对每篇库文章，归一化标题后在各栏目区域文本中做子串匹配（首命中）。
- 仅输出能在目录.txt中匹配到的文章（即 EXE 病症研究真实收录的文章）。
"""
import sys, re, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web_app")
sys.path.insert(0, WEB)
import server as S

ART = S.ARTICLES

# 22 个真实栏目（key 与文件夹名对应）
CAT_ORDER = [
    "aizibing", "feibing", "ganai", "guzhishu", "laonianchidai",
    "rubing", "shenzangbing", "weitaming", "xinzangbing", "yizangai",
    "zisha", "dachangai", "fuke", "ganmao", "hongbanlangchuang",
    "naobing", "shenprostate", "tangniaobing", "weibing", "xueai",
    "zhongfeng", "aizheng",
]
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
NAME2KEY = {v: k for k, v in CAT_NAME.items()}

# 内嵌标记（非独立栏目）
EMBED_MARKERS = {"健康警讯", "解密谣言", "医药保健", "肠胃型流感"}

def norm(s):
    return re.sub(r"\s+", "", re.sub(r"[，。、！？；：“”‘’（）()《》~～\-—!?]", "", str(s)))

CATALOG = os.path.join(
    "E:\\Soft\\倪海夏三套学习系统\\QQ频道号talktyph0id\\医学论文医案查询系统",
    "病症研究", "目录.txt"
)

# 1) 解析区域
regions = []  # (key, text)
cur_key = None
buf = []
with open(CATALOG, encoding="utf-8", errors="replace") as f:
    for line in f:
        s = line.strip()
        if not s:
            continue
        m = re.match(r"^《(.+?)》", s)
        if m:
            nm = m.group(1).strip()
            if nm in NAME2KEY:
                # 新栏目
                if cur_key is not None:
                    regions.append((cur_key, "\n".join(buf)))
                cur_key = NAME2KEY[nm]
                buf = []
                rest = s[m.end():].strip()
                if rest:
                    buf.append(rest)
            else:
                # 内嵌标记或未知《》：作为当前栏目的标题内容
                if cur_key is not None:
                    buf.append(s)
                # 若尚未进入任何栏目，则忽略
        else:
            if cur_key is None:
                continue
            buf.append(s)
if cur_key is not None:
    regions.append((cur_key, "\n".join(buf)))

# 合并同名 key 区域（理论上无重复，保险）
merged = {}
for k, txt in regions:
    merged[k] = merged.get(k, "") + "\n" + txt

# 2) 归一化区域文本
norm_regions = {k: norm(v) for k, v in merged.items()}

# 3) 逐篇匹配
result = {}
unmatched = 0
for r in ART:
    tid = r.get("ID")
    title = str(r.get("MZ", "") or "").strip()
    if not title:
        continue
    nt = norm(title)
    if not nt or len(nt) < 4:
        continue
    hit = None
    for k in CAT_ORDER:
        rgn = norm_regions.get(k, "")
        if rgn and (nt in rgn or (len(nt) > 6 and rgn[:len(nt)] == nt)):
            hit = k
            break
    if hit:
        result[str(tid)] = hit
    else:
        unmatched += 1

# 4) 输出
out_path = os.path.join(WEB, "bz_map.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=0)

from collections import Counter
c = Counter(result.values())
print("输出映射文件:", out_path)
print("匹配文章总数:", len(result))
print("未匹配(不归入病症研究):", unmatched)
print("=== 各栏目篇数 ===")
for k in CAT_ORDER:
    print("  %-14s %-14s %d" % (k, CAT_NAME[k], c.get(k, 0)))
