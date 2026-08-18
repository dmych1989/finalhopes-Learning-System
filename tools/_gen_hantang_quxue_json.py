# -*- coding: utf-8 -*-
"""
汉唐取穴 临床取穴数据生成器（层级版）
---------------------------------
读取:
  - 人纪学习系统/汉唐取穴/导出/汉唐取穴_导出.txt   (4 大类临床树 + 条目正文，扁平但带 ●▶◇○ 标记)
  - 人纪学习系统/倪海厦汉唐中医馆人纪针灸内部学习系统V2022.exe  (Delphi .dfm, 针刺手法文本)
  - web_app/data.db 的 renji_data(tu)         (校验图表名真实存在)
产出:
  - web_app/hantang_quxue.json
    结构:
      methods: {
        jingluo/zangfu/duizheng/bianzheng -> {
          name,
          groups: [ {name, charts:[<MZ名>], children:[ {name, text, charts:[]} | 子group ] } ]
        }
      }
      shoufa:  { name, items:[{name, text, imgs:[<图名无扩展名>]}], overview:[<图名>] }
图表名与图名均不带扩展名，直接对应 IMG_INDEX["renji"] 的 key，供 /renji/img?name= 使用。

目录层级规则（来自 导出.txt 的 ●▶◇○ 标记）：
  ● 一级组（经脉 / 系 / 腑 / 病症分类）—— 若无直接 ○ 条目而只有 ▶/◇ 子组，则为纯容器，提升其子组为组；
  ▶ / ◇ 二级子组（如 胃肠病症 / 心血管病症）—— 直接作为组；
  ○ 条目（如 肺火上炎 / 风寒痹阻）—— 可点击，带辨证选穴正文。
取穴图表(charts) 挂在「组」上（经脉/系/腑/病症分类），点击条目时一并展示父组图表。
"""
import os, re, struct, json, sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB  = os.path.join(ROOT, "web_app")
BASE = r"E:\Soft\倪海夏三套学习系统\QQ频道号talktyph0id\人纪学习系统"
EXE  = os.path.join(BASE, "倪海厦汉唐中医馆人纪针灸内部学习系统V2022.exe")
EXPORT = os.path.join(BASE, "汉唐取穴", "导出", "汉唐取穴_导出.txt")
OUT  = os.path.join(WEB, "hantang_quxue.json")

# ---------- 1. 条目 -> 图表映射 (nishitu MZ 名, 无扩展名) ----------
MERIDIAN = {
 "手太阴肺经病辩证选穴": ["各脏腑经络的生理病理与治疗配穴列表-手太阴肺经"],
 "手阳明大肠经病辩证选穴": ["各脏腑经络的生理病理与治疗配穴列表-手阳明大肠经"],
 "足阳明胃经病辩证选穴": ["各脏腑经络的生理病理与治疗配穴列表-足阳明胃经"],
 "足太阴脾经病辩证选穴": ["各脏腑经络的生理病理与治疗配穴列表-足太阴脾经"],
 "手少阴心经病辩证选穴": ["各脏腑经络的生理病理与治疗配穴列表-手少阴心经"],
 "手太阳小肠经病辩证选穴": ["各脏腑经络的生理病理与治疗配穴列表-手太阳小肠经"],
 "足太阳膀胱经病辩证选穴": ["各脏腑经络的生理病理与治疗配穴列表-足太阳膀胱经"],
 "手厥阴心包经病辩证选穴": ["各脏腑经络的生理病理与治疗配穴列表-手厥阴心包经"],
 "手少阳三焦经病辩证选穴": ["各脏腑经络的生理病理与治疗配穴列表-手少阳三焦经"],
 "足少阳胆经病辩证选穴": ["各脏腑经络的生理病理与治疗配穴列表-足少阳胆经"],
 "足厥阴肝经病辩证选穴": ["各脏腑经络的生理病理与治疗配穴列表-足厥阴肝经"],
 "足少阴肾经病辩证选穴": ["各脏腑经络的生理病理与治疗配穴列表-足少阴肾经"],
}
QIJING = ["督脉病辩证选穴","任脉病辩证选穴","冲脉病辩证选穴","带脉病辩证选穴",
          "阴维脉病辩证选穴","阳维脉病辩证选穴","阴跷脉病辩证选穴","阳跷脉病辩证选穴"]
QIJING_CHARTS = ["八脉交会穴表","十五络穴表","十四经经穴的主治概要归类表","八穴配属九宫表"]
ORGAN = {
 "心系病辩证选穴": ["各脏腑经络的生理病理与治疗配穴列表-手少阴心经"],
 "肝系病辩证选穴": ["各脏腑经络的生理病理与治疗配穴列表-足厥阴肝经"],
 "脾系病辩证选穴": ["各脏腑经络的生理病理与治疗配穴列表-足太阴脾经"],
 "肺系病辩证选穴": ["各脏腑经络的生理病理与治疗配穴列表-手太阴肺经"],
 "肾系病辩证选穴": ["各脏腑经络的生理病理与治疗配穴列表-足少阴肾经"],
 "心包病辩证选穴": ["各脏腑经络的生理病理与治疗配穴列表-手厥阴心包经"],
 "胆腑病辩证选穴": ["各脏腑经络的生理病理与治疗配穴列表-足少阳胆经"],
 "胃腑病辩证选穴": ["各脏腑经络的生理病理与治疗配穴列表-足阳明胃经"],
 "大肠腑病辩证选穴": ["各脏腑经络的生理病理与治疗配穴列表-手阳明大肠经"],
 "膀胱腑病辩证选穴": ["各脏腑经络的生理病理与治疗配穴列表-足太阳膀胱经"],
}
GENERAL = ["俞募穴主要治疗范围表","下合六表","五腧穴表","五输穴表","五腧穴五行表",
           "基本补泻归类表","十二经主客原络治症配穴见下表","母子经子母补泻取穴表"]
BIANBING = {
 "消化系病选穴": ["各脏腑经络的生理病理与治疗配穴列表-足阳明胃经",
               "各脏腑经络的生理病理与治疗配穴列表-手阳明大肠经",
               "各脏腑经络的生理病理与治疗配穴列表-足太阴脾经"],
 "呼吸系病选穴": ["各脏腑经络的生理病理与治疗配穴列表-手太阴肺经"],
 "心脑血管系病症选穴": ["各脏腑经络的生理病理与治疗配穴列表-手少阴心经",
                    "各脏腑经络的生理病理与治疗配穴列表-手厥阴心包经"],
 "精神神经系统辩病取穴": ["各脏腑经络的生理病理与治疗配穴列表-手少阴心经",
                      "各脏腑经络的生理病理与治疗配穴列表-手厥阴心包经",
                      "各脏腑经络的生理病理与治疗配穴列表-足厥阴肝经"],
 "泌尿生殖系统辩病取穴": ["各脏腑经络的生理病理与治疗配穴列表-足少阴肾经",
                      "各脏腑经络的生理病理与治疗配穴列表-足太阳膀胱经"],
 "运动系统辩证取穴": ["各脏腑经络的生理病理与治疗配穴列表-足太阳膀胱经",
                   "各脏腑经络的生理病理与治疗配穴列表-足厥阴肝经"],
 "腰椎、颈椎病症": ["各脏腑经络的生理病理与治疗配穴列表-足太阳膀胱经"],
 "五官病辩选穴": [],
 "皮肤病辩证取穴": ["各脏腑经络的生理病理与治疗配穴列表-手太阴肺经",
                 "各脏腑经络的生理病理与治疗配穴列表-手阳明大肠经"],
 "传染性疾病辩病取穴": [],
 "内分泌病辩选穴": [],
}

def charts_for(group_name, cat):
    if group_name in MERIDIAN:
        return MERIDIAN[group_name]
    if group_name in QIJING:
        return list(QIJING_CHARTS)
    if group_name in ORGAN:
        return ORGAN[group_name]
    if group_name in BIANBING:
        return BIANBING[group_name] + list(GENERAL)
    if cat in ("汉唐对症取穴", "汉唐辩病取穴法"):
        return list(GENERAL)
    return list(GENERAL)

# ---------- 2. 解析 导出.txt 临床树（层级） ----------
METHOD_MAP = {
    "经络辩证取穴": "jingluo",
    "脏腑辩证取穴": "zangfu",
    "汉唐对症取穴": "duizheng",
    "汉唐辩病取穴法": "bianzheng",
}
NAME_TO_KEY = {v: k for k, v in METHOD_MAP.items()}

methods = {}
cur_method = None
groups = None          # 当前 method 的 groups 列表
stack = []             # 当前 method 内的节点栈：[top_group] 或 [top_group, subgroup]
cur_leaf = None

with open(EXPORT, encoding="utf-8") as f:
    for raw in f:
        line = raw.rstrip("\n")
        s = line.strip()
        if not s:
            continue
        if s.startswith("【第五章"):   # EXE 导航索引垃圾，停止
            break
        m = re.match(r"^【(.+?)】", s)
        if m:
            nm = m.group(1)
            if nm in METHOD_MAP:
                cur_method = METHOD_MAP[nm]
                groups = []
                methods[cur_method] = {"name": nm, "groups": groups}
                stack = []
                cur_leaf = None
            else:
                cur_method = None
            continue
        if cur_method is None:
            continue
        if s.startswith("●"):
            node = {"name": s[1:].strip(), "kind": "group", "children": []}
            groups.append(node)
            stack = [node]
            cur_leaf = None
        elif s.startswith("▶") or s.startswith("◇"):
            node = {"name": s[1:].strip(), "kind": "subgroup", "children": []}
            if stack:
                stack[-1]["children"].append(node)
            else:
                groups.append(node)
            stack = [stack[0], node] if stack else [node]
            cur_leaf = None
        elif s.startswith("○"):
            leaf = {"name": s[1:].strip(), "kind": "leaf", "text": ""}
            if stack:
                stack[-1]["children"].append(leaf)
            else:
                groups.append(leaf)
            cur_leaf = leaf
        else:
            if cur_leaf is not None:
                cur_leaf["text"] = (cur_leaf["text"] + "\n" if cur_leaf["text"] else "") + s

# 提升纯容器 ● 组（只有 ▶/◇ 子组、无 ○ 条目）；删除无条目后代的空组
def flatten(grp_list):
    out = []
    for g in grp_list:
        if g.get("kind") in ("group", "subgroup"):
            leaves = [c for c in g["children"] if c.get("kind") == "leaf"]
            subs = [c for c in g["children"] if c.get("kind") in ("group", "subgroup")]
            if subs and not leaves:
                out.extend(flatten(subs))          # 纯容器 -> 提升子组
            else:
                g["children"] = flatten(g["children"])
                out.append(g)
        else:
            out.append(g)  # 孤立 ○（理论上不会发生）
    return out

def drop_empty(grp_list):
    out = []
    for g in grp_list:
        if g.get("kind") in ("group", "subgroup"):
            g["children"] = drop_empty(g["children"])
            has_leaf = any(c.get("kind") == "leaf" or (c.get("kind") in ("group","subgroup") and _has_leaf(c))
                           for c in g["children"])
            if has_leaf:
                out.append(g)
        else:
            out.append(g)
    return out

def _has_leaf(node):
    if node.get("kind") == "leaf":
        return True
    return any(_has_leaf(c) for c in node.get("children", []))

for key in methods:
    methods[key]["groups"] = drop_empty(flatten(methods[key]["groups"]))

# ---------- 3. 校验图表名真实存在于 tu ----------
con = sqlite3.connect(os.path.join(WEB, "data.db"))
tu_names = set(json.loads(con.execute("SELECT v FROM renji_data WHERE k='tu'").fetchone()[0]))
con.close()

def build_node(node, cat):
    if node.get("kind") == "leaf":
        return {"name": node["name"], "text": node.get("text", "").strip(),
                "charts": []}
    # group / subgroup
    charts = [c for c in charts_for(node["name"], cat) if c in tu_names]
    return {"name": node["name"], "charts": charts,
            "children": [build_node(c, cat) for c in node.get("children", [])]}

DATA_METHODS = {}
for key, mv in methods.items():
    cat = mv["name"]
    DATA_METHODS[key] = {
        "name": cat,
        "groups": [build_node(g, cat) for g in mv["groups"]],
    }

# ---------- 4. 从 EXE 提取 针刺手法 文本 ----------
def extract_widestr(data, content_off):
    ln = struct.unpack_from("<I", data, content_off - 4)[0]
    if ln <= 0 or ln > 4000:
        raise ValueError("bad length %d at %d" % (ln, content_off))
    raw = data[content_off: content_off + ln * 2]
    return raw.decode("utf-16-le")

exe_data = open(EXE, "rb").read()
SHOUFA_OFF = {
 "烧山火": 7648778, "透天凉": 7649344, "开阖补法": 7667818, "开阖泻法": 7668160,
 "提插补法": 7555965, "提插泻法": 7563279, "捻转补法": 7553743, "捻转泻法": 7561048,
}
SHOUFA_IMG = {
 "烧山火": ["山火透天凉手法图", "透天凉手法图"], "透天凉": ["透天凉手法图", "山火透天凉手法图"],
 "开阖补法": ["痰闭针孔针刺图"], "开阖泻法": ["痰闭针孔针刺图"],
 "提插补法": ["提插捻转补泻图(阴阳)"], "提插泻法": ["提插捻转补泻图(阴阳)"],
 "捻转补法": ["提插捻转补泻图(阴阳)"], "捻转泻法": ["提插捻转补泻图(阴阳)"],
}
SHOUFA_ORDER = list(SHOUFA_OFF.keys())
shoufa_items = []
for name in SHOUFA_ORDER:
    txt = extract_widestr(exe_data, SHOUFA_OFF[name]).strip()
    shoufa_items.append({"name": name, "text": txt, "imgs": list(SHOUFA_IMG.get(name, []))})
SHOUFA_OVERVIEW = ["龙、虎、龟、凤操作表", "提插，捻转补泻表",
                   "提插，捻转补泻的主要的综合手法", "脉象主证取穴表", "足躯逆对法"]

DATA = {
    "methods": DATA_METHODS,
    "shoufa": {"name": "针刺手法", "items": shoufa_items, "overview": SHOUFA_OVERVIEW},
}

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=1)

# 统计
def count_leaves(node):
    if "children" not in node:
        return 1
    return sum(count_leaves(c) for c in node["children"])

for key in ("jingluo", "zangfu", "duizheng", "bianzheng"):
    mv = DATA_METHODS[key]
    ng = len(mv["groups"])
    nl = sum(count_leaves(g) for g in mv["groups"])
    print("  %-9s %s: 组=%d 条目=%d" % (key, mv["name"], ng, nl))
print("OK ->", OUT)
print("JSON 大小: %.1f KB" % (os.path.getsize(OUT)/1024))
