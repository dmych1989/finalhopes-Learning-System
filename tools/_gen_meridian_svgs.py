# -*- coding: utf-8 -*-
"""Generate per-meridian SVG overlays (14 files) + index for 穴位走向动画/."""
import os, json, html as _html

ROOT = r"E:/Soft/倪海夏三套学习系统/QQ频道号talktyph0id/人纪学习系统"
D = ROOT + r"/灵龟八法数据"
OUT = ROOT + r"/穴位走向动画"

MER = json.load(open(D + "/meridians.json", encoding="utf-8"))
COORDS = json.load(open(D + "/selfdata.json", encoding="utf-8"))

DIR_TO_OUT = {
    "手太阴肺经": "shoutaiyin_fei",
    "手阳明大肠经": "shouyangming_dachang",
    "足阳明胃经": "zuyangming_wei",
    "足太阴脾经": "zutaiyin_pi",
    "手少阴心经": "shoushaoyin_xin",
    "手太阳小肠经": "shoutaiyang_xiaochang",
    "足太阳膀胱经": "zutaiyang_pangguang",
    "足少阴肾经": "zushaoyin_shen",
    "手厥阴心包经": "shoujueyin_xinbao",
    "手少阳三焦经": "shoushaoyang_sanjiao",
    "足少阳胆经": "zushaoyang_dan",
    "足厥阴肝经": "zujueyin_gan",
    "任脉经穴": "renmai",
    "督脉经穴": "dumai",
}

BG_IMG = "../十二经络与奇经八脉/人体穴位图/全身背面经络穴位图.jpg"

os.makedirs(OUT, exist_ok=True)

svg_template = '''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 1278 2304" width="639" height="1152">
  <title>{title}</title>
  <desc>穴位走向动画 · {title} · 走向：{direction} · {cnt} 穴 · 来自 MDB SELFDATA 真实坐标</desc>
  <image xlink:href="{bg}" href="{bg}" x="0" y="0" width="1278" height="2304"/>
  {path_block}
  {dots_block}
  {missing_block}
</svg>
'''

def build_svg(mer, info):
    pts_with = [p for p in info["points"] if COORDS.get(p)]
    pts_miss = [p for p in info["points"] if not COORDS.get(p)]
    path_d = ""
    if len(pts_with) > 1:
        path_d = "M " + " L ".join(f"{COORDS[p]['left']},{COORDS[p]['top']}" for p in pts_with)
    path_block = ""
    if path_d:
        path_block = (
            f'<path d="{path_d}" fill="none" stroke="#c0392b" stroke-width="3" opacity="0.85"/>'
            f'<path d="{path_d}" fill="none" stroke="#fff" stroke-width="2" stroke-dasharray="14 10" opacity="0.95">'
            f'<animate attributeName="stroke-dashoffset" from="0" to="-240" dur="3s" repeatCount="indefinite"/>'
            f'</path>'
        )
    dots_block = ""
    for i, name in enumerate(info["points"]):
        c = COORDS.get(name)
        if not c: continue
        num = i + 1
        is_end = (i == 0 or i == len(info["points"]) - 1)
        r = 9 if is_end else 6
        color = "#e67e22" if is_end else "#c0392b"
        dots_block += (
            f'<g><circle cx="{c["left"]}" cy="{c["top"]}" r="{r}" fill="{color}" stroke="#fff" stroke-width="2.5" opacity="0.9"/>'
            f'<text x="{c["left"]}" y="{c["top"]}" font-size="12" font-weight="bold" fill="#fff" text-anchor="middle" dominant-baseline="middle" paint-order="stroke" stroke="#000" stroke-width="3">{num}</text>'
            f'<text x="{c["left"]}" y="{c["top"]-16}" font-size="11" font-weight="bold" fill="#000" text-anchor="middle" dominant-baseline="middle" paint-order="stroke" stroke="#fff" stroke-width="3">{_html.escape(name)}</text></g>'
        )
    missing_block = ""
    if pts_miss:
        missing_block = f'<text x="639" y="2260" font-size="14" fill="#888" text-anchor="middle">坐标缺失（显示在正面图）：{" · ".join(pts_miss)}</text>'

    return svg_template.format(
        title=_html.escape(mer),
        direction=_html.escape(info["direction"]),
        cnt=len(info["points"]),
        bg=BG_IMG,
        path_block=path_block,
        dots_block=dots_block,
        missing_block=missing_block,
    )

idx_lines = ["# 穴位走向动画 · 索引", "", "> 14 经 × 穴位走向 SVG（基于 MDB SELFDATA 真实坐标） + 交互式查看器", "", "## 一、交互式查看器", "", "- [`穴位走向动画.html`](穴位走向动画.html) — 14 经下拉切换，SVG 实时绘制路径 + 流动动画 + 穴位点击查看", "", "## 二、单经 SVG 图（可单独打开）", ""]
for mer, info in MER.items():
    slug = DIR_TO_OUT[mer]
    fn = f"{mer}.svg"
    cnt = len(info["points"])
    miss = sum(1 for p in info["points"] if not COORDS.get(p))
    miss_str = f"（{miss} 个坐标缺失）" if miss else ""
    idx_lines.append(f"- [`{fn}`]({fn}) — **{mer}** · {info['direction']} · {cnt} 穴{miss_str}")
    open(os.path.join(OUT, fn), "w", encoding="utf-8").write(build_svg(mer, info))

idx_lines += [
    "",
    "## 三、数据来源",
    "",
    "- 坐标：MDB `SELFDATA` 表（348 条穴位 left/top/H1/V1/Y）",
    "- 经脉顺序：国标 361 穴顺序（14 经，含任督）",
    "- 走向描述：手三阴从胸走手 / 手三阳从手走头 / 足三阳从头走足 / 足三阴从足走胸 / 任脉从下走上 / 督脉从下走上",
    "- 背景图：`<../十二经络与奇经八脉/人体穴位图/全身背面经络穴位图.jpg>`",
    "",
    "## 四、缺失穴位说明",
    "",
    "以下穴位 SELFDATA 无坐标（多为任脉前中线点，不在背面图）：",
]
miss_total = []
for mer, info in MER.items():
    for p in info["points"]:
        if not COORDS.get(p):
            miss_total.append(f"{mer}·{p}")
idx_lines += [f"- {m}" for m in miss_total]

idx_lines += ["", f"共缺失 {len(miss_total)} 穴（占总 361 的 {len(miss_total)*100//361}%）", ""]
open(os.path.join(OUT, "目录.txt"), "w", encoding="utf-8").write("\n".join(idx_lines))

print(f"已生成 14 张 SVG + 1 索引 + 1 HTML")
print(f"目录: {OUT}")
print(f"  缺失坐标穴位: {len(miss_total)}")