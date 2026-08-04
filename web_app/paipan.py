# -*- coding: utf-8 -*-
"""排盘聚合 + 命理解读。

聚合三套排盘引擎：
  · bazi.ziwei  → 八字四柱 / 紫微斗数命盘
  · 本命卦       → 梅花易数先天起卦（农历年月日时数）
并基于计算结果，从天纪现有 MDB 知识库（八字命例 / 天纪理论）检索相关内容，
生成格局 / 十神 / 六亲 / 大运 / 命宫主星 的解读草稿。
"""
import datetime

import cnlunar

import bazi
import ziwei
import tianji_db

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


def paipan(solar_dt, gender, birthplace=""):
    if isinstance(solar_dt, str):
        solar_dt = datetime.datetime.strptime(solar_dt, "%Y-%m-%d %H:%M")
    b = bazi.bazi_chart(solar_dt, gender)
    z = ziwei.ziwei_chart(solar_dt, gender)
    g = benming_gua(solar_dt)
    a = analyze(b, z, g)
    return {"bazi": b, "ziwei": z, "gua": g, "analysis": a,
            "birthplace": birthplace}


if __name__ == "__main__":
    import json
    r = paipan(datetime.datetime(1985, 3, 12, 10, 30), "男", "北京")
    print(json.dumps(r, ensure_ascii=False, indent=2)[:2500])
