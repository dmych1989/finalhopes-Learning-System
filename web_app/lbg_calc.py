# -*- coding: utf-8 -*-
"""灵龟八法 / 子午流注 时间计算模块（供 /renji 灵龟八法整页使用）。

对外函数：
  - lbg_compute(y, m, d, h, minute)  -> 干支 + 阴历 + 节气 + 纳子/纳甲/灵龟八法 开穴
  - lbg_calendar(y, m)               -> 当月日历（阳历/阴历/24节气）

干支时通过「五虎遁」手算（cnlunar 仅提供 day8Char/month8Char/year8Char，无 hour8Char）。
节气日期取自 cnlunar「寿星天文历」内嵌的 solar24 表（精确到日）。
"""
import calendar as _cal
import datetime

import cnlunar

import renji_db

TIANGAN = "甲乙丙丁戊己庚辛壬癸"
DIZHI = "子丑寅卯辰巳午未申酉戌亥"

# 日干 -> 当日「子时」的时干起算天干序号（五虎遁：甲己日起甲子）
#   甲己→甲(0)  乙庚→丙(2)  丙辛→戊(4)  丁壬→庚(6)  戊癸→壬(8)
DAY_GAN_ZISHI = {
    "甲": 0, "己": 0, "乙": 2, "庚": 2,
    "丙": 4, "辛": 4, "丁": 6, "壬": 6, "戊": 8, "癸": 8,
}

# 12 时辰 => 地支 + 名称 + 起始小时（子时跨午夜 23:00-00:59）
SHICHEN_RANGES = [
    ("子", "子时", 23, 1), ("丑", "丑时", 1, 3), ("寅", "寅时", 3, 5),
    ("卯", "卯时", 5, 7), ("辰", "辰时", 7, 9), ("巳", "巳时", 9, 11),
    ("午", "午时", 11, 13), ("未", "未时", 13, 15), ("申", "申时", 15, 17),
    ("酉", "酉时", 17, 19), ("戌", "戌时", 19, 21), ("亥", "亥时", 21, 23),
]

# 八法穴（灵龟八法 8 穴）固定配色，供前端 SVG 圆盘使用
BAFA_COLORS = {
    "内关": "#e23b3b", "公孙": "#2f6fed", "足临泣": "#2faf5a",
    "照海": "#f3901f", "列缺": "#8a4fd0", "外关": "#1aa3a3",
    "后溪": "#e0569b", "申脉": "#9c6b3f",
}

# 后天八卦（顺时针自正上方起）对应八法穴（标准灵龟八法配穴）
BAGUA_ORDER = [
    ("离", "列缺06"), ("坤", "后溪32"), ("兑", "足临泣64"), ("乾", "公孙24"),
    ("坎", "申脉42"), ("艮", "内关54"), ("震", "外关61"), ("巽", "照海48"),
]

# 12 地支（顺时针自正上方起）对应时辰序号
DIZHI_ORDER = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 生肖 / 纳音（按 60 甲子序号）
SHENGXIAO = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]
NAYIN_60 = [
    "海中金", "炉中火", "大林木", "路旁土", "剑锋金", "山头火",
    "涧下水", "城头土", "白蜡金", "杨柳木", "泉中水", "大海水",
    "沙中金", "山下火", "平地木", "壁上土", "金箔金", "覆灯火",
    "天河水", "大驿土", "钗钏金", "桑柘木", "大溪水", "沙中土",
    "天上火", "石榴木", "大海水",
]
CYCLE60 = [TIANGAN[i % 10] + DIZHI[i % 12] for i in range(60)]


def shichen_of(hour):
    """返回 (时辰地支, 时辰名)。"""
    if hour == 23 or hour == 0:
        return "子", "子时"
    for zhi, name, h0, h1 in SHICHEN_RANGES[1:]:
        if h0 <= hour < h1:
            return zhi, name
    return "子", "子时"


def gz_hour(day_gan, hour):
    """由日干与小时算「干支时」(2 字)。返回 (干支时, 时辰地支, 时辰名)。"""
    zhi, zhi_name = shichen_of(hour)
    zhi_idx = DIZHI.index(zhi)
    start = DAY_GAN_ZISHI[day_gan]
    gan_idx = (start + zhi_idx) % 10
    return TIANGAN[gan_idx] + zhi, zhi, zhi_name


def _parse_xue(cell):
    """解析八法穴 cell（如 '内关54  '）-> (穴名, 序号)。"""
    cell = (cell or "").strip()
    if not cell:
        return "", ""
    num = "".join(filter(str.isdigit, cell))
    name = "".join(ch for ch in cell if not ch.isdigit()).strip()
    return name, num


def _build_tables(Z):
    najia = Z["najia"]
    nazi = Z["nazi"]
    lingui = Z["lingui"]
    ncols = najia["cols"]
    najia_map = {}
    for row in najia["rows"]:
        rec = {ncols[i]: (row[i] or "").strip() for i in range(len(ncols))}
        najia_map[rec["时辰"]] = rec
    zcols = nazi["cols"]
    nazi_map = {}
    for row in nazi["rows"]:
        rec = {zcols[i]: (row[i] or "").strip() for i in range(len(zcols))}
        nazi_map[rec["时辰"]] = rec
    lcols = lingui["cols"]  # ['时辰','子','丑',...,'亥']
    lingui_map = {}
    for row in lingui["rows"]:
        gzday = (row[0] or "").strip()
        lingui_map[gzday] = {lcols[i]: (row[i] or "").strip() for i in range(len(lcols))}
    return najia_map, nazi_map, lingui_map


def lbg_compute(y, m, d, h, minute=0, Z=None):
    """根据年月日时算出全部开穴数据。

    返回 dict：
      ganzhi: {year, month, day, hour}
      shichen: {zhi, name}
      nazifa:  十二经纳子法（按 时辰 查 najia 表）
      najiafa: 十二经纳甲法（按 日干+时辰 查 nazi 表）
      lingui:  灵龟八法（按 干支日+时辰 查 lingui 表）
      lunar:   阴历信息
    """
    if Z is None:
        Z = renji_db.ZIWU
    najia_map, nazi_map, lingui_map = _build_tables(Z)
    dt = datetime.datetime(y, m, d, h, minute)
    l = cnlunar.Lunar(dt)
    gz_year = l.year8Char
    gz_month = l.month8Char
    gz_day = l.day8Char  # 干支日（2 字）
    day_gan = gz_day[0]
    gz_hr, zhi, zhi_name = gz_hour(day_gan, h)

    # 十二经纳子法（najia 表，按 时辰）
    nj = najia_map.get(zhi, {})
    nazifa = {
        "流经脏腑经络": nj.get("当旺经脉", ""),
        "本穴": nj.get("本穴", ""),
        "源穴": nj.get("原穴", ""),
        "补泄": nj.get("补母穴", ""),
        "开穴": nj.get("泻子穴", ""),
    }

    # 十二经纳甲法（nazi 表，按 日干+时辰）
    nk_key = day_gan + zhi
    nk = nazi_map.get(nk_key, {})
    najiafa = {
        "流注输穴": nk.get("纳子取穴（一）", ""),
        "主经过原": nk.get("纳子取穴（二）", ""),
        "合日互用": nk.get("纳子取穴（三）", ""),
    }

    # 灵龟八法（lingui 表，按 干支日 + 时辰支）
    lg = lingui_map.get(gz_day, {})
    lg_cell = lg.get(zhi, "")
    xue_name, xue_num = _parse_xue(lg_cell)

    return {
        "ganzhi": {"year": gz_year, "month": gz_month, "day": gz_day, "hour": gz_hr},
        "shichen": {"zhi": zhi, "name": zhi_name},
        "nazifa": nazifa,
        "najiafa": najiafa,
        "lingui": {
            "xue": xue_name, "num": xue_num, "raw": lg_cell,
            "ganzhi_day": gz_day, "ganzhi_hour": gz_hr,
        },
        "lunar": {
            "year": l.lunarYear, "month": l.lunarMonth, "day": l.lunarDay,
            "month_cn": l.lunarMonthCn, "day_cn": l.lunarDayCn, "year_cn": l.lunarYearCn,
        },
        "shengxiao": SHENGXIAO[CYCLE60.index(gz_year) % 12],
        "nayin": NAYIN_60[CYCLE60.index(gz_year) // 2 % 26],
    }


def lbg_calendar(y, m):
    """返回当月日历（阳历/阴历/节气）。"""
    l = cnlunar.Lunar(datetime.datetime(y, m, 1))
    terms = l.getSolarTermsDateList(y)  # 24 x (month, day)
    term_names = l.thisYearSolarTermsDic  # name -> (month, day)
    term_dict = {td: name for name, td in term_names.items() if td[0] == m}
    first_wd = _cal.weekday(y, m, 1)  # 0=Mon
    n_days = _cal.monthrange(y, m)[1]
    days = []
    for d in range(1, n_days + 1):
        ll = cnlunar.Lunar(datetime.datetime(y, m, d))
        td = (m, d)
        term = term_dict.get(td, "")
        wd = _cal.weekday(y, m, d)  # 0=Mon
        sun_idx = (wd + 1) % 7  # 0=Sun
        days.append({
            "d": d, "lunar": ll.lunarDayCn,
            "term": term, "weekday": wd, "sun": sun_idx,
        })
    return {
        "year": y, "month": m, "n_days": n_days,
        "first_sun": (first_wd + 1) % 7, "days": days,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(lbg_compute(2026, 8, 9, 20, 30), ensure_ascii=False, indent=2))
    print(json.dumps(lbg_calendar(2026, 8), ensure_ascii=False, indent=2)[:600])
