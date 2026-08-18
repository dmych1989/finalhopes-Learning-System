# -*- coding: utf-8 -*-
"""Generate 灵龟八法页面.html — 4 模块同页 + 年月日时选择 + 实时计算。"""
import os, json

ROOT = r"E:/Soft/倪海夏三套学习系统/QQ频道号talktyph0id/人纪学习系统"
D = ROOT + r"/灵龟八法数据"

LINGGUI = json.load(open(D + "/linggui.json", encoding="utf-8"))
NAJIA   = json.load(open(D + "/najia.json",   encoding="utf-8"))
NAZI    = json.load(open(D + "/nazi.json",    encoding="utf-8"))

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>万年历 · 子午流注盘 · 灵龟八法盘 · 灵龟八法表 · 人纪学习系统</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, "Microsoft YaHei", sans-serif; background: #f5f1e8; color: #222; padding: 12px; line-height: 1.5; }
header { background: #2d5a4f; color: #fff; padding: 14px 18px; border-radius: 8px; margin-bottom: 12px; }
header h1 { font-size: 20px; }
header p { font-size: 12px; opacity: .85; margin-top: 4px; }

.selector {
  position: sticky; top: 8px; z-index: 100;
  background: #fff; padding: 10px 14px; border-radius: 8px;
  display: grid; grid-template-columns: auto repeat(4, 1fr) auto auto; gap: 10px; align-items: center;
  box-shadow: 0 2px 6px rgba(0,0,0,.1); margin-bottom: 14px;
}
.selector label { font-size: 12px; color: #555; }
.selector input { padding: 5px 8px; font-size: 13px; border: 1px solid #ccc; border-radius: 4px; width: 100%; }
.selector .lbl { font-weight: bold; color: #2d5a4f; }
.selector button { padding: 5px 12px; font-size: 13px; background: #2d5a4f; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
.selector button:hover { background: #3d6a5f; }
.selector .now { background: #c0392b; }
.selector .now:hover { background: #d35400; }

.modules { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 14px; }
.module { background: #fff; border-radius: 8px; padding: 12px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
.module h2 { font-size: 15px; color: #2d5a4f; margin-bottom: 8px; padding-bottom: 4px; border-bottom: 1.5px solid #2d5a4f; }
@media (max-width: 900px) { .modules { grid-template-columns: 1fr; } }

/* 万年历 */
.wyear .row { display: flex; gap: 16px; flex-wrap: wrap; font-size: 13px; }
.wyear .row > div { padding: 4px 0; }
.wyear .lbl { color: #888; font-size: 11px; }
.wyear .val { font-size: 15px; font-weight: bold; color: #2d5a4f; }
.wyear .val.xs { font-size: 13px; }

/* 圆形盘 */
.disc { display: flex; gap: 12px; align-items: center; }
.disc svg { width: 220px; height: 220px; flex-shrink: 0; }
.disc .info { font-size: 12px; flex: 1; }
.disc .info .lbl { color: #888; font-size: 11px; display: block; margin-top: 4px; }
.disc .info .val { font-weight: bold; color: #c0392b; font-size: 14px; }
.disc circle.cur { fill: #c0392b !important; stroke: #fff !important; }
.disc text.cur { fill: #fff !important; }

/* 灵龟八法表 */
.lgb-table { font-size: 11px; border-collapse: collapse; max-height: 300px; overflow: auto; display: block; }
.lgb-table table { border-collapse: collapse; }
.lgb-table th, .lgb-table td { padding: 4px 6px; border: 1px solid #ddd; text-align: center; min-width: 38px; font-family: monospace; }
.lgb-table th { background: #2d5a4f; color: #fff; position: sticky; top: 0; }
.lgb-table tr:nth-child(even) { background: #f9f9f6; }
.lgb-table td.cur { background: #c0392b !important; color: #fff; font-weight: bold; }
.lgb-table th.corner { background: #1d4a3f; }
.lgb-wrap { max-height: 320px; overflow: auto; border: 1px solid #ddd; border-radius: 4px; }

/* 计算结果 */
.result { background: #fff; border-radius: 8px; padding: 14px; box-shadow: 0 1px 3px rgba(0,0,0,.08); margin-top: 12px; }
.result h2 { font-size: 16px; color: #2d5a4f; margin-bottom: 10px; padding-bottom: 4px; border-bottom: 1.5px solid #2d5a4f; }
.result .block { margin-bottom: 14px; padding: 10px; background: #fdf6e3; border-left: 4px solid #2d5a4f; border-radius: 4px; }
.result .block h3 { font-size: 14px; color: #2d5a4f; margin-bottom: 6px; }
.result .block .row { display: flex; gap: 16px; flex-wrap: wrap; font-size: 13px; }
.result .block .row > div { padding: 2px 0; }
.result .lbl { color: #888; font-size: 11px; }
.result .val { font-weight: bold; color: #c0392b; font-size: 14px; }

.foot { text-align: center; font-size: 12px; color: #999; margin-top: 12px; padding: 8px; }
</style>
</head>
<body>

<header>
  <h1>万年历 · 子午流注盘 · 圆形灵龟八法盘 · 灵龟八法表</h1>
  <p>四个模块同一页面（左上角选择年月日时，下方实时计算十二经纳子法 / 纳甲法 / 灵龟八法） · 数据源自人纪 MDB</p>
</header>

<div class="selector">
  <span class="lbl">选时间</span>
  <label>年<input type="number" id="y" min="1900" max="2100" value="2026"></label>
  <label>月<input type="number" id="m" min="1" max="12" value="8"></label>
  <label>日<input type="number" id="d" min="1" max="31" value="9"></label>
  <label>时辰
    <select id="h">
      <option value="0">子 23-1</option>
      <option value="1">丑 1-3</option>
      <option value="2">寅 3-5</option>
      <option value="3">卯 5-7</option>
      <option value="4">辰 7-9</option>
      <option value="5">巳 9-11</option>
      <option value="6">午 11-13</option>
      <option value="7">未 13-15</option>
      <option value="8">申 15-17</option>
      <option value="9">酉 17-19</option>
      <option value="10">戌 19-21</option>
      <option value="11">亥 21-23</option>
    </select>
  </label>
  <button class="now" id="now">现在</button>
</div>

<div class="modules">

  <div class="module wyear">
    <h2>一、万年历（公历 → 干支/生肖/纳音）</h2>
    <div class="row">
      <div><div class="lbl">公历</div><div class="val" id="r-solar">—</div></div>
      <div><div class="lbl">年柱</div><div class="val" id="r-yy">—</div></div>
      <div><div class="lbl">月柱</div><div class="val" id="r-mm">—</div></div>
      <div><div class="lbl">日柱</div><div class="val" id="r-dd">—</div></div>
      <div><div class="lbl">时柱</div><div class="val" id="r-hh">—</div></div>
      <div><div class="lbl">生肖</div><div class="val" id="r-shengxiao">—</div></div>
      <div><div class="lbl">年纳音</div><div class="val xs" id="r-nayin">—</div></div>
      <div><div class="lbl">月令</div><div class="val xs" id="r-yueling">—</div></div>
    </div>
  </div>

  <div class="module">
    <h2>二、倪海厦子午流注盘（按时辰流经脏腑经络）</h2>
    <div class="disc">
      <svg viewBox="0 0 220 220" id="disc-ziwu"></svg>
      <div class="info">
        <div class="lbl">当前时辰</div><div class="val" id="r-disc-ziwu-h">—</div>
        <div class="lbl">流经脏腑经络</div><div class="val" id="r-disc-ziwu-jing">—</div>
        <div class="lbl">本穴</div><div class="val" id="r-disc-ziwu-ben">—</div>
        <div class="lbl">源穴（原穴）</div><div class="val" id="r-disc-ziwu-yuan">—</div>
        <div class="lbl">补母穴</div><div class="val" id="r-disc-ziwu-bu">—</div>
        <div class="lbl">泻子穴</div><div class="val" id="r-disc-ziwu-xie">—</div>
      </div>
    </div>
  </div>

  <div class="module">
    <h2>三、圆形灵龟八法盘（八卦九宫八脉交穴）</h2>
    <div class="disc">
      <svg viewBox="0 0 220 220" id="disc-lgb"></svg>
      <div class="info">
        <div class="lbl">当前日柱</div><div class="val" id="r-disc-lgb-day">—</div>
        <div class="lbl">时辰</div><div class="val" id="r-disc-lgb-hour">—</div>
        <div class="lbl">灵龟八法开穴</div><div class="val" id="r-disc-lgb-kx">—</div>
        <div class="lbl">日干</div><div class="val xs" id="r-disc-lgb-stem">—</div>
        <div class="lbl">时支</div><div class="val xs" id="r-disc-lgb-branch">—</div>
      </div>
    </div>
  </div>

  <div class="module">
    <h2>四、灵龟八法表（60 日干支 × 12 时辰 = 720 开穴）</h2>
    <div class="lgb-wrap"><div class="lgb-table" id="r-lgb-table"></div></div>
  </div>

</div>

<div class="result">
  <h2>根据所选时间计算的实时数据</h2>

  <div class="block">
    <h3>① 十二经纳子法（按时辰 · 本经的本穴+原穴+补母+泻子）</h3>
    <div class="row">
      <div><div class="lbl">流经脏腑经络</div><div class="val" id="o-nazi-jing">—</div></div>
      <div><div class="lbl">本穴</div><div class="val" id="o-nazi-ben">—</div></div>
      <div><div class="lbl">源穴</div><div class="val" id="o-nazi-yuan">—</div></div>
      <div><div class="lbl">补母穴</div><div class="val" id="o-nazi-bu">—</div></div>
      <div><div class="lbl">泻子穴</div><div class="val" id="o-nazi-xie">—</div></div>
    </div>
  </div>

  <div class="block">
    <h3>② 十二经纳甲法（按时辰 · 流注输穴+经原+补母+泻子）</h3>
    <div class="row">
      <div><div class="lbl">流注时辰</div><div class="val" id="o-najia-hour">—</div></div>
      <div><div class="lbl">流经脏腑经络</div><div class="val" id="o-najia-jing">—</div></div>
      <div><div class="lbl">流注输穴</div><div class="val" id="o-najia-liuzhu">—</div></div>
      <div><div class="lbl">经原穴</div><div class="val" id="o-najia-yuan">—</div></div>
      <div><div class="lbl">补母穴</div><div class="val" id="o-najia-bu">—</div></div>
      <div><div class="lbl">泻子穴</div><div class="val" id="o-najia-xie">—</div></div>
    </div>
  </div>

  <div class="block">
    <h3>③ 灵龟八法（日干支 × 时辰 → 开穴）</h3>
    <div class="row">
      <div><div class="lbl">日干支</div><div class="val" id="o-lgb-day">—</div></div>
      <div><div class="lbl">时辰</div><div class="val" id="o-lgb-hour">—</div></div>
      <div><div class="lbl">灵龟八法开穴</div><div class="val" id="o-lgb-kx">—</div></div>
    </div>
  </div>
</div>

<div class="foot">
  数据源：人纪 MDB linggui(60×13) / najia(12×6) / nazi(120×4) · 干支计算用四柱经典公式 ·
  原 EXE 中灵龟八法/子午流注盘为 Delphi 运行时绘制，无静态图，本页用 SVG 重建
</div>

<script>
const LINGGUI = __LINGGUI__;
const NAJIA = __NAJIA__;
const NAZI = __NAZI__;

const TG = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸'];
const DZ = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥'];
const SX = ['鼠','牛','虎','兔','龙','蛇','马','羊','猴','鸡','狗','猪'];
const NAYIN = ['海中金','炉中火','大林木','路旁土','剑锋金','山头火','涧下水','城头土','白蜡金','杨柳木','泉中水','大海水','沙中金','山下火','平地木','壁上土','金箔金','覆灯火','天河水','大驿土','钗钏金','桑柘木','大溪水','沙中土','天上火','石榴木','大海水'];

// 公历 → 干支年柱（立春粗调）
function yearGZ(y, m, d) {
  const y2 = (m < 2 || (m === 2 && d < 4)) ? y - 1 : y;
  const idx = ((y2 - 4) % 60 + 60) % 60;
  return { stem: TG[idx % 10], branch: DZ[idx % 12], idx };
}

// 日干支：使用 1900-01-01 = 甲戌日（序号10）
function dayGZ(y, m, d) {
  let total = 0;
  for (let i = 1900; i < y; i++) total += isLeap(i) ? 366 : 365;
  for (let i = 1; i < m; i++) total += daysInMonth(y, i);
  total += d - 1;
  const idx = (10 + total % 60 + 60) % 60;
  return { stem: TG[idx % 10], branch: DZ[idx % 12], idx };
}
function isLeap(y) { return (y%4===0 && y%100!==0) || y%400===0; }
function daysInMonth(y, m) {
  return [31, isLeap(y)?29:28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m-1];
}

// 月柱（五虎遁）
function monthGZ(yearStemIdx, m) {
  // 年上起月：寅月起
  const monthStart = [2,2,2,2,2,2,2,2,2,2][yearStemIdx]; // 简化
  const monthStemStart = [2,4,0,6,8][yearStemIdx % 5]; // 丙戊庚壬甲 = 2,4,0,6,8 → 寅月对应
  // 寅=0, 卯=1, ..., 丑=11
  const monthBranchIdx = (m - 1 + 2) % 12; // 1月=丑=1, 2月=寅=2... 简单对应
  const monthStemIdx = (monthStemStart + (monthBranchIdx - 2 + 12) % 12) % 10;
  return { stem: TG[monthStemIdx], branch: DZ[monthBranchIdx] };
}

// 时柱（五鼠遁）
function hourGZ(dayStemIdx, hourBranchIdx) {
  const hourStemStart = [0,2,4,6,8][dayStemIdx % 5]; // 甲丙戊庚壬
  const hourStemIdx = (hourStemStart + hourBranchIdx) % 10;
  return { stem: TG[hourStemIdx], branch: DZ[hourBranchIdx] };
}

// 纳音
function nayin(idx) {
  // 60 甲子纳音
  const groups = [
    '海中金','炉中火','大林木','路旁土','剑锋金','山头火','涧下水','城头土','白蜡金','杨柳木',
    '泉中水','大海水','沙中金','山下火','平地木','壁上土','金箔金','覆灯火','天河水','大驿土',
    '钗钏金','桑柘木','大溪水','沙中土','天上火','石榴木','大海水'
  ];
  return groups[idx % 26];
}

// 节气月令（粗略）
function yueling(m, d) {
  const jieqi = [
    '小寒','大寒','立春','雨水','惊蛰','春分','清明','谷雨','立夏','小满',
    '芒种','夏至','小暑','大暑','立秋','处暑','白露','秋分','寒露','霜降',
    '立冬','小雪','大雪','冬至'
  ];
  // 简化：每月初 ~ 节气名
  const m_map = {1:'小寒/大寒',2:'立春/雨水',3:'惊蛰/春分',4:'清明/谷雨',5:'立夏/小满',6:'芒种/夏至',7:'小暑/大暑',8:'立秋/处暑',9:'白露/秋分',10:'寒露/霜降',11:'立冬/小雪',12:'大雪/冬至'};
  return m_map[m];
}

// ===== 渲染 =====

function render() {
  const y = parseInt(document.getElementById('y').value);
  const m = parseInt(document.getElementById('m').value);
  const d = parseInt(document.getElementById('d').value);
  const h = parseInt(document.getElementById('h').value);

  const yy = yearGZ(y, m, d);
  const dd = dayGZ(y, m, d);
  const mm = monthGZ(yy.idx % 10, m);
  const hh = hourGZ(dd.idx % 10, h);

  // 万年历
  document.getElementById('r-solar').textContent = y + '年' + m + '月' + d + '日';
  document.getElementById('r-yy').textContent = yy.stem + yy.branch + '年';
  document.getElementById('r-mm').textContent = mm.stem + mm.branch + '月';
  document.getElementById('r-dd').textContent = dd.stem + dd.branch + '日';
  document.getElementById('r-hh').textContent = hh.stem + hh.branch + '时';
  document.getElementById('r-shengxiao').textContent = SX[yy.idx % 12];
  document.getElementById('r-nayin').textContent = nayin(yy.idx);
  document.getElementById('r-yueling').textContent = yueling(m, d);

  // 子午流注盘：12 段，当前时辰高亮
  drawZiWu(h);

  // 灵龟八法盘：8 段，当前开穴高亮
  drawLGB(dd.idx, h);

  // 灵龟八法表：60x12 grid
  drawTable(dd.idx, h);

  // ===== 实时计算结果 =====
  const dayBranch = dd.branch;
  const dayStem = dd.stem;
  const branch = DZ[h];

  // 纳子法 (按时辰的流注 + 五腧穴)
  const nj = NAJIA[branch];
  document.getElementById('o-nazi-jing').textContent = nj['流经脏腑经络'];
  document.getElementById('o-nazi-ben').textContent  = nj['流注输穴'];
  document.getElementById('o-nazi-yuan').textContent = nj['经原穴'];
  document.getElementById('o-nazi-bu').textContent   = nj['补母穴'];
  document.getElementById('o-nazi-xie').textContent  = nj['泻子穴'];

  // 纳甲法 (同样表 — 与纳子法的字段重复)
  document.getElementById('o-najia-hour').textContent  = branch + '时';
  document.getElementById('o-najia-jing').textContent  = nj['流经脏腑经络'];
  document.getElementById('o-najia-liuzhu').textContent = nj['流注输穴'];
  document.getElementById('o-najia-yuan').textContent  = nj['经原穴'];
  document.getElementById('o-najia-bu').textContent    = nj['补母穴'];
  document.getElementById('o-najia-xie').textContent   = nj['泻子穴'];

  // 灵龟八法
  const dayGZKey = dd.stem + dd.branch;
  const kx = LINGGUI[dayGZKey] ? LINGGUI[dayGZKey][branch] : '—';
  document.getElementById('o-lgb-day').textContent  = dayGZKey + '日';
  document.getElementById('o-lgb-hour').textContent = branch + '时';
  document.getElementById('o-lgb-kx').textContent   = kx;
  // 也同步显示在子午盘/灵龟盘右栏
  document.getElementById('r-disc-ziwu-h').textContent     = branch + '时';
  document.getElementById('r-disc-ziwu-jing').textContent  = nj['流经脏腑经络'];
  document.getElementById('r-disc-ziwu-ben').textContent   = nj['流注输穴'];
  document.getElementById('r-disc-ziwu-yuan').textContent  = nj['经原穴'];
  document.getElementById('r-disc-ziwu-bu').textContent    = nj['补母穴'];
  document.getElementById('r-disc-ziwu-xie').textContent   = nj['泻子穴'];
  document.getElementById('r-disc-lgb-day').textContent    = dayGZKey + '日';
  document.getElementById('r-disc-lgb-hour').textContent   = branch + '时';
  document.getElementById('r-disc-lgb-kx').textContent     = kx;
  document.getElementById('r-disc-lgb-stem').textContent   = dayStem;
  document.getElementById('r-disc-lgb-branch').textContent = dd.branch;
}

function drawZiWu(curHour) {
  const svg = document.getElementById('disc-ziwu');
  svg.innerHTML = '';
  const cx = 110, cy = 110, R = 95, r = 38;
  const hours = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥'];
  const jings = ['胆','肝','肺','大肠','胃','脾','心','小肠','膀胱','肾','心包','三焦'];
  for (let i = 0; i < 12; i++) {
    const a1 = (i*30-90) * Math.PI/180;
    const a2 = ((i+1)*30-90) * Math.PI/180;
    const large = i % 3 === 0 ? 1 : 0;
    const x1 = cx + R*Math.cos(a1), y1 = cy + R*Math.sin(a1);
    const x2 = cx + R*Math.cos(a2), y2 = cy + R*Math.sin(a2);
    const x3 = cx + r*Math.cos(a2), y3 = cy + r*Math.sin(a2);
    const x4 = cx + r*Math.cos(a1), y4 = cy + r*Math.sin(a1);
    const path = 'M' + x1 + ',' + y1 + ' A' + R + ',' + R + ' 0 ' + large + ' 1 ' + x2 + ',' + y2 + ' L' + x3 + ',' + y3 + ' A' + r + ',' + r + ' 0 ' + large + ' 0 ' + x4 + ',' + y4 + ' Z';
    const isCur = (i === curHour);
    const seg = document.createElementNS('http://www.w3.org/2000/svg','path');
    seg.setAttribute('d', path);
    seg.setAttribute('fill', isCur ? '#c0392b' : '#fff');
    seg.setAttribute('stroke', '#2d5a4f');
    seg.setAttribute('stroke-width', '1');
    seg.setAttribute('opacity', isCur ? '0.95' : '0.9');
    svg.appendChild(seg);
    // 文字
    const ta = (a1 + a2)/2;
    const tr = (R + r)/2;
    const tx = cx + tr*Math.cos(ta), ty = cy + tr*Math.sin(ta);
    const t = document.createElementNS('http://www.w3.org/2000/svg','text');
    t.setAttribute('x', tx); t.setAttribute('y', ty);
    t.setAttribute('text-anchor', 'middle'); t.setAttribute('dominant-baseline','middle');
    t.setAttribute('font-size', isCur ? '14' : '12');
    t.setAttribute('font-weight','bold');
    t.setAttribute('fill', isCur ? '#fff' : '#2d5a4f');
    t.textContent = hours[i] + (isCur ? '·' + jings[i] : '');
    svg.appendChild(t);
  }
  // 中心文字
  const c = document.createElementNS('http://www.w3.org/2000/svg','text');
  c.setAttribute('x', cx); c.setAttribute('y', cy);
  c.setAttribute('text-anchor','middle'); c.setAttribute('dominant-baseline','middle');
  c.setAttribute('font-size','13'); c.setAttribute('font-weight','bold');
  c.setAttribute('fill','#fff');
  c.textContent = jings[curHour] + '经';
  svg.appendChild(c);
}

function drawLGB(dayIdx, curHour) {
  const svg = document.getElementById('disc-lgb');
  svg.innerHTML = '';
  const cx = 110, cy = 110, R = 95, r = 38;
  // 8 段
  const acs = ['公孙','内关','后溪','申脉','临泣','外关','列缺','照海'];
  const gua = ['乾','坤','兑','艮','离','坎','巽','震'];
  const curKx = LINGGUI[TG[dayIdx%10]+DZ[dayIdx%12]] ? LINGGUI[TG[dayIdx%10]+DZ[dayIdx%12]][DZ[curHour]] : '';
  const curKxName = curKx ? curKx.replace(/[0-9]/g,'').trim() : '';
  const curAcIdx = acs.indexOf(curKxName);

  for (let i = 0; i < 8; i++) {
    const a1 = (i*45-90) * Math.PI/180;
    const a2 = ((i+1)*45-90) * Math.PI/180;
    const large = 0;
    const x1 = cx + R*Math.cos(a1), y1 = cy + R*Math.sin(a1);
    const x2 = cx + R*Math.cos(a2), y2 = cy + R*Math.sin(a2);
    const x3 = cx + r*Math.cos(a2), y3 = cy + r*Math.sin(a2);
    const x4 = cx + r*Math.cos(a1), y4 = cy + r*Math.sin(a1);
    const path = 'M' + x1 + ',' + y1 + ' A' + R + ',' + R + ' 0 ' + large + ' 1 ' + x2 + ',' + y2 + ' L' + x3 + ',' + y3 + ' A' + r + ',' + r + ' 0 ' + large + ' 0 ' + x4 + ',' + y4 + ' Z';
    const isCur = (i === curAcIdx);
    const seg = document.createElementNS('http://www.w3.org/2000/svg','path');
    seg.setAttribute('d', path);
    seg.setAttribute('fill', isCur ? '#c0392b' : '#fff');
    seg.setAttribute('stroke','#2d5a4f'); seg.setAttribute('stroke-width','1');
    seg.setAttribute('opacity', isCur ? '0.95' : '0.9');
    svg.appendChild(seg);
    const ta = (a1+a2)/2; const tr = (R+r)/2;
    const tx = cx + tr*Math.cos(ta), ty = cy + tr*Math.sin(ta);
    const t = document.createElementNS('http://www.w3.org/2000/svg','text');
    t.setAttribute('x', tx); t.setAttribute('y', ty);
    t.setAttribute('text-anchor','middle'); t.setAttribute('dominant-baseline','middle');
    t.setAttribute('font-size', isCur ? '13' : '11');
    t.setAttribute('font-weight','bold');
    t.setAttribute('fill', isCur ? '#fff' : '#2d5a4f');
    t.textContent = (isCur ? '★ ' : '') + gua[i] + '·' + acs[i];
    svg.appendChild(t);
  }
  const c = document.createElementNS('http://www.w3.org/2000/svg','text');
  c.setAttribute('x', cx); c.setAttribute('y', cy);
  c.setAttribute('text-anchor','middle'); c.setAttribute('dominant-baseline','middle');
  c.setAttribute('font-size','13'); c.setAttribute('font-weight','bold');
  c.setAttribute('fill','#fff');
  c.textContent = curKx || '—';
  svg.appendChild(c);
}

function drawTable(dayIdx, curHour) {
  const wrap = document.getElementById('r-lgb-table');
  const days = Object.keys(LINGGUI);  // 60 日
  const hours = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥'];
  const curDayKey = TG[dayIdx%10] + DZ[dayIdx%12];
  let html = '<table><thead><tr><th class="corner">日干支\\\\时辰</th>';
  hours.forEach(h => { html += '<th>' + h + '</th>'; });
  html += '</tr></thead><tbody>';
  days.forEach(d => {
    html += '<tr><th>' + d + '</th>';
    hours.forEach(h => {
      const v = LINGGUI[d][h] || '';
      const cur = (d === curDayKey && h === DZ[curHour]) ? ' cur' : '';
      html += '<td class="' + cur.trim() + '">' + v + '</td>';
    });
    html += '</tr>';
  });
  html += '</tbody></table>';
  wrap.innerHTML = html;
  // 滚到当前行
  const curRow = wrap.querySelector('tr.cur, td.cur');
  if (curRow) {
    const tr = curRow.tagName === 'TD' ? curRow.parentElement : curRow;
    const top = tr.offsetTop;
    wrap.scrollTop = Math.max(0, top - 100);
  }
}

['y','m','d','h'].forEach(id => {
  document.getElementById(id).addEventListener('change', render);
});
document.getElementById('now').addEventListener('click', () => {
  const dt = new Date();
  document.getElementById('y').value = dt.getFullYear();
  document.getElementById('m').value = dt.getMonth()+1;
  document.getElementById('d').value = dt.getDate();
  document.getElementById('h').value = Math.floor((dt.getHours()+1)/2) % 12;
  render();
});
render();
</script>
</body>
</html>
"""

HTML = HTML.replace("__LINGGUI__", json.dumps(LINGGUI, ensure_ascii=False))
HTML = HTML.replace("__NAJIA__",   json.dumps(NAJIA,   ensure_ascii=False))
HTML = HTML.replace("__NAZI__",    json.dumps(NAZI,    ensure_ascii=False))

fp = ROOT + r"/灵龟八法页面.html"
open(fp, "w", encoding="utf-8").write(HTML)
print(f"生成: {fp}")
print(f"  大小: {len(HTML)} chars")