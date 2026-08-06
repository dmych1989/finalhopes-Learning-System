# -*- coding: utf-8 -*-
"""64-bit local web server for the 倪海厦 medical reference system.
Reads Data/LILUN.mdb live (via 64-bit Access ODBC) and decrypts on the fly."""
import os
import re
import json
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import HTMLResponse, JSONResponse, Response, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import common

# 人纪学习系统：独立的第二数据库（人纪针灸学习系统 LILUN.mdb），同密码同加密。
import renji_db
# 天纪学习系统：三个独立数据库（LILUN/CollData/MasterData，密码各不相同），易经/紫微/天文/命理。
import tianji_db
# 天纪目录树（按 列表.txt 重组，每叶带 src/idx，复用 /api/tianji/item 渲染）
import tianji_tree
# 天纪排盘 / 命理系统：八字 + 紫微斗数 + 本命卦 引擎（纯 Python）。
import paipan

# 图片索引：extract_images.py 把 yaotu/renji/tianji 三库图片抽出到 public/img/{sub}/，
# 并把「原名 -> 文件名」映射写入 web_app/img_index.py；图片端点 302 重定向到 CDN 静态路径。
try:
    import img_index
    IMG_INDEX = getattr(img_index, "IMG_INDEX", {})
except Exception:
    IMG_INDEX = {}

app = FastAPI(title="论文医案查询系统 (网页版)")

# 医案数据懒加载：首次访问时才从 data.db 读取，避免 Vercel 冷启动导入期就触发
# 92MB 下载 / 解密，导致函数初始化超时（FUNCTION_INVOCATION_FAILED）。
CASES = None

def case_title(rec):
    for c in ["【来诊原因】", "【诊断】", "【问诊】"]:
        v = (rec.get(c) or "").strip()
        if v:
            return v[:24]
    if rec.get("【姓名】"):
        return rec["【姓名】"][:24]
    return "医案记录"

def get_cases():
    global CASES
    if CASES is None:
        print("Loading 医案 from data.db ...")
        try:
            rows = common.load_table("1234567")
        except Exception as _e:
            print("WARN: CASES 加载失败：", repr(_e))
            rows = []
        for _c in rows:
            _c["_title"] = case_title(_c)
        CASES = rows
    return CASES

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
              ("【诊断】", "【来诊原因】", "【解说】", "【中药处方】")) for _r in get_cases()]
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
# 给每篇文章标注其栏目(未归入任何栏目的为空字符串)
for _r in ARTICLES:
    _r["_art_cat"] = ARTICLE_MAP.get(str(_r.get("ID", "")), "")

# 模块专属范围：归属于 13 个栏目之一的文章索引集合。默认（含「全部论文」）只显示这些，
# 而非把整库 3499 篇一股脑倒出——倪海厦论文板块只展示本板块内容，避免与病症研究/时事评论雷同。
ARTICLE_ALL = set(i for i, _r in enumerate(ARTICLES) if _r.get("_art_cat", ""))

# ---- 病症研究（按 EXE 目录.txt 真实栏目归类）模块 ---------------------------------
# 原 EXE 菜单含一组「疾病专论」栏目，其真实栏目结构见
# 「医学论文医案查询系统/病症研究/目录.txt」（艾滋病专论 / 肺病专论 / 肝癌专论 …
# 癌症专论 等共 22 个栏目）。由 tools/build_bz_map.py 解析该目录，离线生成
# 文章ID -> 栏目key 的映射 web_app/bz_map.json（含《健康警讯/解密谣言/医药保健/
# 肠胃型流感》等内嵌标记处理），这里加载它驱动分类，保证网页病症研究板块与 EXE 原貌一致。
BZ_CATS = [
    {"key": "aizibing",  "name": "艾滋病专论"},
    {"key": "feibing",   "name": "肺病专论"},
    {"key": "ganai",     "name": "肝癌专论"},
    {"key": "guzhishu",  "name": "骨质疏松症"},
    {"key": "laonianchidai", "name": "老年痴呆症"},
    {"key": "rubing",    "name": "乳癌专论"},
    {"key": "shenzangbing", "name": "肾脏病专论"},
    {"key": "weitaming", "name": "维他命专论"},
    {"key": "xinzangbing", "name": "心脏病专论"},
    {"key": "yizangai",  "name": "胰脏癌专论"},
    {"key": "zisha",     "name": "自杀案例"},
    {"key": "dachangai", "name": "大肠癌专论"},
    {"key": "fuke",      "name": "妇科专论"},
    {"key": "ganmao",    "name": "感冒与疫苗"},
    {"key": "hongbanlangchuang", "name": "红斑狼疮"},
    {"key": "naobing",   "name": "脑病专论"},
    {"key": "shenprostate", "name": "摄护腺癌"},
    {"key": "tangniaobing", "name": "糖尿病专论"},
    {"key": "weibing",   "name": "胃病区专论"},
    {"key": "xueai",     "name": "血癌专论"},
    {"key": "zhongfeng", "name": "中风专论"},
    {"key": "aizheng",   "name": "癌症专论"},
]
# 加载 ID->栏目key 映射（由 tools/build_bz_map.py 依据 EXE 目录.txt 预计算）
_BZ_MAP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bz_map.json")
try:
    with open(_BZ_MAP_PATH, encoding="utf-8") as _f:
        _BZ_MAP = json.load(_f)
except Exception:
    _BZ_MAP = {}
_id_to_idx = {str(r.get("ID", "")): i for i, r in enumerate(ARTICLES)}
BZ_CAT_SETS = {c["key"]: set() for c in BZ_CATS}
for _aid, _key in _BZ_MAP.items():
    _i = _id_to_idx.get(str(_aid))
    if _i is not None and _key in BZ_CAT_SETS:
        BZ_CAT_SETS[_key].add(_i)
BZ_CAT_CTR = {k: len(v) for k, v in BZ_CAT_SETS.items()}
# 模块专属范围：归属于任一个病症研究栏目的文章索引集合。默认（含「全部病症」）只显示这些，
# 而非把整库 3499 篇一股脑倒出——否则病症研究会与论文/时事评论显示完全相同的列表。
BZ_ALL = set().union(*BZ_CAT_SETS.values())
BZ_TOTAL = len(BZ_ALL)

# ---- 时事评论（按「倪师论×」主题归类）模块 ---------------------------------
# 原 EXE（医案论文内部查询系统V2022c61.exe）菜单含「时事评论」节点，其下为一组
# 主题专论：倪师论癌症 / 倪师论肝病 / 倪师论流感 / 倪师论感冒 / 倪师论牛奶 /
# 倪师论肾脏 / 倪师论糖尿 / 倪师论心病 / 倪师论血液 / 倪师论中药 / 倪师论抗生素 /
# 最新研究成果时事评论 / 倪师论乳癌 / 倪师论忧郁 / 倪师论妇科 / 未归类评论。
# 源数据无独立「评论」字段，故以主题关键词对 nhxlwj 全库做一次离线归类
# （每篇取 标题 + 正文前 160 字 做子串匹配），与 病症研究 同源做法一致。
# 注：用户清单中的「倪师论感自」即「倪师论感冒」、「时倪师论肾脏」即「倪师论肾脏」。
SSPL_CATS = [
    {"key": "ai",         "name": "倪师论癌症"},
    {"key": "ganbing",    "name": "倪师论肝病"},
    {"key": "liugan",     "name": "倪师论流感"},
    {"key": "shenzang",   "name": "倪师论肾脏"},
    {"key": "niunai",     "name": "倪师论牛奶"},
    {"key": "tangniao",   "name": "倪师论糖尿"},
    {"key": "xinbing",    "name": "倪师论心病"},
    {"key": "xueye",      "name": "倪师论血液"},
    {"key": "zhongyao",   "name": "倪师论中药"},
    {"key": "kangshengsu", "name": "倪师论抗生素"},
    {"key": "zuixin",     "name": "最新研究成果时事评论"},
    {"key": "ruanai",     "name": "倪师论乳癌"},
    {"key": "youyu",      "name": "倪师论忧郁"},
    {"key": "fuke",       "name": "倪师论妇科"},
    {"key": "baojian",    "name": "保健锦囊"},
    {"key": "fkmenzhen",  "name": "妇科门诊"},
    {"key": "weifanlei",  "name": "未归类评论"},
    {"key": "foodinc",    "name": "食品帝国FoodInc."},
]
# 加载 ID->栏目key 映射（由 tools/build_sspl_map.py 依据 EXE 目录.txt 预计算）
_SSPL_MAP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sspl_map.json")
try:
    with open(_SSPL_MAP_PATH, encoding="utf-8") as _f:
        _SSPL_MAP = json.load(_f)
except Exception:
    _SSPL_MAP = {}
# 文章 ID -> 索引
_id_to_idx = {str(r.get("ID", "")): i for i, r in enumerate(ARTICLES)}
SSPL_CAT_SETS = {c["key"]: set() for c in SSPL_CATS}
for _aid, _key in _SSPL_MAP.items():
    _i = _id_to_idx.get(str(_aid))
    if _i is not None and _key in SSPL_CAT_SETS:
        SSPL_CAT_SETS[_key].add(_i)
SSPL_CAT_CTR = {k: len(v) for k, v in SSPL_CAT_SETS.items()}
# 模块专属范围：归属于任一时事评论栏目的文章索引集合。默认（含「全部评论」）
# 只显示这些，避免与论文/病症研究显示同一份整库列表。
SSPL_ALL = set().union(*SSPL_CAT_SETS.values())
SSPL_TOTAL = len(SSPL_ALL)

# ---- 三板块分区（评论/病症各自按 EXE 目录.txt 权威认领，论文为 13 栏目核心）----
# 时事评论与病症研究均依据各自 EXE 目录.txt 认领全部文章（评论=1015、病症=555），
# 二者在文章层面仅少量重叠（约 16 篇，EXE 中同文跨模块），予以保留以忠实于 EXE 原貌。
# 论文(13栏目)为权威核心板块，需剔除同时被评论/病症认领的文章，保证论文不重复显示。
# 1) 清除被评论/病症认领文章在论文中的栏目归属，并同步下调论文各栏计数
_REMOVED_CATS = {}
for _i in (SSPL_ALL | BZ_ALL):
    _old = ARTICLES[_i].get("_art_cat", "")
    if _old:
        ARTICLES[_i]["_art_cat"] = ""
        _REMOVED_CATS[_old] = _REMOVED_CATS.get(_old, 0) + 1
for _c, _n in _REMOVED_CATS.items():
    _ART_CTR[_c] = max(0, _ART_CTR.get(_c, 0) - _n)
# 2) 重建论文集合（已剔除被评论/病症认领的文章）
ARTICLE_ALL = set(i for i, _r in enumerate(ARTICLES) if _r.get("_art_cat", ""))
# 3) 评论/病症各自为完整 EXE 栏目集合，不相互剔除（保留 EXE 跨模块重叠）
BZ_TOTAL = len(BZ_ALL)
SSPL_TOTAL = len(SSPL_ALL)
SSPL_TOTAL = len(SSPL_ALL)

# ---- 黄帝外经（外经微言，陈士铎本）独立模块 ---------------------------------
# 原 EXE(医案论文内部查询系统V2022c61.exe) 菜单含独立的「黄帝外经」节点，其下即
# 《外经微言》八十一篇（雷公问·岐伯曰 体例）。这些篇章在源库中存于 nhxlwj 表，
# MZ 字段为篇章名（如「任督死生篇」），NR 为全文（XOR-0x0F 解密后）。
# 注：「黄帝内经篇」「跟诊案例研究篇」「醒世篇」是倪师本人的随笔/教学笔记，
# 在原 EXE 中各有独立节点，不属于《外经微言》，故排除。
HDWJ_EXCLUDE = {"黄帝内经篇", "跟诊案例研究篇", "醒世篇"}
# 《外经微言》八十一篇（陈士铎本）权威卷次顺序，用作目录正确排序与篇次序号。
# 数据源自清·陈士铎《外经微言》通行本目录（九卷·每卷九篇）；本库缺「五行生克篇」
# 「小心真主篇」「六气分门篇」三篇（非排除项），余 78 篇据此排序并标注原书第 N 篇。
HDWJ_CANON = [
    "阴阳颠倒篇", "顺逆探原篇", "回天生育篇", "天人寿夭篇", "命根养生篇", "救母篇",
    "红铅损益篇", "初生微论篇", "骨阴篇",
    "媾精受妊篇", "社生篇", "天厌火衰篇", "经脉相行篇", "经脉终始篇", "经气本标篇",
    "脏腑阐微篇", "考订经脉篇", "包络配腑篇",
    "胆腑命名篇", "任督死生篇", "阴阳二跷篇", "奇恒篇", "小络篇", "肺金篇", "肝木篇",
    "肾水篇", "心火篇",
    "脾土篇", "胃土篇", "包络火篇", "三焦火篇", "胆木篇", "膀胱水篇", "大肠金篇",
    "小肠火篇", "命门真火篇",
    "命门经主篇", "五行生克篇", "小心真主篇", "水不克火篇", "三关升降篇", "表微篇",
    "呼吸篇", "脉动篇", "瞳子散大篇",
    "诊原篇", "精气引血篇", "天人一气篇", "地气合人篇", "三才并论篇", "五运六气离合篇",
    "六气分门篇", "六气独胜篇", "三合篇",
    "四时六气异同篇", "司天在泉分合篇", "从化篇", "冬夏火热篇", "暑火二气篇", "阴阳上下篇",
    "营卫交重篇", "五脏互根篇", "八风固本篇",
    "八风命名篇", "太乙篇", "亲阳亲阴篇", "异传篇", "伤寒知变篇", "伤寒同异篇",
    "风寒殊异篇", "阴寒格阳篇", "春温似疫篇",
    "补泻阴阳篇", "善养篇", "亡阳亡阴篇", "昼夜轻重篇", "解阳解阴篇", "真假疑似篇",
    "从逆窥源篇", "移寒篇", "寒热舒肝篇",
]
HDWJ_CANON_POS = {_n: _i + 1 for _i, _n in enumerate(HDWJ_CANON)}
# 源库个别篇章名与通行本略有出入，按原书位置对齐（否则会落到末尾）。
HDWJ_ALIAS = {"热舒肝篇": "寒热舒肝篇", "六气异同篇": "四时六气异同篇"}
_HDWJ_UNSORTED = 10 ** 9
def _hdwj_pos(name):
    if name in HDWJ_CANON_POS:
        return HDWJ_CANON_POS[name]
    if name in HDWJ_ALIAS and HDWJ_ALIAS[name] in HDWJ_CANON_POS:
        return HDWJ_CANON_POS[HDWJ_ALIAS[name]]
    return _HDWJ_UNSORTED
_seen_hdwj = set()
_HDWJ_RAW = []
for _r in ARTICLES:
    _mz = str(_r.get("MZ", ""))
    if _mz.endswith("篇") and _mz not in HDWJ_EXCLUDE and _mz not in _seen_hdwj:
        _seen_hdwj.add(_mz)
        _HDWJ_RAW.append(_r)
# 按《外经微言》原书卷次排序；拷贝避免污染 ARTICLES 共享 dict，并标注篇次序号。
HDWJ = []
for _r in sorted(_HDWJ_RAW, key=lambda r: _hdwj_pos(str(r.get("MZ", "")))):
    _r = dict(_r)
    _pos = _hdwj_pos(str(_r.get("MZ", "")))
    if _pos < _HDWJ_UNSORTED:
        _r["_idx"] = _pos
    HDWJ.append(_r)
del _HDWJ_RAW

# 黄帝外经《外经微言》现代白话译文（参考 Obsidian 外经微言.md，按篇章名映射）。
# 与 MDB 原文（文言文）形成「原文 / 译文」对照；缺译文的篇章（如缺卷三篇）留空。
HDWJ_YI_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hdwj_yi.json")
HDWJ_YI = {}
try:
    with open(HDWJ_YI_PATH, encoding="utf-8") as _f:
        HDWJ_YI = json.load(_f)
except Exception:
    HDWJ_YI = {}

# yaotu 中药图：图片已从 data.db 抽出为静态资源 public/img/yaotu/（XOR-0x0F 解密后），
# 由 /api/herb_image 302 重定向到 CDN 静态文件；索引见 web_app/img_index.py。
def yaotu_type(name):
    """The herb-image name is '药名-形态' (e.g. 麻黄-原态). The suffix after the
    last '-' is the 形态/类别 (原态 / 药材 / 饮片 / 草药); names without a dash
    fall back to '其他'. A stray '药材_副本' artifact is normalized to '药材'."""
    t = name.rsplit("-", 1)[1] if "-" in name else "其他"
    if t.endswith("_副本"):
        t = t[:-3]
    return t


YAOTU_NAMES = sorted(IMG_INDEX.get("yaotu", {}).keys())
YAOTU_TYPES = sorted(set(yaotu_type(n) for n in YAOTU_NAMES))
HERB_IMG = {}
for hname in HERBS:
    for yname in YAOTU_NAMES:
        if yname == hname or yname.startswith(hname + "-"):
            HERB_IMG[hname] = yname
            break
print("Loaded: cases=%d herbs=%d articles=%d yaotu=%d" %
      (len(CASES), len(HERBS), len(ARTICLES), len(YAOTU_NAMES)))

# ---- 外部《中医》资料索引（穴位 / 中药图片，来自 GitHub 仓库，按经络/文件夹分类） ----
# 优先从预构建的 extra_data.json 加载（生产环境无本地中医目录）；
# 若 JSON 不存在则尝试扫描本地目录（开发环境）。
HERE = os.path.dirname(os.path.abspath(__file__))
_EXTRA_JSON = os.path.join(HERE, "extra_data.json")
XUEWEI = {"cats": [], "points": [], "total": 0}
HERB_IMGS = {"cats": [], "items": [], "total": 0}
try:
    if os.path.isfile(_EXTRA_JSON):
        import json as _json
        _ed = _json.load(open(_EXTRA_JSON, encoding="utf-8"))
        XUEWEI = _ed["xuewei"]
        HERB_IMGS = _ed["herb_imgs"]
        print("Loaded extra (json): xuewei=%d herb_imgs=%d" %
              (XUEWEI["total"], HERB_IMGS["total"]))
    else:
        import extra_index
        EXTRA = extra_index.build()
        XUEWEI = EXTRA["xuewei"]
        HERB_IMGS = EXTRA["herb_imgs"]
        print("Loaded extra (scan): xuewei=%d herb_imgs=%d" %
              (XUEWEI["total"], HERB_IMGS["total"]))
except Exception as _e:
    print("WARN: failed to load extra index:", _e)

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

# 医学论文医案查询系统：仅保留三大板块——文章 / 医案 / 黄帝外经。
# 其余参考模块（中药/穴位/针灸/方剂/八法等）已并入「人纪学习系统」融合，
# 故从本系统侧栏移除；其后端接口（/api/herbs、/api/ref、/api/yaotu、
# /api/xuewei、/api/acu 等）保留不动，供人纪页面跨系统调用，数据不丢失。
MODULES = [
    {"key": "articles","name": "倪海厦论文",      "table": "nhxlwj",  "desc": "3499 篇文章/讲记（13 栏目 + 全部论文）"},
    {"key": "cases",   "name": "医案查询",        "table": "1234567", "desc": "1475 则临床医案（问诊/脉诊/处方/针灸）"},
    {"key": "hdwj",    "name": "黄帝外经",        "table": "",       "desc": f"《外经微言》(陈士铎本) 共 {len(HDWJ)} 篇黄帝外经全文"},
    {"key": "bz",      "name": "病症研究",        "table": "",       "desc": f"按 22 类疾病专论归类（艾滋病/肺病/肝癌/乳癌/糖尿病…共 {BZ_TOTAL} 篇）"},
    {"key": "sspl",    "name": "时事评论",        "table": "",       "desc": f"按 16 类倪师论题归类（癌症/肝病/流感/牛奶/肾脏/糖尿/心病/血液/中药/抗生素/乳癌/忧郁/妇科…共 {SSPL_TOTAL} 篇）"},
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
    return {"cats": out, "total": len(ARTICLE_ALL)}


@app.get("/api/articles")
def api_articles(q: str = "", cat: str = "", page: int = 1, size: int = 20):
    # 默认（含「全部论文」）仅显示归属于 13 个栏目之一的文章，而非整库
    data = [ARTICLES[i] for i in ARTICLE_ALL] if ARTICLE_ALL else []
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


# ---- 病症研究：按疾病专论筛选 nhxlwj 文章 ----
@app.get("/api/bz/cats")
def api_bz_cats():
    """22 个疾病专论栏目及命中文章数，供病症研究模块左侧目录侧栏使用。"""
    out = [{"key": c["key"], "name": c["name"], "count": BZ_CAT_CTR.get(c["key"], 0)}
           for c in BZ_CATS]
    return {"cats": out, "total": BZ_TOTAL}


@app.get("/api/bz")
def api_bz(cat: str = "", q: str = "", page: int = 1, size: int = 20):
    if cat and cat in BZ_CAT_SETS:
        data = [ARTICLES[i] for i in BZ_CAT_SETS[cat]]
    else:
        # 默认（含「全部病症」）仅显示归属于任一疾病专论的文章，而非整库
        data = [ARTICLES[i] for i in BZ_ALL] if BZ_ALL else []
    if q:
        data = [r for r in data if search_in(r, q)]
    items, total = paginate(data, page, size)
    return {"total": total, "page": page, "size": size, "items": items}


# ---- 时事评论：按「倪师论×」主题筛选 nhxlwj 文章 ----
@app.get("/api/sspl/cats")
def api_sspl_cats():
    """16 个主题栏目及命中文章数，供时事评论模块左侧目录侧栏使用。"""
    out = [{"key": c["key"], "name": c["name"], "count": SSPL_CAT_CTR.get(c["key"], 0)}
           for c in SSPL_CATS]
    return {"cats": out, "total": SSPL_TOTAL}


@app.get("/api/sspl")
def api_sspl(cat: str = "", q: str = "", page: int = 1, size: int = 20):
    if cat and cat in SSPL_CAT_SETS:
        data = [ARTICLES[i] for i in SSPL_CAT_SETS[cat]]
    else:
        # 默认（含「全部评论」）仅显示归属于任一时事评论主题+未归类评论的文章
        data = [ARTICLES[i] for i in SSPL_ALL] if SSPL_ALL else []
    if q:
        data = [r for r in data if search_in(r, q)]
    items, total = paginate(data, page, size)
    return {"total": total, "page": page, "size": size, "items": items}


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
        r = dict(HDWJ[idx])
        mz = str(r.get("MZ", ""))
        yi = HDWJ_YI.get(mz)
        if not yi:  # 个别篇章名与通行本略有出入（如「热舒肝篇」↔「寒热舒肝篇」）
            yi = HDWJ_YI.get(HDWJ_ALIAS.get(mz))
        if yi:
            r["yi"] = yi
        return r
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
    fn = IMG_INDEX.get("yaotu", {}).get(name)
    if not fn:
        raise HTTPException(404, "no image")
    return RedirectResponse("/img/yaotu/%s" % fn, status_code=302)


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


# ---- 穴位详解：十四经络（主系统《中医》按经络分组 + 任纪倪师注解交叉挂接）----
_MER_LABELS = {c["key"]: c["label"] for c in XUEWEI.get("cats", [])}


def _meridians():
    out = []
    for key in renji_db.MERIDIAN_ORDER:
        pts = [p for p in XUEWEI["points"] if p.get("cat") == key]
        out.append({
            "key": key,
            "label": _MER_LABELS.get(key, key),
            "count": len(pts),
            "diagram": next((c.get("diagram") for c in XUEWEI.get("cats", [])
                             if c["key"] == key), None),
        })
    return out


@app.get("/api/renji/meridians")
def api_renji_meridians():
    return _meridians()


@app.get("/api/renji/meridian/{key}")
def api_renji_meridian(key: str):
    pts = [p for p in XUEWEI["points"] if p.get("cat") == key]
    items = []
    for p in pts:
        nishi = renji_db.nishi_fields(p.get("name", ""))
        items.append({
            "name": p.get("name", ""),
            "cat": p.get("cat"),
            "cat_name": p.get("cat_name", ""),
            "sub": p.get("sub", ""),
            "content": p.get("content", ""),
            "images": p.get("images", []),
            "nishi": nishi,   # 任纪倪师穴位详解 13 字段
        })
    return {
        "key": key,
        "label": _MER_LABELS.get(key, key),
        "total": len(items),
        "items": items,
    }


# ---- 汉唐取穴：252 首汉唐方剂按 经络/脏腑/对症/辨证 四法尽力归类 ----
_HANTANG_KW = {
    "jingluo": ["经络", "经穴", "循行", "流注", "手太阴", "手阳明", "足阳明", "足太阴",
            "手少阴", "手太阳", "足太阳", "手厥阴", "手少阳", "足少阳", "足厥阴",
            "任脉", "督脉", "井荥俞经合", "五输"],
    "zangfu": ["肝", "心", "脾", "肺", "肾", "胃", "胆", "膀胱", "大肠", "小肠",
            "三焦", "心包", "脏腑", "胸", "腹"],
    "duizheng": ["痛", "咳", "喘", "炎", "肿", "泻", "秘", "晕", "麻", "痿", "痹",
            "血", "汗", "渴", "呕", "胀", "症", "失眠", "惊"],
    "bianzheng": ["虚", "实", "寒", "热", "阴", "阳", "表", "里", "辨证", "不足",
            "有余", "湿", "燥", "风", "火", "气滞", "血瘀"],
}


def _hantang_by_method(method):
    kws = _HANTANG_KW.get(method, [])
    out = []
    for it in renji_db.HANTANG:
        text = (it.get("name", "") + " " + it.get("fields", {}).get("讲解", ""))
        if any(k in text for k in kws):
            out.append({"name": it.get("name", ""), "num": it.get("num", 0),
                        "desc": (it.get("fields", {}).get("讲解", "") or "")[:120]})
    out.sort(key=lambda x: x.get("num", 0))
    return out


@app.get("/api/renji/hantang/{method}")
def api_renji_hantang(method: str):
    return {"method": method, "total": len(_hantang_by_method(method)),
            "items": _hantang_by_method(method)}


@app.get("/api/renji/hantang/{method}/item")
def api_renji_hantang_item(method: str, name: str = ""):
    for it in renji_db.HANTANG:
        if it.get("name") == name:
            return {"name": it.get("name", ""),
                    "fields": it.get("fields", {})}
    raise HTTPException(404, "not found")


# ---- 交互工具数据 ----
@app.get("/api/renji/tool/{tool}")
def api_renji_tool(tool: str):
    if tool == "ziwwu_pan":
        return {"ziwwu": renji_db.ZIWU,
                "meridians": _meridians()}
    if tool == "lingui_dial":
        return renji_db.ZIWU.get("lingui", {})
    if tool == "wanianli":
        return {"ok": True, "note": "万年历由前端 JS 计算（干支年 + 节气）"}
    raise HTTPException(404, "unknown tool")


@app.get("/api/renji/ziwwu")
def api_renji_ziwwu():
    return renji_db.ZIWU


@app.get("/renji/img")
def renji_img(name: str = ""):
    fn = IMG_INDEX.get("renji", {}).get(name)
    if not fn:
        raise HTTPException(404, "no image")
    return RedirectResponse("/img/renji/%s" % fn, status_code=302)


# ---------------------------------------------------------------------------
# 天纪学习系统（三库 tianji_db：易经 / 紫微 / 天文 / 八字命例）
# ---------------------------------------------------------------------------
def _norm_catalog(s):
    return re.sub(r"[\s（）()【】\[\]、，。:：·\-]", "", s or "")


def _build_tianji_catalog():
    """按天纪目录大纲(tianji_catalog.txt) 构建三层章节树，并把天纪全部文章按归一化标题归入对应条目：
       - lilun(八字/紫微理论+断法) → 基础理论/断法细则/子女/时辰效验
       - gua(六十四卦) / rendao(人间道) → 天纪卦象查询（按子分类名偏好六十四卦/人间道）
       - mingli(八字命例) → 案例查询（大师案例/收集案例/自断案例）
       - 每条目录条目直接对应文章标题，确保 506 篇全部不丢（未命中条目者进「未归类」）。"""
    base = os.path.dirname(os.path.abspath(__file__))
    p1 = os.path.join(base, "tianji_catalog.txt")
    p2 = r"E:\Soft\倪海夏三套学习系统\QQ频道号talktyph0id\天纪学习系统\列表.txt"
    src = p1 if os.path.exists(p1) else p2
    try:
        lines = open(src, encoding="utf-8").read().splitlines()
    except Exception:
        lines = []

    cats = {}; order = []
    cur_cat = None; cur_sub = None
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if s.startswith("#"):
            name = s.lstrip("#").strip()
            if s.startswith("##"):
                if cur_cat is not None:
                    exist = next((x for x in cur_cat["subs"] if x["name"] == name), None)
                    if exist:
                        cur_sub = exist
                    else:
                        cur_sub = {"name": name, "entries": []}
                        cur_cat["subs"].append(cur_sub)
            else:
                if name not in cats:
                    cats[name] = {"name": name, "subs": []}
                    order.append(name)
                cur_cat = cats[name]
                cur_sub = None
            continue
        if re.match(r"^[0-9]+[.．、)]", s):
            continue
        if re.match(r"^[一二三四五六七八九十]+[.．、]", s):
            continue
        if re.match(r"^\([0-9]+\)", s):
            continue
        if cur_sub is not None:
            cur_sub["entries"].append({"name": s, "articles": []})
    tree = [cats[n] for n in order]

    def names(src_list):
        return [(i, (r.get("name") or "").strip())
                for i, r in enumerate(src_list)
                if (r.get("name") or "").strip()]
    SRC = {
        "lilun": names(tianji_db.LILUN),
        "gua": names(tianji_db.GUA),
        "rendao": names(tianji_db.RENDAO),
        "mingli": names(tianji_db.MINGLI),
    }
    # 每个来源允许归入的顶层分类
    ALLOW = {"lilun": {"基础理论", "断法细则", "子女", "时辰效验"},
             "gua": {"天纪卦象查询"}, "rendao": {"天纪卦象查询"},
             "mingli": {"案例查询"}}
    # 同名条目（如「乾为天」同时存在于六十四卦与人间道）时，按子分类名偏好挑选来源
    SUBHINT = {"gua": "卦", "rendao": "道"}

    # 扁平化所有条目，附带其所属 顶层/子分类 名
    flat = []
    for cat in tree:
        for sub in cat["subs"]:
            for e in sub["entries"]:
                flat.append((e, cat["name"], sub["name"]))

    used = {k: set() for k in SRC}
    for sk, lst in SRC.items():
        allowed = ALLOW[sk]
        hint = SUBHINT.get(sk)
        for (i, n) in lst:
            nn = _norm_catalog(n)
            if not nn:
                continue
            best = None
            bestscore = -1
            for (e, cn, sn) in flat:
                if cn not in allowed:
                    continue
                en = _norm_catalog(e["name"])
                if not en:
                    continue
                if nn == en or en in nn or nn in en:
                    score = 0
                    if nn == en:
                        score += 5
                    if hint and hint in sn:
                        score += 10
                    if score > bestscore:
                        bestscore = score
                        best = e
            if best is not None:
                best["articles"].append({"src": sk, "i": i, "name": n})
                used[sk].add(i)

    # 安全网：任何未命中的 gua/rendao/mingli 整体挂载，确保零丢失
    def find_cat(name):
        for c in tree:
            if c["name"] == name:
                return c
        return None
    _fallback = {"gua": "天纪卦象查询", "rendao": "天纪卦象查询", "mingli": "案例查询"}
    for sk in ("gua", "rendao", "mingli"):
        un = [(i, n) for (i, n) in SRC[sk] if i not in used[sk]]
        if un:
            c = find_cat(_fallback[sk])
            if c is not None:
                c["subs"].append({
                    "name": f"{sk}未归类({len(un)})",
                    "entries": [{"name": n,
                                 "articles": [{"src": sk, "i": i, "name": n}]}
                                for i, n in un],
                })

    uncat = [{"src": "lilun", "i": i, "name": n}
             for (i, n) in SRC["lilun"] if i not in used["lilun"]]
    total = sum(len(v) for v in SRC.values())
    return ({"tree": tree, "uncat": {"name": "未归类", "articles": uncat}}, total)


TIANJI_CATALOG, TIANJI_CATALOG_TOTAL = _build_tianji_catalog()


@app.get("/api/tianji/modules")
def api_tianji_modules():
    return tianji_db.modules() + [{
        "key": "catalog", "name": "天纪目录", "kind": "catalog",
        "count": TIANJI_CATALOG_TOTAL,
        "desc": "按理论体系（基础理论 / 断法细则 / 卦象 / 案例）分章节整理的全部天纪内容",
    }]


@app.get("/api/tianji/catalog")
def api_tianji_catalog():
    return TIANJI_CATALOG


@app.get("/api/tianji/tree")
def api_tianji_tree():
    """按 列表.txt 重组的天纪目录树（斗数/断法细则/卦象/子女/时辰效验/案例查询）。
    每个叶子带 src(数据源) 与 idx(序号)，前端点击调用 /api/tianji/item?sub=<src>&i=<idx>。"""
    return {"tree": tianji_tree.TIANJI_TREE}


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
    fn = IMG_INDEX.get("tianji", {}).get(name)
    if not fn:
        raise HTTPException(404, "no image")
    return RedirectResponse("/img/tianji/%s" % fn, status_code=302)


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


@app.get("/api/tianji/mingli_cases")
def api_tianji_mingli_cases():
    """八字命例列表（供排盘系统左侧『命理』面板；点击即排双盘）。"""
    return {"cases": paipan.mingli_cases()}


@app.post("/api/tianji/mingli_chart")
def api_tianji_mingli_chart(payload: dict = Body(default={})):
    """按命例索引重建出生时间，排出八字 + 紫微 + 解读，并附带原版命盘分析。"""
    try:
        i = int(payload.get("i", -1))
        return paipan.mingli_chart(i)
    except ValueError as e:
        raise HTTPException(400, "命例排盘失败：" + str(e))
    except Exception as e:
        raise HTTPException(500, "命例排盘计算失败：" + str(e))


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

# 本地开发：把 public/img 挂载为 /img（Vercel 上由 CDN 静态托管 public/，函数不会收到 /img 请求）。
_IMG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public", "img")
if os.path.isdir(_IMG_DIR):
    app.mount("/img", StaticFiles(directory=_IMG_DIR), name="img_static")
