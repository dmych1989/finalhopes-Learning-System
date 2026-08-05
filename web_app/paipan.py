# -*- coding: utf-8 -*-
"""排盘聚合 + 命理解读。

聚合三套排盘引擎：
  · bazi.ziwei  → 八字四柱 / 紫微斗数命盘
  · 本命卦       → 梅花易数先天起卦（农历年月日时数）
并基于计算结果，从天纪现有 MDB 知识库（八字命例 / 天纪理论）检索相关内容，
生成格局 / 十神 / 六亲 / 大运 / 命宫主星 的解读草稿。
"""
import datetime
import re

import cnlunar

import bazi
import ziwei
import tianji_db
from tianji_db import clean_text, _dec_rtf_str

# 八卦先天数：1乾 2兑 3离 4震 5巽 6坎 7艮 8坤
GUA_NUM_CHAR = {1: "乾", 2: "兑", 3: "离", 4: "震", 5: "巽", 6: "坎", 7: "艮", 8: "坤"}
# 文王卦序：(卦名, 上卦数, 下卦数)
_GUA64 = [
    ("乾", 1, 1), ("坤", 8, 8), ("屯", 6, 4), ("蒙", 7, 6), ("需", 6, 1),
    ("讼", 1, 6), ("师", 8, 6), ("比", 6, 8), ("小畜", 5, 1), ("履", 1, 2),
    ("泰", 8, 1), ("否", 1, 8), ("同人", 1, 3), ("大有", 3, 1), ("谦", 8, 7),
    ("豫", 4, 8), ("随", 2, 4), ("蛊", 7, 5), ("临", 8, 2), ("观", 5, 8),
    ("噬嗑", 3, 4), ("贲", 7, 3), ("剥", 7, 8), ("复", 8, 4), ("无妄", 1, 4),
    ("大畜", 7, 1), ("颐", 7, 4), ("大过", 2, 5), ("坎", 6, 6), ("离", 3, 3),
    ("咸", 2, 7), ("恒", 4, 5), ("遯", 1, 7), ("大壮", 4, 1), ("晋", 3, 8),
    ("明夷", 8, 3), ("家人", 5, 3), ("睽", 3, 2), ("蹇", 6, 7), ("解", 4, 6),
    ("损", 7, 2), ("益", 5, 4), ("夬", 2, 1), ("姤", 1, 5), ("萃", 2, 8),
    ("升", 8, 5), ("困", 2, 6), ("井", 6, 5), ("革", 2, 3), ("鼎", 3, 5),
    ("震", 4, 4), ("艮", 7, 7), ("渐", 5, 7), ("归妹", 4, 2), ("丰", 4, 3),
    ("旅", 3, 7), ("巽", 5, 5), ("兑", 2, 2), ("涣", 5, 6), ("节", 6, 2),
    ("中孚", 5, 2), ("小过", 4, 7), ("既济", 6, 3), ("未济", 3, 6),
]
GUA64_BY = {(s, x): n for n, s, x in _GUA64}
# 三爻(阳=1) → 先天卦数
_THREE = {0: 8, 1: 4, 2: 6, 3: 2, 4: 7, 5: 5, 6: 3, 7: 1}


def _shang_xia_to_num(shang3, xia3):
    return GUA64_BY.get((_THREE[shang3], _THREE[xia3]), "未知")


def benming_gua(solar_dt):
    """梅花易数先天本命卦：农历年月日时数起卦。"""
    if isinstance(solar_dt, str):
        solar_dt = datetime.datetime.strptime(solar_dt, "%Y-%m-%d %H:%M")
    l = cnlunar.Lunar(solar_dt, godType="8char")
    ly, lm, ld = l.lunarYear, l.lunarMonth, l.lunarDay
    lh = bazi._hour_zhi(solar_dt.hour) + 1     # 子1…亥12
    total = ly + lm + ld + lh
    up = (ly + lm + ld) % 8 or 8
    down = total % 8 or 8
    dong = total % 6 or 6                       # 动爻 1..6（初→上）
    ben = GUA64_BY.get((up, down), "未知")
    # 变卦：把动爻（从初爻起，位 dong-1）阴阳翻转
    # 先把卦数(1-8)还原成三爻二进制(0-7)，再翻转动爻位
    THREE_INV = {v: k for k, v in _THREE.items()}
    upper = THREE_INV[up]
    lower = THREE_INV[down]
    bits = ((upper & 7) << 3) | (lower & 7)     # 6-bit，初爻 LSB
    bits ^= (1 << (dong - 1))
    new_up = (bits >> 3) & 7
    new_low = bits & 7
    bian = _shang_xia_to_num(new_up, new_low)
    return {
        "ben": ben, "bian": bian, "dong_yao": dong,
        "up": GUA_NUM_CHAR[up], "down": GUA_NUM_CHAR[down],
        "lunar": "%d年%d月%d日 时辰%d" % (ly, lm, ld, lh),
        "method": "梅花易数先天卦（农历年月日时数）",
    }


def _related_cases(ri_gan, limit=6):
    """从八字命例中检索日干相同者。"""
    out = []
    for it in tianji_db.MINGLI:
        raw = it.get("raw", {})
        rz = (raw.get("RZ") or "")
        rz = rz[0] if rz else ""
        if rz == ri_gan:
            zhu = " ".join([str(raw.get(k) or "") for k in ("NZ", "YZ", "RZ", "SZ")])
            yc = tianji_db._dec_rtf_str(raw.get("YCNR"))
            out.append({"name": it["name"], "zhu": zhu,
                        "snippet": yc[:120]})
        if len(out) >= limit:
            break
    return out


def _related_lilun(ri_wx, limit=8):
    """从天纪理论中检索与日主五行 / 紫微 / 命宫相关的篇目。"""
    keys = [ri_wx, "紫微", "命宫", "格局", "五行", "身强", "身弱", "十神"]
    out = []
    for it in tianji_db.LILUN:
        nm = it["name"]
        if any(k in nm for k in keys):
            out.append({"name": nm})
        if len(out) >= limit:
            break
    return out


def analyze(b, z, g):
    """基于八字/紫微/本命卦生成解读草稿。"""
    ri_gan = b["ri_gan"]
    ri_wx = b["ri_wx"]
    # 十神汇总
    shishen = [p["gan_shi"] for p in b["pillars"]]
    # 六亲（以日干为我，按性别取向）
    liuqin = []
    gender = b["gender"]
    for p, label in zip(b["pillars"], ["年干", "月干", "日干(我)", "时干"]):
        if label.startswith("日"):
            continue
        ss = p["gan_shi"]
        meaning = _liuqin_mean(ss, gender)
        liuqin.append({"from": label, "gan": p["gan"], "shi": ss, "meaning": meaning})

    # 命宫主星 + 四化
    ming_stars = []
    for pal in z["palace"]:
        if pal["gong"] == "命宫":
            ming_stars = [s["name"] + (("·" + s["sihua"]) if s["sihua"] else "")
                          for s in pal["stars"]]
            break
    sihua = z["sihua"]

    cases = _related_cases(ri_gan)
    lilun = _related_lilun(ri_wx)

    pattern = ("%s日主，%s（%s），生于%s月，五行分布：木%.1f 火%.1f 土%.1f 金%.1f 水%.1f。"
               % (ri_gan, b["strength"], ri_wx + "命",
                  b["pillars"][1]["zhi"], b["wx_score"]["木"], b["wx_score"]["火"],
                  b["wx_score"]["土"], b["wx_score"]["金"], b["wx_score"]["水"]))

    return {
        "day_master": ri_gan + "（" + ri_wx + "）",
        "strength": b["strength"],
        "pattern": pattern,
        "shishen": shishen,
        "liuqin": liuqin,
        "ming_gong_stars": ming_stars,
        "sihua": sihua,
        "dayun_note": ("%s，%s排大运，%d岁%d个月起运（近%s，相距%d天）。"
                       % (z["ju"], "顺" if b["dayun"]["shun"] else "逆",
                          b["dayun"]["start_age"], b["dayun"]["start_mon"],
                          b["dayun"]["near_jie"], b["dayun"]["near_days"])),
        "benming_gua": g,
        "related_cases": cases,
        "related_lilun": lilun,
    }


def _liuqin_mean(ss, gender):
    """十神 → 六亲含义（按性别取向）。"""
    m = {
        "正官": "女命夫星 / 男命女儿星",
        "七杀": "女命偏夫(情人) / 男命儿子星",
        "正财": "男命妻星 / 财源",
        "偏财": "父星 / 男命外财",
        "正印": "母星 / 荫护",
        "偏印": "继母 / 偏荫",
        "比肩": "兄弟(同) / 朋友",
        "劫财": "姐妹(异) / 同辈",
        "食神": "女命女儿星 / 福气",
        "伤官": "女命儿子星 / 才华",
    }
    note = m.get(ss, "")
    if gender == "女" and ss in ("正财", "偏财"):
        note += "（女命财亦为父象）"
    return note


# ---- EXE 逆向：紫微斗数·局 查表（天纪权威落宫数据）-----------------------------
def _load_ju_table():
    """从 tianji_db.ZIWEI（ziweibiao 表）构建 {局名: {农历日: 地支序}}。"""
    try:
        src = tianji_db.ZIWEI
        tb = src.get("ziweibiao", {})
        cols = tb.get("cols", [])
        rows = tb.get("rows", [])
        ju = {}
        for r in rows:
            name = r[0]
            m = {}
            for i in range(1, len(cols)):
                try:
                    m[i] = int(r[i])
                except (ValueError, TypeError):
                    pass
            if m:
                ju[name] = m
        return ju
    except Exception:
        return {}


JU_TABLE = _load_ju_table()


# ---- 八字命例（MINGLI）归一化与点击排盘 --------------------------------------
_ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]


def _mingli_fields(rec):
    """归一化命例记录（兼容 SQLite fields 与 mdb raw 两种结构）。"""
    if "fields" in rec:
        f = rec["fields"]
        return {
            "name": rec.get("name", ""),
            "gender_raw": f.get("性别", "") or "",
            "pillars": f.get("四柱（干支）", "") or f.get("四柱", "") or "",
            "birth": f.get("生辰", "") or "",
            "birthplace": f.get("出生地", "") or "",
            "analysis": f.get("命盘分析", "") or "",
        }
    r = rec.get("raw", {})
    def g(k):
        v = r.get(k, "")
        return clean_text(str(v)) if v is not None else ""
    zhu = "　".join(["年柱 " + g("NZ"), "月柱 " + g("YZ"),
                     "日柱 " + g("RZ"), "时柱 " + g("SZ")])
    birth = "　".join(["生年 " + g("NN"), "月 " + g("YY"),
                       "日 " + g("RR"), "时 " + g("FF")])
    return {
        "name": rec.get("name", "") or g("XM"),
        "gender_raw": g("XB"),
        "pillars": zhu,
        "birth": birth,
        "birthplace": g("CSD"),
        "analysis": _dec_rtf_str(r.get("YCNR")),
    }


def _mingli_dt(f):
    """由『生辰 + 时柱』重建阳历 datetime（生辰为阳历，已验证 103/107 还原四柱一致）。"""
    m = re.search(r"时柱\s*([甲乙丙丁戊己庚辛壬癸])([子丑寅卯辰巳午未申酉戌亥])",
                  f["pillars"])
    if not m:
        raise ValueError("命例缺少时柱，无法排盘")
    sz_zhi = _ZHI.index(m.group(2))
    hour = sz_zhi * 2                      # 时辰中点（子0/丑2/…/亥22）
    y = re.search(r"生年\s*(\d+)", f["birth"])
    mo = re.search(r"月\s*(\d+)", f["birth"])
    d = re.search(r"日\s*(\d+)", f["birth"])
    hm = re.search(r"时\s*(\d+)", f["birth"])
    if not (y and mo and d):
        raise ValueError("命例缺少生辰")
    minute = int(hm.group(1)) if (hm and 0 <= int(hm.group(1)) <= 59) else 0
    return datetime.datetime(int(y.group(1)), int(mo.group(1)),
                             int(d.group(1)), hour, minute)


def mingli_cases():
    """命例列表（供左侧『命理』面板）。"""
    out = []
    for i, rec in enumerate(tianji_db.MINGLI):
        f = _mingli_fields(rec)
        gender = "男" if "乾" in f["gender_raw"] else "女"
        out.append({
            "i": i, "name": f["name"], "gender": gender,
            "birth": f["birth"], "pillars": f["pillars"],
            "birthplace": f["birthplace"],
            "has_analysis": bool(f["analysis"] and len(f["analysis"]) > 10),
        })
    return out


def mingli_chart(i):
    """按命例索引直接排出八字 + 紫微 + 解读，并附带原版命盘分析文本。"""
    recs = tianji_db.MINGLI
    if i < 0 or i >= len(recs):
        raise ValueError("命例索引越界")
    f = _mingli_fields(recs[i])
    gender = "男" if "乾" in f["gender_raw"] else "女"
    dt = _mingli_dt(f)
    res = paipan(dt, gender, f["birthplace"])
    res["case"] = {
        "name": f["name"], "gender": gender, "birth": f["birth"],
        "pillars": f["pillars"], "birthplace": f["birthplace"],
        "original_analysis": f["analysis"],
    }
    res["solar_used"] = dt.strftime("%Y-%m-%d %H:%M")
    return res


def paipan(solar_dt, gender, birthplace=""):
    if isinstance(solar_dt, str):
        solar_dt = datetime.datetime.strptime(solar_dt, "%Y-%m-%d %H:%M")
    b = bazi.bazi_chart(solar_dt, gender)
    z = ziwei.ziwei_chart(solar_dt, gender, ju_table=JU_TABLE)
    g = benming_gua(solar_dt)
    a = analyze(b, z, g)
    return {"bazi": b, "ziwei": z, "gua": g, "analysis": a,
            "birthplace": birthplace}


if __name__ == "__main__":
    import json
    r = paipan(datetime.datetime(1985, 3, 12, 10, 30), "男", "北京")
    print(json.dumps(r, ensure_ascii=False, indent=2)[:2500])
