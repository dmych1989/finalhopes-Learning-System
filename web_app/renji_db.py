# -*- coding: utf-8 -*-
"""人纪学习系统 data layer.

Two backends, auto-selected by data.db presence (see common.USE_SQLITE):
  * SQLite  — preferred (Vercel + local). No pyodbc / ODBC.
  * Access .mdb (人纪针灸学习系统 LILUN.mdb) — fallback for conversion time only.
Same password (JiSkS92A30) and same XOR-0x0F RTF(GBK) cipher as the main app.

Tables (人纪-specific):
  nishixuewei (357) 倪师穴位详解  - 13 encrypted attributes per point
  zhenjiuyian  (220) 针灸医案     - 歌诀/穴位介绍/病因病理分析/医疗案例
  xuewei4      (252) 汉唐方剂     - MZ='HT-n…', NR is XOR-encrypted memo RTF
  nishitu      (63)  倪师图       - NR = XOR -> JPEG (tables / diagrams)
  SELFDATA     (348) 穴位坐标     - ID=穴名 + left/top/H1/V1/Y (for body map)
Shared (plaintext) reference tables: BBXX / BZDZ / ZFBZ / ZJDCJL / linggui / najia / nazi
"""
import os
import json
import sqlite3

from common import (decrypt_bytes, rtf_to_text, clean_text, text_of,
                    DATA_DB, USE_SQLITE)

RENJI_DB = r"E:\Soft\倪海夏三套学习系统\QQ频道号talktyph0id\人纪学习系统\Data\LILUN.mdb"
PWD = "JiSkS92A30"


def connect():
    import pyodbc
    return pyodbc.connect(
        "Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=%s;PWD=%s;" % (RENJI_DB, PWD)
    )


def decrypt_memo(s):
    """xuewei4.NR is an XOR-0x0F ciphered RTF stored inside a memo (TEXT) field.
    pyodbc returns it as a str whose codepoints equal the original bytes; round-trip
    through latin1 to recover bytes, then XOR + RTF decode."""
    if not s:
        return ""
    b = s.encode("latin1", "ignore")
    return rtf_to_text(decrypt_bytes(b))


def _rows(table):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM [%s]" % table)
    cols = [d[0] for d in cur.description]
    out = [dict(zip(cols, r)) for r in cur.fetchall()]
    conn.close()
    return cols, out


def _fields(rec, cols, cipher_table=None):
    """Build {col: decrypted_text} for every column except the name column."""
    return {c: text_of(c, rec[c], cipher_table) for c in cols if c != "MZ"}


# ---- 列名 → 中文标题映射 ----------------------------------------------------
COLUMN_TITLES = {
    ("BBXX", "NR"): "针灸处方",
    ("BZDZ", "NR"): "论治",
    ("ZFBZ", "NR1"): "辨证（病机）", ("ZFBZ", "NR2"): "取穴治疗",
    ("ZJDCJL", "NR1"): "症候病机", ("ZJDCJL", "NR2"): "针灸治法",
    ("najia", "time"): "时辰", ("najia", "nazi_1"): "当旺经脉",
    ("najia", "nazi_2"): "补母穴", ("najia", "nazi_3"): "泻子穴",
    ("najia", "nazi_4"): "本穴", ("najia", "nazi_5"): "原穴",
    ("nazi", "time"): "时辰", ("nazi", "naja_1"): "纳子取穴（一）",
    ("nazi", "naja_2"): "纳子取穴（二）", ("nazi", "naja_3"): "纳子取穴（三）",
    ("linggui", "time"): "时辰",
}


def _col_title(table, col):
    return COLUMN_TITLES.get((table, col), col)


# ---- mdb-mode loaders ------------------------------------------------------
def _load_xuewei():
    cols, rows = _rows("nishixuewei")
    items = []
    for r in rows:
        name = clean_text(r.get("MZ") or "")
        if not name:
            continue
        items.append({"name": name, "fields": _fields(r, cols, "nishixuewei")})
    return items


def _load_zhenjiu():
    cols, rows = _rows("zhenjiuyian")
    items = []
    for r in rows:
        name = clean_text(r.get("MZ") or "")
        if not name:
            continue
        items.append({"name": name, "fields": _fields(r, cols, "zhenjiuyian")})
    return items


def _load_hantang():
    cols, rows = _rows("xuewei4")
    items = []
    for r in rows:
        name = clean_text(r.get("MZ") or "")
        nr = decrypt_memo(r.get("NR"))
        if not name:
            continue
        m = __import__("re").search(r"(\d+)", name)
        num = int(m.group(1)) if m else 99999
        items.append({"name": name, "num": num, "fields": {"讲解": nr}})
    items.sort(key=lambda x: x["num"])
    return items


def _load_tu_names():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT MZ FROM [nishitu]")
    names = [clean_text(r[0] or "") for r in cur.fetchall() if r[0]]
    conn.close()
    return names


def _load_points():
    cols, rows = _rows("SELFDATA")
    pts = []
    for r in rows:
        try:
            pts.append({
                "id": clean_text(r.get("ID") or ""),
                "left": int(r.get("left") or 0),
                "top": int(r.get("top") or 0),
                "h": int(r.get("H1") or 0),
                "v": int(r.get("V1") or 0),
                "y": int(r.get("Y") or 0),
            })
        except Exception:
            continue
    return pts


def _load_plain(table, name_col="MZ", extra=None):
    cols, rows = _rows(table)
    items = []
    for r in rows:
        name = clean_text(r.get(name_col) or "")
        if not name:
            continue
        fields = {}
        for c in cols:
            if c == name_col or c == "No1":
                continue
            v = r.get(c)
            if v is None:
                continue
            fields[_col_title(table, c)] = clean_text(str(v))
        items.append({"name": name, "fields": fields})
    return items


def _load_ziwwu():
    lg_cols, lg = _rows("linggui")
    najia_cols, najia = _rows("najia")
    nazi_cols, nazi = _rows("nazi")
    return {
        "lingui": {"cols": [_col_title("linggui", c) for c in lg_cols],
                   "rows": [list(r.values()) for r in lg]},
        "najia": {"cols": [_col_title("najia", c) for c in najia_cols],
                   "rows": [list(r.values()) for r in najia]},
        "nazi": {"cols": [_col_title("nazi", c) for c in nazi_cols],
                  "rows": [list(r.values()) for r in nazi]},
    }


# ---- SQLite-mode loader ----------------------------------------------------
def _load_sqlite():
    con = sqlite3.connect(DATA_DB)
    data = {}
    for sub in ("xuewei", "zhenjiu", "hantang", "tu", "points",
                "bbxx", "bzdz", "zfbz", "zjdcjl", "ziwwu"):
        cur = con.execute("SELECT v FROM renji_data WHERE k=?", (sub,))
        row = cur.fetchone()
        data[sub] = json.loads(row[0]) if row else []
    con.close()
    return data


# ---- dispatch --------------------------------------------------------------
if USE_SQLITE:
    print("Loading 人纪 from SQLite (data.db) …")
    _SD = _load_sqlite()
    XUEWEI = _SD["xuewei"]
    ZHENJIU = _SD["zhenjiu"]
    HANTANG = _SD["hantang"]
    TU_NAMES = _SD["tu"]
    POINTS = _SD["points"]
    BBXX = _SD["bbxx"]
    BZDZ = _SD["bzdz"]
    ZFBZ = _SD["zfbz"]
    ZJDCJL = _SD["zjdcjl"]
    ZIWU = _SD["ziwwu"]
else:
    print("Loading 人纪 LILUN.mdb …")
    XUEWEI = _load_xuewei()
    ZHENJIU = _load_zhenjiu()
    HANTANG = _load_hantang()
    TU_NAMES = _load_tu_names()
    POINTS = _load_points()
    BBXX = _load_plain("BBXX")
    BZDZ = _load_plain("BZDZ")
    ZFBZ = _load_plain("ZFBZ")
    ZJDCJL = _load_plain("ZJDCJL")
    ZIWU = _load_ziwwu()

print("人纪 loaded: xuewei=%d zhenjiu=%d hantang=%d tu=%d points=%d bbxx=%d bzdz=%d zfbz=%d zjdcjl=%d"
      % (len(XUEWEI), len(ZHENJIU), len(HANTANG), len(TU_NAMES), len(POINTS),
         len(BBXX), len(BZDZ), len(ZFBZ), len(ZJDCJL)))


# ---- 人纪学习系统五大板块（与「人纪针灸」EXE 菜单一致）---------------------
# 每个板块( board )含若干子模块( sub )；sub 的 kind 决定前端渲染方式：
#   meridians      十四经络穴位（主系统《中医》按经络分组 + 任纪倪师注解）
#   points         人体穴位图（SELFDATA 坐标）
#   fields         倪师注解型数据（name + fields 字典）
#   image          倪师图集（tu，按关键词筛选）
#   ziwwu_table    子午流注/灵龟八法表（najia / nazi / lingui）
#   hantang_method 汉唐方剂按四法归类（经络/脏腑/对症/辨证）
#   cross          跨系统复用主系统接口（herbs / yaotu）
#   tool           交互工具（万年历 / 子午流注盘 / 圆形灵龟八法盘）
#   animation      SVG 经络走向动画
BOARD_STRUCT = [
    {
        "key": "xuewei", "name": "穴位详解",
        "subs": [
            {"key": "meridians", "name": "十四经络穴位", "kind": "meridians",
             "desc": "任督二脉 + 十二正经，共 767 穴（含倪师注解）"},
            {"key": "points", "name": "人体穴位图", "kind": "points", "src": "points",
             "desc": "按原软件坐标的可点击人体穴位图"},
            {"key": "nishi_exp", "name": "倪师傅经验", "subs": [
                {"key": "cifa", "name": "针刺手法", "kind": "image", "src": "tu",
                 "filter": ("补泻", "刺激", "手法", "针刺", "井穴"),
                 "desc": "倪师针刺补泻 / 手法图表"},
                {"key": "zongjie", "name": "针灸穴位总结图表", "kind": "image", "src": "tu",
                 "filter": ("配穴", "八脉", "交会", "生理病理", "脏腑经络"),
                 "desc": "各经络生理病理与治疗配穴总表"},
            ]},
            {"key": "zhenjiu", "name": "针灸医案", "kind": "fields", "src": "zhenjiu",
             "desc": "220 则针灸医案"},
            {"key": "bbxx", "name": "病症方剂", "kind": "fields", "src": "bbxx",
             "desc": "206 条病症对应方剂"},
            {"key": "bzdz", "name": "辨证论治", "kind": "fields", "src": "bzdz",
             "desc": "50 条辨证思路"},
            {"key": "zfbz", "name": "正副辨证", "kind": "fields", "src": "zfbz",
             "desc": "30 条正治与反治"},
            {"key": "zjdcjl", "name": "针灸记录", "kind": "fields", "src": "zjdcjl",
             "desc": "27 条针灸记录"},
        ],
    },
    {
        "key": "linggui", "name": "灵龟八法",
        "subs": [
            {"key": "wanianli", "name": "万年历", "kind": "tool", "tool": "wanianli",
             "desc": "公历 ↔ 农历/干支年 + 二十四节气"},
            {"key": "pan", "name": "倪海厦子午流注盘", "kind": "tool", "tool": "ziwwu_pan",
             "desc": "输入年月日时 → 四柱干支 + 纳子/纳甲/灵龟八法开穴"},
            {"key": "dial", "name": "圆形灵龟八法盘", "kind": "tool", "tool": "lingui_dial",
             "desc": "九宫八穴交互圆盘，标出当前时辰开穴"},
            {"key": "lingui", "name": "灵龟八法表", "kind": "ziwwu_table", "table": "lingui",
             "desc": "灵龟八法 60 穴（日干支 → 开穴）"},
        ],
    },
    {
        "key": "ziwwu", "name": "子午流注",
        "subs": [
            {"key": "najia", "name": "十二经纳甲法", "kind": "ziwwu_table", "table": "najia",
             "desc": "纳甲 12 日干对应开穴"},
            {"key": "nazi", "name": "十二经脉纳子法", "kind": "ziwwu_table", "table": "nazi",
             "desc": "纳子 120 时辰对应开穴"},
        ],
    },
    {
        "key": "hantang", "name": "汉唐取穴",
        "subs": [
            {"key": "jingluo", "name": "经络取穴法", "kind": "hantang_method", "method": "jingluo",
             "desc": "按经络辨证取穴"},
            {"key": "zangfu", "name": "脏腑取穴法", "kind": "hantang_method", "method": "zangfu",
             "desc": "按脏腑辨证取穴"},
            {"key": "duizheng", "name": "对症取穴法", "kind": "hantang_method", "method": "duizheng",
             "desc": "对症治疗取穴"},
            {"key": "bianzheng", "name": "辨证取穴法", "kind": "hantang_method", "method": "bianzheng",
             "desc": "按八纲辨证取穴"},
            {"key": "tu", "name": "倪师取穴图表", "kind": "image", "src": "tu",
             "desc": "63 张倪师取穴 / 经络图表"},
            {"key": "herbs", "name": "中药查询", "kind": "cross", "endpoint": "/api/herbs",
             "desc": "中药查询（神农本草经 + 补全）"},
            {"key": "yaotu", "name": "药图", "kind": "cross", "endpoint": "/api/yaotu",
             "desc": "中药图（形态 + 功效分类）"},
        ],
    },
    {
        "key": "donghua", "name": "动画演示",
        "subs": [
            {"key": "shier", "name": "十二经络穴位走向动画", "kind": "animation", "group": "shier",
             "desc": "十二正经循行走向（SVG 重建）"},
            {"key": "qijing", "name": "奇经八脉穴位走向动画", "kind": "animation", "group": "qijing",
             "desc": "奇经八脉循行走向（SVG 重建）"},
        ],
    },
]


def _count_board(b):
    n = 0
    for s in b.get("subs", []):
        if "subs" in s:
            n += len(s["subs"])
        else:
            n += 1
    return n


BOARDS = []
for _b in BOARD_STRUCT:
    _copy = dict(_b)
    _copy["count"] = _count_board(_b)
    BOARDS.append(_copy)

del _b, _copy
GROUP_NAME = {
    "shier": "十二经络",
    "qijing": "奇经八脉",
}
MERIDIAN_ORDER = ["ren", "du", "fei", "chang", "wei", "pi", "xin", "xiao",
                  "pang", "shen", "bao", "jiao", "dan", "gan"]

_DATA = {
    "xuewei": XUEWEI, "zhenjiu": ZHENJIU, "hantang": HANTANG, "tu": TU_NAMES,
    "points": POINTS, "bbxx": BBXX, "bzdz": BZDZ, "zfbz": ZFBZ, "zjdcjl": ZJDCJL,
    "ziwwu": ZIWU,
}


def modules():
    return BOARDS


# 倪师穴位详解（nishixuewei）按穴名建立索引，供「穴位详解」交叉挂接倪师注解。
_NISHI_BY_NAME = {}
for _it in XUEWEI:
    _NISHI_BY_NAME[_it["name"]] = _it.get("fields", {})


def nishi_fields(name):
    return _NISHI_BY_NAME.get(name, {})


def list_items(sub, q=""):
    if sub == "points":
        return _DATA["points"]
    if sub == "ziwwu":
        return _DATA["ziwwu"]
    raw = _DATA.get(sub, [])
    if raw and isinstance(raw[0], str):
        items = [{"i": idx, "name": nm} for idx, nm in enumerate(raw)]
    else:
        items = [{"i": idx, "name": it["name"]} for idx, it in enumerate(raw)]
    if q:
        ql = q.lower()
        items = [it for it in items if ql in it["name"].lower()
                 or ql in (it.get("fields", {}).get("讲解", "") or "").lower()
                 or any(ql in str(v).lower() for v in it.get("fields", {}).values())]
    return items


def get_item(sub, i):
    items = _DATA.get(sub, [])
    try:
        return items[int(i)]
    except (ValueError, IndexError):
        return None


def image_bytes(name):
    if USE_SQLITE:
        con = sqlite3.connect(DATA_DB)
        cur = con.execute("SELECT data FROM renji_img WHERE name=?", (name,))
        row = cur.fetchone()
        con.close()
        return bytes(row[0]) if row and row[0] is not None else None
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT NR FROM [nishitu] WHERE MZ=?", (name,))
        row = cur.fetchone()
        conn.close()
        return decrypt_bytes(row[0]) if (row and row[0] is not None) else None
    except Exception:
        return None


__all__ = ["modules", "list_items", "get_item", "image_bytes", "nishi_fields",
           "BOARDS", "GROUP_NAME", "MERIDIAN_ORDER"]
