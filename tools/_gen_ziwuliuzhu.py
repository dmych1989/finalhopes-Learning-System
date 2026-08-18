# -*- coding: utf-8 -*-
"""Generate 子午流注.html — 左=十二经纳甲法表，右=十二经脉纳子法表（取消下拉，平铺全表）。"""
import os, json

ROOT = r"E:/Soft/倪海夏三套学习系统/QQ频道号talktyph0id/人纪学习系统"
D = ROOT + r"/灵龟八法数据"

NAJIA = json.load(open(D + "/najia.json", encoding="utf-8"))
NAZI  = json.load(open(D + "/nazi.json",  encoding="utf-8"))

# 时辰顺序
HOURS = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
# 纳子法 key 排序：天干+时辰（甲子..甲亥, 乙子..乙亥, ... 癸子..癸亥）
TG = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
NAZI_ORDER = [t + h for t in TG for h in HOURS]

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>子午流注 · 十二经纳甲法表 + 十二经脉纳子法表 · 人纪学习系统</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, "Microsoft YaHei", sans-serif; background: #f5f1e8; color: #222; padding: 10px; line-height: 1.4; }
header { background: #2d5a4f; color: #fff; padding: 12px 18px; border-radius: 8px; margin-bottom: 10px; }
header h1 { font-size: 18px; }
header p { font-size: 12px; opacity: .85; margin-top: 4px; }

.selector { background: #fff; padding: 10px 14px; border-radius: 8px; display: flex; gap: 10px; align-items: flex-end; flex-wrap: wrap; box-shadow: 0 1px 3px rgba(0,0,0,.08); margin-bottom: 12px; }
.selector label { font-size: 11px; color: #555; display: block; }
.selector input, .selector select { padding: 4px 6px; font-size: 12px; border: 1px solid #ccc; border-radius: 3px; width: 90px; }
.selector button { padding: 5px 14px; font-size: 12px; background: #c0392b; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
.selector .hint { font-size: 11px; color: #888; margin-left: auto; align-self: center; }

.layout { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
@media (max-width: 900px) { .layout { grid-template-columns: 1fr; } }

.panel { background: #fff; border-radius: 8px; padding: 12px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
.panel h2 { font-size: 15px; color: #2d5a4f; margin-bottom: 8px; padding-bottom: 4px; border-bottom: 1.5px solid #2d5a4f; }
.panel .note { font-size: 11px; color: #999; margin-bottom: 6px; }

.tbl-wrap { max-height: 620px; overflow: auto; border: 1px solid #ddd; border-radius: 4px; }
table { border-collapse: collapse; width: 100%; font-size: 12px; }
th, td { border: 1px solid #ddd; padding: 5px 8px; text-align: center; }
th { background: #fdf6e3; color: #5a4a30; position: sticky; top: 0; z-index: 1; }
tr:nth-child(even) { background: #faf9f4; }
td.cur, tr.cur td { background: #fdebd0 !important; color: #c0392b; font-weight: bold; }
td.cur-th, tr.cur-th td { background: #fdebd0 !important; font-weight: bold; }
.hour { font-weight: bold; color: #2d5a4f; }
.empty { color: #ccc; }

.result { background: #fff; border-radius: 8px; padding: 12px 16px; box-shadow: 0 1px 3px rgba(0,0,0,.08); margin-top: 12px; font-size: 12px; }
.result h3 { font-size: 13px; color: #2d5a4f; margin-bottom: 6px; }
.result .row { display: flex; gap: 18px; flex-wrap: wrap; }
.result .lbl { color: #888; font-size: 11px; display: block; }
.result .val { font-weight: bold; color: #c0392b; font-size: 13px; }
.foot { text-align: center; font-size: 11px; color: #999; margin-top: 10px; }
</style>
</head>
<body>

<header>
  <h1>子午流注 · 十二经纳甲法表（左） + 十二经脉纳子法表（右）</h1>
  <p>两表同页平铺显示（无下拉切换）· 左上选年月日时定位当前行/列 · 数据源自人纪 MDB najia/nazi 表</p>
</header>

<div class="selector">
  <label>年<input type="number" id="y" min="1900" max="2100" value="2026"></label>
  <label>月<input type="number" id="m" min="1" max="12" value="8"></label>
  <label>日<input type="number" id="d" min="1" max="31" value="9"></label>
  <label>时辰
    <select id="h">
      <option value="0">子 23-1</option><option value="1">丑 1-3</option>
      <option value="2">寅 3-5</option><option value="3">卯 5-7</option>
      <option value="4">辰 7-9</option><option value="5">巳 9-11</option>
      <option value="6">午 11-13</option><option value="7">未 13-15</option>
      <option value="8">申 15-17</option><option value="9">酉 17-19</option>
      <option value="10">戌 19-21</option><option value="11">亥 21-23</option>
    </select>
  </label>
  <button id="now">现在</button>
  <div class="hint" id="cur-hint">—</div>
</div>

<div class="layout">

  <div class="panel">
    <h2>十二经纳甲法表（按时辰 · 12 行）</h2>
    <div class="note">流经脏腑经络 / 补母穴 / 泻子穴 / 流注输穴 / 经原穴 —— MDB najia 表</div>
    <div class="tbl-wrap" id="wrap-najia"><table id="tbl-najia"></table></div>
  </div>

  <div class="panel">
    <h2>十二经脉纳子法表（日干×时辰 · 120 行）</h2>
    <div class="note">日干 + 时辰 → 穴1 / 穴2 / 穴3 —— MDB nazi 表</div>
    <div class="tbl-wrap" id="wrap-nazi"><table id="tbl-nazi"></table></div>
  </div>

</div>

<div class="result">
  <h3>当前选择：<span id="cur-label">—</span></h3>
  <div class="row" id="cur-result"></div>
</div>

<div class="foot">
  数据：人纪 MDB najia(12×6) / nazi(120×4) · 纳甲按「时辰」，纳子按「日干+时辰」 · 当前行橙色高亮
</div>

<script>
const NAJIA = __NAJIA__;
const NAZI = __NAZI__;
const HOURS = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥'];
const TG = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸'];
const NAZI_ORDER = __NAZI_ORDER__;
const SX = ['鼠','牛','虎','兔','龙','蛇','马','羊','猴','鸡','狗','猪'];
const NAYIN60 = ['海中金','炉中火','大林木','路旁土','剑锋金','山头火','涧下水','城头土','白蜡金','杨柳木','泉中水','大海水','沙中金','山下火','平地木','壁上土','金箔金','覆灯火','天河水','大驿土','钗钏金','桑柘木','大溪水','沙中土','天上火','石榴木','大海水'];

function isLeap(y) { return (y%4===0 && y%100!==0) || y%400===0; }
function daysInMonth(y, m) { return [31, isLeap(y)?29:28, 31,30,31,30,31,31,30,31,30,31][m-1]; }
function yearGZ(y, m, d) {
  const y2 = (m < 2 || (m === 2 && d < 4)) ? y - 1 : y;
  const idx = ((y2 - 4) % 60 + 60) % 60;
  return { stem: TG[idx % 10], branch: HOURS[idx % 12], idx };
}
function dayGZ(y, m, d) {
  let total = 0;
  for (let i = 1900; i < y; i++) total += isLeap(i) ? 366 : 365;
  for (let i = 1; i < m; i++) total += daysInMonth(y, i);
  total += d - 1;
  const idx = (10 + total % 60 + 60) % 60;
  return { stem: TG[idx % 10], branch: HOURS[idx % 12], idx };
}
function monthGZ(yearStemIdx, m) {
  const monthStemStart = [2,4,0,6,8][yearStemIdx % 5];
  const monthBranchIdx = (m + 1) % 12;
  const monthStemIdx = (monthStemStart + (monthBranchIdx - 2 + 12) % 12) % 10;
  return { stem: TG[monthStemIdx], branch: HOURS[monthBranchIdx] };
}
function hourGZ(dayStemIdx, h) {
  const hourStemStart = [0,2,4,6,8][dayStemIdx % 5];
  return { stem: TG[(hourStemStart + h) % 10], branch: HOURS[h] };
}

// ========= 渲染两张表 =========
function renderTables() {
  const y = parseInt(document.getElementById('y').value);
  const m = parseInt(document.getElementById('m').value);
  const d = parseInt(document.getElementById('d').value);
  const h = parseInt(document.getElementById('h').value);

  const yy = yearGZ(y, m, d);
  const dd = dayGZ(y, m, d);
  const mm = monthGZ(yy.idx % 10, m);
  const hh = hourGZ(dd.idx % 10, h);

  const curHour = HOURS[h];
  const curDayStem = dd.stem;
  const curKey = curDayStem + curHour;

  document.getElementById('cur-hint').textContent =
    y + '年' + m + '月' + d + '日 ' + yy.stem + yy.branch + '年 ' + mm.stem + mm.branch + '月 ' +
    dd.stem + dd.branch + '日 ' + hh.stem + hh.branch + '时 · 日干=' + curDayStem + ' 时辰=' + curHour;
  document.getElementById('cur-label').textContent =
    curKey + '（' + curDayStem + '日 ' + curHour + '时）';

  // ---- 左：纳甲法表（12 行） ----
  let na1 = '<thead><tr><th>时辰</th><th>流经脏腑经络</th><th>补母穴</th><th>泻子穴</th><th>流注输穴</th><th>经原穴</th></tr></thead><tbody>';
  for (const hr of HOURS) {
    const r = NAJIA[hr] || {};
    const cls = hr === curHour ? ' class="cur"' : '';
    na1 += '<tr' + cls + '><td class="hour">' + hr + '时</td>' +
      '<td>' + (r['流经脏腑经络'] || '-') + '</td>' +
      '<td>' + (r['补母穴'] || '-') + '</td>' +
      '<td>' + (r['泻子穴'] || '-') + '</td>' +
      '<td>' + (r['流注输穴'] || '-') + '</td>' +
      '<td>' + (r['经原穴'] || '-') + '</td></tr>';
  }
  na1 += '</tbody>';
  document.getElementById('tbl-najia').innerHTML = na1;

  // ---- 右：纳子法表（120 行） ----
  let na2 = '<thead><tr><th>日干时辰</th><th>穴1</th><th>穴2</th><th>穴3</th></tr></thead><tbody>';
  let curRowId = '';
  NAZI_ORDER.forEach((key, i) => {
    const r = NAZI[key] || {};
    const cls = key === curKey ? ' class="cur"' : '';
    if (key === curKey) curRowId = 'row-' + i;
    na2 += '<tr' + cls + ' id="row-' + i + '"><td class="hour">' + key + '</td>' +
      '<td>' + (r['穴1'] || '<span class="empty">—</span>') + '</td>' +
      '<td>' + (r['穴2'] || '<span class="empty">—</span>') + '</td>' +
      '<td>' + (r['穴3'] || '<span class="empty">—</span>') + '</td></tr>';
  });
  na2 += '</tbody>';
  document.getElementById('tbl-nazi').innerHTML = na2;

  // 滚动到当前行
  if (curRowId) {
    const el = document.getElementById(curRowId);
    if (el) el.scrollIntoView({ block: 'center' });
  }

  // ---- 当前结果 ----
  const na = NAJIA[curHour] || {};
  const nz = NAZI[curKey] || {};
  document.getElementById('cur-result').innerHTML =
    '<div><span class="lbl">纳甲·流经脏腑经络</span><span class="val">' + (na['流经脏腑经络'] || '-') + '</span></div>' +
    '<div><span class="lbl">纳甲·补母穴</span><span class="val">' + (na['补母穴'] || '-') + '</span></div>' +
    '<div><span class="lbl">纳甲·泻子穴</span><span class="val">' + (na['泻子穴'] || '-') + '</span></div>' +
    '<div><span class="lbl">纳甲·流注输穴</span><span class="val">' + (na['流注输穴'] || '-') + '</span></div>' +
    '<div><span class="lbl">纳甲·经原穴</span><span class="val">' + (na['经原穴'] || '-') + '</span></div>' +
    '<div><span class="lbl">纳子·穴1</span><span class="val">' + (nz['穴1'] || '—') + '</span></div>' +
    '<div><span class="lbl">纳子·穴2</span><span class="val">' + (nz['穴2'] || '—') + '</span></div>' +
    '<div><span class="lbl">纳子·穴3</span><span class="val">' + (nz['穴3'] || '—') + '</span></div>';
}

['y','m','d','h'].forEach(id => document.getElementById(id).addEventListener('change', renderTables));
document.getElementById('now').addEventListener('click', () => {
  const dt = new Date();
  document.getElementById('y').value = dt.getFullYear();
  document.getElementById('m').value = dt.getMonth()+1;
  document.getElementById('d').value = dt.getDate();
  document.getElementById('h').value = Math.floor((dt.getHours()+1)/2) % 12;
  renderTables();
});
renderTables();
</script>
</body>
</html>
"""

html = html.replace("__NAJIA__", json.dumps(NAJIA, ensure_ascii=False))
html = html.replace("__NAZI__", json.dumps(NAZI, ensure_ascii=False))
html = html.replace("__NAZI_ORDER__", json.dumps(NAZI_ORDER, ensure_ascii=False))

fp = ROOT + r"/子午流注.html"
open(fp, "w", encoding="utf-8").write(html)
print(f"生成: {fp} ({len(html)} chars)")
print(f"纳甲表 {len(HOURS)} 行, 纳子表 {len(NAZI_ORDER)} 行")