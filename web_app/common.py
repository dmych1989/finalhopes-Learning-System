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
import tempfile
import hashlib

HERE = os.path.dirname(os.path.abspath(__file__))          # web_app dir
DEFAULT_DB = os.path.join(HERE, "data.db")
# 原始 .mdb 仍保留在「原始文件目录」下（保持原始文件目录），仅转换期回退用。
BASE = os.environ.get("LILUN_MDB_BASE", r"E:\Soft\倪海夏三套学习系统\QQ频道号talktyph0id\医学论文医案查询系统")
DB = os.path.join(BASE, "Data", "LILUN.mdb")
KEY = 0x0F
PWD = "JiSkS92A30"

# On platforms where the large SQLite blob is NOT bundled (e.g. Vercel), fetch it
# once into a writable cache at import time. Override via env DATA_DB_URL.
# 远程 data.db 仅允许私有地址（PRIVATE_DB_URL）。默认不再指向任何公开仓库，
# 避免核心数据被公开抓取。未配置时 _download_db 直接跳过（需随包 data.db / .enc）。
REMOTE_DB_URL = os.environ.get("PRIVATE_DB_URL", "")

# Vercel 打包器（@vercel/nft）无法追踪运行时的 DEFAULT_DB + ".enc" 动态拼接，
# 这里以字面量显式引用加密库，确保 *.db.enc 被收入函数包（明文 *.db 不随包）。
_NFT_ENC_REFS = [
    os.path.join(HERE, "data.db.enc"),
    os.path.join(HERE, "images_renji.db.enc"),
    os.path.join(HERE, "images_shoufa.db.enc"),
    os.path.join(HERE, "images_tianji.db.enc"),
    os.path.join(HERE, "images_xuewei.db.enc"),
    os.path.join(HERE, "images_yaotu_list.db.enc"),
    os.path.join(HERE, "images_yaotu.db.enc"),
    os.path.join(HERE, "images_zhongyi.db.enc"),
]


def _decrypt_to(enc_path, dest):
    """若 enc_path 存在且配置了 DB_DECRYPT_KEY，则 AES(Fernet) 解密到 dest（已解密则跳过）。
    返回解密后的路径；无密钥或无加密文件时返回 None。与 encrypt_dbs.py 配套。"""
    import base64
    from cryptography.fernet import Fernet
    key = os.environ.get("DB_DECRYPT_KEY", "")
    if not key or not os.path.isfile(enc_path):
        return None
    if os.path.exists(dest) and os.path.getsize(dest) > 1_000_000:
        return dest
    k = base64.urlsafe_b64encode(hashlib.sha256(key.encode("utf-8")).digest())
    with open(enc_path, "rb") as f:
        blob = f.read()
    try:
        plain = Fernet(k).decrypt(blob)
    except Exception as e:
        # 密钥不匹配/文件损坏：回退明文或无数据分支，不让端点 500
        print("WARN: 解密失败(密钥不匹配?):", enc_path, repr(e))
        return None
    with open(dest, "wb") as f:
        f.write(plain)
    print("Decrypted %s -> %s (%d KB)" % (enc_path, dest, len(plain) // 1024))
    return dest


def _resolve_db_path():
    """Return a usable SQLite path if a local copy exists; else None (no network).

    优先使用加密副本 data.db.enc（需 DB_DECRYPT_KEY）：Vercel 部署仅随包 *.db.enc，
    运行时解密到 /tmp，明文从不落部署包。本地开发 / 已随包明文 data.db 的实例走
    DEFAULT_DB 分支（瞬时返回，仅拷贝到 /tmp 以绕过只读 FS）。
    真正的下载在 _ensure_db() 中按需、懒触发，且只走私有地址（PRIVATE_DB_URL）。
    """
    cache = os.path.join(tempfile.gettempdir(), "finalhopes_data.db")
    dec = _decrypt_to(DEFAULT_DB + ".enc", cache)
    if dec:
        return dec
    if os.path.exists(DEFAULT_DB):
        # Vercel's function FS (/var/task) is read-only; copy to writable /tmp
        # so sqlite3 can open read-write. Local dev keeps using web_app/data.db.
        try:
            import shutil
            shutil.copyfile(DEFAULT_DB, cache)
            return cache
        except Exception as e:  # pragma: no cover - /tmp should be writable
            print("WARN: copy data.db -> /tmp failed:", repr(e))
            return DEFAULT_DB
    if os.path.exists(cache) and os.path.getsize(cache) > 1_000_000:
        return cache
    return None


def _download_db(dest, timeout=55):
    """仅从私有地址（PRIVATE_DB_URL / PUBLIC_DB_URL 环境变量）下载 data.db；
    不再使用任何公开 GitHub / jsDelivr 地址，避免核心数据被公开抓取。
    未配置私有地址时直接返回 False（请随部署打包 data.db 或 data.db.enc）。
    """
    import urllib.request as _urllib
    urls = []
    priv = os.environ.get("PRIVATE_DB_URL") or os.environ.get("PUBLIC_DB_URL")
    if priv:
        urls.append(priv)
    if not urls:
        print("WARN: 未配置 PRIVATE_DB_URL，跳过 data.db 远程下载（请随部署打包 data.db / data.db.enc）")
        return False
    last = None
    for url in urls:
        try:
            _urllib.urlretrieve(url, dest, timeout=timeout)
            if os.path.getsize(dest) > 1_000_000:
                return True
            last = "too small (%d)" % os.path.getsize(dest)
        except Exception as e:
            last = repr(e)
    print("WARN: data.db 下载失败：", last)
    return False


def _ensure_db():
    """Lazily resolve a SQLite path (local /tmp cache / download). Sets USE_SQLITE."""
    global DATA_DB, USE_SQLITE
    if USE_SQLITE and DATA_DB and os.path.exists(DATA_DB):
        return True
    # 本地 /tmp 缓存（同实例复用，避免重复下载）
    cache = os.path.join(tempfile.gettempdir(), "finalhopes_data.db")
    if os.path.exists(cache) and os.path.getsize(cache) > 1_000_000:
        DATA_DB, USE_SQLITE = cache, True
        return True
    if _download_db(cache):
        DATA_DB, USE_SQLITE = cache, True
        return True
    return False


DATA_DB = _resolve_db_path()
USE_SQLITE = DATA_DB is not None


def _sqlite_json(table, key):
    if not _ensure_db():
        return None
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
    if _ensure_db():
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
    if _ensure_db():
        d = _sqlite_json("main_table", table)
        return d if d is not None else {}
    return {r.get(key_col, ""): r for r in load_table(table)}


def get_yaotu_images():
    """Return {name: jpeg_bytes} for the 药图 (yaotu) herb images."""
    if _ensure_db():
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

