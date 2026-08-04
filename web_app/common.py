# -*- coding: utf-8 -*-
"""Data layer.

Two backends, auto-selected:
  * SQLite  (data.db)  — preferred. Pure stdlib (sqlite3), NO pyodbc / ODBC driver.
                        Works on Vercel (Linux serverless) and locally.
  * Access .mdb        — fallback, only used when data.db is absent (conversion time).
                        Requires a local 64-bit Access ODBC driver + pyodbc.

The decrypted content is identical between backends; the converter
(tools/mdb_to_sqlite.py) materializes the .mdb into data.db once.
"""
import os
import re
import json
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))          # web_app dir
DEFAULT_DB = os.path.join(HERE, "data.db")
# 原始 .mdb 仍保留在「原始文件目录」下（保持原始文件目录），仅转换期回退用。
BASE = r"E:\Soft\倪海夏三套学习系统\QQ频道号talktyph0id\医学论文医案查询系统"
DB = os.path.join(BASE, "Data", "LILUN.mdb")
KEY = 0x0F
PWD = "JiSkS92A30"

# On platforms where the large SQLite blob is NOT bundled (e.g. Vercel), fetch it
# once into a writable cache at import time. Override via env DATA_DB_URL.
REMOTE_DB_URL = os.environ.get(
    "DATA_DB_URL",
    "https://raw.githubusercontent.com/dmych1989/finalhopes-Learning-System/main/web_app/data.db",
)


def _resolve_db_path():
    """Return a usable SQLite path: local file if present, else a downloaded cache."""
    if os.path.exists(DEFAULT_DB):
        return DEFAULT_DB
    cache = os.path.join("/tmp", "finalhopes_data.db")
    if os.path.exists(cache):
        return cache
    try:
        import urllib.request as _urllib
        _urllib.urlretrieve(REMOTE_DB_URL, cache)
        return cache
    except Exception:
        return None


DATA_DB = _resolve_db_path()
USE_SQLITE = DATA_DB is not None


def _sqlite_json(table, key):
    con = sqlite3.connect(DATA_DB)
    cur = con.execute("SELECT v FROM %s WHERE k=?" % table, (key,))
    row = cur.fetchone()
    con.close()
    return json.loads(row[0]) if row else None


# Columns stored as text but XOR-0x0F ciphered (RTF). Bytes columns are always decrypted.
CIPHER_TEXT_COLS = {
    "ZYX": ["【出自】", "【简述】", "【性能】", "【功效】", "【用法用量】",
            "【使用注意】", "【古籍摘要】", "【现代研究】"],
}


# ---- pyodbc is imported lazily so the SQLite/Vercel path never needs it ----
def connect():
    import pyodbc
    return pyodbc.connect(
        "Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=%s;PWD=%s;" % (DB, PWD)
    )


def decrypt_bytes(b):
    return bytes(c ^ KEY for c in b)


# Attribution / source-branding strings to strip from ALL displayed content.
_GUJIZHAI_PHRASES = [
    "古籍斋倪海厦医案数据库",
    "古籍斋倪海厦内部资料教学下载QQ群：27742146",
    "古籍斋经方学习组整理录入",
    "古籍斋", "经方学习组", "经方学习",
]


def clean_text(s):
    """Strip legacy source-branding (古籍斋 / 经方学习组 / gujizhai) from text."""
    if not s:
        return s
    for p in _GUJIZHAI_PHRASES:
        s = s.replace(p, "")
    s = re.sub(r"https?://[^\s]*gujizhai[^\s]*", "", s, flags=re.I)
    s = re.sub(r"www\.gujizhai[^\s]*", "", s, flags=re.I)
    s = re.sub(r"gujizhai\.com[^\s]*", "", s, flags=re.I)
    # 移除 Word/RTF 转换残留的版式标记（非医学内容）
    s = re.sub(r"Normalheading\s*\d*\s*heading\s*\d+", "", s)
    s = re.sub(r"heading\s+\d+", "", s)
    # 移除商业水印（微信公众号 / 400 电话）——非倪师内容
    s = re.sub(r"^\s*微信公众号[:：].*$", "", s, flags=re.M)
    s = re.sub(r"^\s*官方\s*400\s*电话[:：]?\s*400-188-2625.*$", "", s, flags=re.M)
    s = re.sub(r"\n{2,}", "\n", s)
    s = re.sub(r"[ \t]+\n", "\n", s)
    s = re.sub(r"^\s+|\s+$", "", s)
    return s


def rtf_to_text(b):
    """Walk an RTF byte stream; collect \\'hh hex bytes, skip control words / font+color
    tables / * destinations, decode the rest as GBK (cp936)."""
    out = bytearray()
    stack = [(0, False)]  # (depth, skip)
    i, n = 0, len(b)
    while i < n:
        c = b[i]
        if c == 0x5C:  # backslash
            if i + 1 < n and b[i + 1] == 0x27:  # \'
                if (not stack[-1][1]) and i + 3 < n:
                    try:
                        out.append(int(b[i + 2:i + 4], 16))
                    except ValueError:
                        pass
                i += 4
                continue
            j = i + 1
            word = ""
            while j < n and (65 <= b[j] <= 90 or 97 <= b[j] <= 122):
                word += chr(b[j])
                j += 1
            k = j
            while k < n and (48 <= b[k] <= 57 or b[k] == 0x2D):
                k += 1
            if not stack[-1][1]:
                if word == "par":
                    out.append(0x0A)
                elif word in ("fonttbl", "colortbl") or word == "*" or word.startswith("*"):
                    stack[-1] = (stack[-1][0], True)
            i = k
            if i < n and b[i] == 0x20:
                i += 1
            continue
        elif c == 0x7B:  # {
            stack.append((stack[-1][0] + 1, stack[-1][1]))
            i += 1
            continue
        elif c == 0x7D:  # }
            if len(stack) > 1:
                stack.pop()
            i += 1
            continue
        elif c == 0x3B:  # ;
            i += 1
            continue
        else:
            if not stack[-1][1]:
                out.append(c)
            i += 1
    text = out.decode("cp936", "ignore")
    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    text = re.sub(r"^\s+|\s+$", "", text)
    return clean_text(text)


def text_of(col, val, table=None):
    if val is None:
        return ""
    if isinstance(val, bytes):
        return clean_text(rtf_to_text(decrypt_bytes(val)))
    if table in CIPHER_TEXT_COLS and col in CIPHER_TEXT_COLS[table]:
        return clean_text(rtf_to_text(decrypt_bytes(val.encode("cp936", "ignore"))))
    return clean_text(val) if isinstance(val, str) else val


def _clean_row(v):
    """Recursively apply display-layer cleaning to string values (idempotent)."""
    if isinstance(v, dict):
        return {k: _clean_row(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_clean_row(x) for x in v]
    if isinstance(v, str):
        return clean_text(v)
    return v


def load_table(table, cipher_table=None):
    if USE_SQLITE:
        rows = _sqlite_json("main_table", table)
        # SQLite 模式在转换期已做过一次 clean_text；此处再跑一遍以应用
        # 后续新增的版式/水印清理规则（Normalheading、微信公众号等），幂等。
        return [_clean_row(r) for r in rows] if rows is not None else []
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM [%s]" % table)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    tbl = cipher_table or table
    data = []
    for r in rows:
        data.append({cols[i]: text_of(cols[i], r[i], tbl) for i in range(len(cols))})
    conn.close()
    return data


def decrypt_image(val):
    if isinstance(val, bytes):
        return decrypt_bytes(val)
    return b""


def load_dict(table, key_col="MZ"):
    if USE_SQLITE:
        d = _sqlite_json("main_table", table)
        return d if d is not None else {}
    return {r.get(key_col, ""): r for r in load_table(table)}


def get_yaotu_images():
    """Return {name: jpeg_bytes} for the 药图 (yaotu) herb images."""
    if USE_SQLITE:
        con = sqlite3.connect(DATA_DB)
        cur = con.execute("SELECT name, data FROM yaotu_img")
        d = {r[0]: r[1] for r in cur.fetchall()}
        con.close()
        return d
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT MZ, NR FROM [yaotu]")
    d = {}
    for mz, nr in cur.fetchall():
        if isinstance(nr, bytes) and len(nr) > 200:
            d[mz] = decrypt_bytes(nr)
    conn.close()
    return d

