# -*- coding: utf-8 -*-
"""Generate 倪师取穴图表.html — 方形小图+图名网格，点击右侧放大预览."""
import os, re

D = r"E:/Soft/倪海夏三套学习系统/QQ频道号talktyph0id/人纪学习系统/倪师傅经验/针灸穴位总结图表"

# 从索引.txt 读取有序 (图名, 文件名)
pairs = []
for line in open(os.path.join(D, "索引.txt"), encoding="utf-8"):
    m = re.match(r"\s*(.+?)\s*→\s*(.+\.jpg)\s*$", line)
    if m:
        pairs.append((m.group(1).strip(), m.group(2).strip()))

# 兜底：补上索引里没有但磁盘有的 jpg
on_disk = sorted(f for f in os.listdir(D) if f.lower().endswith(".jpg"))
have = {fn for _, fn in pairs}
for fn in on_disk:
    if fn not in have:
        name = os.path.splitext(fn)[0]
        pairs.append((name, fn))

print(f"图表记录: {len(pairs)} 张")
for n, f in pairs[:5]: print("  ", n, "->", f)

# 生成 HTML
html = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>倪师取穴图表 · 图库</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, "Microsoft YaHei", sans-serif; background: #f5f1e8; color: #222; }
header { background: #2d5a4f; color: #fff; padding: 12px 18px; }
header h1 { font-size: 18px; }
header p { font-size: 12px; opacity: .85; margin-top: 3px; }
.layout { display: grid; grid-template-columns: 1fr 360px; gap: 0; height: calc(100vh - 58px); }
@media (max-width: 860px) { .layout { grid-template-columns: 1fr; height: auto; } .preview { min-height: 60vh; order: -1; } }

.thumbs { overflow-y: auto; padding: 14px; background: #faf6ec; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 10px; }
.item { background: #fff; border: 1px solid #e0d8c0; border-radius: 6px; overflow: hidden; cursor: pointer;
  box-shadow: 0 1px 2px rgba(0,0,0,.06); transition: box-shadow .15s, transform .1s; }
.item:hover { box-shadow: 0 3px 8px rgba(0,0,0,.12); transform: translateY(-2px); }
.item.active { outline: 3px solid #c0392b; }
.item .imgbox { aspect-ratio: 1/1; overflow: hidden; background: #fff; }
.item img { width: 100%; height: 100%; object-fit: contain; display: block; }
.item .nm { font-size: 11px; text-align: center; padding: 5px 4px; color: #444; line-height: 1.35;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.item .nm small { display: block; color: #aaa; font-size: 9px; }

.preview { display: flex; flex-direction: column; border-left: 1px solid #e0d8c0; background: #26241f; }
.preview .ph { flex: 1; display: flex; align-items: center; justify-content: center; overflow: hidden; padding: 12px; position: relative; }
.preview img { max-width: 100%; max-height: 100%; object-fit: contain; display: none; }
.preview img.show { display: block; }
.preview .placeholder { color: #9b957a; font-size: 14px; text-align: center; line-height: 1.8; }
.preview .phmeta { padding: 8px 12px; background: #33302a; color: #eee; font-size: 12px; display: none; }
.preview .phmeta.show { display: block; }
.preview .phmeta .t { font-weight: bold; color: #fff; font-size: 13px; }
.preview .phmeta .s { color: #aaa; margin-left: 8px; }
</style>
</head>
<body>

<header>
  <h1>倪师取穴图表（针灸穴位总结图表 · 62 张）</h1>
  <p>点击左侧小图 → 右侧放大查看 · 来源：人纪 MDB nishitu 表</p>
</header>

<div class="layout">
  <div class="thumbs">
    <div class="grid" id="grid"></div>
  </div>
  <div class="preview">
    <div class="ph">
      <div class="placeholder" id="placeholder">点击左侧图表查看大图</div>
      <img id="big" alt="大图">
    </div>
    <div class="phmeta" id="phmeta">
      <span class="t" id="big-name"></span>
      <span class="s" id="big-file"></span>
    </div>
  </div>
</div>

<script>
const CHARTS = __CHARTS__;

const grid = document.getElementById('grid');
const big = document.getElementById('big');
const placeholder = document.getElementById('placeholder');
const phmeta = document.getElementById('phmeta');
const bigName = document.getElementById('big-name');
const bigFile = document.getElementById('big-file');
let active = null;

grid.innerHTML = CHARTS.map((c, i) =>
  '<div class="item" data-i="' + i + '" title="' + c.n + '">' +
    '<div class="imgbox"><img src="' + c.f + '" loading="lazy" alt="' + c.n + '"></div>' +
    '<div class="nm">' + c.n + '<small>' + (c.s ? Math.round(c.s/1024) + 'KB' : '') + '</small></div>' +
  '</div>'
).join('');

function show(i) {
  const c = CHARTS[i];
  big.src = c.f;
  big.classList.add('show');
  placeholder.style.display = 'none';
  phmeta.classList.add('show');
  bigName.textContent = c.n;
  bigFile.textContent = c.f + (c.s ? ' · ' + Math.round(c.s/1024) + ' KB' : '');
  if (active !== null) grid.children[active].classList.remove('active');
  grid.children[i].classList.add('active');
  active = i;
}

grid.addEventListener('click', e => {
  const it = e.target.closest('.item');
  if (it) show(parseInt(it.dataset.i));
});

// 键盘导航（左右方向键）
document.addEventListener('keydown', e => {
  if (active === null) return;
  if (e.key === 'ArrowRight' && active < CHARTS.length-1) { show(active+1); grid.children[active].scrollIntoView({block:'nearest'}); }
  if (e.key === 'ArrowLeft' && active > 0) { show(active-1); grid.children[active].scrollIntoView({block:'nearest'}); }
});

show(0);
</script>
</body>
</html>
"""

# 注入数据（含文件大小）
import json
data = []
for n, f in pairs:
    p = os.path.join(D, f)
    s = os.path.getsize(p) if os.path.exists(p) else 0
    data.append({"n": n, "f": f, "s": s})

html = html.replace("__CHARTS__", json.dumps(data, ensure_ascii=False))
fp = os.path.join(D, "倪师取穴图表.html")
open(fp, "w", encoding="utf-8").write(html)
print(f"\n生成: {fp} ({len(html)} chars)")