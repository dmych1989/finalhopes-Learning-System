# -*- coding: utf-8 -*-
"""人纪「云端算法」模块：干支/万年历/四柱、子午流注盘、灵龟八法（代数法）。

设计目标：把原先在前端浏览器本地执行的推算逻辑全部搬到服务端，
浏览器只负责渲染（不再携带算法）。公式与前端 js_src 原实现逐字一致，
保证口径/结果不变。

对外函数：
  - wanianli(y, m, d)                -> 年/月/日柱 + 生肖 + 日干支序
  - lingui_alg(y, m, d, h, mi, gender) -> 灵龟八法「代数法」实时开穴（含算式明细）
  - tool_compute(tool, y, m, d, hb)  -> 子午流注盘 / 圆形灵龟盘（四柱 + 开穴 + 纳子 + 纳甲）
  - hour_branch(h)                   -> 小时 -> 时辰支序(0..11)
"""
import datetime

GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
SHENGXIAO = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]

# ---- 万年历 / 四柱（原 renji_app.js 80-125 的等价实现） ----
# 节气近似（用于定月柱起点）：寅月起，各「节」的公历月-日
SOLAR = [[2, 4], [3, 6], [4, 5], [5, 6], [6, 6], [7, 7],
         [8, 8], [9, 8], [10, 8], [11, 7], [12, 7], [1, 6]]


def year_gz(y):
    return GAN[((y - 4) % 10 + 10) % 10] + ZHI[((y - 4) % 12 + 12) % 12]


def _jdn(y, m, d):
    a = (14 - m) // 12
    yy = y + 4800 - a
    mm = m + 12 * a - 3
    return (d + (153 * mm + 2) // 5 + 365 * yy + yy // 4
            - yy // 100 + yy // 400 - 32045)


def day_gz(y, m, d):
    j = _jdn(y, m, d)
    idx = ((j + 49) % 60 + 60) % 60
    return {"idx": idx, "g": idx % 10, "z": idx % 12,
            "str": GAN[idx % 10] + ZHI[idx % 12]}


def _month_index(y, m, d):
    for i in range(12):
        sm, sd = SOLAR[i]
        if m == sm and d >= sd:
            return i
        if i > 0 and m == SOLAR[i - 1][0] and d >= SOLAR[i - 1][1] and d < sd:
            return i - 1
    if m == 1 and d < 6:
        return 11
    return 0


def month_gz(y, m, d):
    mi = _month_index(y, m, d)
    ys = ((y - 4) % 10 + 10) % 10
    base = (ys * 2 + 2) % 10
    return {"str": GAN[(base + mi) % 10] + ZHI[(2 + mi) % 12], "mi": mi}


def hour_branch(h):
    return ((h + 1) % 24) // 2


def hour_gz(h, day_g):
    b = hour_branch(h)
    base = (day_g * 2) % 10
    return {"str": GAN[(base + b) % 10] + ZHI[b], "b": b}


def hour_gz_b(day_g, b):
    """按「时辰支序（0=子）」直接取时柱干支（供工具盘使用）。"""
    base = (day_g * 2) % 10
    return GAN[(base + b) % 10] + ZHI[b]


def wanianli(y, m, d):
    dg = day_gz(y, m, d)
    return {"year": year_gz(y), "month": month_gz(y, m, d)["str"], "day": dg["str"],
            "shengxiao": SHENGXIAO[dg["z"]], "day_idx": dg["idx"]}


# ---- 灵龟八法「代数法」（原 app.js 859-898 的等价实现） ----
LG_DAY_GAN = {"甲": 10, "己": 10, "乙": 9, "庚": 9, "丁": 8, "壬": 8,
              "戊": 7, "癸": 7, "丙": 7, "辛": 7}
LG_DAY_ZHI = {"辰": 10, "戌": 10, "丑": 10, "未": 10, "申": 9, "酉": 9,
              "寅": 8, "卯": 8, "子": 7, "巳": 7, "午": 7, "亥": 7}
LG_HOUR_GAN = {"甲": 9, "己": 9, "乙": 8, "庚": 8, "丙": 7, "辛": 7,
               "丁": 6, "壬": 6, "戊": 5, "癸": 5}
LG_HOUR_ZHI = {"子": 9, "午": 9, "丑": 8, "未": 8, "寅": 7, "申": 7,
               "卯": 6, "酉": 6, "辰": 5, "戌": 5, "巳": 4, "亥": 4}
LG_REM2ACU = {1: "申脉", 2: "照海", 3: "外关", 4: "足临泣",
              5: "照海", 6: "公孙", 7: "后溪", 8: "内关", 9: "列缺"}
LG_HOUR_DESC = {"子": "23:00-1:00", "丑": "1:00-3:00", "寅": "3:00-5:00",
                "卯": "5:00-7:00", "辰": "7:00-9:00", "巳": "9:00-11:00",
                "午": "11:00-13:00", "未": "13:00-15:00", "申": "15:00-17:00",
                "酉": "17:00-19:00", "戌": "19:00-21:00", "亥": "21:00-23:00"}
_YANG_GAN = ("甲", "丙", "戊", "庚", "壬")


def lingui_alg(y, m, d, h, mi=0, gender="男"):
    dg = day_gz(y, m, d)
    hz_idx = hour_branch(h)
    hz = ZHI[hz_idx]
    hg_gan = hour_gz(h, dg["g"])["str"][0]
    total = (LG_DAY_GAN[dg["str"][0]] + LG_DAY_ZHI[dg["str"][1]]
             + LG_HOUR_GAN[hg_gan] + LG_HOUR_ZHI[hz])
    yang = dg["str"][0] in _YANG_GAN
    div = 9 if yang else 6
    rem = total % div
    if rem == 0:
        rem = 9 if yang else 6
    acu = LG_REM2ACU[rem]
    if rem == 5:
        acu = "内关" if gender == "女" else "照海"
    return {
        "y": y, "m": m, "d": d, "h": h, "mi": mi, "gender": gender,
        "day": {"gan": dg["str"][0], "zhi": dg["str"][1], "yang": yang,
                "gan_val": LG_DAY_GAN[dg["str"][0]], "zhi_val": LG_DAY_ZHI[dg["str"][1]]},
        "hour": {"gan": hg_gan, "zhi": hz,
                 "gan_val": LG_HOUR_GAN[hg_gan], "zhi_val": LG_HOUR_ZHI[hz]},
        "hour_range": LG_HOUR_DESC[hz],
        "sum": total, "div": div, "rem": rem, "acu": acu,
    }


# ---- 九宫配穴（灵龟八法 洛书） ----
JIUGONG = {1: ["申脉"], 2: ["照海"], 3: ["外关"], 4: ["临泣"],
           6: ["公孙"], 7: ["后溪"], 8: ["内关"], 9: ["列缺"]}


def acupoint_gong(name):
    if not name:
        return 0
    for g in range(1, 10):
        if g == 5:
            continue
        for a in JIUGONG.get(g, []):
            if a in name:
                return g
    return 0


# ---- 工具盘：子午流注盘 / 圆形灵龟盘（原 renji_app.js 431-523 的等价实现） ----
def _ziwu():
    import renji_db
    try:
        renji_db._ensure_renji()
    except Exception:
        pass
    return renji_db.ZIWU


def _find_row(rows, key_idx, key):
    for r in rows:
        if (r[key_idx] or "").strip() == key:
            return r
    return None


def tool_compute(tool, y, m, d, hb):
    Z = _ziwu()
    dg = day_gz(y, m, d)
    hg = hour_gz_b(dg["g"], hb)
    pillars = {"year": year_gz(y), "month": month_gz(y, m, d)["str"],
               "day": dg["str"], "hour": hg}

    out = {"tool": tool, "y": y, "m": m, "d": d, "hb": hb, "pillars": pillars}

    if tool == "lingui_dial":
        t = Z.get("lingui", {})
        row = _find_row(t.get("rows", []), 0, dg["str"])
        open_ling = ((row[1 + hb] if row and len(row) > 1 + hb else "") or "").strip()
        out["lingui"] = {"xue": open_ling, "gong": acupoint_gong(open_ling)}
        return out

    # ziwwu_pan：灵龟开穴 + 纳子取穴 + 纳甲当旺
    lg = Z.get("lingui", {})
    row = _find_row(lg.get("rows", []), 0, dg["str"])
    open_ling = ((row[1 + hb] if row and len(row) > 1 + hb else "") or "").strip()

    nz_key = dg["str"][0] + ZHI[hb]
    nz = _find_row(Z.get("nazi", {}).get("rows", []), 0, nz_key) or ["", "", "", ""]
    out["lingui"] = {"xue": open_ling, "gong": acupoint_gong(open_ling)}
    out["nazi"] = {"key": nz_key,
                   "items": [(nz[1] or "").strip(), (nz[2] or "").strip(), (nz[3] or "").strip()]}
    naj = _find_row(Z.get("najia", {}).get("rows", []), 0, ZHI[hb]) or []
    out["najia"] = {"zhi": ZHI[hb],
                    "mai": ((naj[1] if len(naj) > 1 else "") or "").strip(),
                    "ben": ((naj[4] if len(naj) > 4 else "") or "").strip(),
                    "yuan": ((naj[5] if len(naj) > 5 else "") or "").strip()}
    return out


def now_tool_defaults():
    """服务端当前日期 + 时辰支序（供前端初始化工具盘下拉框）。"""
    n = datetime.datetime.now()
    return n.year, n.month, n.day, hour_branch(n.hour)
