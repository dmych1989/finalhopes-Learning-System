# -*- coding: utf-8 -*-
"""64-bit local web server for the 倪海厦 medical reference system.
Reads Data/LILUN.mdb live (via 64-bit Access ODBC) and decrypts on the fly."""
import os
import re
import json
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import HTMLResponse, JSONResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
import common

# 人纪学习系统：独立的第二数据库（人纪针灸学习系统 LILUN.mdb），同密码同加密。
import renji_db
# 天纪学习系统：三个独立数据库（LILUN/CollData/MasterData，密码各不相同），易经/紫微/天文/命理。
import tianji_db
# 天纪排盘 / 命理系统：八字 + 紫微斗数 + 本命卦 引擎（纯 Python）。
import paipan

app = FastAPI(title="倪海厦医学查询系统 (网页版)")

print("Loading data from LILUN.mdb ...")
CASES = common.load_table("1234567")
# The original case MZ field is just "N.古籍斋倪海厦医案数据库" (a distributor
# watermark), so give each case a meaningful title derived from its content.
def case_title(rec):
    for c in ["【来诊原因】", "【诊断】", "【问诊】"]:
        v = (rec.get(c) or "").strip()
        if v:
            return v[:24]
    if rec.get("【姓名】"):
        return rec["【姓名】"][:24]
    return "医案记录"
for _c in CASES:
    _c["_title"] = case_title(_c)

# ---- 医案「按证型浏览」分类体系（倪海厦以伤寒六经 + 脏腑辨证立论） ----
# 每条: (key, 显示名, [关键词]) ；关键词命中 诊断/来诊原因/解说/中药处方 即归入。
# 多归属允许（一个医案可同时出现在多个证型下）；"other" 为未匹配任何关键词者。
CASE_CATS = [
    ("all", "全部医案", None),
    # —— 伤寒六经 ——
    ("taiyang", "太阳病（经）", ["太阳"]),
    ("yangming", "阳明病（经）", ["阳明"]),
    ("shaoyang", "少阳病（经）", ["少阳"]),
    ("taiyin", "太阴病（经）", ["太阴"]),
    ("shaoyin", "少阴病（经）", ["少阴"]),
    ("jueyin", "厥阴病（经）", ["厥阴"]),
    # —— 脏腑病机 ——
    ("shen", "肾（阳/阴·肾虚）", ["肾阳", "肾阴", "肾虚", "右肾", "左肾", "肾着", "肾气"]),
    ("xin", "心（阳·血·包）", ["心阳", "心血", "心气", "心包", "心积"]),
    ("gan", "肝（积·家·郁）", ["肝积", "肝家", "肝郁", "肝阴", "肝阳", "肝受损", "肝寒"]),
    ("pi", "脾（阳·虚·湿）", ["脾阳", "脾虚", "脾湿", "脾"]),
    ("fei", "肺（阴实·寒·湿）", ["肺阴", "肺寒", "肺中", "肺湿", "肺"]),
    ("wei", "胃（家·寒·热）", ["胃家", "胃寒", "胃热", "胃病", "胃"]),
    ("dan", "胆（泥·阻·石）", ["胆泥", "胆阻", "胆结石", "胆"]),
    ("sanji", "三焦", ["三焦"]),
    # —— 常见证型/病种 ——
    ("shangre", "上热下寒", ["上热下寒"]),
    ("lihan", "里寒·寒湿", ["里寒", "寒湿", "阴寒", "寒症", "寒证"]),
    ("shire", "湿热", ["湿热", "溼热", "湿重"]),
    ("fengshi", "风湿·关节炎", ["风湿", "关节炎", "类风湿"]),
    ("xure", "虚热·血虚·阴虚", ["虚热", "血虚", "阴虚"]),
    ("xueyu", "瘀血·活血", ["瘀血", "活血", "血淤", "血瘀"]),
    ("zhongfeng", "中风", ["中风"]),
    ("aizheng", "肿瘤·癌症·阴实", ["癌", "肿瘤", "癥", "阴实", "积毒", "肝积毒素"]),
    ("fuke", "妇科·经期", ["经期", "月经", "妇科", "带下", "崩漏", "孕"]),
    ("xiaoer", "儿科", ["小儿", "儿科", "婴幼儿"]),
    ("shimian", "失眠", ["失眠", "不眠", "不得眠"]),
    ("tengtong", "头痛·痛证", ["头痛", "偏头痛", "风痛"]),
    ("liaocheng", "复诊·疗程中", ["进步中", "疗程中", "效不更方", "同前", "阴阳仍在相抗",
                                "阳气回复", "好转中", "回复中", "仍有些"]),
    ("other", "未归类 / 其他", None),
]

# 预计算每条医案归属的证型集合（按索引），供计数与过滤使用。
_CASE_TEXT = [" ".join((_r.get(f) or "") for f in
              ("【诊断】", "【来诊原因】", "【解说】", "【中药处方】")) for _r in CASES]
CASE_CAT_SETS = {}
for _key, _label, _kws in CASE_CATS:
    if _kws is None:
        continue
    _s = set()
    for _i, _t in enumerate(_CASE_TEXT):
        for _kw in _kws:
            if _kw in _t:
                _s.add(_i)
                break
    CASE_CAT_SETS[_key] = _s

BBXX = common.load_table("BBXX")
BZDZ = common.load_table("BZDZ")
ZFBZ = common.load_table("ZFBZ")
ZJDCJL = common.load_table("ZJDCJL")
HANTANG = common.load_table("hantang")
LINGUI = common.load_table("linggui")
NAJIA = common.load_table("najia")
NAZI = common.load_table("nazi")
ARTICLES = common.load_table("nhxlwj")
HERBS = common.load_dict("ZYX")

# ---- 论文「栏目」精确目录 ----
# 直接还原原 EXE（医案论文内部查询系统V2022c61.exe）的菜单结构：
# 「文章分类.txt」是从 EXE 提取的真实「栏目→文章清单」，build_cat_map.py 据此生成
# article_cat_map.json = {cats:[13栏目名(有序)], map:{文章ID: 栏目名}}。
# 注：第7栏原文用「........」缩写 01-100，已把文章库全部「汉唐-XX号」补录进去。
_MAP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "article_cat_map.json")
with open(_MAP_PATH, encoding="utf-8") as _f:
    _ACM = json.load(_f)
ARTICLE_CAT_NAMES = _ACM["cats"]            # 13 个栏目名(有序)
ARTICLE_MAP = _ACM["map"]                    # {文章ID: 栏目名}
_ART_CTR = {}
for _v in ARTICLE_MAP.values():
    _ART_CTR[_v] = _ART_CTR.get(_v, 0) + 1
# 给每篇文章标注其栏目(未归入任何栏目的为空字符串, 仅出现在「全部论文」)
for _r in ARTICLES:
    _r["_art_cat"] = ARTICLE_MAP.get(str(_r.get("ID", "")), "")

# ---- 黄帝外经（外经微言，陈士铎本）独立模块 ---------------------------------
# 原 EXE(医案论文内部查询系统V2022c61.exe) 菜单含独立的「黄帝外经」节点，其下即
# 《外经微言》八十一篇（雷公问·岐伯曰 体例）。这些篇章在源库中存于 nhxlwj 表，
# MZ 字段为篇章名（如「任督死生篇」），NR 为全文（XOR-0x0F 解密后）。
# 注：「黄帝内经篇」「跟诊案例研究篇」「醒世篇」是倪师本人的随笔/教学笔记，
# 在原 EXE 中各有独立节点，不属于《外经微言》，故排除。
HDWJ_EXCLUDE = {"黄帝内经篇", "跟诊案例研究篇", "醒世篇"}
_seen_hdwj = set()
HDWJ = []
for _r in ARTICLES:
    _mz = str(_r.get("MZ", ""))
    if _mz.endswith("篇") and _mz not in HDWJ_EXCLUDE and _mz not in _seen_hdwj:
        _seen_hdwj.add(_mz)
        HDWJ.append(_r)

# yaotu 中药图（JPEG，XOR-0x0F 解密后存入 SQLite；无 data.db 时回退直连 .mdb）
YAOTU_IMG = common.get_yaotu_images()
YAOTU_NAMES = sorted(YAOTU_IMG.keys())


def yaotu_type(name):
    """The herb-image name is '药名-形态' (e.g. 麻黄-原态). The suffix after the
    last '-' is the 形态/类别 (原态 / 药材 / 饮片 / 草药); names without a dash
    fall back to '其他'. A stray '药材_副本' artifact is normalized to '药材'."""
    t = name.rsplit("-", 1)[1] if "-" in name else "其他"
    if t.endswith("_副本"):
        t = t[:-3]
    return t


YAOTU_TYPES = sorted(set(yaotu_type(n) for n in YAOTU_NAMES))
HERB_IMG = {}
for hname in HERBS:
    for yname in YAOTU_NAMES:
        if yname == hname or yname.startswith(hname + "-"):
            HERB_IMG[hname] = yname
            break
print("Loaded: cases=%d herbs=%d articles=%d yaotu=%d" %
      (len(CASES), len(HERBS), len(ARTICLES), len(YAOTU_IMG)))

# ---- 外部《中医》资料索引（穴位 / 中药图片，来自 GitHub 仓库，按经络/文件夹分类） ----
try:
    import extra_index
    EXTRA = extra_index.build()
    XUEWEI = EXTRA["xuewei"]
    HERB_IMGS = EXTRA["herb_imgs"]
    print("Loaded extra: xuewei=%d herb_imgs=%d" %
          (XUEWEI["total"], HERB_IMGS["total"]))
except Exception as _e:
    print("WARN: failed to build extra index:", _e)
    XUEWEI = {"cats": [], "points": [], "total": 0}
    HERB_IMGS = {"cats": [], "items": [], "total": 0}

# ---- 神农本草经 ordering + 补全 (sourced from 神农注解) ----
HERE = os.path.dirname(os.path.abspath(__file__))
SHENNONG = json.load(open(os.path.join(HERE, "shennong.json"), encoding="utf-8"))
_SN_LOOKUP = SHENNONG["lookup"]  # herb name/alias -> [cat, rank, pos]

def _herb_key(name):
    d = _SN_LOOKUP.get(name)
    if d:
        return (d[1], d[2], 0, name)   # (rank, pos, 0=in-shennong, name)
    return (5, 0, 1, name)            # 其他/后世本草 -> end

# Combined list sorted by 神农本草经 order: ZYX herbs first, then the 补全
# herbs that exist only in 神农注解, all interleaved by category+sequence.
_HERB_SORTED = []
for _name, _rec in HERBS.items():
    _r = dict(_rec)
    _sn = _SN_LOOKUP.get(_name)
    _r["_cat"] = (_sn[0] if _sn else "其他")   # 永远是字符串（上经/中经/下经/增补/其他）
    _HERB_SORTED.append((_herb_key(_name), _r))
for _m in SHENNONG["missing"]:
    _name = _m["name"]
    _rec = {"MZ": _name, "【古籍摘要】": _m.get("benjing", ""),
            "【简述】": _m.get("note", ""), "_shennong": True, "_cat": _m["cat"]}
    HERBS[_name] = _rec
    _HERB_SORTED.append((_herb_key(_name), _rec))
_HERB_SORTED.sort(key=lambda x: x[0])
# 神农本草经序：给四经草药赋全局序号 _seq 与本经内序号 _cat_seq，
# 后世本草(其他) 排在最后，_seq 为 None（不在神农序列内）。
_seq = 0
_cat_seq = {}
_ordered = []
for _key, _r in _HERB_SORTED:
    _cat = _r.get("_cat")
    if _cat in ("上经", "中经", "下经", "增补"):
        _seq += 1
        _r["_seq"] = _seq
        _cat_seq[_cat] = _cat_seq.get(_cat, 0) + 1
        _r["_cat_seq"] = _cat_seq[_cat]
        # HERBS 存的是原始记录（ZYX 草药是副本），详情接口读 HERBS，需同步赋值。
        _nm = _r.get("MZ")
        if _nm in HERBS:
            HERBS[_nm]["_seq"] = _seq
            HERBS[_nm]["_cat_seq"] = _cat_seq[_cat]
            HERBS[_nm]["_cat"] = _cat
    else:
        _r["_seq"] = None
        _r["_cat_seq"] = None
    _ordered.append(_r)
HERBS_SORTED = _ordered

# ---- 汉唐方剂 内容补全 (sourced from 倪师100方剂 Obsidian notes) ----
# Mapping rule verified against the source DB: Obsidian filename number N
# corresponds to 汉唐-N. The 15 cross-ref "mismatches" are the same formula
# written under a different commercial codename in the source zygn
# (e.g. 女子白带过多 = 玉洁一号), so number-based mapping is authoritative.
HANTANG_ENRICH = json.load(open(os.path.join(HERE, "hantang_enrich.json"), encoding="utf-8"))
for _r in HANTANG:
    _m = re.match(r"汉唐-(\d+)", str(_r.get("ID", "")))
    if _m and _m.group(1) in HANTANG_ENRICH:
        _e = HANTANG_ENRICH[_m.group(1)]
        _r["_name"] = _e.get("name", "")
        _r["_obs"] = {k: _e[k] for k in ("name", "body", "composition", "usage", "caution")}
        _r["_enriched"] = True
# Obsidian-only formulas lacking a source record (e.g. 32/66/95) -> synthesize
# so the 汉唐方剂 module is complete rather than showing gaps.
for _n, _e in HANTANG_ENRICH.items():
    if not any(re.match(r"汉唐-" + re.escape(_n) + r"$", str(r.get("ID", ""))) for r in HANTANG):
        HANTANG.append({
            "ID": "汉唐-" + _n,
            "_name": _e.get("name", ""),
            "_obs": {k: _e[k] for k in ("name", "body", "composition", "usage", "caution")},
            "_enriched": True, "_extra": True,
        })

MODULES = [
    {"key": "cases",   "name": "医案查询",        "table": "1234567", "desc": "1475 则临床医案（问诊/脉诊/处方/针灸）"},
    {"key": "herbs",   "name": "中药查询",        "table": "ZYX",     "desc": f"{len(HERBS)} 味中药（神农本草经序 + 补全）"},
    {"key": "bbxx",    "name": "病症方剂",        "table": "BBXX",    "desc": "206 条病症对应方剂"},
    {"key": "bzdz",    "name": "辨证论治",        "table": "BZDZ",    "desc": "50 条辨证思路"},
    {"key": "zfbz",    "name": "正副辨证",        "table": "ZFBZ",    "desc": "30 条正治与反治"},
    {"key": "zjdcjl",  "name": "针灸记录",        "table": "ZJDCJL",  "desc": "27 条针灸医案"},
    {"key": "hantang", "name": "汉唐方剂",        "table": "hantang", "desc": f"{len(HANTANG)} 首汉唐方剂（含倪师100方剂补全）"},
    {"key": "acu",     "name": "子午流注·灵龟八法", "table": "",       "desc": "纳甲/纳子/灵龟八法开穴"},
    {"key": "articles","name": "倪海厦论文",      "table": "nhxlwj",  "desc": "3499 篇文章/讲记"},
    {"key": "hdwj",    "name": "黄帝外经",        "table": "",       "desc": f"《外经微言》(陈士铎本) 共 {len(HDWJ)} 篇黄帝外经全文"},
    {"key": "yaotu",   "name": "药图",            "table": "yaotu",   "desc": f"{len(YAOTU_NAMES)+HERB_IMGS['total']} 张中药图（形态 + 功效分类）"},
    {"key": "xuewei",  "name": "穴位查询",        "table": "",       "desc": f"{XUEWEI['total']} 个穴位/图文（按经络分类）"},
]

REF_TABLES = {"BBXX": BBXX, "BZDZ": BZDZ, "ZFBZ": ZFBZ,
              "ZJDCJL": ZJDCJL, "hantang": HANTANG}
ACU_TABLES = {"lingui": LINGUI, "najia": NAJIA, "nazi": NAZI}


def _natural_key(rec):
    """Sort by the embedded number in ID/MZ so '汉唐-2' < '汉唐-10' < '汉唐-100'."""
    s = str(rec.get("ID") or rec.get("MZ") or next(iter(rec.values()), ""))
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", s)]


# Reference tables are presented in a stable, human-friendly order (by number).
for _t in REF_TABLES.values():
    _t.sort(key=_natural_key)


def search_in(rec, q):
    q = q.lower()
    for v in rec.values():
        if v and q in str(v).lower():
            return True
    return False


def paginate(lst, page, size):
    page = max(1, page)
    start = (page - 1) * size
    return lst[start:start + size], len(lst)


@app.get("/api/modules")
def api_modules():
    return MODULES


@app.get("/api/cases")
def api_cases(q: str = "", cat: str = "", page: int = 1, size: int = 20):
    data = CASES
    if cat and cat != "all":
        if cat == "other":
            _union = set().union(*CASE_CAT_SETS.values()) if CASE_CAT_SETS else set()
            data = [r for i, r in enumerate(data) if i not in _union]
        elif cat in CASE_CAT_SETS:
            _idx = CASE_CAT_SETS[cat]
            data = [r for i, r in enumerate(data) if i in _idx]
    if q:
        data = [r for r in data if search_in(r, q)]
    items, total = paginate(data, page, size)
    return {"total": total, "page": page, "size": size, "items": items}


@app.get("/api/cases/cats")
def api_cases_cats():
    """证型分类与计数，供医案模块左侧「按证型浏览」侧栏使用。"""
    _union = set().union(*CASE_CAT_SETS.values()) if CASE_CAT_SETS else set()
    out = []
    for key, label, kws in CASE_CATS:
        if kws is None:
            cnt = len(CASES) if key == "all" else (len(CASES) - len(_union))
        else:
            cnt = len(CASE_CAT_SETS.get(key, set()))
        out.append({"key": key, "label": label, "count": cnt})
    return {"cats": out}


@app.get("/api/case/{idx}")
def api_case(idx: int):
    if 0 <= idx < len(CASES):
        return CASES[idx]
    raise HTTPException(404, "not found")


@app.get("/api/herbs")
def api_herbs(q: str = "", cat: str = "", page: int = 1, size: int = 30):
    # HERBS_SORTED is already ordered by 神农本草经 (category + sequence).
    base = [dict(r) for r in HERBS_SORTED]
    if q:
        base = [r for r in base if search_in(r, q)]
    cats = [{"key": c, "label": c, "count": sum(1 for r in base if r.get("_cat") == c)}
            for c in SHENNONG["cats"] + ["其他"]]
    cats = [c for c in cats if c["count"] > 0]
    items = base if not cat else [r for r in base if r.get("_cat") == cat]
    # Keep the list payload light: drop the long commentary field.
    items = [{k: v for k, v in r.items() if k != "note"} for r in items]
    for r in items:
        r["_image"] = HERB_IMG.get(r.get("MZ"))
    out, total = paginate(items, page, size)
    return {"total": total, "page": page, "size": size, "cats": cats, "items": out}


@app.get("/api/herb/{name}")
def api_herb(name: str):
    r = HERBS.get(name)
    if not r:
        raise HTTPException(404, "not found")
    r = dict(r)
    r["_image"] = HERB_IMG.get(name)
    return r


@app.get("/api/ref/{table}")
def api_ref(table: str, q: str = "", page: int = 1, size: int = 50):
    data = REF_TABLES.get(table)
    if data is None:
        raise HTTPException(404, "unknown table")
    if q:
        data = [r for r in data if search_in(r, q)]
    items, total = paginate(data, page, size)
    return {"total": total, "page": page, "size": size, "items": items}


@app.get("/api/articles/cats")
def api_articles_cats():
    """论文 13 个栏目（来自原 EXE 真实目录）及其文章数，供左侧栏目侧栏使用。"""
    out = [{"key": name, "name": name, "count": _ART_CTR.get(name, 0)}
           for name in ARTICLE_CAT_NAMES]
    return {"cats": out}


@app.get("/api/articles")
def api_articles(q: str = "", cat: str = "", page: int = 1, size: int = 20):
    data = ARTICLES
    if cat:
        data = [r for r in data if r.get("_art_cat", "") == cat]
    if q:
        data = [r for r in data if search_in(r, q)]
    items, total = paginate(data, page, size)
    return {"total": total, "page": page, "size": size, "items": items}


@app.get("/api/article/{aid}")
def api_article(aid: str):
    for r in ARTICLES:
        if str(r.get("ID", "")) == str(aid):
            return r
    raise HTTPException(404, "not found")


# ---- 黄帝外经（外经微言）模块：nhxlwj 中以篇章名为 MZ 的 78 篇 ----
@app.get("/api/hdwj")
def api_hdwj(q: str = "", page: int = 1, size: int = 20):
    data = HDWJ
    if q:
        ql = q.lower()
        data = [r for r in data
                if ql in str(r.get("MZ", "")).lower()
                or ql in str(r.get("NR", "")).lower()]
    items, total = paginate(data, page, size)
    return {"total": total, "page": page, "size": size, "items": items}


@app.get("/api/hdwj/{idx}")
def api_hdwj_item(idx: int):
    if 0 <= idx < len(HDWJ):
        return HDWJ[idx]
    raise HTTPException(404, "not found")


@app.get("/api/search")
def api_search(q: str = "", module: str = "", page: int = 1, size: int = 50):
    """Global search across every module.

    - Without `module`: returns an overview with every category group
      (top 8 hits each) plus a `total` per group, so the UI can render
      switchable category tabs.
    - With `module` (cases/herbs/articles/ref/yaotu): returns ONLY that
      category's full (paginated) results, for the tab-filter view.
    """
    if not q:
        return {"q": q, "groups": [], "page": page, "size": size}
    cases_hits = [r for r in CASES if search_in(r, q)]
    herb_hits = [dict(r, _image=HERB_IMG.get(r.get("MZ"))) for r in HERBS.values() if search_in(r, q)]
    article_hits = [r for r in ARTICLES if search_in(r, q)]
    ref_hits = []
    for tname, tdata in REF_TABLES.items():
        for r in tdata:
            if search_in(r, q):
                rr = dict(r)
                rr["_table"] = tname
                ref_hits.append(rr)
    ql = q.lower()
    yaotu_hits = [{"name": n} for n in YAOTU_NAMES if ql in n.lower()]
    # 合并《中医》仓库「中药图片」文件夹内的药名
    yaotu_hits += [{"name": it["name"], "_folder": True, "_rel": it["_rel"]}
                   for it in HERB_IMGS["items"] if ql in it["name"].lower()]
    # 穴位（按经络）：穴名 / 内容 / 所属部位
    xuewei_hits = [{"name": p["name"], "cat_name": p["cat_name"],
                    "sub": p.get("sub", ""), "content": p.get("content", ""),
                    "images": p.get("images", [])}
                   for p in XUEWEI["points"]
                   if ql in p["name"].lower() or ql in (p.get("content") or "").lower()
                   or ql in (p.get("sub") or "").lower()]

    catalog = {
        "cases": ("医案", cases_hits),
        "herbs": ("中药", herb_hits),
        "articles": ("论文", article_hits),
        "ref": ("参考", ref_hits),
        "yaotu": ("药图", yaotu_hits),
        "xuewei": ("穴位", xuewei_hits),
    }

    if module:
        m = catalog.get(module)
        if not m:
            return {"q": q, "groups": [], "page": page, "size": size}
        name, items = m
        out, total = paginate(items, page, size)
        return {"q": q, "page": page, "size": size,
                "groups": [{"name": name, "module": module, "total": total,
                            "items": out, "single": True}]}

    groups = []
    for mod, (name, items) in catalog.items():
        if items:
            groups.append({"name": name, "module": mod, "total": len(items),
                           "items": items[:8]})
    return {"q": q, "groups": groups, "page": page, "size": size}


@app.get("/api/acu/{table}")
def api_acu(table: str):
    data = ACU_TABLES.get(table)
    if data is None:
        raise HTTPException(404, "unknown table")
    return data


@app.get("/api/xuewei")
def api_xuewei(cat: str = "", q: str = "", page: int = 1, size: int = 60):
    """Acupoint (穴位) material, grouped by 经络 (meridian).

    - Without `cat`: returns every point (paginated).
    - With `cat` (meridian key, e.g. 'fei'/'ren'/'tupu'): filters to that group.
    - `q`: matches name / content / sub-location.
    `cats` always carries the full category list (key/label/count/diagram).
    """
    pts = XUEWEI["points"]
    if cat:
        pts = [p for p in pts if p["cat"] == cat]
    if q:
        ql = q.lower()
        pts = [p for p in pts
               if ql in p["name"].lower()
               or ql in (p.get("content") or "").lower()
               or ql in (p.get("sub") or "").lower()]
    out, total = paginate(pts, page, size)
    return {"total": total, "page": page, "size": size,
            "cats": XUEWEI["cats"], "items": out}


@app.get("/api/yaotu")
def api_yaotu(q: str = "", cat: str = "", page: int = 1, size: int = 60):
    # MDB 形态类型（原态/药材/饮片/草药…）
    items = [{"name": n, "type": yaotu_type(n)} for n in YAOTU_NAMES]
    # 合并《中医》仓库「中药图片」文件夹（按功效分类），以 _folder 标记来源
    for it in HERB_IMGS["items"]:
        items.append({"name": it["name"], "type": it["cat_label"],
                      "cat_label": it["cat_label"],
                      "_folder": True, "_rel": it["_rel"]})
    if q:
        ql = q.lower()
        items = [i for i in items if ql in i["name"].lower()]
    if cat:
        items = [i for i in items if i["type"] == cat]
    # 合并分类：MDB 形态类型 + 文件夹功效分类（去重计数）
    cnt = {}
    for i in items:
        cnt[i["type"]] = cnt.get(i["type"], 0) + 1
    seen = set()
    cats = []
    for c in list(YAOTU_TYPES) + [c["label"] for c in HERB_IMGS["cats"]]:
        if c in seen:
            continue
        seen.add(c)
        cats.append({"key": c, "label": c, "count": cnt.get(c, 0)})
    out, total = paginate(items, page, size)
    return {"total": total, "page": page, "size": size,
            "cats": cats, "items": out}


@app.get("/api/herb_image/{name}")
def herb_image(name: str):
    img = YAOTU_IMG.get(name)
    if not img:
        raise HTTPException(404, "no image")
    return Response(content=img, media_type="image/jpeg")


# ---------------------------------------------------------------------------
# 人纪学习系统（独立数据库 renji_db）
# ---------------------------------------------------------------------------
@app.get("/api/renji/modules")
def api_renji_modules():
    return renji_db.modules()


@app.get("/api/renji/list")
def api_renji_list(sub: str = "", q: str = "", page: int = 1, size: int = 60):
    """List items for a 人纪 sub-module.
    - fields / image subs: returns paginated [{i, name}]
    - points / ziwwu: returned whole (no pagination); caller knows the kind
    """
    items = renji_db.list_items(sub, q)
    if sub in ("points", "ziwwu"):
        return {"total": len(items), "page": 1, "size": len(items), "items": items}
    page = max(1, page)
    start = (page - 1) * size
    chunk = items[start:start + size]
    return {"total": len(items), "page": page, "size": size, "items": chunk}


@app.get("/api/renji/item")
def api_renji_item(sub: str = "", i: int = 0):
    item = renji_db.get_item(sub, i)
    if not item:
        raise HTTPException(404, "not found")
    return item


@app.get("/api/renji/ziwwu")
def api_renji_ziwwu():
    return renji_db.ZIWU


@app.get("/renji/img")
def renji_img(name: str = ""):
    img = renji_db.image_bytes(name)
    if not img:
        raise HTTPException(404, "no image")
    return Response(content=img, media_type="image/jpeg")


# ---------------------------------------------------------------------------
# 天纪学习系统（三库 tianji_db：易经 / 紫微 / 天文 / 八字命例）
# ---------------------------------------------------------------------------
@app.get("/api/tianji/modules")
def api_tianji_modules():
    return tianji_db.modules()


@app.get("/api/tianji/list")
def api_tianji_list(sub: str = "", q: str = "", page: int = 1, size: int = 60):
    """List items for a 天纪 sub-module (fields subs; tables subs handled by /tables)."""
    items = tianji_db.list_items(sub, q)
    if isinstance(items, dict):
        # tables sub returned whole (no pagination)
        return {"total": len(items), "page": 1, "size": len(items), "items": items}
    page = max(1, page)
    start = (page - 1) * size
    chunk = items[start:start + size]
    return {"total": len(items), "page": page, "size": size, "items": chunk}


@app.get("/api/tianji/item")
def api_tianji_item(sub: str = "", i: int = 0):
    item = tianji_db.get_item(sub, i)
    if not item:
        raise HTTPException(404, "not found")
    return item


@app.get("/api/tianji/tables")
def api_tianji_tables(sub: str = ""):
    """Return {tables:[{key,label,cols,rows}]} for a tables-kind sub-module."""
    return tianji_db.tables(sub)


@app.get("/tianji/img")
def tianji_img(name: str = ""):
    img, mt = tianji_db.image_bytes(name)
    if not img:
        raise HTTPException(404, "no image")
    return Response(content=img, media_type=mt or "image/jpeg")


# ---- 天纪·排盘系统 / 命理系统（新增强化模块）----------------------------------
@app.post("/api/tianji/paipan")
def api_tianji_paipan(payload: dict = Body(default={})):
    """输入阳历生日 / 时辰 / 性别，排出八字四柱、紫微斗数命盘、本命卦，并给出命理解读。"""
    solar = payload.get("solar") or ""
    gender = payload.get("gender") or "男"
    birthplace = payload.get("birthplace") or ""
    if not solar:
        raise HTTPException(400, "缺少出生时间")
    try:
        return paipan.paipan(solar, gender, birthplace)
    except ValueError as e:
        raise HTTPException(400, "日期格式错误：" + str(e))
    except Exception as e:
        raise HTTPException(500, "排盘计算失败：" + str(e))


# Serve images from the external 《中医》 GitHub repo (穴位 diagrams/photos and
# 中药图片). `p` is a URL-encoded relative path under EXTRA_BASE; we normalize
# and reject any path that escapes the base directory (directory traversal).
_EXTIMG_BASE = r"E:/Soft/GitHub/中医"
_EXTIMG_MT = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
              "gif": "image/gif", "bmp": "image/bmp"}


@app.get("/extimg")
def ext_img(p: str = ""):
    from urllib.parse import unquote
    if not p:
        raise HTTPException(400, "missing p")
    rel = unquote(p).replace("/", os.sep).replace("\\", os.sep)
    full = os.path.normpath(os.path.join(_EXTIMG_BASE, rel))
    base_norm = os.path.normpath(_EXTIMG_BASE)
    if full != base_norm and not full.startswith(base_norm + os.sep):
        raise HTTPException(403, "forbidden")
    if not os.path.isfile(full):
        raise HTTPException(404, "not found")
    ext = os.path.splitext(full)[1].lower().lstrip(".")
    mt = _EXTIMG_MT.get(ext, "application/octet-stream")
    with open(full, "rb") as f:
        data = f.read()
    return Response(content=data, media_type=mt)


@app.get("/", response_class=HTMLResponse)
def index():
    with open(os.path.join(os.path.dirname(__file__), "static", "index.html"),
              encoding="utf-8") as f:
        return f.read()


# 三套学习系统：各自独立页面（顶部系统切换器跳转），互不在对方侧栏出现。
_STATIC = os.path.join(os.path.dirname(__file__), "static")


@app.get("/renji", response_class=HTMLResponse)
def renji_page():
    return FileResponse(os.path.join(_STATIC, "renji.html"))


@app.get("/tianji", response_class=HTMLResponse)
def tianji_page():
    return FileResponse(os.path.join(_STATIC, "tianji.html"))


app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")),
          name="static")
