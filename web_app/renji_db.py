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


MODULES = [
    {"key": "xuewei",  "name": "倪师穴位详解", "kind": "fields", "count": len(XUEWEI),
     "desc": "357 个穴位：别名/定位/解剖/主治/穴义/刺灸/配伍/特征/规律/名词解析/倪师注解/治法"},
    {"key": "zhenjiu", "name": "针灸医案",     "kind": "fields", "count": len(ZHENJIU),
     "desc": "220 则针灸医案：歌诀/穴位介绍/病因病理分析/医疗案例"},
    {"key": "hantang", "name": "汉唐方剂",     "kind": "fields", "count": len(HANTANG),
     "desc": "252 首汉唐方剂（倪师讲解）"},
    {"key": "tu",      "name": "倪师图",       "kind": "image",  "count": len(TU_NAMES),
     "desc": "63 张倪师表格 / 经络图（八脉交会穴表、各脏腑经络生理病理与治疗配穴列表…）"},
    {"key": "points",  "name": "人体穴位图",   "kind": "points", "count": len(POINTS),
     "desc": "按原软件 SELFDATA 坐标的可点击人体穴位图"},
    {"key": "bbxx",    "name": "病症方剂",     "kind": "fields", "count": len(BBXX),
     "desc": "206 条病症对应方剂"},
    {"key": "bzdz",    "name": "辨证论治",     "kind": "fields", "count": len(BZDZ),
     "desc": "50 条辨证思路"},
    {"key": "zfbz",    "name": "正副辨证",     "kind": "fields", "count": len(ZFBZ),
     "desc": "30 条正治与反治"},
    {"key": "zjdcjl",  "name": "针灸记录",     "kind": "fields", "count": len(ZJDCJL),
     "desc": "27 条针灸记录"},
    {"key": "ziwwu",   "name": "子午流注·灵龟八法", "kind": "tables", "count":
     len(ZIWU["lingui"]["rows"]) + len(ZIWU["najia"]["rows"]) + len(ZIWU["nazi"]["rows"]),
     "desc": "灵龟八法 60 / 纳甲 12 / 纳子 120"},
]

_DATA = {
    "xuewei": XUEWEI, "zhenjiu": ZHENJIU, "hantang": HANTANG, "tu": TU_NAMES,
    "points": POINTS, "bbxx": BBXX, "bzdz": BZDZ, "zfbz": ZFBZ, "zjdcjl": ZJDCJL,
    "ziwwu": ZIWU,
}


def modules():
    return MODULES


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


__all__ = ["modules", "list_items", "get_item", "image_bytes", "MODULES"]
