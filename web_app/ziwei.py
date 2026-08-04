# -*- coding: utf-8 -*-
"""紫微斗数排盘引擎（纯组合规则，无天文依赖）。

采用传统中州派通用安星法：
  · 命宫：寅宫起正月，顺数至生月，逆数至生时。
  · 身宫：寅宫起正月，顺数至生月，顺数至生时。
  · 五行局：命宫干支纳音五行 → 水二/木三/金四/土五/火六。
  · 紫微星：生日数顺数局数定落宫。
  · 十四主星：紫微星系（逆）与天府星系（顺）固定相对位置。
  · 十二宫：命宫起逆时针排宫名；每宫汇总统辖主星。
  · 四化：依生年天干定禄权科忌。
  · 大限：依五行局数从命宫顺/逆排（阳男阴女顺）。

说明：紫微斗数流派繁多（北派/中州派/三合派），本引擎实现最通用的「三合派」
安星规则，用于学习排盘演示；与倪师原版若有流派差异，以原版为准。
"""
import datetime

import cnlunar

from bazi import (GAN, ZHI, WX, GAN_WX, ZHI_WX, _gz_index, _advance,
                  _NAYIN, NAYIN_JU, _hour_zhi)

# 十二宫名（命宫起逆时针）
GONG_NAMES = ["命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄", "迁移", "交友",
              "官禄", "田宅", "福德", "父母"]

# 紫微星系：相对于紫微的「逆数」宫数（紫微所在宫不含）
ZIWEI_XING = {
    "紫微": 0, "天机": -1, "太阳": -3, "武曲": -4, "天同": -5, "廉贞": -8,
}
# 天府星系：相对于天府的「顺数」宫数（天府所在宫不含）
TIANFU_XING = {
    "天府": 0, "太阴": 1, "贪狼": 2, "巨门": 3, "天相": 4, "天梁": 5,
    "七杀": 6, "破军": 10,
}
# 天府落宫由紫微落宫决定（紫微地支序 → 天府地支序）
TIANFU_BY_ZIWEI = {0: 0, 1: 11, 2: 2, 3: 1, 4: 0, 5: 9, 6: 8, 7: 7,
                    8: 8, 9: 6, 10: 4, 11: 5}
# 五虎遁：年干序 → 寅月天干序
WUHU_DUN = {0: 2, 1: 4, 2: 6, 3: 8, 4: 0, 5: 2, 6: 4, 7: 6, 8: 8, 9: 0}

# 十四主星简义（用于命理解读与悬浮提示）
STAR_MEANING = {
    "紫微": "北斗帝星，主尊贵、领导、权柄。",
    "天机": "智谋之星，主思辨、机变、谋略。",
    "太阳": "官禄主，主光明、名声、父兄。",
    "武曲": "财星，主财富、刚毅、行动力。",
    "天同": "福德主，主福气、安逸、和缓。",
    "廉贞": "次桃花，主权柄、才艺、情绪。",
    "天府": "南斗库星，主财富、守成、稳重。",
    "太阴": "财星，主内敛、情感、母妻。",
    "贪狼": "桃花星，主欲望、交际、才艺。",
    "巨门": "口舌星，主是非、洞察、口才。",
    "天相": "印星，主协调、服务、掌印。",
    "天梁": "荫星，主解厄、长辈、学术。",
    "七杀": "将星，主开创、决断、孤克。",
    "破军": "先锋星，主破耗、变革、波折。",
}
# 四化：生年天干 → {禄,权,科,忌} 主星
SIHUA = {
    "甲": ("廉贞", "破军", "武曲", "太阳"),
    "乙": ("天机", "天梁", "紫微", "太阴"),
    "丙": ("天同", "天机", "文昌", "廉贞"),
    "丁": ("太阴", "天同", "天机", "巨门"),
    "戊": ("贪狼", "太阴", "右弼", "天机"),
    "己": ("武曲", "贪狼", "天梁", "文曲"),
    "庚": ("太阳", "武曲", "太阴", "天同"),
    "辛": ("巨门", "太阳", "文曲", "文昌"),
    "壬": ("天梁", "紫微", "左辅", "武曲"),
    "癸": ("破军", "巨门", "太阴", "贪狼"),
}


def _zhi_at(base_zhi_idx, offset):
    """地支序 base 顺/逆 offset（负=逆），返回地支序。"""
    return (base_zhi_idx + offset) % 12


def ziwei_chart(solar_dt, gender):
    if isinstance(solar_dt, str):
        solar_dt = datetime.datetime.strptime(solar_dt, "%Y-%m-%d %H:%M")
    l = cnlunar.Lunar(solar_dt, godType="8char")
    year_gz = l.year8Char
    month_gz = l.month8Char
    lunar_day = l.lunarDay

    year_gan_idx = GAN.index(year_gz[0])
    month_zhi_idx = ZHI.index(month_gz[1])
    hour_zhi_idx = _hour_zhi(solar_dt.hour)

    # 命宫 / 身宫（寅坐标：寅=0…丑=11）
    mb = (month_zhi_idx - 2) % 12             # 生月宫（寅坐标）
    hour_h = hour_zhi_idx
    ming = (mb - (hour_h + 1)) % 12           # 命宫（寅坐标）
    shen = (mb + (hour_h + 1)) % 12           # 身宫（寅坐标）
    ming_zhi = (2 + ming) % 12                # 地支序
    shen_zhi = (2 + shen) % 12

    # 命宫天干（五虎遁）
    ming_gan = (WUHU_DUN[year_gan_idx] + ming) % 10
    ming_gz = GAN[ming_gan] + ZHI[ming_zhi]

    # 五行局
    seq = _gz_index(ming_gz)
    nayin_wx = _NAYIN[seq][1]
    ju_name, ju_num = NAYIN_JU[nayin_wx]

    # 紫微落宫（寅坐标）：生日数顺数局数
    ziwei_step = (lunar_day - 1) % ju_num
    ziwei_zhi = (2 + ziwei_step) % 12

    # 十四主星落宫
    star_zhi = {}
    for name, off in ZIWEI_XING.items():
        star_zhi[name] = _zhi_at(ziwei_zhi, off)
    tf_zhi = TIANFU_BY_ZIWEI[ziwei_zhi]
    for name, off in TIANFU_XING.items():
        star_zhi[name] = _zhi_at(tf_zhi, off)

    # 十二宫：命宫起逆时针排宫名（宫名 i 在 地支 (ming_zhi - i) % 12）
    gong_by_zhi = {}     # 地支序 → [宫名]
    gong_order = {}      # 地支序 → 宫名（主，命宫优先）
    for i, gname in enumerate(GONG_NAMES):
        z = (ming_zhi - i) % 12
        gong_order[z] = gname

    # 每宫主星
    palace = {}          # 地支序 → {gong, zhi, stars:[{name, sihua}]}
    for z in range(12):
        palace[z] = {"zhi": ZHI[z], "gong": gong_order.get(z, ""),
                     "stars": []}
    # 四化映射（仅限主星）
    sihua_tuple = SIHUA.get(year_gz[0], ("", "", "", ""))
    sihua_map = {}
    for k, nm in zip(("禄", "权", "科", "忌"), sihua_tuple):
        if nm in STAR_MEANING:
            sihua_map[nm] = k
    for name, z in star_zhi.items():
        palace[z]["stars"].append({"name": name,
                                   "sihua": sihua_map.get(name, "")})
    # 排序：主星按固定顺序
    star_rank = {s: i for i, s in enumerate(
        ["紫微", "天机", "太阳", "武曲", "天同", "廉贞", "天府", "太阴",
         "贪狼", "巨门", "天相", "天梁", "七杀", "破军"])}
    for z in palace:
        palace[z]["stars"].sort(key=lambda s: star_rank.get(s["name"], 99))

    # 大限（紫微大运）：从命宫起，依阴阳顺逆，每限管局数年
    yinyang_yang = (year_gan_idx % 2 == 0)
    is_male = (gender == "男")
    shun = (yinyang_yang and is_male) or ((not yinyang_yang) and (not is_male))
    dayun = []
    for i in range(12):
        z = ((ming_zhi - i) if shun else (ming_zhi + i)) % 12
        age0 = i * ju_num
        dayun.append({"idx": i, "gong": gong_order.get(z, ""),
                      "zhi": ZHI[z], "age0": age0, "age1": age0 + ju_num - 1,
                      "shun": shun})

    return {
        "solar": solar_dt.strftime("%Y-%m-%d %H:%M"),
        "gender": gender,
        "ming_gong": {"zhi": ZHI[ming_zhi], "gz": ming_gz,
                      "gan": GAN[ming_gan], "nayin": _NAYIN[seq][0]},
        "shen_gong": {"zhi": ZHI[shen_zhi]},
        "ju": ju_name,
        "ju_num": ju_num,
        "ziwei_zhi": ZHI[ziwei_zhi],
        "palace": [palace[z] for z in range(12)],   # 顺序按地支 子..亥
        "star_zhi": {k: ZHI[v] for k, v in star_zhi.items()},
        "sihua": {"禄": sihua_tuple[0], "权": sihua_tuple[1],
                  "科": sihua_tuple[2], "忌": sihua_tuple[3]},
        "dayun": dayun,
    }


if __name__ == "__main__":
    import json
    r = ziwei_chart(datetime.datetime(1985, 3, 12, 10, 30), "男")
    print(json.dumps(r, ensure_ascii=False, indent=2))
