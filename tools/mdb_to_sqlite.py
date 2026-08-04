# -*- coding: utf-8 -*-
"""一次性转换工具：把 3 套 Access .mdb 解密后序列化为 SQLite (web_app/data.db)。

运行环境需要本机有 64 位 Access ODBC 驱动（转换期用）；生成 data.db 后，运行时
(reader: common/renji_db/tianji_db + server) 改为读 SQLite，不再依赖 pyodbc/ODBC。

用法：在 web_app 目录的「父目录」下用本机 python 运行：
    python tools/mdb_to_sqlite.py
"""
import os
import sys
import json
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(os.path.dirname(HERE), "web_app")   # finalhopes-Learning-System/web_app
DATA_DB = os.path.join(WEB, "data.db")

# 必须在 import 数据层之前删除旧 data.db：否则 common/renji/tianji 在导入时会
# 检测到 data.db 而走 SQLite 模式（且加载的是旧数据），转换器就无法从 .mdb 重新生成。
if os.path.exists(DATA_DB):
    os.remove(DATA_DB)
    print("已删除旧的 data.db（将以 mdb 模式重新生成）")

# 让转换器能 import 现有数据层（它们会以 mdb 模式加载，因为 data.db 此刻不存在）
sys.path.insert(0, WEB)
import common
import renji_db
import tianji_db
from tianji_db import _dec_bytes, _dec_rtf_str, clean_text

# ---- 主库需转换的表（load_table 已返回解密后的 list[dict]） ----
MAIN_TABLES = ["1234567", "BBXX", "BZDZ", "ZFBZ", "ZJDCJL",
               "hantang", "linggui", "najia", "nazi", "nhxlwj"]
MAIN_DICT_TABLES = ["ZYX"]


def build():
    if os.path.exists(DATA_DB):
        os.remove(DATA_DB)
        print("已删除旧的 data.db")
    con = sqlite3.connect(DATA_DB)
    con.execute("PRAGMA journal_mode=WAL")

    def put_blob(table, name, data, ctype="image/jpeg"):
        con.execute("CREATE TABLE IF NOT EXISTS %s "
                    "(name TEXT PRIMARY KEY, data BLOB, ctype TEXT)" % table)
        con.execute("INSERT OR REPLACE INTO %s VALUES (?,?,?)" % table,
                    (name, sqlite3.Binary(data), ctype))

    def put_json(table, key, payload):
        con.execute("CREATE TABLE IF NOT EXISTS %s "
                    "(k TEXT PRIMARY KEY, v TEXT)" % table)
        con.execute("INSERT OR REPLACE INTO %s VALUES (?,?)" % table,
                    (key, json.dumps(payload, ensure_ascii=False)))

    # ---------- 1) 主库表 ----------
    for t in MAIN_TABLES:
        rows = common.load_table(t)
        put_json("main_table", t, rows)
        print("main %-10s -> %d 行" % (t, len(rows)))
    for t in MAIN_DICT_TABLES:
        d = common.load_dict(t)
        put_json("main_table", t, d)
        print("main %-10s -> %d 条(dict)" % (t, len(d)))

    # ---------- 2) 主库 yaotu 图片 ----------
    conn = common.connect()
    cur = conn.cursor()
    cur.execute("SELECT MZ, NR FROM [yaotu]")
    n = 0
    for mz, nr in cur.fetchall():
        if isinstance(nr, bytes) and len(nr) > 200:
            put_blob("yaotu_img", mz, common.decrypt_bytes(nr))
            n += 1
    conn.close()
    print("yaotu 图片 -> %d 张" % n)

    # ---------- 3) 人纪 ----------
    for sub, items in renji_db._DATA.items():
        put_json("renji_data", sub, items)
        print("renji %-8s -> %d" % (sub, len(items) if hasattr(items, "__len__") else 0))
    # 人纪图（nishitu）
    for name in renji_db.TU_NAMES:
        b = renji_db.image_bytes(name)
        if b:
            put_blob("renji_img", name, b)
    print("renji 图 -> %d 张" % len(renji_db.TU_NAMES))

    # ---------- 4) 天纪 ----------
    tj = {}
    for sub in ("gua", "rendao", "lilun"):
        out = []
        for rec in tianji_db._DATA[sub]:
            nr = rec.get("nr") or ""
            title = "图象 / 卦辞" if sub != "lilun" else "正文"
            out.append({"name": rec.get("name", ""), "dd": rec.get("dd") or "",
                        "fields": {title: clean_text(nr)}})
        tj[sub] = out
    # riyue：字节密文，需解码
    out = []
    for rec in tianji_db._DATA["riyue"]:
        out.append({"name": rec.get("name", ""),
                    "fields": {"解说": _dec_bytes(rec.get("nr"))}})
    tj["riyue"] = out
    # jingdu：已解码
    tj["jingdu"] = tianji_db._DATA["jingdu"]
    # mingli：YCNR 为文本 RTF，需解码
    out = []
    for rec in tianji_db._DATA["mingli"]:
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
        out.append({"name": rec.get("name", ""), "fields": fields})
    tj["mingli"] = out
    # 表格型子模块：存 tables(sub) 输出
    for sub in ("ziwei", "yijing"):
        tj[sub] = tianji_db.tables(sub)
    for sub, payload in tj.items():
        put_json("tianji_data", sub, payload)
        cnt = len(payload) if hasattr(payload, "__len__") else 0
        print("tianji %-8s -> %s" % (sub, cnt))

    # 天纪卦图
    guatu_dir = tianji_db.GUATU_DIR
    gn = 0
    if os.path.isdir(guatu_dir):
        for fn in os.listdir(guatu_dir):
            if fn.lower().endswith((".jpg", ".png")):
                with open(os.path.join(guatu_dir, fn), "rb") as f:
                    data = f.read()
                ctype = "image/png" if fn.lower().endswith(".png") else "image/jpeg"
                put_blob("tianji_img", os.path.splitext(fn)[0], data, ctype)
                gn += 1
    print("tianji 卦图 -> %d 张" % gn)

    con.commit()
    con.close()
    size = os.path.getsize(DATA_DB) / 1024 / 1024
    print("\n完成：%s (%.1f MB)" % (DATA_DB, size))


if __name__ == "__main__":
    build()
