#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据「医学论文医案查询系统/时事评论/目录.txt」（EXE 时事评论原始栏目结构）
构建 文章ID -> EXE栏目key 的映射，输出为 web_app/sspl_map.json，供 server.py 加载。

处理逻辑：
- 按行首《xxx》切分栏目区域；合并同名栏目（倪师论流感出现两次）；修正错别字
  「时倪师论肾脏」->「倪师论肾脏」。
- 内嵌栏目「保健锦囊」仅在倪师论乳癌某行里出现 1 篇，单独提取归到 baojian。
- 妇科门诊 / 食品帝国FoodInc. 为干净独立栏目。
- 「黄帝内经」仅文末一篇标题提及，非独立栏目，随其所在区域(食品帝国)归类。
- 匹配：对每篇库文章，归一化标题后在各栏目区域文本中做子串匹配（首命中），
  baojian 用专门规则优先判定。
- 仅输出能在目录.txt中匹配到的文章（即 EXE 时事评论真实收录的 1033 篇左右）。
"""
import sys, re, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web_app")
sys.path.insert(0, WEB)
import server as S

ART = S.ARTICLES

# 归类用栏目 key（与 server.py SSPL_CATS 对应）
CAT_ORDER = [
    "ai", "ganbing", "liugan", "shenzang", "niunai", "tangniao",
    "xinbing", "xueye", "zhongyao", "kangshengsu", "zuixin",
    "ruanai", "youyu", "fuke", "baojian", "fkmenzhen", "weifanlei", "foodinc",
]
CAT_NAME = {
    "ai": "倪师论癌症", "ganbing": "倪师论肝病", "liugan": "倪师论流感",
    "shenzang": "倪师论肾脏", "niunai": "倪师论牛奶", "tangniao": "倪师论糖尿",
    "xinbing": "倪师论心病", "xueye": "倪师论血液", "zhongyao": "倪师论中药",
    "kangshengsu": "倪师论抗生素", "zuixin": "最新研究成果时事评论",
    "ruanai": "倪师论乳癌", "youyu": "倪师论忧郁", "fuke": "倪师论妇科",
    "baojian": "保健锦囊", "fkmenzhen": "妇科门诊", "weifanlei": "未归类评论",
    "foodinc": "食品帝国FoodInc.",
}
# 目录.txt 栏目名 -> key（含合并/修正）
NAME2KEY = {
    "倪师论癌症": "ai", "倪师论肝病": "ganbing",
    "倪师论流感": "liugan", "时倪师论肾脏": "shenzang", "倪师论肾脏": "shenzang",
    "倪师论牛奶": "niunai", "倪师论糖尿": "tangniao", "倪师论心病": "xinbing",
    "倪师论血液": "xueye", "倪师论中药": "zhongyao", "倪师论抗生素": "kangshengsu",
    "最新研究成果时事评论": "zuixin", "倪师论乳癌": "ruanai", "倪师论忧郁": "youyu",
    "倪师论妇科": "fuke", "妇科门诊": "fkmenzhen", "未归类评论": "weifanlei",
    "食品帝国FoodInc.": "foodinc",
}

def norm(s):
    return re.sub(r"\s+", "", re.sub(r"[，。、！？；：“”‘’（）()《》~～\-—!?]", "", str(s)))

CATALOG = os.path.join(
    "E:\\Soft\\倪海夏三套学习系统\\QQ频道号talktyph0id\\医学论文医案查询系统",
    "时事评论", "目录.txt"
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
            if cur_key is not None:
                regions.append((cur_key, "\n".join(buf)))
            nm = m.group(1).strip()
            cur_key = NAME2KEY.get(nm)
            buf = []
            rest = s[m.end():].strip()
            if rest and cur_key:
                buf.append(rest)
        else:
            if cur_key is None:
                continue
            buf.append(s)
if cur_key is not None:
    regions.append((cur_key, "\n".join(buf)))

# 合并同名 key 区域
merged = {}
for k, txt in regions:
    if k is None:
        continue
    merged[k] = merged.get(k, "") + "\n" + txt

# 提取保健锦囊：目录.txt 仅在倪师论乳癌某行内嵌《保健锦囊》并跟随 1 篇确切标题。
# 提取《保健锦囊》后到下一个《 之前的文本，并截取首个可识别标题（以「中西医合治乳癌可减轻」
# 起算，到该标题自然结束）。避免把后续拼接的乳癌标题误并入保健锦囊。
baojian_titles = []
if "ruanai" in merged:
    rt = merged["ruanai"]
    for mm in re.finditer(r"《保健锦囊》([^《]*)", rt):
        seg = mm.group(1)
        # 确切的保健锦囊文章标题（目录.txt 中唯一明确带《保健锦囊》标记者）
        anchor = "中西医合治乳癌可减轻放、化疗副作用"
        if anchor in seg:
            baojian_titles.append(anchor)
merged["baojian"] = "\n".join(baojian_titles)

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
    # 保健锦囊优先（其标题在 ruanai 区，会被误判，故提前单独判定）
    hit = None
    if baojian_titles and any(norm(t) and (norm(t) in nt or nt in norm(t)) for t in baojian_titles):
        hit = "baojian"
    else:
        for k in CAT_ORDER:
            if k == "baojian":
                continue
            rgn = norm_regions.get(k, "")
            if rgn and (nt in rgn or (len(nt) > 6 and rgn[:len(nt)] == nt)):
                hit = k
                break
    if hit:
        result[str(tid)] = hit
    else:
        unmatched += 1

# 4) 输出
out_path = os.path.join(WEB, "sspl_map.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=0)

# 统计
from collections import Counter
c = Counter(result.values())
print("输出映射文件:", out_path)
print("匹配文章总数:", len(result))
print("未匹配(不归入时事评论):", unmatched)
print("=== 各栏目篇数 ===")
for k in CAT_ORDER:
    print("  %-12s %-22s %d" % (k, CAT_NAME[k], c.get(k, 0)))
