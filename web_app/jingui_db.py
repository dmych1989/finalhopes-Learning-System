# -*- coding: utf-8 -*-
"""金匮要略（倪海厦人纪）data layer.

数据来源：`_提取文章/金匮要略/金匮要略方剂数据.json` → 部署副本 `web_app/jingui.json`。
覆盖 226 首经方 × 21 篇，每方含七个维度：
  脉证治方（原文条文）/ 方组与用量 / 煎服法 / 主治 / 方歌 / 方解 / 倪海厦讲解 / 现代医案。

本模块为纯数据层（仅标准库），加载期构建索引，运行期 O(1)/O(n) 查询。
"""
import os
import re
import json

HERE = os.path.dirname(os.path.abspath(__file__))
_JSON = os.path.join(HERE, "jingui.json")


def _s(v):
    if v is None:
        return ""
    return v.strip() if isinstance(v, str) else str(v).strip()


def _clean(t):
    """正文轻量清洗：修正源数据中的 OCR 残片与断字。"""
    t = _s(t)
    if not t:
        return ""
    for a, b in (
        ("KT KT", "几几"), ("KTKT", "几几"),
        ("黄 芍药", "黄芪芍药"), ("黄 汤", "黄芪汤"),
    ):
        t = t.replace(a, b)
    return t


def _clean_name(n):
    """方名清洗：去 EXE 字符串拼接残留（「主方 ：附加方」）、修复 OCR 断字、去重复。"""
    n = _s(n)
    if not n:
        return ""
    # EXE 内嵌字符串常把「方名 ＋ 后续方名」用全角冒号拼接，取第一个方名
    if "：" in n:
        n = n.split("：")[0]
    n = n.strip()
    # 形如「小儿疳虫蚀齿方 小儿疳虫蚀齿方」的重复
    parts = n.split()
    if len(parts) == 2 and parts[0] == parts[1]:
        n = parts[0]
    # OCR 断字：「黄 汤」「防己黄 汤」实为「黄芪…」
    n = n.replace("黄 ", "黄芪")
    n = re.sub(r"\s+", "", n)
    return n


# ---- 加载 -----------------------------------------------------------------
try:
    with open(_JSON, encoding="utf-8") as _f:
        _RAW = json.load(_f)
except Exception as _e:  # 数据缺失时优雅降级，不阻断整个站点
    print("WARN: 金匮要略数据加载失败：", repr(_e))
    _RAW = []


_SEQ = []          # 全量（按篇号、篇内序）
_BY_NO = {}        # 全局序号（唯一）→ item
_BY_NAME = {}      # 方名（含别名）→ item（同名取首见）
_BY_CHAPTER = {}   # 篇号 → [item]


def _norm(rec):
    gj = rec.get("gejue") or {}
    return {
        "name": _clean_name(rec.get("name")),
        "chapter_no": int(rec.get("chapter_no") or 0),
        "chapter": _s(rec.get("chapter")),
        "pian": _s(rec.get("yuanwen_pian")),
        "tiaowen": _clean(rec.get("tiaowen")),
        "zucheng": _clean(rec.get("zucheng")),
        "jianfu": _clean(rec.get("jianfu")),
        "zhuzhi": _clean(gj.get("zhuzhi")),
        "gejue": _clean(gj.get("gejue")),
        "fangjie": _clean(gj.get("fangjie")),
        "jiangjie": [_clean(x) for x in (rec.get("nhx_obsidian") or []) if _s(x)],
        "yian": [
            {
                "title": _s(y.get("title")),
                "date": _s(y.get("date")),
                "disease": _s(y.get("disease")),
                "liujing": _s(y.get("liujing")),
                "content": _s(y.get("content")),
            }
            for y in (rec.get("yian") or []) if isinstance(y, dict)
        ],
        "aliases": [_clean_name(a) for a in (rec.get("aliases") or []) if _s(a)],
    }


for _r in _RAW:
    if not isinstance(_r, dict):
        continue
    _it = _norm(_r)
    if not _it["name"]:
        continue
    _it["no"] = len(_SEQ) + 1
    _SEQ.append(_it)
    _BY_NO[_it["no"]] = _it
    _BY_NAME.setdefault(_it["name"], _it)
    for _a in _it["aliases"]:
        _BY_NAME.setdefault(_a, _it)
    _BY_CHAPTER.setdefault(_it["chapter_no"], []).append(_it)

_JUNK_SUFFIX = re.compile(r"(病脉证并治|病脉证治|脉证并治|脉证治)方?$")


def _short_chapter(name):
    """篇名简称：去掉「…脉证治（方）/ 脉证并治（方）」后缀，便于窄侧栏展示。"""
    n = _JUNK_SUFFIX.sub("", name or "").strip()
    return n or (name or "")


_CHAPTERS = [
    {"no": _no,
     "name": _BY_CHAPTER[_no][0]["chapter"],
     "short": _short_chapter(_BY_CHAPTER[_no][0]["chapter"]),
     "count": len(_BY_CHAPTER[_no])}
    for _no in sorted(_BY_CHAPTER.keys())
]

print("金匮要略 loaded: chapters=%d formulas=%d" % (len(_CHAPTERS), len(_SEQ)))


# ---- 查询接口 -------------------------------------------------------------
def chapters():
    return _CHAPTERS


def chapter(no):
    try:
        no = int(no)
    except (TypeError, ValueError):
        return None
    items = _BY_CHAPTER.get(no)
    if items is None:
        return None
    return {
        "no": no,
        "name": items[0]["chapter"],
        "count": len(items),
        "items": [{"name": x["name"], "no": x["no"]} for x in items],
    }


def item(name, chapter_no=None):
    it = _BY_NAME.get(_s(name))
    if it is None:
        return None
    if chapter_no is not None:
        try:
            cn = int(chapter_no)
        except (TypeError, ValueError):
            return it
        for x in _BY_CHAPTER.get(cn, []):
            if x["name"] == it["name"]:
                return x
    return it


def item_by_no(no):
    try:
        return _BY_NO.get(int(no))
    except (TypeError, ValueError):
        return None


def list_all():
    return [
        {"name": x["name"], "no": x["no"], "chapter_no": x["chapter_no"],
         "chapter": x["chapter"]}
        for x in _SEQ
    ]


def search(q, limit=150):
    q = _s(q).lower()
    if not q:
        return []
    out = []
    for x in _SEQ:
        blob = " ".join([
            x["name"], x["chapter"], " ".join(x["aliases"]),
            x["tiaowen"], x["zucheng"], x["zhuzhi"], x["fangjie"],
            " ".join(x["jiangjie"]), x["pian"],
        ]).lower()
        if q in blob:
            out.append({"name": x["name"], "no": x["no"],
                        "chapter": x["chapter"], "chapter_no": x["chapter_no"]})
            if len(out) >= limit:
                break
    return out


def stats():
    return {
        "chapters": len(_CHAPTERS),
        "formulas": len(_SEQ),
        "with_tiaowen": sum(1 for x in _SEQ if x["tiaowen"]),
        "with_zucheng": sum(1 for x in _SEQ if x["zucheng"]),
        "with_jiangjie": sum(1 for x in _SEQ if x["jiangjie"]),
        "with_yian": sum(1 for x in _SEQ if x["yian"]),
    }


__all__ = ["chapters", "chapter", "item", "item_by_no", "list_all", "search", "stats"]
