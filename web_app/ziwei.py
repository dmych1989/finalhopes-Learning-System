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
# 天府落宫由紫微落宫决定（紫微地支序 → 天府地支序）。
# 修正：原表多项错误；正确对照（寅/申 紫府同宫；子→辰、丑→卯、卯→丑、辰→子、
# 巳→亥、午→戌、未→酉、酉→未、戌→午、亥→巳）。
TIANFU_BY_ZIWEI = {0: 4, 1: 3, 2: 2, 3: 1, 4: 0, 5: 11, 6: 10, 7: 8,
                    8: 8, 9: 7, 10: 6, 11: 5}
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

# ===========================================================================
# 辅星 / 杂曜 安星规则（标准紫微斗数安星诀；以 iztro 真值校验对齐）
# 地支序：子0 丑1 寅2 卯3 辰4 巳5 午6 未7 申8 酉9 戌10 亥11
# 天干序：甲0 乙1 丙2 丁3 戊4 己5 庚6 辛7 壬8 癸9
# kind: "major" 主星 | "minor" 辅星 | "adjective" 杂曜
# ===========================================================================

# 天魁（阳贵）/ 天钺（阴贵）：年干 → 地支序
TIANKUI = {0: 1, 1: 0, 2: 11, 3: 11, 4: 1, 5: 0, 6: 1, 7: 6, 8: 3, 9: 3}
TIANYUE = {0: 7, 1: 8, 2: 9, 3: 9, 4: 7, 5: 8, 6: 7, 7: 2, 8: 5, 9: 5}

# 禄存：年干 → 地支序
LUCOUNT = {0: 2, 1: 3, 2: 5, 3: 6, 4: 5, 5: 6, 6: 8, 7: 9, 8: 11, 9: 0}

# 年支三合分组：0=申子辰 1=寅午戌 2=亥卯未 3=巳酉丑
SANHE = {0: 0, 8: 0, 4: 0, 2: 1, 6: 1, 10: 1, 3: 2, 7: 2, 11: 2, 5: 3, 9: 3, 1: 3}
# 天马（四马地）：三合组 → 地支序
TIANMA_BASE = {0: 2, 1: 8, 2: 5, 3: 11}
# 咸池：年支 → 地支序（败地）
XIANCHI = {0: 9, 8: 9, 4: 9, 2: 3, 6: 3, 10: 3, 3: 0, 7: 0, 11: 0, 5: 6, 9: 6, 1: 6}
# 华盖：年支 → 地支序
HUAGAI = {0: 4, 8: 4, 4: 4, 2: 10, 6: 10, 10: 10, 3: 7, 7: 7, 11: 7, 5: 1, 9: 1, 1: 1}
# 孤辰：年支 → 地支序（寅卯辰→巳5；巳午未→申8；申酉戌→亥11；亥子丑→寅2）
GUCHEN = {0: 2, 1: 2, 2: 5, 3: 5, 4: 5, 5: 8, 6: 8, 7: 8, 8: 11, 9: 11, 10: 11, 11: 2}
# 寡宿：年支 → 地支序（寅卯辰→丑1；巳午未→辰4；申酉戌→未7；亥子丑→戌10）
GUASU = {0: 10, 1: 10, 2: 1, 3: 1, 4: 1, 5: 4, 6: 4, 7: 4, 8: 7, 9: 7, 10: 7, 11: 10}
# 火星 / 铃星 base：三合组 → 地支序（起子时顺数至生时）
HUOXING_BASE = {0: 2, 1: 1, 2: 9, 3: 3}
LINGXING_BASE = {0: 10, 1: 3, 2: 10, 3: 10}


def aux_stars(year_gan_idx, year_zhi_idx, lunar_month, hour_zhi_idx, ming_zhi_idx):
    """计算辅星与杂曜落宫，返回 [(name, zhi_index, kind), ...]。

    lunar_month: 农历月序（1-12，闰月取同序数）；hour_zhi_idx: 时辰地支序。
    """
    g, z, m, h = year_gan_idx, year_zhi_idx, lunar_month, hour_zhi_idx
    sh = SANHE[z]
    luc = LUCOUNT[g]
    out = []
    # ---- 辅星（14）----
    # 左辅：辰宫(4)起正月顺数至生月；右弼：戌宫(10)起正月逆数
    out.append(("左辅", (4 + m - 1) % 12, "minor"))
    out.append(("右弼", (11 - m) % 12, "minor"))
    # 文昌：随时辰逆数（子时亥宫）；文曲：随时辰顺数（子时卯宫）
    out.append(("文昌", (10 - h) % 12, "minor"))
    out.append(("文曲", (h + 4) % 12, "minor"))
    # 天魁 / 天钺：年干
    out.append(("天魁", TIANKUI[g], "minor"))
    out.append(("天钺", TIANYUE[g], "minor"))
    # 禄存 / 天马：年干 / 年支三合
    out.append(("禄存", luc, "minor"))
    out.append(("天马", TIANMA_BASE[sh], "minor"))
    # 擎羊（禄存前） / 陀罗（禄存后）
    out.append(("擎羊", (luc + 1) % 12, "minor"))
    out.append(("陀罗", (luc - 1) % 12, "minor"))
    # 火星 / 铃星：年支三合 base 起子时顺数至生时
    out.append(("火星", (HUOXING_BASE[sh] + h) % 12, "minor"))
    out.append(("铃星", (LINGXING_BASE[sh] + h) % 12, "minor"))
    # 地空 / 地劫：随生时（子时起亥宫逆/顺）
    out.append(("地空", (11 - h) % 12, "minor"))
    out.append(("地劫", (h + 11) % 12, "minor"))
    # ---- 杂曜 ----
    # 红鸾：卯宫(3)起子年逆数至生年支；天喜：红鸾对宫
    hl = (3 - z) % 12
    out.append(("红鸾", hl, "adjective"))
    out.append(("天喜", (hl + 6) % 12, "adjective"))
    # 咸池 / 华盖 / 孤辰 / 寡宿：年支
    out.append(("咸池", XIANCHI[z], "adjective"))
    out.append(("华盖", HUAGAI[z], "adjective"))
    out.append(("孤辰", GUCHEN[z], "adjective"))
    out.append(("寡宿", GUASU[z], "adjective"))
    # 天才：命宫起子年顺数至生年支
    out.append(("天才", (ming_zhi_idx + z) % 12, "adjective"))
    # 天刑：酉宫(9)起子月顺数至生月
    out.append(("天刑", (8 + m) % 12, "adjective"))
    return out


def _zhi_at(base_zhi_idx, offset):
    """地支序 base 顺/逆 offset（负=逆），返回地支序。"""
    return (base_zhi_idx + offset) % 12


def ziwei_chart(solar_dt, gender, ju_table=None):
    """紫微斗数排盘。

    ju_table: EXE 逆向出的「紫微斗数·局」查表 {局名: {农历日: 地支序}}，
    用于精确确定紫微落宫（替代近似公式）。未提供时回退到通用公式。
    """
    if isinstance(solar_dt, str):
        solar_dt = datetime.datetime.strptime(solar_dt, "%Y-%m-%d %H:%M")
    l = cnlunar.Lunar(solar_dt, godType="8char")
    year_gz = l.year8Char
    month_gz = l.month8Char
    lunar_day = l.lunarDay

    year_gan_idx = GAN.index(year_gz[0])
    year_zhi_idx = ZHI.index(year_gz[1])
    month_zhi_idx = ZHI.index(month_gz[1])
    hour_zhi_idx = _hour_zhi(solar_dt.hour)
    # 农历月序（1-12，闰月取同序数，用于辅星/杂曜安星）
    lunar_month = abs(int(l.lunarMonth))

    # 命宫 / 身宫（寅坐标：寅=0…丑=11）
    # 命宫：寅宫起正月顺数至生月（农历月序 m → 生月宫 = m-1 寅坐标），
    #       再逆数至生时（时辰地支序 hour，子=0…亥=11，不 +1）。
    # 校验：命宫地支序 = ((m+1) - hour) % 12，与 iztro 12 例完全一致。
    mb = (lunar_month - 1) % 12               # 生月宫（寅坐标）
    hour_h = hour_zhi_idx
    ming = (mb - hour_h) % 12                 # 命宫（寅坐标）
    shen = (mb + hour_h) % 12                 # 身宫（寅坐标）
    ming_zhi = (2 + ming) % 12                # 地支序
    shen_zhi = (2 + shen) % 12

    # 命宫天干（五虎遁）
    ming_gan = (WUHU_DUN[year_gan_idx] + ming) % 10
    ming_gz = GAN[ming_gan] + ZHI[ming_zhi]

    # 五行局
    seq = _gz_index(ming_gz)
    nayin_wx = _NAYIN[seq][1]
    ju_name, ju_num = NAYIN_JU[nayin_wx]

    # 紫微落宫：优先用 EXE 局表（天纪权威数据），否则用近似公式
    ziwei_zhi = None
    if ju_table:
        _zt = ju_table.get(ju_name)
        if _zt and lunar_day in _zt:
            ziwei_zhi = int(_zt[lunar_day]) % 12
    if ziwei_zhi is None:
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
    # 四化映射（主星与部分辅星 文昌/文曲/左辅/右弼 亦可化）
    sihua_tuple = SIHUA.get(year_gz[0], ("", "", "", ""))
    sihua_map = {}
    for k, nm in zip(("禄", "权", "科", "忌"), sihua_tuple):
        sihua_map[nm] = k
    for name, z in star_zhi.items():
        palace[z]["stars"].append({"name": name, "kind": "major",
                                   "sihua": sihua_map.get(name, "")})
    # 辅星 / 杂曜 安星
    aux = aux_stars(year_gan_idx, year_zhi_idx, lunar_month, hour_zhi_idx, ming_zhi)
    for name, z, kind in aux:
        palace[z]["stars"].append({"name": name, "kind": kind,
                                   "sihua": sihua_map.get(name, "")})
    # 排序：主星按固定顺序，辅星/杂曜次之
    star_rank = {s: i for i, s in enumerate(
        ["紫微", "天机", "太阳", "武曲", "天同", "廉贞", "天府", "太阴",
         "贪狼", "巨门", "天相", "天梁", "七杀", "破军"])}
    kind_rank = {"major": 0, "minor": 1, "adjective": 2}
    for z in palace:
        palace[z]["stars"].sort(
            key=lambda s: (star_rank.get(s["name"], 99)
                           if s["kind"] == "major" else 99,
                           kind_rank.get(s["kind"], 9)))

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
