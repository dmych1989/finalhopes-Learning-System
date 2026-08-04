# -*- coding: utf-8 -*-
"""八字（四柱）排盘引擎。

以 cnlunar 做公历→干支/农历/生肖/节气的基础换算，本模块在其之上补齐：
  · 十神（四柱天干 + 地支本气）
  · 纳音五行（六十甲子纳音，紫微定局也用纳音）
  · 五行强弱（简易评分：得令/得地/得势）
  · 起运与大运（顺逆排，按出生到最近「节」的天数推算起运岁数）
  · 流年（以当前公历年为起点若干年，配十神）

输入：公历 datetime + 性别（'男'/'女'）。输出结构化 dict，供 Web 渲染。
"""
import datetime
from collections import Counter

import cnlunar

GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
WX = ["木", "火", "土", "金", "水"]          # 五行编号：木1 火2 土3 金4 水5
GAN_WX = ["木", "木", "火", "火", "土", "土", "金", "金", "水", "水"]
ZHI_WX = ["水", "土", "木", "木", "土", "火", "火", "土", "金", "金", "土", "水"]
# 地支藏干（本气权重 1.0，中气 0.5，余气 0.3）——用于五行强弱评估
ZHI_CANG = {
    0: [(9, 1.0)],               # 子 癸
    1: [(5, 1.0), (9, 0.5), (7, 0.3)],   # 丑 己癸辛
    2: [(0, 1.0), (2, 0.5), (5, 0.3)],   # 寅 甲丙戊
    3: [(1, 1.0)],               # 卯 乙
    4: [(5, 1.0), (1, 0.5), (9, 0.3)],   # 辰 戊乙癸
    5: [(2, 1.0), (5, 0.5), (7, 0.3)],   # 巳 丙戊庚
    6: [(3, 1.0), (5, 1.0)],     # 午 丁己（丁本气，己中气，简化并列）
    7: [(5, 1.0), (3, 0.5), (1, 0.3)],   # 未 己丁乙
    8: [(7, 1.0), (8, 0.5), (5, 0.3)],   # 申 庚壬戊
    9: [(8, 1.0)],               # 酉 辛
    10: [(5, 1.0), (7, 0.5), (3, 0.3)],  # 戌 戊辛丁
    11: [(8, 1.0), (0, 0.5)],    # 亥 壬甲
}
# 六十甲子纳音（甲子=0 … 癸亥=59）： (纳音名, 五行)
_NAYIN = [
    ("海中金", "金"), ("海中金", "金"), ("炉中火", "火"), ("炉中火", "火"), ("大林木", "木"),
    ("大林木", "木"), ("路旁土", "土"), ("路旁土", "土"), ("剑锋金", "金"), ("剑锋金", "金"),
    ("山头火", "火"), ("山头火", "火"), ("涧下水", "水"), ("涧下水", "水"), ("城头土", "土"),
    ("城头土", "土"), ("白蜡金", "金"), ("白蜡金", "金"), ("杨柳木", "木"), ("杨柳木", "木"),
    ("泉中水", "水"), ("泉中水", "水"), ("屋上土", "土"), ("屋上土", "土"), ("霹雳火", "火"),
    ("霹雳火", "火"), ("松柏木", "木"), ("松柏木", "木"), ("长流水", "水"), ("长流水", "水"),
    ("沙中金", "金"), ("沙中金", "金"), ("山下火", "火"), ("山下火", "火"), ("平地木", "木"),
    ("平地木", "木"), ("壁上土", "土"), ("壁上土", "土"), ("金箔金", "金"), ("金箔金", "金"),
    ("覆灯火", "火"), ("覆灯火", "火"), ("天河水", "水"), ("天河水", "水"), ("大驿土", "土"),
    ("大驿土", "土"), ("钗钏金", "金"), ("钗钏金", "金"), ("桑柘木", "木"), ("桑柘木", "木"),
    ("大溪水", "水"), ("大溪水", "水"), ("沙中土", "土"), ("沙中土", "土"), ("天上火", "火"),
    ("天上火", "火"), ("石榴木", "木"), ("石榴木", "木"), ("大海水", "水"), ("大海水", "水"),
]
# 紫微斗数五行局：纳音五行 → 局名/局数
NAYIN_JU = {"水": ("水二局", 2), "木": ("木三局", 3), "金": ("金四局", 4),
            "土": ("土五局", 5), "火": ("火六局", 6)}

# 十二「节」（月分界）名称（顺序：从小寒所起的丑月开始）
JIE_NAMES = ["小寒", "立春", "惊蛰", "清明", "立夏", "芒种",
             "小暑", "立秋", "白露", "寒露", "立冬", "大雪"]

_SHENG = {0: 4, 1: 0, 2: 1, 3: 2, 4: 3}   # 五行相生：木→火→土→金→水
_KE = {0: 3, 1: 4, 2: 0, 3: 1, 4: 2}       # 五行相克：木克土 火克金 土克水 金克木 水克火


def _gz_index(gz):
    """干支字符串 → 60 甲子序号（甲子=0）。"""
    g = GAN.index(gz[0]); z = ZHI.index(gz[1])
    for i in range(60):
        if i % 10 == g and i % 12 == z:
            return i
    return 0


def _advance(gz, step):
    """干支顺(+)/逆(-)推移 step 步，返回新干支字符串。"""
    i = (_gz_index(gz) + step) % 60
    return GAN[i % 10] + ZHI[i % 12]


def _shishen(other_gan, ri_gan):
    """other 天干相对 日主 的十神。"""
    oe = WX.index(GAN_WX[GAN.index(other_gan)])
    re_ = WX.index(GAN_WX[GAN.index(ri_gan)])
    o_yy = (GAN.index(other_gan) % 2 == 0)   # 阳=True
    r_yy = (GAN.index(ri_gan) % 2 == 0)
    same = (oe == re_)
    if same:
        return "比肩" if o_yy == r_yy else "劫财"
    if _SHENG[re_] == oe:          # 我生
        return "食神" if o_yy == r_yy else "伤官"
    if _SHENG[oe] == re_:          # 生我
        return "偏印" if o_yy == r_yy else "正印"
    if _KE[re_] == oe:             # 我克
        return "偏财" if o_yy == r_yy else "正财"
    if _KE[oe] == re_:             # 克我
        return "七杀" if o_yy == r_yy else "正官"
    return "?"


def _jie_dates(year):
    """返回某年 12 节 的 datetime（date，正午近似）。"""
    l = cnlunar.Lunar(datetime.datetime(year, 1, 1), godType="8char")
    d = l.thisYearSolarTermsDic
    out = {}
    for name in JIE_NAMES:
        if name in d:
            m, day = d[name]
            out[name] = datetime.datetime(year, m, day, 12, 0)
    return out


def _hour_zhi(hour):
    """公历小时 → 时辰地支序号（子=0…亥=11）。"""
    if hour == 23:
        return 0
    return (hour + 1) // 2


def _five_ele_strength(pillars_wx, ri_wx):
    """简易五行强弱：天干(1) + 地支本气(1) + 中余气(0.5/0.3)。"""
    score = 0.0
    for w, wgt in pillars_wx:
        # 天干/本气按 1，中余气按权重已由调用方给出
        score += wgt
        if w == ri_wx:
            pass
    return score


def bazi_chart(solar_dt, gender):
    """返回八字排盘结构化结果。"""
    if isinstance(solar_dt, str):
        solar_dt = datetime.datetime.strptime(solar_dt, "%Y-%m-%d %H:%M")
    l = cnlunar.Lunar(solar_dt, godType="8char")
    y_gz, m_gz, d_gz, h_gz = l.year8Char, l.month8Char, l.day8Char, l.twohour8Char

    # 干支序号 / 五行
    def pillar(gz):
        gi, zi = GAN.index(gz[0]), ZHI.index(gz[1])
        seq = _gz_index(gz)
        nayin, nwx = _NAYIN[seq]
        return {"gz": gz, "gan": gz[0], "zhi": gz[1], "gan_idx": gi,
                "zhi_idx": zi, "gan_wx": GAN_WX[gi], "zhi_wx": ZHI_WX[zi],
                "nayin": nayin, "nayin_wx": nwx}

    yz, mz, rz, sz = pillar(y_gz), pillar(m_gz), pillar(d_gz), pillar(h_gz)
    ri_gan = d_gz[0]
    day_gan_idx = GAN.index(ri_gan)
    ri_wx = GAN_WX[day_gan_idx]

    # 十神（四柱天干 + 地支本气）
    def ten(gz_p):
        return {"gz": gz_p["gz"], "gan": gz_p["gan"], "zhi": gz_p["zhi"],
                "gan_shi": _shishen(gz_p["gan"], ri_gan),
                "zhi_ben_shi": _shishen(GAN[ZHI_CANG[gz_p["zhi_idx"]][0][0]], ri_gan),
                "nayin": gz_p["nayin"]}
    pillars = [ten(yz), ten(mz), ten(rz), ten(sz)]

    # 五行统计（含藏干权重）——用于强弱
    wx_score = {w: 0.0 for w in WX}
    gain = 0.0
    for p in (yz, mz, rz, sz):
        wx_score[p["gan_wx"]] += 1.0
        wx_score[p["zhi_wx"]] += 0.6
        for gi, wgt in ZHI_CANG[p["zhi_idx"]]:
            wx_score[GAN_WX[gi]] += wgt * 0.5
    # 得令：月支生/同 日主
    month_zhi_wx = mz["zhi_wx"]
    de_ling = (_SHENG[WX.index(month_zhi_wx)] == WX.index(ri_wx)) or (month_zhi_wx == ri_wx)
    # 得地：日支或时支同/生
    de_di = (rz["zhi_wx"] == ri_wx) or (_SHENG[WX.index(rz["zhi_wx"])] == WX.index(ri_wx))
    # 得势：天干比劫/印
    bi_yin = sum(1 for p in (yz, mz, sz)
                 if p["gan_wx"] == ri_wx or _SHENG[WX.index(p["gan_wx"])] == WX.index(ri_wx))
    qiang = (de_ling + de_di + (bi_yin >= 2))
    strength = "身强" if qiang >= 2 else ("中和" if qiang == 1 else "身弱")

    # ---------- 大运 ----------
    year_gan_yy = (GAN.index(y_gz[0]) % 2 == 0)
    is_male = (gender == "男")
    shun = (year_gan_yy and is_male) or ((not year_gan_yy) and (not is_male))  # 阳男阴女顺
    # 收集相邻三年节气
    jies = []
    for y in (solar_dt.year - 1, solar_dt.year, solar_dt.year + 1):
        for name, dt in _jie_dates(y).items():
            jies.append((dt, name))
    jies.sort()
    birth = solar_dt
    prev_j = None
    next_j = None
    for dt, name in jies:
        if dt <= birth:
            prev_j = (dt, name)
        if dt > birth and next_j is None:
            next_j = (dt, name)
    if shun and next_j:
        delta = (next_j[0].date() - birth.date()).days
        near = next_j
    elif (not shun) and prev_j:
        delta = (birth.date() - prev_j[0].date()).days
        near = prev_j
    else:
        delta = 0
        near = (birth, "—")
    start_age = delta // 3
    start_mon = (delta % 3) * 4
    # 大运干支：从月柱顺/逆推
    dayun = []
    for k in range(1, 11):
        step = k if shun else -k
        gz = _advance(m_gz, step)
        dayun.append({"age": start_age + k - 1, "gz": gz,
                      "gan_shi": _shishen(gz[0], ri_gan)})

    # ---------- 流年（当前公历年起 10 年）----------
    this_year = datetime.datetime.now().year
    liu = []
    for y in range(this_year, this_year + 10):
        # 年干支 = 公元年 → 干支
        seq = (y - 4) % 60
        gz = GAN[seq % 10] + ZHI[seq % 12]
        liu.append({"year": y, "gz": gz, "gan_shi": _shishen(gz[0], ri_gan)})

    return {
        "solar": solar_dt.strftime("%Y-%m-%d %H:%M"),
        "lunar": "%d年%s%d日" % (l.lunarYear, l.lunarMonthCn, l.lunarDay),
        "zodiac": l.chineseYearZodiac,
        "gender": gender,
        "pillars": pillars,           # [年,月,日,时] 每柱含 十神/纳音
        "ri_gan": ri_gan,
        "ri_wx": ri_wx,
        "wx_score": wx_score,
        "strength": strength,
        "de_ling": de_ling, "de_di": de_di, "bi_yin": bi_yin,
        "dayun": {"start_age": start_age, "start_mon": start_mon, "shun": shun,
                  "near_jie": near[1], "near_days": delta, "list": dayun},
        "liunian": liu,
    }


if __name__ == "__main__":
    import json
    r = bazi_chart(datetime.datetime(1985, 3, 12, 10, 30), "男")
    print(json.dumps(r, ensure_ascii=False, indent=2))
