# -*- coding: utf-8 -*-
"""Generate 穴位走向动画.html in 人纪学习系统/穴位走向动画/."""
import os, json

ROOT = r"E:/Soft/倪海夏三套学习系统/QQ频道号talktyph0id/人纪学习系统"
D = ROOT + r"/灵龟八法数据"

MER = json.load(open(D + "/meridians.json", encoding="utf-8"))
COORDS = json.load(open(D + "/selfdata.json", encoding="utf-8"))

MER_WITH_POS = {}
for mer, info in MER.items():
    pts = []
    for i, name in enumerate(info["points"]):
        if name in COORDS:
            c = COORDS[name]
            pts.append({"i": i + 1, "name": name, "x": c["left"], "y": c["top"]})
        else:
            pts.append({"i": i + 1, "name": name, "x": None, "y": None})
    MER_WITH_POS[mer] = {**info, "points": pts}
print(f"合并 {len(MER_WITH_POS)} 经, 总穴数 {sum(len(v['points']) for v in MER_WITH_POS.values())}")

HTML_HEAD = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>穴位走向动画 · 人纪学习系统</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, "Microsoft YaHei", sans-serif; background: #f5f1e8; color: #222; padding: 16px; }
header { background: #2d5a4f; color: #fff; padding: 16px 20px; border-radius: 8px; margin-bottom: 16px; }
header h1 { font-size: 22px; }
header p { font-size: 13px; opacity: .85; margin-top: 4px; }
.selector { display: flex; gap: 12px; align-items: center; background: #fff; padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,.08); flex-wrap: wrap; }
.selector label { font-size: 14px; color: #555; }
.selector select { padding: 6px 12px; font-size: 14px; border: 1px solid #ccc; border-radius: 4px; min-width: 180px; }
.selector .info { margin-left: auto; font-size: 14px; }
.selector .info strong { color: #2d5a4f; }
.viewer { display: grid; grid-template-columns: 1fr 320px; gap: 16px; }
@media (max-width: 900px) { .viewer { grid-template-columns: 1fr; } }
.body-wrap { position: relative; background: #fff; border-radius: 8px; padding: 8px; box-shadow: 0 1px 3px rgba(0,0,0,.08); overflow: auto; }
.body-wrap img { display: block; max-width: 100%; height: auto; }
.body-wrap svg { position: absolute; top: 8px; left: 8px; width: calc(100% - 16px); height: auto; pointer-events: none; }
.dot { fill: #c0392b; stroke: #fff; stroke-width: 2; opacity: .9; }
.dot.active { fill: #e67e22; animation: pulse 1.2s ease-in-out infinite alternate; }
@keyframes pulse { from { r: 6; } to { r: 11; } }
.path-line { fill: none; stroke: #c0392b; stroke-width: 2.5; opacity: .8; }
.path-anim { fill: none; stroke: #fff; stroke-width: 2; stroke-dasharray: 12 8; opacity: .9;
  animation: dash 2.5s linear infinite; }
@keyframes dash { to { stroke-dashoffset: -200; } }
.label { fill: #fff; font-size: 10px; font-weight: bold; text-anchor: middle; dominant-baseline: middle;
  paint-order: stroke; stroke: #000; stroke-width: 3px; stroke-linejoin: round; pointer-events: none; }
.name-tag { fill: #000; font-size: 11px; font-weight: bold; text-anchor: middle; dominant-baseline: middle;
  paint-order: stroke; stroke: #fff; stroke-width: 3px; stroke-linejoin: round; pointer-events: none; }
.detail { background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
.detail h2 { font-size: 18px; color: #2d5a4f; margin-bottom: 10px; padding-bottom: 6px; border-bottom: 2px solid #2d5a4f; }
.detail .meta { font-size: 13px; line-height: 1.8; color: #555; }
.detail .meta span { display: inline-block; margin-right: 12px; }
.detail .meta .lbl { color: #999; }
.point-list { margin-top: 14px; max-height: 480px; overflow-y: auto; font-size: 13px; line-height: 1.8; border-top: 1px solid #eee; padding-top: 10px; }
.point-list .pt { display: flex; padding: 2px 4px; border-radius: 3px; }
.point-list .pt.cur { background: #fdebd0; font-weight: bold; color: #c0392b; }
.point-list .pt:hover { background: #f4f4f4; cursor: pointer; }
.point-list .num { display: inline-block; width: 28px; color: #999; }
.point-list .nm  { display: inline-block; width: 80px; font-weight: bold; }
.point-list .xy  { display: inline-block; color: #888; font-family: monospace; font-size: 11px; }
.point-list .miss { color: #ccc; font-style: italic; }
.point-list .miss .nm { color: #bbb; }
.foot { text-align: center; font-size: 12px; color: #999; margin-top: 16px; }
.legend { font-size: 11px; color: #777; padding: 6px 0; }
.legend span { margin-right: 12px; }
.legend .k { display: inline-block; width: 10px; height: 10px; border-radius: 50%; vertical-align: middle; margin-right: 4px; }
</style>
</head>
<body>
<header>
  <h1>穴位走向动画 · 14 经流注次序</h1>
  <p>基于 SELFDATA 真实穴位坐标（MDB 表）+ 全身背面经络穴位图 · 点击穴位可查看流向</p>
</header>

<div class="selector">
  <label>经脉：<select id="mer"></select></label>
  <div class="info">走向：<strong id="dir"></strong></div>
</div>

<div class="viewer">
  <div class="body-wrap">
    <img src="../十二经络与奇经八脉/人体穴位图/全身背面经络穴位图.jpg" alt="背面经络穴位图">
    <svg id="svg" viewBox="0 0 1278 2304" preserveAspectRatio="xMidYMid meet"></svg>
  </div>
  <div class="detail">
    <h2 id="title">—</h2>
    <div class="meta">
      <span><span class="lbl">代码：</span><strong id="code"></strong></span>
      <span><span class="lbl">阴阳：</span><strong id="yin"></strong></span>
      <span><span class="lbl">五行：</span><strong id="element"></strong></span>
      <span><span class="lbl">穴位：</span><strong id="cnt"></strong></span>
    </div>
    <div class="legend">
      <span><span class="k" style="background:#c0392b"></span>穴位</span>
      <span><span class="k" style="background:#e67e22"></span>当前选中</span>
      <span><span class="k" style="background:#fff;border:1px solid #c0392b"></span>流动路径</span>
    </div>
    <div class="point-list" id="list"></div>
  </div>
</div>

<div class="foot">
  数据：MDB SELFDATA（348 穴位坐标） + 14 经标准穴位顺序 ·
  图像：<a href="../十二经络与奇经八脉/人体穴位图/全身背面经络穴位图.jpg">全身背面经络穴位图.jpg</a>
</div>

<script>
const DATA = __DATA_PLACEHOLDER__;

const merSel = document.getElementById('mer');
const svg = document.getElementById('svg');
const list = document.getElementById('list');
const $ = id => document.getElementById(id);

Object.keys(DATA).forEach(m => {
  const o = document.createElement('option');
  o.value = m; o.textContent = m + ' (' + DATA[m].points.length + ' 穴)';
  merSel.appendChild(o);
});
merSel.value = '手太阴肺经';

let activeIdx = 0;

function render() {
  const m = merSel.value;
  const info = DATA[m];
  $('title').textContent = m;
  $('code').textContent = info.code;
  $('yin').textContent  = info.yin === 'yin' ? '阴经' : '阳经';
  $('element').textContent = info.element;
  $('cnt').textContent = info.points.length;
  $('dir').textContent = info.direction;

  svg.innerHTML = '';
  const pts = info.points.filter(p => p.x != null);
  if (pts.length > 1) {
    const d = pts.map((p,i) => (i===0?'M':'L') + p.x + ',' + p.y).join(' ');
    const basePath = document.createElementNS('http://www.w3.org/2000/svg','path');
    basePath.setAttribute('d', d); basePath.setAttribute('class','path-line');
    svg.appendChild(basePath);
    const animPath = document.createElementNS('http://www.w3.org/2000/svg','path');
    animPath.setAttribute('d', d); animPath.setAttribute('class','path-anim');
    svg.appendChild(animPath);
  }
  info.points.forEach((p, i) => {
    if (p.x == null) return;
    const c = document.createElementNS('http://www.w3.org/2000/svg','circle');
    c.setAttribute('cx', p.x); c.setAttribute('cy', p.y);
    c.setAttribute('r', 6);
    c.setAttribute('class', 'dot' + (i === activeIdx ? ' active' : ''));
    c.style.pointerEvents = 'all';
    c.style.cursor = 'pointer';
    c.addEventListener('click', () => { activeIdx = i; render(); });
    svg.appendChild(c);
    const num = document.createElementNS('http://www.w3.org/2000/svg','text');
    num.setAttribute('x', p.x); num.setAttribute('y', p.y);
    num.setAttribute('class','label');
    num.textContent = p.i;
    svg.appendChild(num);
    const nm = document.createElementNS('http://www.w3.org/2000/svg','text');
    nm.setAttribute('x', p.x); nm.setAttribute('y', p.y - 14);
    nm.setAttribute('class','name-tag');
    nm.textContent = p.name;
    svg.appendChild(nm);
  });
  list.innerHTML = info.points.map((p,i) => {
    const cur = i === activeIdx ? ' cur' : '';
    const xy = p.x == null ? '<span class="miss">坐标缺(显示在正面图)</span>' : '(' + p.x + ',' + p.y + ')';
    return '<div class="pt' + cur + '" data-idx="' + i + '">' +
      '<span class="num">' + p.i + '.</span>' +
      '<span class="nm">' + p.name + '</span>' +
      '<span class="xy">' + xy + '</span></div>';
  }).join('');
  list.querySelectorAll('.pt').forEach(el => {
    el.addEventListener('click', () => { activeIdx = parseInt(el.dataset.idx); render(); });
  });
  list.scrollTop = Math.max(0, (activeIdx - 3) * 26);
}

merSel.addEventListener('change', () => { activeIdx = 0; render(); });
render();
</script>
</body>
</html>
"""

html = HTML_HEAD.replace("__DATA_PLACEHOLDER__", json.dumps(MER_WITH_POS, ensure_ascii=False))

out_dir = ROOT + r"/穴位走向动画"
os.makedirs(out_dir, exist_ok=True)
fp = out_dir + r"/穴位走向动画.html"
open(fp, "w", encoding="utf-8").write(html)
print("生成:", fp)
print("大小:", len(html), "chars")