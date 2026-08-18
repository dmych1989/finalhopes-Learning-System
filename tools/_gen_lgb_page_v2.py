# -*- coding: utf-8 -*-
"""Generate 灵龟八法页面.html v2 — 完整灵龟八法盘(月历版)/ SVG 按截图重画 + 4 模块新布局."""
import os, json

ROOT = r"E:/Soft/倪海夏三套学习系统/QQ频道号talktyph0id/人纪学习系统"
D = ROOT + r"/灵龟八法数据"

LINGGUI = json.load(open(D + "/linggui.json", encoding="utf-8"))
NAJIA   = json.load(open(D + "/najia.json",   encoding="utf-8"))
NAZI    = json.load(open(D + "/nazi.json",    encoding="utf-8"))
LUNAR   = json.load(open(D + "/lunar.json",   encoding="utf-8"))

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>万年历 · 灵龟八法盘 · 人纪学习系统</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, "Microsoft YaHei", sans-serif; background: #f5f1e8; color: #222; padding: 10px; line-height: 1.5; }
header { background: #2d5a4f; color: #fff; padding: 12px 18px; border-radius: 8px; margin-bottom: 10px; }
header h1 { font-size: 18px; }
header p { font-size: 12px; opacity: .85; margin-top: 4px; }

.layout { display: grid; grid-template-columns: 460px 1fr; gap: 12px; }
@media (max-width: 900px) { .layout { grid-template-columns: 1fr; } }

.leftcol { display: flex; flex-direction: column; gap: 10px; }
.selector { background: #fff; padding: 10px 14px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
.selector .row1 { display: grid; grid-template-columns: repeat(4, 1fr) auto; gap: 8px; align-items: center; }
.selector label { font-size: 11px; color: #555; display: block; }
.selector input, .selector select { padding: 4px 6px; font-size: 12px; border: 1px solid #ccc; border-radius: 3px; width: 100%; }
.selector button { padding: 5px 12px; font-size: 12px; background: #c0392b; color: #fff; border: none; border-radius: 4px; cursor: pointer; }

.computed { background: #fff; border-radius: 8px; padding: 10px 14px; box-shadow: 0 1px 3px rgba(0,0,0,.08); font-size: 12px; }
.computed h3 { font-size: 13px; color: #2d5a4f; margin: 6px 0 4px; padding-bottom: 3px; border-bottom: 1px solid #eee; }
.computed .blk { padding: 6px 8px; background: #fdf6e3; border-left: 3px solid #2d5a4f; border-radius: 3px; margin-bottom: 6px; }
.computed .row { display: flex; gap: 8px; flex-wrap: wrap; font-size: 11px; }
.computed .row > div { padding: 1px 0; }
.computed .lbl { color: #888; font-size: 10px; display: block; }
.computed .val { font-weight: bold; color: #c0392b; font-size: 13px; }

.cal { background: #fff; border-radius: 8px; padding: 10px 14px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
.cal h3 { font-size: 13px; color: #2d5a4f; margin-bottom: 6px; }
.cal .calhead { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.cal .calhead .ym { font-size: 14px; font-weight: bold; }
.cal table { border-collapse: collapse; width: 100%; font-size: 12px; }
.cal th, .cal td { border: 1px solid #e0d8c0; padding: 4px 2px; text-align: center; vertical-align: middle; height: 44px; }
.cal th { background: #fdf6e3; color: #5a4a30; font-weight: bold; font-size: 11px; }
.cal td.cur { background: #c0392b; color: #fff; font-weight: bold; }
.cal td.cur .lun { color: #fff; }
.cal td .solar { font-weight: bold; font-size: 13px; }
.cal td .lun { color: #999; font-size: 10px; margin-top: 2px; }
.cal td .jq { display: block; color: #c0392b; font-size: 9px; margin-top: 1px; }
.cal td.today .solar { background: #c0392b; color: #fff; border-radius: 50%; padding: 1px 5px; display: inline-block; }

/* 右侧大圆盘 */
.rightcol { background: #fff; border-radius: 8px; padding: 10px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
.disc-wrap { position: relative; width: 100%; }
.disc-wrap svg { width: 100%; max-width: 700px; height: auto; margin: 0 auto; display: block; }

.yq-info { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-top: 10px; font-size: 12px; }
.yq-info .card { background: #fdf6e3; border-radius: 4px; padding: 6px 10px; text-align: center; }
.yq-info .card .lbl { color: #888; font-size: 11px; }
.yq-info .card .val { font-weight: bold; color: #2d5a4f; }

.foot { text-align: center; font-size: 11px; color: #999; margin-top: 10px; }
</style>
</head>
<body>

<header>
  <h1>万年历 + 子午流注盘 + 圆形灵龟八法盘 + 灵龟八法表</h1>
  <p>四模块同页（左上选时间+实时计算 + 左下月历 + 右侧大圆盘） · 灵龟盘按截图结构 SVG 重建</p>
</header>

<div class="layout">

  <div class="leftcol">

    <div class="selector">
      <div class="row1">
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
      </div>
    </div>

    <div class="computed" id="computed">
      <h3>四柱 / 生肖</h3>
      <div class="blk" id="r-sizhu"></div>
      <h3>① 十二经纳子法（按时辰的本穴/源穴/补母/泻子）</h3>
      <div class="blk" id="r-nazi"></div>
      <h3>② 十二经纳甲法（按时辰的流注输穴/经原/补母/泻子）</h3>
      <div class="blk" id="r-najia"></div>
      <h3>③ 灵龟八法开穴（日干支 × 时辰）</h3>
      <div class="blk" id="r-lgb"></div>
    </div>

    <div class="cal">
      <div class="calhead">
        <button id="prev-m">◀</button>
        <span class="ym" id="cal-ym">2026年8月</span>
        <button id="next-m">▶</button>
      </div>
      <table id="cal-tbl">
        <thead><tr><th>日</th><th>一</th><th>二</th><th>三</th><th>四</th><th>五</th><th>六</th></tr></thead>
        <tbody id="cal-body"></tbody>
      </table>
    </div>

  </div>

  <div class="rightcol">

    <svg id="disc" viewBox="0 0 700 720" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <radialGradient id="discBg" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="#fefcf0"/>
          <stop offset="100%" stop-color="#f7eccf"/>
        </radialGradient>
      </defs>
      <!-- 主体由 JS 渲染 -->
    </svg>

    <div class="yq-info">
      <div class="card"><div class="lbl">年干支</div><div class="val" id="yq-y">—</div></div>
      <div class="card"><div class="lbl">中运</div><div class="val" id="yq-zy">—</div></div>
      <div class="card"><div class="lbl">司天 / 在泉</div><div class="val" id="yq-sq">—</div></div>
      <div class="card"><div class="lbl">当前节气</div><div class="val" id="yq-jq">—</div></div>
      <div class="card"><div class="lbl">主气</div><div class="val" id="yq-zq">—</div></div>
      <div class="card"><div class="lbl">客气</div><div class="val" id="yq-kq">—</div></div>
    </div>

  </div>

</div>

<div class="foot">
  数据源：人纪 MDB linggui/najia/nazi · 阴历数据 cnlunar 预抽 2024-2030 共 2557 天 · 圆盘 SVG 按原软件截图结构重建
</div>

<script>
const LINGGUI = __LINGGUI__;
const NAJIA = __NAJIA__;
const LUNAR = __LUNAR__;

const TG = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸'];
const DZ = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥'];
const SX = ['鼠','牛','虎','兔','龙','蛇','马','羊','猴','鸡','狗','猪'];
const NAYIN_FULL = ['海中金','炉中火','大林木','路旁土','剑锋金','山头火','涧下水','城头土','白蜡金','杨柳木','泉中水','大海水','沙中金','山下火','平地木','壁上土','金箔金','覆灯火','天河水','大驿土','钗钏金','桑柘木','大溪水','沙中土','天上火','石榴木','大海水'];
// 经
const JING = ['胆经','肝经','肺经','大肠经','胃经','脾经','心经','小肠经','膀胱经','肾经','心包经','三焦经'];
const JING_ABBR = ['胆','肝','肺','大肠','胃','脾','心','小肠','膀胱','肾','心包','三焦'];
// 八脉交穴 + 卦
const ACS = ['公孙','内关','后溪','申脉','足临泣','外关','列缺','照海'];
const GUA = ['乾','坤','兑','艮','离','坎','巽','震'];
const GUA_SYM = ['☰','☷','☱','☶','☲','☵','☴','☳'];
// 八卦颜色（4阳4阴）
const ACS_COLOR = ['#fdebd0','#fadbd8','#d6eaf8','#d4efdf','#fdebd0','#fadbd8','#d6eaf8','#d4efdf'];
const ACS_ACTIVE = '#a9dfbf'; // 当前开穴绿色

// 五运六气（单支为 key）
const SITIAN  = {'子':'少阴君火','午':'少阴君火','丑':'太阴湿土','未':'太阴湿土','寅':'少阳相火','申':'少阳相火','卯':'阳明燥金','酉':'阳明燥金','辰':'太阳寒水','戌':'太阳寒水','巳':'厥阴风木','亥':'厥阴风木'};
const ZAIQUAN = {'子':'阳明燥金','午':'阳明燥金','丑':'太阳寒水','未':'太阳寒水','寅':'厥阴风木','申':'厥阴风木','卯':'少阴君火','酉':'少阴君火','辰':'太阴湿土','戌':'太阴湿土','巳':'少阳相火','亥':'少阳相火'};
const ZHONGYUN = {'甲':'土运太过','己':'土运不及','乙':'金运不及','庚':'金运太过','丙':'水运太过','辛':'水运不及','丁':'木运不及','壬':'木运太过','戊':'火运太过','癸':'火运不及'};
// 主气 6 步按节气时序（固定）
const ZHUQI_PRIMARY = ['厥阴风木','少阴君火','少阳相火','太阴湿土','阳明燥金','太阳寒水'];
// 客气推导按三阴三阳序
const SAN_YIN_SAN_YANG = ['厥阴风木','少阴君火','太阴湿土','少阳相火','阳明燥金','太阳寒水'];
// 客气按 司天 + 位置：三之气=司天，客气六步循环 +offset
function keqi(sitian, step) {
  const idx = SAN_YIN_SAN_YANG.indexOf(sitian);
  if (idx < 0) return '';
  return SAN_YIN_SAN_YANG[(idx + step - 3 + 18) % 6];
}

// 节气 6 步分界（决定 主气/客气 是第几步）
const JIEQI_24 = [
  [1,5,'小寒'],[1,20,'大寒'],[2,4,'立春'],[2,19,'雨水'],
  [3,5,'惊蛰'],[3,20,'春分'],[4,4,'清明'],[4,19,'谷雨'],
  [5,5,'立夏'],[5,20,'小满'],[6,5,'芒种'],[6,21,'夏至'],
  [7,7,'小暑'],[7,22,'大暑'],[8,7,'立秋'],[8,23,'处暑'],
  [9,7,'白露'],[9,22,'秋分'],[10,8,'寒露'],[10,23,'霜降'],
  [11,7,'立冬'],[11,22,'小雪'],[12,7,'大雪'],[12,21,'冬至']
];
// 6 步分界：初之气大寒→春分、二之气春分→小满、三之气小满→大暑、四之气大暑→秋分、五之气秋分→小雪、终之气小雪→大寒
const JIEQI_6 = [
  [1,20,1],[3,20,2],[5,21,3],[7,22,4],[9,23,5],[11,22,6]
];
function getStep(y, m, d) {
  let curName = '小寒', curStep = 1;
  for (const [mm,dd,n] of JIEQI_24) {
    if (mm < m || (mm === m && dd <= d)) curName = n;
  }
  for (const [mm,dd,s] of JIEQI_6) {
    if (mm < m || (mm === m && dd <= d)) curStep = s;
  }
  return { name: curName, step: curStep };
}

// 四柱公式
function isLeap(y) { return (y%4===0 && y%100!==0) || y%400===0; }
function daysInMonth(y, m) { return [31, isLeap(y)?29:28, 31,30,31,30,31,31,30,31,30,31][m-1]; }

function yearGZ(y, m, d) {
  const y2 = (m < 2 || (m === 2 && d < 4)) ? y - 1 : y;
  const idx = ((y2 - 4) % 60 + 60) % 60;
  return { stem: TG[idx % 10], branch: DZ[idx % 12], idx };
}
function dayGZ(y, m, d) {
  let total = 0;
  for (let i = 1900; i < y; i++) total += isLeap(i) ? 366 : 365;
  for (let i = 1; i < m; i++) total += daysInMonth(y, i);
  total += d - 1;
  const idx = (10 + total % 60 + 60) % 60;
  return { stem: TG[idx % 10], branch: DZ[idx % 12], idx };
}
function monthGZ(yearStemIdx, m) {
  const monthStemStart = [2,4,0,6,8][yearStemIdx % 5];
  const monthBranchIdx = (m + 1) % 12;
  const monthStemIdx = (monthStemStart + (monthBranchIdx - 2 + 12) % 12) % 10;
  return { stem: TG[monthStemIdx], branch: DZ[monthBranchIdx] };
}
function hourGZ(dayStemIdx, h) {
  const hourStemStart = [0,2,4,6,8][dayStemIdx % 5];
  const hourStemIdx = (hourStemStart + h) % 10;
  return { stem: TG[hourStemIdx], branch: DZ[h] };
}
function nayin60(idx) {
  // 60甲子纳音，每2个一组
  const arr = ['海中金','炉中火','大林木','路旁土','剑锋金','山头火','涧下水','城头土','白蜡金','杨柳木','泉中水','大海水','沙中金','山下火','平地木','壁上土','金箔金','覆灯火','天河水','大驿土','钗钏金','桑柘木','大溪水','沙中土','天上火','石榴木','大海水'];
  return arr[Math.floor(idx / 2) % 26];
}

// ========= 圆盘 SVG 绘制 =========
function drawDisc(h, dayBranchIdx) {
  const svg = document.getElementById('disc');
  // 先保留 defs
  svg.innerHTML = '<defs><radialGradient id="discBg" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="#fefcf0"/><stop offset="100%" stop-color="#f7eccf"/></radialGradient></defs>';
  const cx = 350, cy = 360;
  const R_HOUR = 310;      // 24小时数字外环
  const R_TIANGAN = 270;   // 24小时配天干 (用于逐时取日干)
  const R_SHICHEN = 240;   // 12时辰
  const R_JING = 200;      // 12经脉简写
  const R_ACS_INNER = 100; // 八脉交穴扇形内半径
  const R_ACS_OUTER = 175; // 八脉交穴扇形外半径

  // 背景大圆
  const bg = document.createElementNS('http://www.w3.org/2000/svg','circle');
  bg.setAttribute('cx',cx); bg.setAttribute('cy',cy); bg.setAttribute('r', R_HOUR+8);
  bg.setAttribute('fill','url(#discBg)'); bg.setAttribute('stroke','#5a4a30'); bg.setAttribute('stroke-width','2');
  svg.appendChild(bg);

  // 子时位置：传统子时 = 23点位置（0点偏左），每时辰30° = 每小时15°
  // 子时居中23:00，丑=1, 寅=3, ..., 亥=21。 每时辰从 h*2+1 开始
  // 角度：子时中心 = 270°(正上)，每小时顺时针15° → 1点 = 285°...23点=255°
  // 简化：让 子时 在顶部(270°)，每小时 +15°，0点 = 子时偏右7.5° → 即子时中心对应 23:00
  // 决定：用 0=北 顺时针。子时中心=23:00 (对应 北偏西 7.5° = 角度 360-7.5 = 352.5°)
  // 实际上让 子 在最上方 (-90° = 270°)，丑=1点偏右(285°)，寅=3点(285+30=315°)，...
  // 这里用标准做法：子时（23-1）中心=北(270°)，每时辰中心 = 子时+30°
  // 即 子=270°, 丑=300°, 寅=330°, 卯=0°, 辰=30°, 巳=60°, 午=90°, 未=120°, 申=150°, 酉=180°, 戌=210°, 亥=240°
  // 对应24小时数字(0-23)：0点=270°+15°/2=277.5°(即 0点在子时和丑时之间偏右)
  // 简化为：24小时数字位置 = (hour*15 - 90)°，子时标签覆盖 23+0 共2小时
  function pos(hour, r) {
    const a = (hour * 15 - 90) * Math.PI / 180;
    return { x: cx + r*Math.cos(a), y: cy + r*Math.sin(a), a: a };
  }
  function pos2(deg, r) {
    const a = (deg - 90) * Math.PI / 180;
    return { x: cx + r*Math.cos(a), y: cy + r*Math.sin(a), a: a };
  }

  // 1. 24小时数字外环
  for (let hh = 0; hh < 24; hh++) {
    const p = pos(hh, R_HOUR);
    const t = document.createElementNS('http://www.w3.org/2000/svg','text');
    t.setAttribute('x', p.x); t.setAttribute('y', p.y);
    t.setAttribute('text-anchor','middle'); t.setAttribute('dominant-baseline','middle');
    t.setAttribute('font-size', hh % 3 === 0 ? '13' : '11');
    t.setAttribute('fill', '#5a4a30');
    t.textContent = hh;
    svg.appendChild(t);
  }

  // 2. 时辰环（12个，覆盖该时辰2小时范围）
  const SHICHEN_NAMES = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥'];
  // 时辰名 = 12，每时辰中心 = 子对应23点 → 在 hour = 23 位置 (旋转 345° = 子中心)
  // 但 pos() 中 0点=277.5°。子时覆盖 23,0 共2小时，中心在23点 = 270°。调整：
  // 时辰h中心 = (23 - h*2) 小时位（取模24）
  // 23点对应 pos 345°, 0点对应 pos 0°, 所以子时中心在 23点位置 = 345°
  // 丑时中心 = 1点 = 15°, 寅=3点=45°, ... 亥=21点=285°
  for (let i = 0; i < 12; i++) {
    const hourIdx = (23 + i*2) % 24;  // 子→23, 丑→1, 寅→3, ...
    const p = pos(hourIdx, R_TIANGAN);
    const t = document.createElementNS('http://www.w3.org/2000/svg','text');
    t.setAttribute('x', p.x); t.setAttribute('y', p.y);
    t.setAttribute('text-anchor','middle'); t.setAttribute('dominant-baseline','middle');
    t.setAttribute('font-size', '14'); t.setAttribute('font-weight','bold');
    t.setAttribute('fill', '#2d5a4f');
    t.textContent = SHICHEN_NAMES[i];
    svg.appendChild(t);
  }

  // 3. 12 经脉简写环（每个时辰位置内）
  for (let i = 0; i < 12; i++) {
    const hourIdx = (23 + i*2) % 24;
    const p = pos(hourIdx, R_JING);
    const t = document.createElementNS('http://www.w3.org/2000/svg','text');
    t.setAttribute('x', p.x); t.setAttribute('y', p.y);
    t.setAttribute('text-anchor','middle'); t.setAttribute('dominant-baseline','middle');
    t.setAttribute('font-size', '11');
    t.setAttribute('fill', '#5a4a30');
    t.textContent = JING_ABBR[i];
    svg.appendChild(t);
  }

  // 4. 八脉交穴 8 段扇形（卦+交穴）
  // 当前开穴：来自 linggui[日干支][时辰] → 解析 交穴名
  const dayGZKey = TG[dayBranchIdx % 10] + DZ[dayBranchIdx % 12];
  const kx = LINGGUI[dayGZKey] ? LINGGUI[dayGZKey][DZ[h]] : '';
  const kxName = kx ? kx.replace(/[0-9]/g,'').trim() : '';
  const activeIdx = ACS.indexOf(kxName);

  for (let i = 0; i < 8; i++) {
    // 8 段 = 45° 每段，中心位置：8卦在8方位 (北/东北/东/东南/南/西南/西/西北)
    // 按截图：兑在西北(135°), 巽在东北(45°), 离在西南(225°), 坎在东南(-45°=315°)
    // 乾(东90°), 坤(西180°?), 震(南?), 艮(北?)
    // 简化：从子(345°)开始每 45° 一段（i*45+345）
    const a1 = (i * 45 + 345 - 22.5 - 90) * Math.PI / 180;
    const a2 = (i * 45 + 345 + 22.5 - 90) * Math.PI / 180;
    const x1 = cx + R_ACS_OUTER*Math.cos(a1), y1 = cy + R_ACS_OUTER*Math.sin(a1);
    const x2 = cx + R_ACS_OUTER*Math.cos(a2), y2 = cy + R_ACS_OUTER*Math.sin(a2);
    const x3 = cx + R_ACS_INNER*Math.cos(a2), y3 = cy + R_ACS_INNER*Math.sin(a2);
    const x4 = cx + R_ACS_INNER*Math.cos(a1), y4 = cy + R_ACS_INNER*Math.sin(a1);
    const path = 'M' + x1 + ',' + y1 + ' A' + R_ACS_OUTER + ',' + R_ACS_OUTER + ' 0 0 1 ' + x2 + ',' + y2 + ' L' + x3 + ',' + y3 + ' A' + R_ACS_INNER + ',' + R_ACS_INNER + ' 0 0 0 ' + x4 + ',' + y4 + ' Z';
    const isActive = (i === activeIdx);
    const seg = document.createElementNS('http://www.w3.org/2000/svg','path');
    seg.setAttribute('d', path);
    seg.setAttribute('fill', isActive ? ACS_ACTIVE : ACS_COLOR[i]);
    seg.setAttribute('stroke', '#8b6f47'); seg.setAttribute('stroke-width', '1');
    svg.appendChild(seg);
    // 文字 (卦 + 交穴)
    const ta = (a1 + a2) / 2;
    const tr = (R_ACS_INNER + R_ACS_OUTER) / 2;
    const tx = cx + tr*Math.cos(ta), ty = cy + tr*Math.sin(ta);
    const t = document.createElementNS('http://www.w3.org/2000/svg','text');
    t.setAttribute('x', tx); t.setAttribute('y', ty);
    t.setAttribute('text-anchor','middle'); t.setAttribute('dominant-baseline','middle');
    t.setAttribute('font-size', isActive ? '14' : '12');
    t.setAttribute('font-weight','bold');
    t.setAttribute('fill', isActive ? '#1e4a3f' : '#2d5a4f');
    t.textContent = GUA[i] + GUA_SYM[i] + '\n' + ACS[i];
    svg.appendChild(t);
  }

  // 5. 九宫 9 点 (3x3) 中心
  const JG = [[4,9,2],[3,5,7],[8,1,6]];  // 洛书序
  for (let r = 0; r < 3; r++) {
    for (let c = 0; c < 3; c++) {
      const x = cx - 30 + c * 30;
      const y = cy - 30 + r * 30;
      const c1 = document.createElementNS('http://www.w3.org/2000/svg','circle');
      c1.setAttribute('cx', x); c1.setAttribute('cy', y); c1.setAttribute('r', 9);
      c1.setAttribute('fill', '#fdebd0'); c1.setAttribute('stroke','#8b6f47');
      svg.appendChild(c1);
      const t = document.createElementNS('http://www.w3.org/2000/svg','text');
      t.setAttribute('x', x); t.setAttribute('y', y);
      t.setAttribute('text-anchor','middle'); t.setAttribute('dominant-baseline','middle');
      t.setAttribute('font-size', '12'); t.setAttribute('font-weight','bold'); t.setAttribute('fill','#2d5a4f');
      t.textContent = JG[r][c];
      svg.appendChild(t);
    }
  }

  // 6. 当前时间指针（红箭头从中心指向当前小时位）
  const curHour = (h * 2 + 1) % 24;  // 子时=23, 丑时=1, ... 亥时=21
  const curHourDisp = h * 2 + (h === 0 ? 23 : h === 11 ? 21 : 0); // 修正
  // 简单：curHour = (h*2 + 1) % 24... 子时h=0 → 1，丑h=1→3... 这是 "h时开始"
  // 但 h=0(子时) 起于23点结束于1点 → 指针居中位置应该是 0点
  const curPos = ((h * 2 + 1) % 24);
  const pp = pos(curPos, R_HOUR - 20);
  const pointer = document.createElementNS('http://www.w3.org/2000/svg','line');
  pointer.setAttribute('x1', cx); pointer.setAttribute('y1', cy);
  pointer.setAttribute('x2', pp.x); pointer.setAttribute('y2', pp.y);
  pointer.setAttribute('stroke', '#c0392b'); pointer.setAttribute('stroke-width', '3');
  pointer.setAttribute('marker-end','url(#arrowhead)');
  // arrowhead
  const defs = svg.querySelector('defs');
  const marker = document.createElementNS('http://www.w3.org/2000/svg','marker');
  marker.setAttribute('id','arrowhead'); marker.setAttribute('markerWidth','10'); marker.setAttribute('markerHeight','10');
  marker.setAttribute('refX','5'); marker.setAttribute('refY','3'); marker.setAttribute('orient','auto');
  const arrow = document.createElementNS('http://www.w3.org/2000/svg','polygon');
  arrow.setAttribute('points','0 0, 6 3, 0 6'); arrow.setAttribute('fill','#c0392b');
  marker.appendChild(arrow); defs.appendChild(marker);
  svg.appendChild(pointer);

  // 7. 中心当前开穴文字
  const center = document.createElementNS('http://www.w3.org/2000/svg','text');
  center.setAttribute('x', cx); center.setAttribute('y', cy + 70);
  center.setAttribute('text-anchor','middle'); center.setAttribute('font-size','14');
  center.setAttribute('font-weight','bold'); center.setAttribute('fill','#c0392b');
  center.textContent = '开穴：' + kx;
  svg.appendChild(center);
}

// ========= 月历 =========
function drawCal(y, m, curD) {
  document.getElementById('cal-ym').textContent = y + '年' + m + '月';
  const key = y + '-' + (m < 10 ? '0' : '') + m;
  const data = LUNAR[key];
  if (!data) {
    document.getElementById('cal-body').innerHTML = '<tr><td colspan="7">超出预抽范围（2024-2030）</td></tr>';
    return;
  }
  // 第一天 weekday -> 0=日,1=一,...
  const firstDay = new Date(y, m-1, 1).getDay();  // 0=Sunday
  let html = '';
  let cell = 0;
  for (let i = 0; i < firstDay; i++) { html += '<td></td>'; cell++; }
  for (const day of data) {
    const isCur = (day.d === curD);
    const isToday = (day.jieqi !== '');  // 节气日标红
    let cls = '';
    if (isCur) cls += 'cur ';
    let html2 = '<div class="solar">' + day.d + '</div>';
    if (day.jieqi) html2 += '<span class="jq">' + day.jieqi + '</span>';
    html2 += '<div class="lun">' + (day.lunar || '') + '</div>';
    html += '<td class="' + cls.trim() + '">' + html2 + '</td>';
    cell++;
    if (cell % 7 === 0 && day.d !== data.length) html += '</tr><tr>';
  }
  // 补空
  while (cell % 7 !== 0) { html += '<td></td>'; cell++; }
  document.getElementById('cal-body').innerHTML = html;
}

// ========= 主渲染 =========
function render() {
  const y = parseInt(document.getElementById('y').value);
  const m = parseInt(document.getElementById('m').value);
  const d = parseInt(document.getElementById('d').value);
  const h = parseInt(document.getElementById('h').value);

  const yy = yearGZ(y, m, d);
  const dd = dayGZ(y, m, d);
  const mm = monthGZ(yy.idx % 10, m);
  const hh = hourGZ(dd.idx % 10, h);
  const dayGZKey = dd.stem + dd.branch;
  const kx = LINGGUI[dayGZKey] ? LINGGUI[dayGZKey][DZ[h]] : '—';
  const nj = NAJIA[DZ[h]];

  // 四柱
  document.getElementById('r-sizhu').innerHTML =
    '<div class="row">' +
      '<div><span class="lbl">公历</span><span class="val">' + y + '年' + m + '月' + d + '日</span></div>' +
      '<div><span class="lbl">年柱</span><span class="val">' + yy.stem + yy.branch + '年</span></div>' +
      '<div><span class="lbl">月柱</span><span class="val">' + mm.stem + mm.branch + '月</span></div>' +
      '<div><span class="lbl">日柱</span><span class="val">' + dd.stem + dd.branch + '日</span></div>' +
      '<div><span class="lbl">时柱</span><span class="val">' + hh.stem + hh.branch + '时</span></div>' +
      '<div><span class="lbl">生肖</span><span class="val">' + SX[yy.idx % 12] + '</span></div>' +
      '<div><span class="lbl">纳音</span><span class="val">' + nayin60(yy.idx) + '</span></div>' +
    '</div>';

  // 纳子
  document.getElementById('r-nazi').innerHTML =
    '<div class="row">' +
      '<div><span class="lbl">流经脏腑经络</span><span class="val">' + nj['流经脏腑经络'] + '</span></div>' +
      '<div><span class="lbl">本穴</span><span class="val">' + nj['流注输穴'] + '</span></div>' +
      '<div><span class="lbl">源穴</span><span class="val">' + nj['经原穴'] + '</span></div>' +
      '<div><span class="lbl">补母穴</span><span class="val">' + nj['补母穴'] + '</span></div>' +
      '<div><span class="lbl">泻子穴</span><span class="val">' + nj['泻子穴'] + '</span></div>' +
    '</div>';

  // 纳甲 (字段同名，同数据)
  document.getElementById('r-najia').innerHTML =
    '<div class="row">' +
      '<div><span class="lbl">流注时辰</span><span class="val">' + DZ[h] + '时</span></div>' +
      '<div><span class="lbl">流经脏腑经络</span><span class="val">' + nj['流经脏腑经络'] + '</span></div>' +
      '<div><span class="lbl">流注输穴</span><span class="val">' + nj['流注输穴'] + '</span></div>' +
      '<div><span class="lbl">经原穴</span><span class="val">' + nj['经原穴'] + '</span></div>' +
      '<div><span class="lbl">补母穴</span><span class="val">' + nj['补母穴'] + '</span></div>' +
      '<div><span class="lbl">泻子穴</span><span class="val">' + nj['泻子穴'] + '</span></div>' +
    '</div>';

  // 灵龟
  document.getElementById('r-lgb').innerHTML =
    '<div class="row">' +
      '<div><span class="lbl">日干支</span><span class="val">' + dayGZKey + '</span></div>' +
      '<div><span class="lbl">时辰</span><span class="val">' + DZ[h] + '时</span></div>' +
      '<div><span class="lbl">灵龟八法开穴</span><span class="val">' + kx + '</span></div>' +
    '</div>';

  // 圆盘
  drawDisc(h, dd.idx);

  // 五运六气
  const yz = yy.stem + yy.branch;
  const st = SITIAN[yy.branch + ''] || SITIAN[(yy.branch)];
  const zy = ZHONGYUN[yy.stem] || '';
  const zq = ZAIQUAN[yy.branch] || '';
  document.getElementById('yq-y').textContent = yz + '年';
  document.getElementById('yq-zy').textContent = zy;
  document.getElementById('yq-sq').textContent = st + ' / ' + zq;
  const { name: jq, step } = getStep(y, m, d);
  document.getElementById('yq-jq').textContent = jq;
  document.getElementById('yq-zq').textContent = ZHUQI_PRIMARY[step-1];
  document.getElementById('yq-kq').textContent = keqi(st, step);

  // 月历
  drawCal(y, m, d);
}

['y','m','d','h'].forEach(id => document.getElementById(id).addEventListener('change', render));
document.getElementById('now').addEventListener('click', () => {
  const dt = new Date();
  document.getElementById('y').value = dt.getFullYear();
  document.getElementById('m').value = dt.getMonth()+1;
  document.getElementById('d').value = dt.getDate();
  document.getElementById('h').value = Math.floor((dt.getHours()+1)/2) % 12;
  render();
});
document.getElementById('prev-m').addEventListener('click', () => {
  let m = parseInt(document.getElementById('m').value);
  let y = parseInt(document.getElementById('y').value);
  m--; if (m < 1) { m = 12; y--; }
  document.getElementById('m').value = m;
  document.getElementById('y').value = y;
  render();
});
document.getElementById('next-m').addEventListener('click', () => {
  let m = parseInt(document.getElementById('m').value);
  let y = parseInt(document.getElementById('y').value);
  m++; if (m > 12) { m = 1; y++; }
  document.getElementById('m').value = m;
  document.getElementById('y').value = y;
  render();
});

render();
</script>
</body>
</html>
"""

HTML = HTML.replace("__LINGGUI__", json.dumps(LINGGUI, ensure_ascii=False))
HTML = HTML.replace("__NAJIA__",   json.dumps(NAJIA,   ensure_ascii=False))
HTML = HTML.replace("__LUNAR__",    json.dumps(LUNAR,   ensure_ascii=False))

fp = ROOT + r"/灵龟八法页面.html"
open(fp, "w", encoding="utf-8").write(HTML)
print(f"生成: {fp}")
print(f"  大小: {len(HTML)} chars")
print(f"  lunar.json: {os.path.getsize(D+'/lunar.json')} bytes ({sum(len(v) for v in LUNAR.values())} 天)")