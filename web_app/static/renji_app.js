/* 人纪学习系统 · 前端（独立，不依赖 app.js）
 * 五大板块：穴位详解 / 灵龟八法 / 子午流注 / 汉唐取穴 / 动画演示
 * 与「人纪针灸」EXE 菜单一致。
 */
(function () {
  "use strict";

  // ---------- 注入样式 ----------
  const CSS = `
  .board-tabs{display:flex;flex-wrap:wrap;gap:6px;padding:10px 14px;background:#15324a;
    border-bottom:2px solid #0c2236;position:sticky;top:0;z-index:20}
  .board-tab{padding:8px 14px;border-radius:8px 8px 0 0;color:#cfe3f2;cursor:pointer;
    font-size:15px;font-weight:600;border:1px solid transparent;white-space:nowrap}
  .board-tab:hover{background:#1d4a66}
  .board-tab.active{background:#0c2236;color:#ffd479;border-color:#0c2236;border-bottom:none}
  .sub-group-title{font-weight:700;color:#9fc1da;padding:8px 12px 4px;font-size:13px;
    background:#11304a;border-radius:6px;margin:6px 6px 2px}
  .tu-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;padding:10px}
  .tu-cell{border:1px solid #245;background:#0f2a40;border-radius:8px;overflow:hidden;cursor:pointer}
  .tu-cell:hover{border-color:#ffd479}
  .tu-cell img{width:100%;height:130px;object-fit:contain;background:#fff}
  .tu-cell .cap{font-size:12px;padding:4px 6px;color:#cfe3f2;line-height:1.3}
  .tool-panel{padding:14px;color:#dfeefb}
  .tool-panel label{display:inline-block;margin:4px 8px 4px 0;color:#bcd}
  .tool-panel input,.tool-panel select{padding:5px 8px;border-radius:6px;border:1px solid #357;
    background:#0c2236;color:#fff;font-size:14px}
  .gz-result{display:flex;flex-wrap:wrap;gap:10px;margin:12px 0}
  .gz-card{background:#0f2a40;border:1px solid #2a5;border-radius:8px;padding:8px 12px;text-align:center;min-width:78px}
  .gz-card .lab{font-size:12px;color:#9fc1da}
  .gz-card .val{font-size:20px;font-weight:700;color:#ffd479}
  .open-list{margin-top:10px}
  .open-list .op{background:#0f2a40;border-left:3px solid #ffd479;padding:6px 10px;margin:5px 0;border-radius:4px}
  .dial-wrap{display:flex;gap:20px;flex-wrap:wrap;align-items:center}
  .dial{width:340px;height:340px}
  .dial .cell{fill:#0f2a40;stroke:#2a5;stroke-width:1.5}
  .dial .cell.hot{fill:#ffd479;stroke:#fff}
  .dial .lbl{fill:#dfeefb;font-size:15px;text-anchor:middle;font-weight:600}
  .dial .num{fill:#7fa;font-size:11px;text-anchor:middle}
  .anim-stage{background:#04121f;border-radius:10px;padding:8px}
  .anim-stage .body{stroke:#3a6f9a;stroke-width:2;fill:#0a2236}
  .mer-path{fill:none;stroke-width:3;stroke-linecap:round;opacity:.85}
  .mer-dot{fill:#fff;r:5}
  .mer-comet{fill:#ffd479;r:6}
  .anim-cap{color:#ffd479;font-weight:700;font-size:16px;margin:6px 0}
  .anim-art{color:#cfe3f2;line-height:1.8;white-space:pre-wrap;max-height:300px;overflow:auto;
    background:#0c2236;padding:10px;border-radius:8px;margin-top:8px}
  .mer-filter{display:flex;flex-wrap:wrap;gap:6px;padding:6px 10px}
  .mer-filter button{background:#11304a;color:#cfe3f2;border:1px solid #2a5;border-radius:14px;
    padding:4px 12px;cursor:pointer;font-size:13px}
  .mer-filter button.active{background:#ffd479;color:#102;font-weight:700}
  .point-card{border:1px solid #2a5;background:#0f2a40;border-radius:8px;padding:10px;margin:8px 0}
  .point-card h4{color:#ffd479;margin:0 0 6px}
  .point-card .sec{margin:4px 0}
  .point-card .sec b{color:#9fc1da}
  .nishi-box{border-top:1px dashed #2a5;margin-top:8px;padding-top:6px}
  .table-scroll{overflow:auto}
  table.zi{border-collapse:collapse;width:100%;font-size:13px}
  table.zi th,table.zi td{border:1px solid #2a5;padding:4px 8px;text-align:center;color:#dfeefb;white-space:nowrap}
  table.zi th{background:#11304a;color:#ffd479}
  `;
  const st = document.createElement("style");
  st.textContent = CSS;
  document.head.appendChild(st);

  // ---------- 工具 ----------
  const $ = (s, r) => (r || document).querySelector(s);
  const el = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; };
  function getJSON(url) {
    return new Promise((res, rej) => {
      fetch(url).then(r => r.json()).then(res).catch(rej);
    });
  }
  function esc(s) { return (s == null ? "" : String(s)).replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c])); }

  const sidebar = $("#sidebar"), boardTabs = $("#boardTabs"),
        moduleHead = $("#moduleHead"), listHint = $("#listHint"),
        resultList = $("#resultList"), detailPane = $("#detailPane"),
        filterBar = $("#filterBar"), pager = $("#pager");

  let BOARDS = [], CUR_BOARD = null, CUR_SUB = null;

  // ---------- 干支算法（万年历 / 四柱） ----------
  const GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"];
  const ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"];
  const ZHI_HOUR = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]; // 子丑寅卯辰巳午未申酉戌亥
  function gzIdx(g, z) { for (let i = 0; i < 60; i++) if (i % 10 === g && i % 12 === z) return i; return 0; }
  function yearGZ(y) { return GAN[((y - 4) % 10 + 10) % 10] + ZHI[((y - 4) % 12 + 12) % 12]; }
  function jdn(y, m, d) {
    const a = Math.floor((14 - m) / 12);
    const yy = y + 4800 - a, mm = m + 12 * a - 3;
    return d + Math.floor((153 * mm + 2) / 5) + 365 * yy + Math.floor(yy / 4)
         - Math.floor(yy / 100) + Math.floor(yy / 400) - 32045;
  }
  function dayGZ(y, m, d) {
    const j = jdn(y, m, d);
    const idx = ((j + 49) % 60 + 60) % 60;
    return { idx, g: idx % 10, z: idx % 12, str: GAN[idx % 10] + ZHI[idx % 12] };
  }
  // 节气近似（用于定月柱起点）：返回该年各「节」的公历月-日（寅月起）
  const SOLAR = [[2,4],[3,6],[4,5],[5,6],[6,6],[7,7],[8,8],[9,8],[10,8],[11,7],[12,7],[1,6]];
  function monthIndex(y, m, d) {
    for (let i = 0; i < 12; i++) { const [sm, sd] = SOLAR[i];
      const ny = (i === 11) ? y + 1 : y;
      const cur = (m === sm && d >= sd);
      const prevM = SOLAR[(i + 11) % 12][0], prevY = (i === 0) ? y - 1 : y, prevD = SOLAR[(i + 11) % 12][1];
      const prev = (m === prevM && d >= prevD) || (m === sm && d < sd && (i !== 0 || true));
      if (m === sm && d >= sd) return i;
      if (i > 0 && m === SOLAR[i - 1][0] && d >= SOLAR[i - 1][1] && d < sd) return i - 1;
    }
    // 1月6日前属上年丑月(index 11)
    if (m === 1 && d < 6) return 11;
    return 0;
  }
  function monthGZ(y, m, d) {
    const mi = monthIndex(y, m, d); // 0=寅
    const ys = ((y - 4) % 10 + 10) % 10; // 年干
    const base = (ys * 2 + 2) % 10;       // 五虎遁 寅月天干
    const g = (base + mi) % 10;
    const z = (2 + mi) % 12;              // 寅=2
    return { str: GAN[g] + ZHI[z], mi };
  }
  function hourBranch(h) { return Math.floor(((h + 1) % 24) / 2); } // 23-1子...
  function hourGZ(h, dayG) {
    const b = hourBranch(h);
    const base = (dayG * 2) % 10; // 五鼠遁 子时天干
    const g = (base + b) % 10;
    return { str: GAN[g] + ZHI[b], b };
  }

  // ---------- 板块 / 子模块 渲染 ----------
  function renderBoards() {
    boardTabs.innerHTML = "";
    BOARDS.forEach(b => {
      const t = el("div", "board-tab", esc(b.name) + " <span style='opacity:.6'>(" + b.count + ")</span>");
      t.onclick = () => selectBoard(b);
      if (b === CUR_BOARD) t.classList.add("active");
      boardTabs.appendChild(t);
    });
  }
  function selectBoard(b) {
    CUR_BOARD = b; CUR_SUB = null;
    renderBoards();
    sidebar.innerHTML = "";
    const walk = (subs) => subs.forEach(s => {
      if (s.subs) {
        sidebar.appendChild(el("div", "sub-group-title", esc(s.name)));
        walk(s.subs);
      } else {
        const it = el("div", "sub-item", esc(s.name));
        it.onclick = () => selectSub(s);
        sidebar.appendChild(it);
      }
    });
    walk(b.subs);
    // 默认选中第一个子模块
    const first = firstLeaf(b);
    if (first) selectSub(first);
  }
  function firstLeaf(b) {
    for (const s of b.subs) { if (s.subs) { const f = firstLeaf({ subs: s.subs }); if (f) return f; } else return s; }
    return null;
  }
  function selectSub(s) {
    CUR_SUB = s;
    [...sidebar.querySelectorAll(".sub-item")].forEach(x => x.classList.remove("active"));
    // 高亮当前
    const items = [...sidebar.querySelectorAll(".sub-item")];
    // naive: 重新渲染高亮
    [...sidebar.children].forEach(c => { if (c.textContent.trim() === s.name) c.classList.add("active"); });
    moduleHead.innerHTML = "<h2>" + esc(s.name) + "</h2><p class='brand-sub'>" + esc(s.desc || "") + "</p>";
    listHint.style.display = "none";
    pager.innerHTML = ""; filterBar.innerHTML = "";
    dispatchSub(s);
  }

  function dispatchSub(s) {
    resultList.innerHTML = ""; detailPane.innerHTML = "<div class='hint'>点击左侧条目查看详情。</div>";
    const k = s.kind;
    if (k === "meridians") return renderMeridians(s);
    if (k === "points") return renderPoints(s);
    if (k === "fields") return renderFields(s);
    if (k === "image") return renderImages(s);
    if (k === "ziwwu_table") return renderZiwwuTable(s);
    if (k === "hantang_method") return renderHantang(s);
    if (k === "cross") return renderCross(s);
    if (k === "tool") return renderTool(s);
    if (k === "animation") return renderAnimation(s);
  }

  // ---------- 穴位详解：十四经络 ----------
  function renderMeridians(s) {
    filterBar.innerHTML = "<div class='hint' style='padding:4px'>十四经络穴位（主系统《中医》分组 + 倪师注解）</div>";
    getJSON("/api/renji/meridians").then(ms => {
      const wrap = el("div", "mer-filter");
      ms.forEach(m => {
        const b = el("button", null, esc(m.label) + " (" + m.count + ")");
        b.onclick = () => loadMeridian(m);
        wrap.appendChild(b);
      });
      resultList.appendChild(wrap);
      resultList._ms = ms;
      if (ms[0]) loadMeridian(ms[0]);
    });
  }
  function loadMeridian(m) {
    [...resultList.querySelectorAll(".mer-filter button")].forEach(b => b.classList.remove("active"));
    [...resultList.querySelectorAll(".mer-filter button")].forEach(b => { if (b.textContent.startsWith(m.label)) b.classList.add("active"); });
    getJSON("/api/renji/meridian/" + m.key).then(d => {
      // 重建列表（去掉 filter bar）
      const keep = resultList.querySelector(".mer-filter");
      resultList.innerHTML = ""; resultList.appendChild(keep);
      d.items.forEach((p, i) => {
        const li = el("li", "result-item", esc(p.name) + (p.sub ? " <span style='opacity:.6'>· " + esc(p.sub) + "</span>" : ""));
        li.onclick = () => showPoint(p);
        resultList.appendChild(li);
      });
    });
  }
  function showPoint(p) {
    let h = "<div class='point-card'><h4>" + esc(p.name) + "　<span style='opacity:.6'>「" + esc(p.cat_name) + "」</span></h4>";
    const secs = [["治疗症状", "治疗症状"], ["取穴位置", "取穴位置"], ["针刺方法", "针刺方法"]];
    // 主系统 content 分段
    const c = p.content || "";
    const blocks = {};
    c.split(/\n/).forEach(line => {
      const mm = line.match(/^\[(.+?)\]/);
      if (mm) { blocks[mm[1]] = ""; blocks._cur = mm[1]; }
      else if (blocks._cur) blocks[blocks._cur] += line + "\n";
    });
    ["治疗症状", "取穴位置", "针刺方法"].forEach(k => {
      if (blocks[k]) h += "<div class='sec'><b>" + k + "：</b><br>" + esc(blocks[k].trim()) + "</div>";
    });
    const nishi = p.nishi || {};
    const nk = Object.keys(nishi).filter(k => nishi[k] && nishi[k].trim());
    if (nk.length) {
      h += "<div class='nishi-box'><b style='color:#ffd479'>倪师穴位详解</b>";
      nk.forEach(k => h += "<div class='sec'><b>" + esc(k) + "</b><br>" + esc(nishi[k]) + "</div>");
      h += "</div>";
    }
    if (p.images && p.images.length) {
      h += "<div class='sec'><b>图谱：</b><br>";
      p.images.forEach(im => { h += "<img src='/extimg?p=" + encodeURIComponent(im) + "' style='max-width:160px;margin:4px;border:1px solid #2a5;border-radius:6px;background:#fff'>"; });
      h += "</div>";
    }
    h += "</div>";
    detailPane.innerHTML = h;
  }

  // ---------- 人体穴位图（points） ----------
  function renderPoints(s) {
    filterBar.innerHTML = "<div class='hint' style='padding:4px'>按原软件坐标的可点击人体穴位图（共 " + "348" + " 穴）</div>";
    getJSON("/api/renji/list?sub=points").then(pts => {
      const items = pts.items || [];
      // 简化 SVG 人体 + 点位
      const svg = "<svg class='anim-stage' viewBox='0 0 200 420' style='width:100%;max-width:320px'>" +
        "<ellipse class='body' cx='100' cy='40' rx='26' ry='30'/>" +
        "<rect class='body' x='70' y='70' width='60' height='150' rx='22'/>" +
        "<rect class='body' x='40' y='80' width='24' height='110' rx='12'/>" +
        "<rect class='body' x='136' y='80' width='24' height='110' rx='12'/>" +
        "<rect class='body' x='80' y='220' width='18' height='120' rx='9'/>" +
        "<rect class='body' x='102' y='220' width='18' height='120' rx='9'/>";
      let dots = "";
      items.forEach(p => {
        const x = 30 + (p.left % 160), y = 30 + (p.top % 360);
        dots += "<circle class='mer-dot' cx='" + x + "' cy='" + y + "' data-n='" + esc(p.id) + "'></circle>";
      });
      detailPane.innerHTML =
        "<div class='anim-stage'>" + svg + dots + "</svg><div class='hint'>点击圆点查看穴位（坐标来自原软件 SELFDATA，已按比例映射到示意人体）。</div></div>";
      // 列表
      items.slice(0, 200).forEach(p => {
        const li = el("li", "result-item", esc(p.id));
        li.onclick = () => { detailPane.innerHTML = "<div class='point-card'><h4>" + esc(p.id) + "</h4>" +
          "<div class='sec'>坐标：左 " + p.left + " 上 " + p.top + "（H1=" + p.h + " V1=" + p.v + " Y=" + p.y + "）</div></div>"; };
        resultList.appendChild(li);
      });
    });
  }

  // ---------- 倪师注解型（fields） ----------
  function renderFields(s) {
    filterBar.innerHTML = "";
    getJSON("/api/renji/list?sub=" + s.src).then(d => {
      resultList.innerHTML = "";
      d.items.forEach(it => {
        const li = el("li", "result-item", esc(it.name));
        li.onclick = () => {
          getJSON("/api/renji/item?sub=" + s.src + "&i=" + it.i).then(rec => {
            let h = "<div class='point-card'><h4>" + esc(rec.name) + "</h4>";
            const f = rec.fields || {};
            Object.keys(f).forEach(k => { if (f[k]) h += "<div class='sec'><b>" + esc(k) + "：</b><br>" + esc(f[k]) + "</div>"; });
            h += "</div>";
            detailPane.innerHTML = h;
          });
        };
        resultList.appendChild(li);
      });
    });
  }

  // ---------- 倪师图集（image） ----------
  function renderImages(s) {
    filterBar.innerHTML = "";
    getJSON("/api/renji/list?sub=tu").then(d => {
      let names = d.items.map(x => x.name);
      if (s.filter) {
        const kw = s.filter;
        names = names.filter(n => kw.some(k => n.indexOf(k) >= 0));
      }
      const grid = el("div", "tu-grid");
      names.forEach(n => {
        const cell = el("div", "tu-cell");
        cell.innerHTML = "<img src='/renji/img?name=" + encodeURIComponent(n) + "' onerror=\"this.style.display='none'\"><div class='cap'>" + esc(n) + "</div>";
        cell.onclick = () => { detailPane.innerHTML = "<div class='anim-stage'><img src='/renji/img?name=" +
          encodeURIComponent(n) + "' style='max-width:100%' onerror=\"this.style.display='none'\"><div class='hint'>" + esc(n) + "</div></div>"; };
        grid.appendChild(cell);
      });
      resultList.innerHTML = ""; resultList.appendChild(grid);
      if (!names.length) resultList.innerHTML = "<div class='hint'>无匹配图表。</div>";
    });
  }

  // ---------- 子午流注 / 灵龟八法 表 ----------
  function renderZiwwuTable(s) {
    filterBar.innerHTML = "";
    getJSON("/api/renji/ziwwu").then(z => {
      const t = z[s.table];
      let h = "<div class='table-scroll'><table class='zi'><tr>";
      t.cols.forEach(c => h += "<th>" + esc(c) + "</th>");
      h += "</tr>";
      t.rows.forEach(r => { h += "<tr>"; r.forEach(c => h += "<td>" + esc(c) + "</td>"); h += "</tr>"; });
      h += "</table></div>";
      resultList.innerHTML = h;
      detailPane.innerHTML = "<div class='hint'>点击表格查看（此为静态 lookup 表，「倪海厦子午流注盘」可按年月日时自动查开穴）。</div>";
    });
  }

  // ---------- 汉唐取穴（四法） ----------
  function renderHantang(s) {
    filterBar.innerHTML = "";
    getJSON("/api/renji/hantang/" + s.method).then(d => {
      resultList.innerHTML = "";
      d.items.forEach(it => {
        const li = el("li", "result-item", esc(it.name));
        li.onclick = () => {
          getJSON("/api/renji/hantang/" + s.method + "/item?name=" + encodeURIComponent(it.name)).then(rec => {
            let h = "<div class='point-card'><h4>" + esc(rec.name) + "</h4>";
            const f = rec.fields || {};
            Object.keys(f).forEach(k => { if (f[k]) h += "<div class='sec'><b>" + esc(k) + "：</b><br>" + esc(f[k]) + "</div>"; });
            h += "</div>";
            detailPane.innerHTML = h;
          });
        };
        resultList.appendChild(li);
      });
      if (!d.items.length) resultList.innerHTML = "<div class='hint'>该分类暂无可归类方剂（按关键词尽力归类）。</div>";
    });
  }

  // ---------- 跨系统：中药 / 药图 ----------
  function renderCross(s) {
    filterBar.innerHTML = "";
    getJSON(s.endpoint + "?size=2000").then(d => {
      resultList.innerHTML = "";
      const items = d.items || [];
      items.slice(0, 400).forEach((it, i) => {
        const li = el("li", "result-item", esc(it.name));
        li.onclick = () => {
          let h = "<div class='point-card'><h4>" + esc(it.name) + "</h4>";
          Object.keys(it).forEach(k => { if (k !== "name" && k !== "_image" && it[k] && typeof it[k] === "string")
            h += "<div class='sec'><b>" + esc(k) + "：</b><br>" + esc(it[k]) + "</div>"; });
          if (it._image) h += "<img src='/api/herb_image/" + encodeURIComponent(it.name) + "' style='max-width:160px;margin:4px;background:#fff;border-radius:6px'>";
          h += "</div>";
          detailPane.innerHTML = h;
        };
        resultList.appendChild(li);
      });
    });
  }

  // ---------- 交互工具 ----------
  function renderTool(s) {
    if (s.tool === "wanianli") return toolWanianli();
    if (s.tool === "ziwwu_pan") return toolZiwwuPan();
    if (s.tool === "lingui_dial") return toolLinguiDial();
  }
  function toolWanianli() {
    resultList.innerHTML = "";
    const now = new Date();
    detailPane.innerHTML = "<div class='tool-panel'>" +
      "<h3>万年历 · 四柱干支</h3>" +
      "<label>公历 <input type='date' id='wlDate' value='" + now.toISOString().slice(0,10) + "'></label>" +
      "<div class='gz-result' id='wlOut'></div>" +
      "<div class='hint'>年柱以立春为界近似；月柱按二十四节气定月；日柱以儒略日推算；时柱按时辰（每 2 小时一辰）。</div>" +
      "</div>";
    const inp = $("#wlDate");
    const calc = () => {
      const [y, m, d] = inp.value.split("-").map(Number);
      const yg = yearGZ(y), mg = monthGZ(y, m, d), dg = dayGZ(y, m, d);
      const out = $("#wlOut");
      out.innerHTML = card("年柱", yg.str) + card("月柱", mg.str) + card("日柱", dg.str) +
        card("生肖", ZOO(dg.z)) + card("日干支序", dg.idx);
    };
    inp.oninput = calc; calc();
  }
  function ZOO(z) { return ["鼠","牛","虎","兔","龙","蛇","马","羊","猴","鸡","狗","猪"][z]; }
  function card(lab, val) { return "<div class='gz-card'><div class='lab'>" + lab + "</div><div class='val'>" + esc(val) + "</div></div>"; }

  function toolZiwwuPan() {
    resultList.innerHTML = "";
    const now = new Date();
    const hh = now.getHours();
    detailPane.innerHTML = "<div class='tool-panel'>" +
      "<h3>倪海厦子午流注盘</h3>" +
      "<label>公历 <input type='date' id='pnDate' value='" + now.toISOString().slice(0,10) + "'></label> " +
      "<label>时辰 <select id='pnHour'>" + ZHI.map((z, i) => "<option value='" + i + "'" + (hourBranch(hh) === i ? " selected" : "") + ">" + z + "时</option>").join("") + "</select></label>" +
      "<div class='gz-result' id='pnGZ'></div>" +
      "<div class='open-list' id='pnOpen'></div>" +
      "<div class='hint'>输入年月日时，自动计算四柱干支，并查表给出：纳甲当旺经脉 / 纳子取穴 / 灵龟八法开穴。</div>" +
      "</div>";
    let Z = null;
    getJSON("/api/renji/tool/ziwwu_pan").then(d => { Z = d.ziwwu; recalc(); });
    const recalc = () => {
      if (!Z) return;
      const inp = $("#pnDate"), hb = Number($("#pnHour").value);
      const [y, m, d] = inp.value.split("-").map(Number);
      const yg = yearGZ(y), mg = monthGZ(y, m, d), dg = dayGZ(y, m, d), hg = hourGZ(hb, dg.g);
      $("#pnGZ").innerHTML = card("年", yg.str) + card("月", mg.str) + card("日", dg.str) + card("时", hg.str);
      // 灵龟八法开穴：直接查权威 lingui 表（日干支 → 时辰列），再由开穴穴名反查九宫。
      const linguiRow = Z.lingui.rows.find(r => r[0] === dg.str) || Z.lingui.rows[0];
      const openLing = (linguiRow[1 + hb] || "").trim();
      const gj = acupointGong(openLing);
      // 纳子取穴：日干+时辰（如 甲子）
      const nzKey = dg.str[0] + ZHI[hb];
      const nzRow = Z.nazi.rows.find(r => r[0] === nzKey) || ["", "", "", ""];
      // 纳甲当旺（按时辰）
      const najRow = Z.najia.rows.find(r => r[0] === ZHI[hb]) || [];
      let html = "<div class='op'><b>灵龟八法开穴</b>" + (gj ? "（九宫 " + gj + "）" : "") + "：" + esc(openLing) + "</div>";
      html += "<div class='op'><b>纳子取穴</b>（" + esc(nzKey) + "）：" +
        [nzRow[1], nzRow[2], nzRow[3]].filter(Boolean).map(x => esc(x.trim())).join("；") + "</div>";
      html += "<div class='op'><b>纳甲当旺经脉</b>（" + esc(ZHI[hb]) + "时）：" + esc((najRow[1] || "").trim()) +
        "；本穴 " + esc((najRow[4] || "").trim()) + "；原穴 " + esc((najRow[5] || "").trim()) + "</div>";
      $("#pnOpen").innerHTML = html;
    };
    $("#pnDate").onchange = recalc; $("#pnHour").onchange = recalc;
  }

  // 灵龟八法 九宫配穴（洛书方位）
  const JIUGONG = { 1:["申脉"], 2:["照海"], 3:["外关"], 4:["临泣"], 6:["公孙"], 7:["内关"], 8:["后溪"], 9:["列缺"] };
  const JG_LAYOUT = { 4:[0,0], 9:[0,1], 2:[0,2], 3:[1,0], 5:[1,1], 7:[1,2], 8:[2,0], 1:[2,1], 6:[2,2] };
  // 由开穴穴名反查其所属九宫（以权威 lingui 表的开穴名为准，避免干支代数法的流派误差）。
  function acupointGong(name) {
    if (!name) return 0;
    for (let g = 1; g <= 9; g++) {
      if (g === 5) continue;
      const arr = JIUGONG[g] || [];
      for (const a of arr) if (name.indexOf(a) >= 0) return g;
    }
    return 0;
  }
  function toolLinguiDial() {
    resultList.innerHTML = "";
    const now = new Date();
    detailPane.innerHTML = "<div class='tool-panel'>" +
      "<h3>圆形灵龟八法盘</h3>" +
      "<label>公历 <input type='date' id='dlDate' value='" + now.toISOString().slice(0,10) + "'></label> " +
      "<label>时辰 <select id='dlHour'>" + ZHI.map((z, i) => "<option value='" + i + "'>" + z + "时</option>").join("") + "</select></label>" +
      "<div class='dial-wrap'><svg class='dial' id='dlSvg' viewBox='0 0 300 300'></svg>" +
      "<div><div class='gz-result' id='dlGZ'></div><div class='open-list' id='dlOpen'></div></div></div>" +
      "<div class='hint'>九宫洛书：戴九履一、左三右七、二四为肩、六八为足、五居中。按「日干支序 + 时干支序」mod 9 定开穴九宫。</div>" +
      "</div>";
    let Z = null;
    getJSON("/api/renji/tool/lingui_dial").then(d => { Z = d; drawDial(0); });
    const drawDial = (hot) => {
      const svg = $("#dlSvg"); const sz = 100, gap = 0;
      let s = "";
      for (let g = 1; g <= 9; g++) {
        if (g === 5) continue;
        const [r, c] = JG_LAYOUT[g];
        const x = 20 + c * 90, y = 20 + r * 90;
        const hotc = (g === hot);
        s += "<rect class='cell" + (hotc ? " hot" : "") + "' x='" + x + "' y='" + y + "' width='80' height='80' rx='8'></rect>";
        s += "<text class='num' x='" + (x + 40) + "' y='" + (y + 18) + "'>" + g + "宫</text>";
        s += "<text class='lbl' x='" + (x + 40) + "' y='" + (y + 50) + "'>" + (JIUGONG[g][0] || "") + "</text>";
      }
      svg.innerHTML = s;
    };
    const recalc = () => {
      if (!Z) return;
      const inp = $("#dlDate"), hb = Number($("#dlHour").value);
      const [y, m, d] = inp.value.split("-").map(Number);
      const dg = dayGZ(y, m, d), hg = hourGZ(hb, dg.g);
      const linguiRow = Z.rows.find(r => r[0] === dg.str) || Z.rows[0];
      const openLing = (linguiRow[1 + hb] || "").trim();
      const gj = acupointGong(openLing);
      $("#dlGZ").innerHTML = card("日", dg.str) + card("时", hg.str) + (gj ? card("九宫", gj) : "");
      $("#dlOpen").innerHTML = "<div class='op'><b>灵龟八法开穴</b>：" + esc(openLing) + "</div>";
      drawDial(gj);
    };
    $("#dlDate").onchange = recalc; $("#dlHour").onchange = recalc;
  }

  // ---------- 动画演示：SVG 经络走向 ----------
  const MER_PATHS = {
    "肺经":"M100,70 L100,110 L80,150 L70,200", "大肠经":"M70,200 L60,240 L90,300 L120,330",
    "胃经":"M120,330 L150,300 L160,240 L150,170 L150,120", "脾经":"M150,120 L150,180 L140,250 L130,320",
    "心经":"M100,100 L110,140 L120,180", "小肠经":"M120,180 L140,230 L150,300 L140,350",
    "膀胱经":"M140,350 L130,290 L120,200 L110,120 L100,80", "肾经":"M100,80 L90,140 L80,220 L85,310",
    "心包经":"M100,95 L105,140 L110,185", "三焦经":"M110,185 L130,235 L145,300 L135,350",
    "胆经":"M135,350 L145,290 L155,210 L160,140 L150,95", "肝经":"M150,95 L145,150 L135,230 L125,320",
    "督脉":"M100,12 L100,40 L100,120 L100,210 L100,300 L100,380", "任脉":"M100,45 L100,120 L100,210 L100,300 L100,360",
    "冲脉":"M95,60 L105,150 L100,250 L100,340", "带脉":"M40,180 L160,180",
    "阴维脉":"M90,70 L85,160 L95,260 L90,350", "阳维脉":"M115,70 L130,160 L120,260 L125,350",
    "阳跷脉":"M140,90 L150,190 L145,290 L150,370", "阴跷脉":"M60,90 L55,190 L65,290 L55,370"
  };
  const SHIER = ["肺经","大肠经","胃经","脾经","心经","小肠经","膀胱经","肾经","心包经","三焦经","胆经","肝经"];
  const QIJING = ["督脉","任脉","冲脉","带脉","阴维脉","阳维脉","阳跷脉","阴跷脉"];
  function renderAnimation(s) {
    filterBar.innerHTML = "";
    const list = s.group === "shier" ? SHIER : QIJING;
    const colors = ["#ff6b6b","#ffd166","#06d6a0","#4d96ff","#c77dff","#ff9f1c","#2ec4b6","#e63946","#a7c957","#457b9d","#f4a261","#9d4edd","#ff70a6","#48cae4","#b5179e","#90be6d","#f9844a","#577590"];
    let svg = "<svg class='anim-stage' viewBox='0 0 200 420' style='width:100%;max-width:360px'>";
    svg += "<ellipse class='body' cx='100' cy='40' rx='24' ry='28'/><rect class='body' x='72' y='68' width='56' height='150' rx='20'/>";
    svg += "<rect class='body' x='44' y='78' width='22' height='105' rx='11'/><rect class='body' x='134' y='78' width='22' height='105' rx='11'/>";
    svg += "<rect class='body' x='82' y='218' width='16' height='120' rx='8'/><rect class='body' x='102' y='218' width='16' height='120' rx='8'/></svg>";
    let buttons = "<div class='mer-filter'>";
    list.forEach((m, i) => { buttons += "<button data-m='" + m + "' style='border-color:" + colors[i % colors.length] + "'>" + m + "</button>"; });
    buttons += "</div>";
    resultList.innerHTML = buttons;
    const art = s.group === "shier" ? ART_SHIER : ART_QIJING;
    detailPane.innerHTML = "<div class='anim-cap'>点击左侧经络查看走向动画</div><div class='anim-art'>" + esc(art) + "</div>";
    resultList.querySelectorAll("button").forEach(b => {
      b.onclick = () => playMeridian(b.getAttribute("data-m"), colors, list);
    });
  }
  function playMeridian(name, colors, list) {
    const idx = list.indexOf(name);
    const color = colors[idx % colors.length];
    const d = MER_PATHS[name] || "M100,40 L100,380";
    detailPane.innerHTML = "<div class='anim-cap' style='color:" + color + "'>" + esc(name) + " · 穴位走向</div>" +
      "<div class='anim-stage'><svg viewBox='0 0 200 420' style='width:100%;max-width:360px'>" +
      "<ellipse class='body' cx='100' cy='40' rx='24' ry='28'/><rect class='body' x='72' y='68' width='56' height='150' rx='20'/>" +
      "<rect class='body' x='44' y='78' width='22' height='105' rx='11'/><rect class='body' x='134' y='78' width='22' height='105' rx='11'/>" +
      "<rect class='body' x='82' y='218' width='16' height='120' rx='8'/><rect class='body' x='102' y='218' width='16' height='120' rx='8'/>" +
      "<path class='mer-path' d='" + d + "' stroke='" + color + "'><animate attributeName='stroke-dasharray' from='0 1000' to='1000 0' dur='3s' repeatCount='indefinite'/></path>" +
      "<circle class='mer-comet' r='6' fill='" + color + "'><animateMotion dur='3s' repeatCount='indefinite' path='" + d + "'/></circle>" +
      "</svg></div><div class='hint'>该动画为依经络循行次序以 SVG 路径流动重建（原软件为 Flash，已停服，无法提取原帧）。</div>" +
      "<div class='anim-art'>" + esc(name === "任脉" || name === "督脉" || QIJING.indexOf(name) >= 0 ? ART_QIJING : ART_SHIER) + "</div>";
  }
  const ART_SHIER = "十二经脉循行走向（说明，逆向自「人纪针灸」EXE）\n\n十二经脉的名称为：手太阴肺经、手阳明大肠经、足阳明胃经、足太阴脾经、手少阴心经、手太阳小肠经、足太阳膀胱经、足少阴肾经、手厥阴心包经、手少阳三焦经、足少阳胆经、足厥阴肝经。\n\n其流注次序是：从手太阴肺经开始，依次传至手阳明大肠经、足阳明胃经、足太阴脾经、手少阴心经、手太阳小肠经、足太阳膀胱经、足少阴肾经、手厥阴心包经、手少阳三焦经、足少阳胆经、足厥阴肝经，再复注于手太阴肺经，如环无端，周而复始。\n\n手三阴从胸走手，手三阳从手走头，足三阳从头走足，足三阴从足走腹（胸）。阴阳相贯，气血周流不息。";
  const ART_QIJING = "奇经八脉循行走向（说明，逆向自「人纪针灸」EXE）\n\n奇经八脉者：督脉、任脉、冲脉、带脉、阴维脉、阳维脉、阴跷脉、阳跷脉也。\n\n督脉行于腰背正中，总督一身之阳；任脉行于胸腹正中，总任一身之阴；冲脉为血海，渗灌诸经；带脉环腰一周，约束纵行诸脉；阴维、阳维分别维络一身之阴经与阳经；阴跷、阳跷分主一身左右之阴阳跷捷。\n\n八脉交会于十二正经，其中公孙（脾）→内关（心包）、临泣（胆）→外关（三焦）、后溪（小肠）→申脉（膀胱）、列缺（肺）→照海（肾）四组，为灵龟八法与飞腾八法之根基。";

  // ---------- 搜索 ----------
  function doSearch(q) {
    if (!q) return;
    moduleHead.innerHTML = "<h2>搜索：人纪</h2>";
    detailPane.innerHTML = "<div class='hint'>搜索中…</div>";
    getJSON("/api/search?q=" + encodeURIComponent(q)).then(d => {
      let h = "<div class='open-list'>";
      (d.groups || []).forEach(g => {
        h += "<div class='op'><b>" + esc(g.name) + "（" + g.total + "）</b></div>";
        g.items.slice(0, 8).forEach(it => {
          const name = it.name || it.MZ || it.title || "";
          h += "<div class='hint' style='padding:2px 8px'>· " + esc(name) + "</div>";
        });
      });
      h += "</div>";
      if (!d.groups || !d.groups.length) h = "<div class='hint'>未找到相关人纪内容。</div>";
      detailPane.innerHTML = h;
      resultList.innerHTML = "";
    });
  }

  // ---------- 初始化 ----------
  function init() {
    const sb = $("#searchBtn"), si = $("#search");
    if (sb) sb.onclick = () => doSearch(si.value);
    if (si) si.onkeydown = e => { if (e.key === "Enter") doSearch(si.value); };
    getJSON("/api/renji/modules").then(bs => {
      BOARDS = bs;
      if (BOARDS[0]) selectBoard(BOARDS[0]);
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
