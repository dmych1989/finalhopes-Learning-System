# -*- coding: utf-8 -*-
"""天纪学习系统 data layer.

Two backends, auto-selected by data.db presence (see common.USE_SQLITE):
  * SQLite  — preferred (Vercel + local). No pyodbc / ODBC.
  * Access .mdb (LILUN / CollData / MasterData) — fallback for conversion time only.

天纪由 THREE independent Access databases 组成（密码各不相同）:
  LILUN.mdb (JiSkS92A30) / CollData.mdb (1043260300A) / MasterData.mdb (ScDO09kj9u)
加密规则与主库一致：字节列 XOR-0x0F → RTF(GBK)；个别 memo 以纯文本 RTF 存储（八字命例 YCNR）。
卦图在磁盘 Data/guatu/ 下（每卦 .jpg / .png）。
"""
import os
import ast
import re
import json
import sqlite3
from collections import defaultdict

from common import (decrypt_bytes, rtf_to_text, clean_text, text_of,
                    DATA_DB, USE_SQLITE)

ROOT = r"E:\Soft\倪海夏三套学习系统\QQ频道号talktyph0id\天纪学习系统\Data"
GUATU_DIR = os.path.join(ROOT, "guatu")
LILUN_DB = os.path.join(ROOT, "LILUN.mdb")
COLL_DB = os.path.join(ROOT, "CollData.mdb")
MASTER_DB = os.path.join(ROOT, "MasterData.mdb")
PWD_LILUN = "JiSkS92A30"
PWD_COLL = "1043260300A"
PWD_MASTER = "ScDO09kj9u"


def connect_lilun():
    import pyodbc
    return pyodbc.connect(
        "Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=%s;PWD=%s;" % (LILUN_DB, PWD_LILUN))


def connect_coll():
    import pyodbc
    return pyodbc.connect(
        "Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=%s;PWD=%s;" % (COLL_DB, PWD_COLL))


def connect_master():
    import pyodbc
    return pyodbc.connect(
        "Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=%s;PWD=%s;" % (MASTER_DB, PWD_MASTER))


# ---- decryption helpers ----------------------------------------------------
def _dec_bytes(b):
    if not b:
        return ""
    return rtf_to_text(decrypt_bytes(b))


def _dec_rtf_str(s):
    if not s:
        return ""
    return rtf_to_text(s.encode("latin1", "ignore"))


def _load_table(factory, table):
    conn = factory()
    cur = conn.cursor()
    cur.execute("SELECT * FROM [%s]" % table)
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    conn.close()
    return cols, rows


# ---- mdb-mode loaders ------------------------------------------------------
def _load_gua():
    _, rows = _load_table(connect_lilun, "liushisigua")
    out = []
    for r in rows:
        nm = clean_text(r.get("MZ") or "")
        if not nm:
            continue
        out.append({"name": nm, "dd": clean_text(str(r.get("DD") or "")),
                    "nr": r.get("NR")})
    return out


def _load_rendao():
    _, rows = _load_table(connect_lilun, "renjiandao")
    out = []
    for r in rows:
        nm = clean_text(r.get("MZ") or "")
        if not nm:
            continue
        out.append({"name": nm, "dd": clean_text(str(r.get("DD") or "")),
                    "nr": r.get("NR")})
    return out


def _load_lilun():
    _, rows = _load_table(connect_lilun, "LILUN")
    out = []
    for r in rows:
        nm = clean_text(r.get("MZ") or "")
        if not nm:
            continue
        out.append({"name": nm, "nr": r.get("NR")})
    return out


def _load_riyue():
    _, rows = _load_table(connect_lilun, "riyue")
    out = []
    for r in rows:
        nm = clean_text(r.get("MZ") or "")
        out.append({"name": nm, "nr": r.get("NR")})  # bytes, decoded on demand
    return out


def _load_jingdu():
    _, rows = _load_table(connect_lilun, "jingdu")
    out = []
    for r in rows:
        sheng = clean_text(str(r.get("SHENG") or ""))
        shi = clean_text(str(r.get("SHI") or ""))
        name = (shi + "（" + sheng + "）") if shi else sheng
        out.append({"name": name, "fields": {
            "省份": sheng,
            "城市": shi,
            "经度": clean_text(str(r.get("JING") or "")),
            "纬度": clean_text(str(r.get("WEI") or "")),
            "时差": clean_text(str(r.get("CHA") or "")),
        }})
    return out


def _load_mingli():
    rows = []
    for factory in (connect_coll, connect_master):
        try:
            _, data = _load_table(factory, "MASTERDATA")
            rows.extend(data)
        except Exception:
            pass
    try:
        _, data = _load_table(connect_coll, "SELFDATA")
        rows.extend(data)
    except Exception:
        pass
    out = []
    for r in rows:
        xm = clean_text(r.get("XM") or "")
        if not xm:
            continue
        out.append({"name": xm, "raw": r})
    return out


def _strip_mingli_contact():
    """四柱·案例查询：剔除命例中的『联系方式』字段（原库里是 QQ/手机号等垃圾数据）。"""
    for rec in MINGLI:
        f = rec.get("fields")
        if isinstance(f, dict):
            f.pop("联系方式", None)


def _load_table_set(tables):
    res = {}
    for t in tables:
        try:
            cols, rows = _load_table(connect_lilun, t)
            res[t] = {"cols": cols, "rows": [list(x.values()) for x in rows]}
        except Exception:
            res[t] = {"cols": [], "rows": []}
    return res


# ---- SQLite-mode loader ----------------------------------------------------
def _normalize_tables(payload):
    """Converter stores tables subs as {"tables":[{key,label,cols,rows}]};
    normalize back to the mdb-mode shape {key:{cols,rows}} so the rest of
    the module (MODULES counts, tables()) works identically in both modes."""
    if not isinstance(payload, dict) or "tables" not in payload:
        return payload
    out = {}
    for t in payload["tables"]:
        out[t["key"]] = {"cols": t.get("cols", []), "rows": t.get("rows", [])}
    return out


def _load_sqlite():
    con = sqlite3.connect(DATA_DB)
    data = {}
    for sub in ("gua", "rendao", "lilun", "riyue", "jingdu", "mingli", "ziwei", "yijing"):
        cur = con.execute("SELECT v FROM tianji_data WHERE k=?", (sub,))
        row = cur.fetchone()
        payload = json.loads(row[0]) if row else []
        if sub in ("ziwei", "yijing"):
            payload = _normalize_tables(payload)
        data[sub] = payload
    con.close()
    return data


# ---- dispatch（懒加载）----------------------------------------------------
# 不在模块导入期加载，避免 Vercel 冷启动把整套数据读进内存导致函数初始化
# 超时（FUNCTION_INVOCATION_FAILED）；首次访问相关数据时才由 server 中间件触发。
GUA = RENDAO = LILUN = RIYUE = JINGDU = MINGLI = ZIWEI = YIJING = None
_TIANJI_LOADED = False


def _ensure_tianji():
    global GUA, RENDAO, LILUN, RIYUE, JINGDU, MINGLI, ZIWEI, YIJING, _TIANJI_LOADED, MODULES, _DATA, _LILUN_SECTIONS
    if _TIANJI_LOADED:
        return
    print("Loading 天纪 from SQLite (data.db) …" if USE_SQLITE else "Loading 天纪 databases …")
    if USE_SQLITE:
        _SD = _load_sqlite()
        GUA = _SD["gua"]; RENDAO = _SD["rendao"]; LILUN = _SD["lilun"]
        RIYUE = _SD["riyue"]; JINGDU = _SD["jingdu"]; MINGLI = _SD["mingli"]
        ZIWEI = _SD["ziwei"]; YIJING = _SD["yijing"]
        _strip_mingli_contact()
    else:
        GUA = _load_gua()
        RENDAO = _load_rendao()
        LILUN = _load_lilun()
        RIYUE = _load_riyue()
        JINGDU = _load_jingdu()
        MINGLI = _load_mingli()
        _strip_mingli_contact()
        ZIWEI = _load_table_set(["ziweibiao", "ziweizhuxing01"])
        YIJING = _load_table_set(["anshixi", "dingtianfu", "tianshi", "yt", "加密换算表"])
    MODULES = [
        {"key": "gua",    "name": "六十四卦",     "kind": "fields", "count": len(GUA),
         "desc": "64 卦：卦名 / 卦象（阴阳爻）/ 卦辞图象，配原版卦图", "hasImg": True},
        {"key": "rendao", "name": "人间道",       "kind": "fields", "count": len(RENDAO),
         "desc": "64 卦的人间道：图象解说与现实启示", "hasImg": False},
        {"key": "lilun",  "name": "天纪理论",     "kind": "fields", "count": len(LILUN),
         "desc": "倪师讲解易经 / 紫微 / 天文的核心理论（%d 篇）" % len(LILUN)},
        {"key": "riyue",  "name": "天文历法",     "kind": "fields", "count": len(RIYUE),
         "desc": "干支 / 日月 / 天时历法（%d 条，密文已解密）" % len(RIYUE)},
        {"key": "ziwei",  "name": "紫微斗数",     "kind": "tables", "count":
         len(ZIWEI["ziweibiao"]["rows"]) + len(ZIWEI["ziweizhuxing01"]["rows"]),
         "desc": "紫微斗数·局（水二局…）/ 紫微诸星"},
        {"key": "mingli", "name": "八字命例",     "kind": "fields", "count": len(MINGLI),
         "desc": "倪师八字命盘案例（%d 例，含四柱与命理分析）" % len(MINGLI)},
        {"key": "jingdu", "name": "经纬度",       "kind": "fields", "count": len(JINGDU),
         "desc": "全国省市经纬度与时差（%d 条）" % len(JINGDU)},
        {"key": "yijing", "name": "易经数表",     "kind": "tables", "count":
         sum(len(v["rows"]) for v in YIJING.values()),
         "desc": "安世袭卦 / 定天符 / 天师 / 易经 / 加密换算表"},
        {"key": "mingli_sys", "name": "命理系统", "kind": "tool", "count": 0,
         "desc": "输入阳历生日 / 时辰 / 性别，排出八字四柱 · 紫微斗数命盘 · 本命卦，并解读日主强弱 · 十神六亲 · 大运走势，关联天纪原有八字命例与理论",
         "hasImg": False},
    ]
    _DATA = {
        "gua": GUA, "rendao": RENDAO, "lilun": LILUN, "riyue": RIYUE, "jingdu": JINGDU,
        "mingli": MINGLI, "ziwei": ZIWEI, "yijing": YIJING,
    }
    _LILUN_SECTIONS = _build_dou_siz_sections(LILUN)
    _DATA.update(_LILUN_SECTIONS)
    _build_lilun_series()
    _TIANJI_LOADED = True
    print("天纪 loaded: gua=%d rendao=%d lilun=%d riyue=%d jingdu=%d mingli=%d "
          "ziwei=%d yijing=%d" % (len(GUA), len(RENDAO), len(LILUN), len(RIYUE),
                                  len(JINGDU), len(MINGLI),
                                  len(ZIWEI["ziweibiao"]["rows"]) + len(ZIWEI["ziweizhuxing01"]["rows"]),
                                  sum(len(v["rows"]) for v in YIJING.values())))


# ---- lilun 系列合并 -------------------------------------------------------
# 仅合并「同名 + 末尾序号（一/二/三…或阿拉伯数字）」的关联文章，例如
# 工作一~四、婚姻感情一/二、学业一/二；并吸收同名无序号的概述篇（工作/学业），
# 形成一篇干净的总文章。命例(mingli) 与 紫微星名重复（衰/博士/财运…）不含序号，
# 不在此列，保持原样。
_CN_NUM = "一二三四五六七八九十百零〇"
_ORD_SUFFIX = re.compile(r"(?:[（(]([%s]+)[）)]|([%s]+)|(\d+))$" % (_CN_NUM, _CN_NUM))

def _lilun_base(name):
    n = (name or "").strip()
    m = _ORD_SUFFIX.search(n)
    return n[:m.start()].strip() if m else n

def _lilun_has_ord(name):
    return bool(_ORD_SUFFIX.search(name or ""))

def _lilun_text(it):
    f = it.get("fields")
    if isinstance(f, str):
        try:
            f = ast.literal_eval(f)
        except Exception:
            f = {"正文": f}
    if isinstance(f, dict):
        return "\n".join(str(v) for v in f.values() if v)
    if USE_SQLITE:
        return ""
    return clean_text(it.get("nr") or "")

def _cn_to_int(s):
    tbl = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7,
           "八": 8, "九": 9, "十": 10, "零": 0, "〇": 0}
    s = (s or "").strip()
    if s.isdigit():
        return int(s)
    if s == "十":
        return 10
    if "十" in s:
        a, _, b = s.partition("十")
        return (tbl.get(a, 1) if a else 1) * 10 + (tbl.get(b, 0) if b else 0)
    return tbl.get(s, 10 ** 9)  # 未知序号排最后

_LILUN_MEMBER_CANON = {}
_LILUN_MERGED = {}
def _build_lilun_series():
    groups = defaultdict(list)
    for idx, it in enumerate(LILUN):
        groups[_lilun_base(it.get("name", ""))].append(idx)
    for base, idxs in groups.items():
        ord_members = [i for i in idxs if _lilun_has_ord(LILUN[i].get("name", ""))]
        if len(ord_members) < 2:
            continue  # 仅当≥2 篇带序号才视为系列；纯重复名（衰/财运…）不合并
        def ord_key(i, _suf=_ORD_SUFFIX):
            m = _suf.search(LILUN[i].get("name", ""))
            if m:
                tok = m.group(1) or m.group(2) or m.group(3)
                return (1, _cn_to_int(tok))
            return (0, 0)  # 无序号概述篇排最前
        ordered = sorted(idxs, key=ord_key)
        fields = {}
        for i in ordered:
            fields[LILUN[i].get("name", "")] = _lilun_text(LILUN[i])
        canon = ordered[0]  # 概述篇（若有）或最小序号篇
        _LILUN_MERGED[canon] = {"name": base, "dd": "", "fields": fields}
        for i in idxs:
            _LILUN_MEMBER_CANON[i] = canon

def _collapse_lilun_tree(node):
    """折叠左侧目录树：移除非首篇系列叶子，将首篇叶子改名为合并总标题，清理空目录。"""
    if isinstance(node, list):
        out = []
        for x in node:
            r = _collapse_lilun_tree(x)
            if r is not None:
                out.append(r)
        return out
    if not isinstance(node, dict):
        return node
    if node.get("src") == "lilun":
        idx = node.get("idx")
        ci = _LILUN_MEMBER_CANON.get(idx)
        if ci is not None and ci != idx:
            return None  # 非首篇系列 → 移除
        if idx in _LILUN_MERGED:
            node = dict(node)
            node["t"] = _LILUN_MERGED[idx]["name"]  # 首篇 → 改名
        return node
    if "children" in node:
        kids = []
        for c in node["children"]:
            r = _collapse_lilun_tree(c)
            if r is not None:
                kids.append(r)
        if not kids:
            return None
        node = dict(node)
        node["children"] = kids
        return node
    return node


# ---- 去重：剥掉「正文首行 == 标题」的那一行 ----------------------------
# 部分「四柱（八字）理论」文章解密后的 memo，首行就是文章标题；而前端已用
# <h3> 渲染大标题，导致标题重复显示。这里在 get_item 返回前，把正文首行
# 与标题完全一致（或仅带标点/空白）的那一行去掉。对无重复的篇目零影响。
_TITLE_TRAIL = re.compile(r"^[\s：:、\-—–·.。，,]+")
def _strip_leading_title(text, *titles):
    """若正文首行（跳过前置空行）等于某个标题，或仅由标题+标点/空白构成，
    则删掉该行（及紧随的空行）；否则原样返回。"""
    if not text:
        return text
    lines = text.split("\n")
    idx = 0
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    if idx >= len(lines):
        return text
    fstripped = lines[idx].strip()
    for t in titles:
        if not t:
            continue
        t = t.strip()
        if fstripped == t:
            del lines[idx]
            while idx < len(lines) and not lines[idx].strip():
                del lines[idx]
            return "\n".join(lines)
        if fstripped.startswith(t):
            rem = _TITLE_TRAIL.sub("", fstripped[len(t):])
            if not rem:
                del lines[idx]
                while idx < len(lines) and not lines[idx].strip():
                    del lines[idx]
                return "\n".join(lines)
    return text

def _clean_lilun_fields(fields, main_title):
    """清理 lilun 文章的 fields：键本身即小节标题（合并系列）→ 用小节标题去重；
    “正文”键 → 用文章主标题去重。返回新 dict，不改原数据。"""
    if not isinstance(fields, dict):
        return fields
    out = {}
    for k, v in fields.items():
        if isinstance(v, str):
            out[k] = _strip_leading_title(v, k, main_title)
        else:
            out[k] = v
    return out


MODULES = []  # 在 _ensure_tianji() 加载数据后填充（含各模块 count）

_DATA = {}

# ---- 斗数 / 四柱 文章分类（从「天纪理论」lilun 分出，供顶部下拉菜单）----
# lilun 271 篇天然分两块：从名为「紫微」那篇起为紫微斗数理论，其前为八字（四柱）理论。
# 各块再按关键词归入 基础 / 分类 / 细则。这些虚拟模块仅注入 _DATA，
# 复用 /api/tianji/list 与 /item（均按 sub 读 _DATA），无需新增端点。
def _build_dou_siz_sections(lilun):
    names = [it.get("name", "") for it in lilun]
    try:
        split = names.index("紫微")
    except ValueError:
        split = len(lilun)
    bazi = lilun[:split]      # 八字 / 四柱 理论
    ziwei = lilun[split:]     # 紫微 / 斗数 理论

    def cat_bazi(n):
        if any(k in n for k in ("八字工作调动", "八字断特殊事", "八字牢狱",
                                "住房条件", "验证时辰法", "择日", "命理怎样择日")):
            return "xf"
        if any(k in n for k in ("大运流年", "命局", "命运年", "吉凶信息",
                                "如何区分六亲", "八字同六亲", "吉凶应在", "看兄弟排行",
                                "婚姻", "合婚", "命理断婚外情", "子女", "学业", "财运",
                                "官运", "工作", "性格", "长相", "相貌", "人体与疾病")):
            return "fl"
        return "ll"

    def cat_ziwei(n):
        if any(k in n for k in ("兄弟宫", "夫妻宫", "子女宫", "财帛宫", "疾厄宫",
                                "迁移宫", "交友宫", "事业宫", "田宅宫", "福德宫", "父母宫",
                                "身宫", "灾厄预测", "车祸预测", "坠跌预测", "水祸",
                                "动物伤害", "药物中毒", "自杀", "火灾", "刑讼",
                                "失窃破财", "事业", "灾祸", "官司", "六亲", "婚姻")):
            return "xf"
        return "ll"

    out = {"_sz_basic": [], "_sz_class": [], "_sz_detail": [],
           "_ds_basic": [], "_ds_detail": []}
    bazi_map = {"ll": "_sz_basic", "fl": "_sz_class", "xf": "_sz_detail"}
    ziwei_map = {"ll": "_ds_basic", "xf": "_ds_detail"}
    for a in bazi:
        out[bazi_map[cat_bazi(a.get("name", ""))]].append(a)
    for a in ziwei:
        out[ziwei_map[cat_ziwei(a.get("name", ""))]].append(a)
    return out

_LILUN_SECTIONS = {}

TABLE_LABELS = {
    "ziweibiao": "紫微斗数·局", "ziweizhuxing01": "紫微诸星",
    "anshixi": "安世袭卦", "dingtianfu": "定天符", "tianshi": "天师",
    "yt": "易经", "加密换算表": "加密换算表",
}


def modules():
    return MODULES


def list_items(sub, q=""):
    raw = _DATA.get(sub, [])
    if isinstance(raw, dict):
        return raw  # tables subs handled by /tables endpoint
    items = []
    for idx, it in enumerate(raw):
        # 天纪理论(lilun)：系列合并后，列表/搜索只保留首篇（合并总文章），其余系列篇去重
        if sub == "lilun" and _LILUN_MEMBER_CANON.get(idx, idx) != idx:
            continue
        name = it["name"]
        if sub == "lilun" and idx in _LILUN_MERGED:
            name = _LILUN_MERGED[idx]["name"]
        items.append({"i": idx, "name": name})
    if q:
        ql = q.lower()
        out = []
        for it in items:
            # 标题命中直接纳入
            if ql in it["name"].lower():
                out.append(it)
                continue
            # 否则匹配文章正文（fields 内容）
            try:
                rec = get_item(sub, it["i"])
            except Exception:
                rec = None
            fields = (rec or {}).get("fields") or {}
            fv = " ".join(str(k) for k in fields) + " " + \
                 " ".join(str(v) for v in fields.values() if v)
            if ql in fv.lower():
                out.append(it)
        items = out
    return items


def get_item(sub, i):
    raw = _DATA.get(sub, [])
    if isinstance(raw, dict) or not raw:
        return None
    # 天纪理论(lilun)：系列合并后，系列内任一篇均返回合并总文章
    if sub == "lilun":
        ci = _LILUN_MEMBER_CANON.get(int(i), int(i))
        if ci in _LILUN_MERGED:
            m = dict(_LILUN_MERGED[ci])
            m["fields"] = _clean_lilun_fields(m.get("fields"), m.get("name"))
            return m
    try:
        rec = raw[int(i)]
    except (ValueError, IndexError):
        return None
    if USE_SQLITE:
        # 转换器已把 riyue/mingli 等密文解码为最终结构；个别旧版本转换器把
        # fields 存成了 dict 的字符串表示（含 dd 键），这里规整为 dict 以保渲染。
        rec = dict(rec)
        f = rec.get("fields")
        if isinstance(f, str):
            try:
                rec["fields"] = ast.literal_eval(f)
            except Exception:
                rec["fields"] = {"正文": f}
        rec["fields"] = _clean_lilun_fields(rec.get("fields"), rec.get("name"))
        return rec
    # ---- mdb 模式：按需解码 ----
    if sub in ("gua", "rendao"):
        fields = {"图象 / 卦辞": clean_text(rec.get("nr") or "")}
        return {"name": rec["name"], "dd": rec.get("dd") or "", "fields": fields}
    if sub == "lilun":
        return {"name": rec["name"],
                "fields": {"正文": _strip_leading_title(clean_text(rec.get("nr") or ""), rec["name"])}}
    if sub == "riyue":
        return {"name": rec["name"], "fields": {"解说": _dec_bytes(rec.get("nr"))}}
    if sub == "jingdu":
        return {"name": rec["name"], "fields": rec.get("fields", {})}
    if sub == "mingli":
        r = rec.get("raw", {})
        zhu = "　".join([
            "年柱 " + clean_text(str(r.get("NZ") or "")),
            "月柱 " + clean_text(str(r.get("YZ") or "")),
            "日柱 " + clean_text(str(r.get("RZ") or "")),
            "时柱 " + clean_text(str(r.get("SZ") or "")),
        ])
        birth = "　".join([
            "生年 " + clean_text(str(r.get("NN") or "")),
            "月 " + clean_text(str(r.get("YY") or "")),
            "日 " + clean_text(str(r.get("RR") or "")),
            "时 " + clean_text(str(r.get("FF") or "")),
        ])
        fields = {
            "性别": clean_text(str(r.get("XB") or "")),
            "四柱（干支）": zhu,
            "生辰": birth,
            "出生地": clean_text(str(r.get("CSD") or "")),
            "命盘分析": _dec_rtf_str(r.get("YCNR")),
        }
        return {"name": rec["name"], "fields": fields}
    return None


def tables(sub):
    """Return {tables:[{key,label,cols,rows}]} for a tables-kind sub-module."""
    src = _DATA.get(sub)
    if not isinstance(src, dict):
        return {"tables": []}
    out = []
    for key, t in src.items():
        out.append({"key": key, "label": TABLE_LABELS.get(key, key),
                    "cols": t["cols"], "rows": t["rows"]})
    return {"tables": out}


def image_bytes(name):
    """卦图：SQLite (tianji_img) 或磁盘 guatu/ 目录。"""
    if USE_SQLITE:
        con = sqlite3.connect(DATA_DB)
        cur = con.execute("SELECT data, ctype FROM tianji_img WHERE name=?", (name,))
        row = cur.fetchone()
        con.close()
        if row and row[0]:
            return bytes(row[0]), (row[1] or "image/jpeg")
        return None, None
    for ext in (".jpg", ".png"):
        p = os.path.join(GUATU_DIR, name + ext)
        if os.path.exists(p):
            try:
                with open(p, "rb") as f:
                    return f.read(), ("image/jpeg" if ext == ".jpg" else "image/png")
            except Exception:
                return None, None
    return None, None


__all__ = ["modules", "list_items", "get_item", "tables", "image_bytes", "MODULES"]
