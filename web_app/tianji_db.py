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
import json
import sqlite3

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


# ---- dispatch --------------------------------------------------------------
if USE_SQLITE:
    print("Loading 天纪 from SQLite (data.db) …")
    _SD = _load_sqlite()
    GUA = _SD["gua"]; RENDAO = _SD["rendao"]; LILUN = _SD["lilun"]
    RIYUE = _SD["riyue"]; JINGDU = _SD["jingdu"]; MINGLI = _SD["mingli"]
    ZIWEI = _SD["ziwei"]; YIJING = _SD["yijing"]
else:
    print("Loading 天纪 databases …")
    GUA = _load_gua()
    RENDAO = _load_rendao()
    LILUN = _load_lilun()
    RIYUE = _load_riyue()
    JINGDU = _load_jingdu()
    MINGLI = _load_mingli()
    ZIWEI = _load_table_set(["ziweibiao", "ziweizhuxing01"])
    YIJING = _load_table_set(["anshixi", "dingtianfu", "tianshi", "yt", "加密换算表"])

print("天纪 loaded: gua=%d rendao=%d lilun=%d riyue=%d jingdu=%d mingli=%d "
      "ziwei=%d yijing=%d" % (len(GUA), len(RENDAO), len(LILUN), len(RIYUE),
                              len(JINGDU), len(MINGLI),
                              len(ZIWEI["ziweibiao"]["rows"]) + len(ZIWEI["ziweizhuxing01"]["rows"]),
                              sum(len(v["rows"]) for v in YIJING.values())))


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
    {"key": "paipan", "name": "排盘系统", "kind": "tool", "count": 0,
     "desc": "输入阳历生日 / 时辰 / 性别，排出八字四柱 · 紫微斗数命盘 · 本命卦（复刻原版排盘界面）",
     "hasImg": False},
    {"key": "mingli_sys", "name": "命理系统", "kind": "tool", "count": 0,
     "desc": "基于排盘结果，解读日主强弱 · 十神六亲 · 大运走势，并关联天纪原有八字命例与理论",
     "hasImg": False},
]

_DATA = {
    "gua": GUA, "rendao": RENDAO, "lilun": LILUN, "riyue": RIYUE, "jingdu": JINGDU,
    "mingli": MINGLI, "ziwei": ZIWEI, "yijing": YIJING,
}

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
    items = [{"i": idx, "name": it["name"]} for idx, it in enumerate(raw)]
    if q:
        ql = q.lower()
        items = [it for it in items if ql in it["name"].lower()]
    return items


def get_item(sub, i):
    raw = _DATA.get(sub, [])
    if isinstance(raw, dict) or not raw:
        return None
    try:
        rec = raw[int(i)]
    except (ValueError, IndexError):
        return None
    if USE_SQLITE:
        # 转换器已把 riyue/mingli 等密文解码为最终结构，直接返回即可
        return rec
    # ---- mdb 模式：按需解码 ----
    if sub in ("gua", "rendao"):
        fields = {"图象 / 卦辞": clean_text(rec.get("nr") or "")}
        return {"name": rec["name"], "dd": rec.get("dd") or "", "fields": fields}
    if sub == "lilun":
        return {"name": rec["name"], "fields": {"正文": clean_text(rec.get("nr") or "")}}
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
            "联系方式": clean_text(str(r.get("LXFS") or "")),
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
