/* 人纪学习系统 · 前端（独立，不依赖 app.js）
 * 五大板块：穴位详解 / 灵龟八法 / 子午流注 / 汉唐取穴 / 动画演示
 * 与「人纪针灸」EXE 菜单一致。
 */
(function () {
  "use strict";

  // ---------- 注入样式 ----------
  const CSS = `
  .app{display:flex;flex-direction:column;height:100vh}
  .layout{flex:1;flex-direction:column;min-height:0}
  .tu-list{display:flex;flex-direction:column;gap:6px;padding:8px 14px 16px}
  .tu-cell{display:flex;align-items:center;gap:10px;margin:0;padding:6px 8px;border:1px solid #245;background:#0f2a40;border-radius:8px;cursor:pointer;transition:border-color .15s,box-shadow .15s;overflow:hidden}
  .tu-cell:hover{border-color:#ffd479;box-shadow:0 2px 8px rgba(0,0,0,.25)}
  .tu-cell.active{border-color:#ffd479;box-shadow:0 0 0 3px rgba(255,212,121,.35)}
  .tu-thumb{flex:0 0 auto;width:34px;height:34px;border-radius:5px;overflow:hidden;background:#fff}
  .tu-thumb img{width:100%;height:100%;object-fit:cover;display:block;background:#fff}
  .tu-name{flex:1;min-width:0;font-size:14px;line-height:1.35;color:#dfeefb;text-align:left;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
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
  .detail-pane.tu-stage{padding-top:0}
  .anim-stage{display:flex;flex-direction:column;align-items:flex-start;justify-content:flex-start;gap:10px;background:#04121f;border-radius:10px;padding:0}
  .anim-stage img{max-width:100%;width:auto;height:auto;display:block;border-radius:8px;background:#fff}
  .anim-stage .hint{font-size:13px;color:#9fc1da;padding:6px 8px}
  .anim-stage .body{stroke:#3a6f9a;stroke-width:2;fill:#0a2236}
  .mer-path{fill:none;stroke-width:3;stroke-linecap:round;opacity:.85}
  .mer-dot{fill:#fff;r:5}
  .mer-comet{fill:#ffd479;r:6}
  .anim-cap{color:#ffd479;font-weight:700;font-size:16px;margin:6px 0}
  .anim-art{color:#cfe3f2;line-height:1.8;white-space:pre-wrap;max-height:300px;overflow:auto;
    background:#0c2236;padding:10px;border-radius:8px;margin-top:8px}
  .point-card{border:1px solid #2a5;background:#0f2a40;border-radius:8px;padding:10px;margin:8px 0}
  .point-card h4{color:#ffd479;margin:0 0 6px}
  .point-card .sec{margin:4px 0}
  .point-card .sec b{color:#9fc1da}
  .nishi-box{border-top:1px dashed #2a5;margin-top:8px;padding-top:6px}
  .table-scroll{overflow:auto}
  table.zi{border-collapse:collapse;width:100%;font-size:13px}
  table.zi th,table.zi td{border:1px solid #2a5;padding:4px 8px;text-align:center;color:#dfeefb;white-space:nowrap}
  table.zi th{background:#11304a;color:#ffd479}
  .flow-wrap{display:grid;grid-template-columns:minmax(260px,440px) 1fr;gap:16px;align-items:start}
  @media (max-width:820px){.flow-wrap{grid-template-columns:1fr}}
  .flow-body{background:#04121f;border:1px solid #16344d;border-radius:10px;padding:6px;overflow:auto;max-height:84vh}
  .flow-svg{display:block;width:100%;height:auto}
  .flow-img{display:block}
  .flow-line{fill:none;stroke:#c0392b;stroke-width:3;stroke-linecap:round;opacity:.85}
  .flow-anim{fill:none;stroke:#fff;stroke-width:2;stroke-dasharray:12 8;opacity:.95;animation:flowdash 2.5s linear infinite}
  @keyframes flowdash{to{stroke-dashoffset:-200}}
  .flow-dot circle{fill:#c0392b;stroke:#fff;stroke-width:2.5;opacity:.9;transition:r .12s}
  .flow-dot.active circle{fill:#e67e22}
  .flow-num{fill:#fff;font-size:12px;font-weight:bold;text-anchor:middle;dominant-baseline:middle;paint-order:stroke;stroke:#000;stroke-width:3px}
  .flow-name{fill:#000;font-size:11px;font-weight:bold;text-anchor:middle;dominant-baseline:middle;paint-order:stroke;stroke:#fff;stroke-width:3px}
  .flow-meta{font-size:13px;color:#cfe3f2;display:flex;flex-wrap:wrap;gap:6px 14px;margin-bottom:10px}
  .flow-meta b{color:#ffd479}
  .flow-legend{font-size:11px;color:#9fc1da;display:flex;gap:14px;margin:2px 0 12px}
  .flow-legend .sw{display:inline-block;width:12px;height:12px;border-radius:50%;vertical-align:middle;margin-right:4px}
  .flow-legend .sw-flow{background:#fff;border:2px solid #c0392b}
  .flow-pts{background:#0c2236;border:1px solid #16344d;border-radius:8px;padding:8px;max-height:70vh;overflow:auto}
  .flow-pts-host{margin-top:10px}
  .flow-pttl{font-size:13px;color:#ffd479;margin-bottom:6px}
  .flow-pt{display:flex;gap:8px;align-items:center;padding:3px 6px;border-radius:4px;cursor:pointer;font-size:13px;color:#dfeefb}
  .flow-pt:hover{background:#0f2a40}
  .flow-pt.cur{background:#fdebd0;color:#c0392b;font-weight:700}
  .flow-pt.miss{opacity:.5}
  .flow-pt .fp-num{width:26px;color:#9fc1da}
  .flow-pt .fp-name{width:88px;font-weight:600}
  .flow-pt .fp-xy{color:#7fd1a0;font-family:monospace;font-size:11px}
  .flow-placeholder{text-align:center;color:#9fc1da;padding:6px 0}
  .flow-placeholder img{width:100%;max-width:360px;max-height:62vh;object-fit:contain;display:block;margin:0 auto 10px;border-radius:8px;background:#fff}
  .flow-phcap{font-size:14px;color:#ffd479;margin-bottom:10px}
  `;
  const st = document.createElement("style");
  st.textContent = CSS;
  document.head.appendChild(st);

  // ---------- 工具 ----------
  const $ = (s, r) => (r || document).querySelector(s);
  const el = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; };
  function isMobile() {
    try { return window.matchMedia("(max-width:820px)").matches; } catch (e) { return false; }
  }
  // 移动端：把 #resultList 的 .result-item 转成「二级目录」下拉，选中即渲染详情；默认自动展示首项。
  // MutationObserver 自动适配所有刷新列表的渲染（穴位/取穴/中药等），无需逐个挂钩。
  let _mListObserver = null, _mListTO = null;
  function mobileListToSelect() {
    const ul = document.getElementById("resultList");
    if (!ul) return;
    // 不再把左侧目录折叠成下拉：所有视口都保持目录列表可见（窄屏由 .workarea 列布局堆叠在顶部）
    const sel = document.getElementById("mListSelect");
    if (sel) sel.remove();
    ul.style.display = "";
    return;
  }
  function observeMobileList() {
    if (_mListObserver) return;
    const ul = document.getElementById("resultList");
    if (!ul) return;
    _mListObserver = new MutationObserver(() => {
      if (_mListTO) clearTimeout(_mListTO);
      _mListTO = setTimeout(mobileListToSelect, 60);
    });
    _mListObserver.observe(ul, { childList: true, subtree: true });
  }
  function getJSON(url) {
    return new Promise((res, rej) => {
      fetch(url).then(r => r.json()).then(res).catch(rej);
    });
  }
  function esc(s) { return (s == null ? "" : String(s)).replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c])); }

  const boardTabs = $("#boardTabs"),
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
  // 顶部板块/工具标签条（横向，桌面/移动一致；移动端由 CSS .board-tabs{flex-wrap} 自动换行）
  function closeDropdowns() {
    [...boardTabs.querySelectorAll(".board-tab.open")].forEach(t => t.classList.remove("open"));
  }
  document.addEventListener("click", closeDropdowns);

  // ---------- 移动端下拉（仿天纪 .tj-mobile-select）；桌面侧栏已移除（遵从"电脑版不动"，桌面仅保留顶部 board-tabs） ----------
  function navLeaf(text, onClick, obj) {
    const l = el("div", "tj-leaf", "");
    l.textContent = text;
    if (obj) l._nav = obj;
    l.onclick = () => { onClick(); applyNavActive(); };
    return l;
  }
  // 递归渲染侧栏节点；depth 用于缩进
  function renderSidebarNode(s, parent, depth) {
    if (s.subs && s.subs.length) {
      const node = el("div", "tj-node open");
      const head = el("div", "tj-node-head",
        "<span class='tj-toggle'>▾</span><span class='tj-node-title'>" + esc(s.name) + "</span>");
      head.onclick = () => {
        node.classList.toggle("open");
        head.querySelector(".tj-toggle").textContent = node.classList.contains("open") ? "▾" : "▸";
      };
      node.appendChild(head);
      const kids = el("div", "tj-node-children", "");
      s.subs.forEach(c => renderSidebarNode(c, kids, depth + 1));
      node.appendChild(kids);
      parent.appendChild(node);
    } else {
      const indent = depth > 1 ? "　".repeat(depth - 1) : "";
      parent.appendChild(navLeaf(indent + s.name, () => selectSub(s), s));
    }
  }
  function renderRenjiSidebar() {
    const side = document.getElementById("sidebar");
    if (!side) return;
    side.innerHTML = "";
    BOARDS.forEach(b => {
      if (b.kind) {                 // 整页板块（灵龟八法 / 子午流注）：顶层可点击项
        side.appendChild(navLeaf(b.name, () => selectBoardPage(b), b));
      } else {
        const root = el("div", "tj-root", esc(b.name));
        side.appendChild(root);
        (b.subs || []).forEach(s => renderSidebarNode(s, side, 1));
      }
    });
  }
  // 移动端：把 板块/子模块 压平成一个 <select>（禁用项作分组标题），选中即渲染
  function renderRenjiMobileNav() {
    const wrap = document.getElementById("renjiMobileNavWrap");
    if (!wrap) return;
    wrap.innerHTML = "";
    const sel = el("select", "tj-mobile-select", "");
    sel.id = "renjiMobileNav";
    const ph = document.createElement("option");
    ph.value = ""; ph.textContent = "选择板块 / 子模块"; ph.disabled = true; ph.selected = true;
    sel.appendChild(ph);
    const mi = { n: 0 };
    BOARDS.forEach(b => {
      if (b.kind) {                 // 整页板块（灵龟八法 / 子午流注）：直接作为可选项，不加禁用分组标题
        const o = document.createElement("option");
        o.value = "b" + (mi.n++); o.textContent = b.name; o._act = () => selectBoardPage(b);
        sel.appendChild(o);
      } else {
        const sep = document.createElement("option");
        sep.disabled = true; sep.textContent = "▸ " + b.name; sel.appendChild(sep);
        (b.subs || []).forEach(s => appendMobileLeaf(sel, s, 1, mi));
      }
    });
    sel.onchange = () => {
      const o = sel.selectedOptions && sel.selectedOptions[0];
      if (o && o._act) o._act();
    };
    wrap.appendChild(sel);
  }
  function appendMobileLeaf(sel, s, depth, mi) {
    if (s.subs && s.subs.length) {
      s.subs.forEach(c => appendMobileLeaf(sel, c, depth + 1, mi));
    } else {
      const o = document.createElement("option");
      o.value = "m" + (mi.n++); o.textContent = "　".repeat(depth) + s.name;
      o._act = () => selectSub(s);
      sel.appendChild(o);
    }
  }
  function applyNavActive() {
    const side = document.getElementById("sidebar");
    if (side) {
      side.querySelectorAll(".tj-leaf").forEach(l => {
        const on = (l._nav === CUR_SUB) || (l._nav === CUR_BOARD && !CUR_SUB);
        l.classList.toggle("active", !!on);
      });
    }
  }
  // 顶部板块/工具标签条（横向，桌面/移动一致；移动端由 CSS .board-tabs{flex-wrap} 自动换行）
  // 桌面：仅顶部标签条（还原原始布局，无侧栏）；移动端：另构建下拉（仿天纪），与顶部栏共享状态。
  function renderBoards() {
    boardTabs.innerHTML = "";
    BOARDS.forEach(b => {
      const t = el("div", "board-tab" + (b === CUR_BOARD ? " active" : ""));
      t.innerHTML = esc(b.name) + (b.subs ? " <span class='bt-count'>(" + b.count + ")</span>" : "");
      const dd = el("div", "board-dropdown");
      const walk = (subs) => subs.forEach(s => {
        if (s.subs) {
          dd.appendChild(el("div", "board-dd-group", esc(s.name)));
          walk(s.subs);
        } else {
          const it = el("div", "board-dd-item");
          if (s === CUR_SUB) it.classList.add("active");
          it.textContent = s.name;
          it.onclick = (e) => { e.stopPropagation(); selectSub(s); };
          dd.appendChild(it);
        }
      });
      if (b.subs) walk(b.subs);
      t.appendChild(dd);
      t.onclick = (e) => {
        e.stopPropagation();
        if (b.kind) {  // 板块级整页（无下拉菜单）：直接渲染整页
          selectBoardPage(b);
          return;
        }
        const wasOpen = t.classList.contains("open");
        closeDropdowns();
        if (wasOpen) return;
        if (b !== CUR_BOARD) {
          CUR_BOARD = b;
          [...boardTabs.children].forEach(c => c.classList.remove("active"));
          t.classList.add("active");
        }
        t.classList.add("open");
      };
      boardTabs.appendChild(t);
    });
    // 左侧目录树 + 移动端下拉（与顶部栏共享状态）
    renderRenjiSidebar();
    renderRenjiMobileNav();
    applyNavActive();
  }
  function selectBoard(b, autoFirst) {
    CUR_BOARD = b; CUR_SUB = null;
    const lp = document.getElementById("listPane"); if (lp) lp.style.display = "";
    renderBoards();
    if (autoFirst) {
      const first = firstLeaf(b);
      if (first) selectSub(first);
    }
  }
  function firstLeaf(b) {
    for (const s of b.subs) { if (s.subs) { const f = firstLeaf({ subs: s.subs }); if (f) return f; } else return s; }
    return null;
  }
  function selectSub(s) {
    CUR_SUB = s;
    const lp = document.getElementById("listPane"); if (lp) lp.style.display = "";
    moduleHead.innerHTML = "<h2>" + esc(s.name) + "</h2><p class='brand-sub'>" + esc(s.desc || "") + "</p>";
    listHint.style.display = "none";
    pager.innerHTML = ""; filterBar.innerHTML = "";
    applyNavActive();
    [...boardTabs.querySelectorAll(".board-dd-item")].forEach(x =>
      x.classList.toggle("active", x.textContent.trim() === s.name));
    dispatchSub(s);
    closeDropdowns();
  }

  // 板块级整页（无子菜单下拉）：点击板块标签即渲染整页内容
  function selectBoardPage(b) {
    CUR_BOARD = b; CUR_SUB = null;
    const lp = document.getElementById("listPane");
    if (lp) lp.style.display = (b.kind === "lbg_page" || b.kind === "ziwwu_page") ? "none" : "";
    const wa = document.querySelector(".workarea");
    if (wa) wa.classList.toggle("page-mode", b.kind === "lbg_page" || b.kind === "ziwwu_page");
    renderBoards();
    moduleHead.innerHTML = "<h2>" + esc(b.name) + "</h2><p class='brand-sub'>" + esc(b.desc || "") + "</p>";
    listHint.style.display = "none";
    pager.innerHTML = ""; filterBar.innerHTML = "";
    dispatchBoard(b);
    closeDropdowns();
  }
  function dispatchBoard(b) {
    resultList.innerHTML = "";
    detailPane.innerHTML = "";
    if (b.kind === "ziwwu_page") return renderZiwwuPage(b);
    if (b.kind === "lbg_page") return renderLbgPage(b);
    detailPane.innerHTML = "<div class='hint'>请从上方导航菜单选择子模块。</div>";
  }

  function dispatchSub(s) {
    resultList.innerHTML = ""; detailPane.className = "detail-pane"; detailPane.innerHTML = "<div class='hint'>请从上方导航菜单选择子模块，点击条目查看详情。</div>";
    const k = s.kind;
    if (s.key === "yaotu") return renderYaotuGallery();   // 药图：用药图列表.html 的 467 张图鉴内容
    if (s.key === "herbs") return renderZhongyao();        // 中药查询：用中药查询.html 的 719 味内容替换
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
    // 真人全身经络穴位图移到右侧，与「穴位详情」并排（左侧仅留经络筛选 + 穴位列表）
    detailPane.className = "detail-pane mer-detail-pane";
    detailPane.innerHTML = "<div class='mer-point'><div class='hint'>点击左侧穴位查看定位 / 主治 / 针刺方法与配图。</div></div>";
    // 经络筛选按钮放进 #filterBar（.filter-bar，与 #resultList 平级，合法的 flex 容器），
    // 绝不能再塞进 <ul id="resultList"> 里（<div> 直接做 <ul> 子节点是非法 HTML，
    // 浏览器纠错后会打乱列表宽度/折行，旧版甚至把穴位渲染成两列网格）。
    filterBar.innerHTML = "<span class='fb-title'>十四经络穴位</span>";
    resultList.innerHTML = "";
    getJSON("/api/renji/meridians").then(ms => {
      ms.forEach(m => {
        const b = el("button", "filter-tab", esc(m.label) + " (" + m.count + ")");
        b.onclick = () => loadMeridian(m);
        filterBar.appendChild(b);
      });
      resultList._ms = ms;
      if (ms[0]) loadMeridian(ms[0]);
    });
  }
  function loadMeridian(m) {
    [...filterBar.querySelectorAll("button")].forEach(b => b.classList.remove("active"));
    [...filterBar.querySelectorAll("button")].forEach(b => { if (b.textContent.startsWith(m.label)) b.classList.add("active"); });
    getJSON("/api/renji/meridian/" + m.key).then(d => {
      // #resultList 只装 <li> 穴位项，保证单列、占满左栏宽度
      resultList.innerHTML = "";
      d.items.forEach((p, i) => {
        const li = el("li", "result-item", "<div class=\"t\">" + esc(p.name) + "</div>" + (p.sub ? "<div class=\"s\">" + esc(p.sub) + "</div>" : ""));
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
    const mp = detailPane.querySelector(".mer-point");
    if (mp) mp.innerHTML = h; else detailPane.innerHTML = h;
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
        const li = el("li", "result-item", "<div class=\"t\">" + esc(p.id) + "</div>");
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
        const li = el("li", "result-item", "<div class=\"t\">" + esc(it.name) + "</div>");
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
      resultList.className = "result-list tu-list";
      resultList.innerHTML = "";
      const cells = [];
      names.forEach(n => {
        const li = el("li", "result-item tu-cell");
        li.innerHTML =
          "<div class='tu-thumb'><img loading='lazy' src='/renji/img?name=" + encodeURIComponent(n) + "' alt='" + esc(n) + "' onerror=\"this.style.display='none'\"></div>" +
          "<div class='tu-name'>" + esc(n) + "</div>";
        li.onclick = () => show(n, li);
        resultList.appendChild(li);
        cells.push(li);
      });
      if (!names.length) resultList.innerHTML = "<div class='hint'>无匹配图表。</div>";

      function show(n, li) {
        cells.forEach(c => c.classList.remove("active"));
        if (li) li.classList.add("active");
        detailPane.className = "detail-pane tu-stage";
        detailPane.innerHTML = "<div class='anim-stage'><img src='/renji/img?name=" +
          encodeURIComponent(n) + "' style='max-width:100%;height:auto;display:block' onerror=\"this.style.display='none'\"><div class='hint'>" + esc(n) + "</div></div>";
      }
      if (names.length) show(names[0], cells[0]);
    });
  }

  // ---------- 子午流注 / 灵龟八法 表 ----------
  function ziwwuTableHTML(t) {
    let h = "<div class='table-scroll'><table class='zi'><tr>";
    t.cols.forEach(c => h += "<th>" + esc(c) + "</th>");
    h += "</tr>";
    t.rows.forEach(r => { h += "<tr>"; r.forEach(c => h += "<td>" + esc(c) + "</td>"); h += "</tr>"; });
    h += "</table></div>";
    return h;
  }
  function renderZiwwuTable(s) {
    filterBar.innerHTML = "";
    getJSON("/api/renji/ziwwu").then(z => {
      resultList.innerHTML = ziwwuTableHTML(z[s.table]);
      detailPane.innerHTML = "<div class='hint'>点击表格查看（此为静态 lookup 表，「倪海厦子午流注盘」可按年月日时自动查开穴）。</div>";
    });
  }


  // ---------- 子午流注 整页（按 人纪学习系统/子午流注.html 复刻：时间选择器 + 纳甲表(左) + 纳子表(右) + 当前结果） ----------
  // 源 HTML 自带 NAJIA/NAZI 表 + 「1900年起累加」干支算法（纯客户端）；
  // 服务端 /api/renji/lbg_compute 当前 400（cnlunar 异常），故内嵌源算法，保证与源一致且必出值。
  let ZWWU_DATA = null;
  function renderZiwwuPage(b) {
    filterBar.innerHTML = "";
    detailPane.innerHTML = "<div class='hint'>加载子午流注数据…</div>";
    const load = ZWWU_DATA ? Promise.resolve(ZWWU_DATA)
                           : getJSON("/static/ziwwu_data.json?v=1").then(d => (ZWWU_DATA = d));
    load.then(LD => { ZWWU_DATA = LD; mountZiwwu(LD); })
         .catch(e => { detailPane.innerHTML = "<div class='hint'>数据加载失败：" + esc(e && e.message) + "</div>"; });
  }

  function mountZiwwu(LD) {
    const { NAJIA, NAZI, HOURS, TG, NAZI_ORDER } = LD;

    detailPane.innerHTML =
      "<div class='zw-wrap'>"
      + "<div class='zw-selector'>"
        + "<label>年<input type='number' id='zw-y' min='1900' max='2100' value='2026'></label>"
        + "<label>月<input type='number' id='zw-m' min='1' max='12' value='8'></label>"
        + "<label>日<input type='number' id='zw-d' min='1' max='31' value='9'></label>"
        + "<label>时辰<select id='zw-h'>"
          + "<option value='0'>子 23-1</option><option value='1'>丑 1-3</option>"
          + "<option value='2'>寅 3-5</option><option value='3'>卯 5-7</option>"
          + "<option value='4'>辰 7-9</option><option value='5'>巳 9-11</option>"
          + "<option value='6'>午 11-13</option><option value='7'>未 13-15</option>"
          + "<option value='8'>申 15-17</option><option value='9'>酉 17-19</option>"
          + "<option value='10'>戌 19-21</option><option value='11'>亥 21-23</option>"
        + "</select></label>"
        + "<button id='zw-now' type='button'>现在</button>"
        + "<div class='zw-hint' id='zw-cur-hint'>—</div>"
      + "</div>"
      + "<div class='zw-layout'>"
        + "<div class='zw-panel'>"
          + "<h2>十二经纳甲法表（按时辰 · 12 行）</h2>"
          + "<div class='zw-note'>流经脏腑经络 / 补母穴 / 泻子穴 / 流注输穴 / 经原穴 —— MDB najia 表</div>"
          + "<div class='zw-tblwrap' id='zw-wrap-najia'><table class='zw-tab' id='zw-tbl-najia'></table></div>"
        + "</div>"
        + "<div class='zw-panel'>"
          + "<h2>十二经脉纳子法表（日干×时辰 · 120 行）</h2>"
          + "<div class='zw-note'>日干 + 时辰 → 穴1 / 穴2 / 穴3 —— MDB nazi 表</div>"
          + "<div class='zw-tblwrap' id='zw-wrap-nazi'><table class='zw-tab' id='zw-tbl-nazi'></table></div>"
        + "</div>"
      + "</div>"
      + "<div class='zw-result'>"
        + "<h3>当前选择：<span id='zw-cur-label'>—</span></h3>"
        + "<div class='zw-row' id='zw-cur-result'></div>"
      + "</div>"
      + "<div class='zw-foot'>"
        + "数据：人纪 MDB najia(12×6) / nazi(120×4) · 纳甲按「时辰」，纳子按「日干+时辰」 · 当前行橙色高亮"
      + "</div>"
      + "</div>";

    // ===== 源算法（与 子午流注.html 完全一致） =====
    function isLeap(y) { return (y % 4 === 0 && y % 100 !== 0) || y % 400 === 0; }
    function daysInMonth(y, m) { return [31, isLeap(y) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]; }
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
      const monthStemStart = [2, 4, 0, 6, 8][yearStemIdx % 5];
      const monthBranchIdx = (m + 1) % 12;
      const monthStemIdx = (monthStemStart + (monthBranchIdx - 2 + 12) % 12) % 10;
      return { stem: TG[monthStemIdx], branch: HOURS[monthBranchIdx] };
    }
    function hourGZ(dayStemIdx, h) {
      const hourStemStart = [0, 2, 4, 6, 8][dayStemIdx % 5];
      return { stem: TG[(hourStemStart + h) % 10], branch: HOURS[h] };
    }

    function renderTables() {
      const y = parseInt(document.getElementById('zw-y').value);
      const m = parseInt(document.getElementById('zw-m').value);
      const d = parseInt(document.getElementById('zw-d').value);
      const h = parseInt(document.getElementById('zw-h').value);

      const yy = yearGZ(y, m, d);
      const dd = dayGZ(y, m, d);
      const mm = monthGZ(yy.idx % 10, m);
      const hh = hourGZ(dd.idx % 10, h);

      const curHour = HOURS[h];
      const curDayStem = dd.stem;
      const curKey = curDayStem + curHour;

      document.getElementById('zw-cur-hint').textContent =
        y + '年' + m + '月' + d + '日 ' + yy.stem + yy.branch + '年 ' + mm.stem + mm.branch + '月 ' +
        dd.stem + dd.branch + '日 ' + hh.stem + hh.branch + '时 · 日干=' + curDayStem + ' 时辰=' + curHour;
      document.getElementById('zw-cur-label').textContent =
        curKey + '（' + curDayStem + '日 ' + curHour + '时）';

      // ---- 左：纳甲法表（12 行） ----
      let na1 = '<thead><tr><th>时辰</th><th>流经脏腑经络</th><th>补母穴</th><th>泻子穴</th><th>流注输穴</th><th>经原穴</th></tr></thead><tbody>';
      for (const hr of HOURS) {
        const r = NAJIA[hr] || {};
        const cls = hr === curHour ? ' class="cur"' : '';
        na1 += '<tr' + cls + '><td class="zw-hour">' + hr + '时</td>'
          + '<td>' + (r['流经脏腑经络'] || '-') + '</td>'
          + '<td>' + (r['补母穴'] || '-') + '</td>'
          + '<td>' + (r['泻子穴'] || '-') + '</td>'
          + '<td>' + (r['流注输穴'] || '-') + '</td>'
          + '<td>' + (r['经原穴'] || '-') + '</td></tr>';
      }
      na1 += '</tbody>';
      document.getElementById('zw-tbl-najia').innerHTML = na1;

      // ---- 右：纳子法表（120 行） ----
      let na2 = '<thead><tr><th>日干时辰</th><th>穴1</th><th>穴2</th><th>穴3</th></tr></thead><tbody>';
      let curRowId = '';
      NAZI_ORDER.forEach((key, i) => {
        const r = NAZI[key] || {};
        const cls = key === curKey ? ' class="cur"' : '';
        if (key === curKey) curRowId = 'zw-row-' + i;
        na2 += '<tr' + cls + ' id="zw-row-' + i + '"><td class="zw-hour">' + key + '</td>'
          + '<td>' + (r['穴1'] || '<span class="zw-empty">—</span>') + '</td>'
          + '<td>' + (r['穴2'] || '<span class="zw-empty">—</span>') + '</td>'
          + '<td>' + (r['穴3'] || '<span class="zw-empty">—</span>') + '</td></tr>';
      });
      na2 += '</tbody>';
      document.getElementById('zw-tbl-nazi').innerHTML = na2;

      if (curRowId) {
        const el = document.getElementById(curRowId);
        if (el) el.scrollIntoView({ block: 'center' });
      }

      // ---- 当前结果 ----
      const na = NAJIA[curHour] || {};
      const nz = NAZI[curKey] || {};
      document.getElementById('zw-cur-result').innerHTML =
        '<div><span class="zw-lbl">纳甲·流经脏腑经络</span><span class="zw-val">' + (na['流经脏腑经络'] || '-') + '</span></div>'
        + '<div><span class="zw-lbl">纳甲·补母穴</span><span class="zw-val">' + (na['补母穴'] || '-') + '</span></div>'
        + '<div><span class="zw-lbl">纳甲·泻子穴</span><span class="zw-val">' + (na['泻子穴'] || '-') + '</span></div>'
        + '<div><span class="zw-lbl">纳甲·流注输穴</span><span class="zw-val">' + (na['流注输穴'] || '-') + '</span></div>'
        + '<div><span class="zw-lbl">纳甲·经原穴</span><span class="zw-val">' + (na['经原穴'] || '-') + '</span></div>'
        + '<div><span class="zw-lbl">纳子·穴1</span><span class="zw-val">' + (nz['穴1'] || '—') + '</span></div>'
        + '<div><span class="zw-lbl">纳子·穴2</span><span class="zw-val">' + (nz['穴2'] || '—') + '</span></div>'
        + '<div><span class="zw-lbl">纳子·穴3</span><span class="zw-val">' + (nz['穴3'] || '—') + '</span></div>';
    }

    ['zw-y', 'zw-m', 'zw-d', 'zw-h'].forEach(id => document.getElementById(id).addEventListener('change', renderTables));
    document.getElementById('zw-now').addEventListener('click', () => {
      const dt = new Date();
      document.getElementById('zw-y').value = dt.getFullYear();
      document.getElementById('zw-m').value = dt.getMonth() + 1;
      document.getElementById('zw-d').value = dt.getDate();
      document.getElementById('zw-h').value = Math.floor((dt.getHours() + 1) / 2) % 12;
      renderTables();
    });
    renderTables();
  }

  // ---------- 灵龟八法 整页（按 人纪学习系统/灵龟八法页面.html 复刻：万年历 + 子午流注盘 + 圆形灵龟八法盘 + 灵龟八法表） ----------
  // 源 HTML 用内嵌 LINGGUI/NAJIA 字面值 + 「1900年起累加」干支算法客户端计算；
  // 服务端 /api/renji/lbg_compute 当前 400（cnlunar 异常），故此处内嵌源算法，保证与源一致且必出值。
  let LBG_DATA = null;
  function renderLbgPage(b) {
    filterBar.innerHTML = "";
    detailPane.innerHTML = "<div class='hint'>加载灵龟八法数据…</div>";
    const load = LBG_DATA ? Promise.resolve(LBG_DATA)
                          : getJSON("/static/lingui_data.json?v=1").then(d => (LBG_DATA = d));
    load.then(LD => { LBG_DATA = LD; mountLingui(LD); })
         .catch(e => { detailPane.innerHTML = "<div class='hint'>数据加载失败：" + esc(e && e.message) + "</div>"; });
  }

  function mountLingui(LD) {
    const { LINGGUI, NAJIA, TG, DZ, SX, JING_ABBR, ACS, GUA, GUA_SYM, ACS_COLOR, ACS_ACTIVE,
            SITIAN, ZAIQUAN, ZHONGYUN, ZHUQI_PRIMARY, SAN_YIN_SAN_YANG } = LD;

    detailPane.innerHTML = `
      <div class='lbg-wrap'>
        <div class='lbg-main'>
          <div class='lbg-left'>
            <div class='selector'>
              <div class='row1'>
                <label>年<input type='number' id='lg-y' min='1900' max='2100' value='2026'></label>
                <label>月<input type='number' id='lg-m' min='1' max='12' value='8'></label>
                <label>日<input type='number' id='lg-d' min='1' max='31' value='9'></label>
                <label>时辰<select id='lg-h'>
                  <option value='0'>子 23-1</option><option value='1'>丑 1-3</option>
                  <option value='2'>寅 3-5</option><option value='3'>卯 5-7</option>
                  <option value='4'>辰 7-9</option><option value='5'>巳 9-11</option>
                  <option value='6'>午 11-13</option><option value='7'>未 13-15</option>
                  <option value='8'>申 15-17</option><option value='9'>酉 17-19</option>
                  <option value='10'>戌 19-21</option><option value='11'>亥 21-23</option>
                </select></label>
                <button id='lg-now' type='button'>现在</button>
              </div>
            </div>
            <div class='computed'>
              <h3>四柱 / 生肖</h3><div class='blk' id='r-sizhu'></div>
              <h3>① 十二经纳子法（按时辰的本穴/源穴/补母/泻子）</h3><div class='blk' id='r-nazi'></div>
              <h3>② 十二经纳甲法（按时辰的流注输穴/经原/补母/泻子）</h3><div class='blk' id='r-najia'></div>
              <h3>③ 灵龟八法开穴（日干支 × 时辰）</h3><div class='blk' id='r-lgb'></div>
            </div>
            <div class='cal'>
              <div class='calhead'>
                <button id='lg-prev' type='button'>◀</button>
                <span class='ym' id='lg-cal-ym'></span>
                <button id='lg-next' type='button'>▶</button>
              </div>
              <table class='cal-tbl'><thead><tr><th>日</th><th>一</th><th>二</th><th>三</th><th>四</th><th>五</th><th>六</th></tr></thead>
              <tbody id='lg-cal-body'></tbody></table>
            </div>
          </div>
          <div class='rightcol'>
            <div class='disc-wrap'>
              <svg id='lg-disc' class='lbg-svg' viewBox='0 0 700 720' xmlns='http://www.w3.org/2000/svg'>
                <defs>
                  <radialGradient id='lg-discBg' cx='50%' cy='50%' r='50%'>
                    <stop offset='0%' stop-color='#fefcf0'/><stop offset='100%' stop-color='#f7eccf'/>
                  </radialGradient>
                  <marker id='lg-arrowhead' markerWidth='10' markerHeight='10' refX='5' refY='3' orient='auto'>
                    <polygon points='0 0,6 3,0 6' fill='#c0392b'/>
                  </marker>
                </defs>
              </svg>
            </div>
            <div class='yq-info'>
              <div class='card'><div class='lbl'>年干支</div><div class='val' id='lg-yq-y'>—</div></div>
              <div class='card'><div class='lbl'>中运</div><div class='val' id='lg-yq-zy'>—</div></div>
              <div class='card'><div class='lbl'>司天 / 在泉</div><div class='val' id='lg-yq-sq'>—</div></div>
              <div class='card'><div class='lbl'>当前节气</div><div class='val' id='lg-yq-jq'>—</div></div>
              <div class='card'><div class='lbl'>主气</div><div class='val' id='lg-yq-zq'>—</div></div>
              <div class='card'><div class='lbl'>客气</div><div class='val' id='lg-yq-kq'>—</div></div>
            </div>
          </div>
        </div>
        <div class='foot'>数据源：人纪 MDB linggui/najia/nazi · 阴历数据 cnlunar 预抽 2024-2030 共 2557 天 · 圆盘 SVG 按原软件截图结构重建</div>
      </div>
      `;

    // ===== 源算法（与 灵龟八法页面.html 完全一致） =====
    function isLeap(y) { return (y % 4 === 0 && y % 100 !== 0) || y % 400 === 0; }
    function daysInMonth(y, m) { return [31, isLeap(y) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]; }
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
      const monthStemStart = [2, 4, 0, 6, 8][yearStemIdx % 5];
      const monthBranchIdx = (m + 1) % 12;
      const monthStemIdx = (monthStemStart + (monthBranchIdx - 2 + 12) % 12) % 10;
      return { stem: TG[monthStemIdx], branch: DZ[monthBranchIdx] };
    }
    function hourGZ(dayStemIdx, h) {
      const hourStemStart = [0, 2, 4, 6, 8][dayStemIdx % 5];
      const hourStemIdx = (hourStemStart + h) % 10;
      return { stem: TG[hourStemIdx], branch: DZ[h] };
    }
    function nayin60(idx) {
      const arr = ['海中金','炉中火','大林木','路旁土','剑锋金','山头火','涧下水','城头土','白蜡金','杨柳木','泉中水','大海水','沙中金','山下火','平地木','壁上土','金箔金','覆灯火','天河水','大驿土','钗钏金','桑柘木','大溪水','沙中土','天上火','石榴木','大海水'];
      return arr[Math.floor(idx / 2) % 26];
    }
    function keqi(sitian, step) {
      const idx = SAN_YIN_SAN_YANG.indexOf(sitian);
      if (idx < 0) return '';
      return SAN_YIN_SAN_YANG[(idx + step - 3 + 18) % 6];
    }
    const JIEQI_24 = [[1,5,'小寒'],[1,20,'大寒'],[2,4,'立春'],[2,19,'雨水'],[3,5,'惊蛰'],[3,20,'春分'],[4,4,'清明'],[4,19,'谷雨'],[5,5,'立夏'],[5,20,'小满'],[6,5,'芒种'],[6,21,'夏至'],[7,7,'小暑'],[7,22,'大暑'],[8,7,'立秋'],[8,23,'处暑'],[9,7,'白露'],[9,22,'秋分'],[10,8,'寒露'],[10,23,'霜降'],[11,7,'立冬'],[11,22,'小雪'],[12,7,'大雪'],[12,21,'冬至']];
    const JIEQI_6 = [[1,20,1],[3,20,2],[5,21,3],[7,22,4],[9,23,5],[11,22,6]];
    function getStep(y, m, d) {
      let curName = '小寒', curStep = 1;
      for (const [mm, dd, n] of JIEQI_24) if (mm < m || (mm === m && dd <= d)) curName = n;
      for (const [mm, dd, s] of JIEQI_6) if (mm < m || (mm === m && dd <= d)) curStep = s;
      return { name: curName, step: curStep };
    }
    const SVGNS = 'http://www.w3.org/2000/svg';
    function svgEl(name, attrs) { const e = document.createElementNS(SVGNS, name); for (const k in attrs) e.setAttribute(k, attrs[k]); return e; }

    // ===== 圆形灵龟八法盘（按源 HTML drawDisc 重建，浅色主题） =====
    function drawDisc(h, dayBranchIdx) {
      const svg = document.getElementById('lg-disc');
      if (!svg) return;
      // 清空并以纯 SVG DOM 重建 defs（避免 innerHTML 命名空间隐患，确保各浏览器一致渲染）
      while (svg.firstChild) svg.removeChild(svg.firstChild);
      const defs = svgEl('defs', {});
      const grad = svgEl('radialGradient', { id: 'lg-discBg', cx: '50%', cy: '50%', r: '50%' });
      grad.appendChild(svgEl('stop', { offset: '0%', 'stop-color': '#fefcf0' }));
      grad.appendChild(svgEl('stop', { offset: '100%', 'stop-color': '#f7eccf' }));
      defs.appendChild(grad);
      const marker = svgEl('marker', { id: 'lg-arrowhead', markerWidth: '10', markerHeight: '10', refX: '5', refY: '3', orient: 'auto' });
      marker.appendChild(svgEl('polygon', { points: '0 0,6 3,0 6', fill: '#c0392b' }));
      defs.appendChild(marker);
      svg.appendChild(defs);
      const cx = 350, cy = 360;
      const R_HOUR = 310, R_TIANGAN = 270, R_SHICHEN = 240, R_JING = 200, R_ACS_IN = 100, R_ACS_OUT = 175;
      const pos = (hour, r) => { const a = (hour * 15 - 90) * Math.PI / 180; return { x: cx + r * Math.cos(a), y: cy + r * Math.sin(a) }; };
      svg.appendChild(svgEl('circle', { cx, cy, r: R_HOUR + 8, fill: 'url(#lg-discBg)', stroke: '#5a4a30', 'stroke-width': 2 }));
      // 1. 24 小时数字外环
      for (let hh = 0; hh < 24; hh++) {
        const p = pos(hh, R_HOUR);
        const t = svgEl('text', { x: p.x, y: p.y, 'text-anchor': 'middle', 'dominant-baseline': 'middle', 'font-size': hh % 3 === 0 ? 13 : 11, fill: '#5a4a30' });
        t.textContent = hh; svg.appendChild(t);
      }
      // 2. 12 时辰环
      const SHICHEN_NAMES = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥'];
      for (let i = 0; i < 12; i++) {
        const p = pos((23 + i * 2) % 24, R_TIANGAN);
        const t = svgEl('text', { x: p.x, y: p.y, 'text-anchor': 'middle', 'dominant-baseline': 'middle', 'font-size': 14, 'font-weight': 'bold', fill: '#2d5a4f' });
        t.textContent = SHICHEN_NAMES[i]; svg.appendChild(t);
      }
      // 3. 12 经脉简写环
      for (let i = 0; i < 12; i++) {
        const p = pos((23 + i * 2) % 24, R_JING);
        const t = svgEl('text', { x: p.x, y: p.y, 'text-anchor': 'middle', 'dominant-baseline': 'middle', 'font-size': 11, fill: '#5a4a30' });
        t.textContent = JING_ABBR[i]; svg.appendChild(t);
      }
      // 4. 八脉交穴 8 段扇形（卦 + 交穴），高亮当前开穴
      const dayGZKey = TG[dayBranchIdx % 10] + DZ[dayBranchIdx % 12];
      const kx = LINGGUI[dayGZKey] ? LINGGUI[dayGZKey][DZ[h]] : '';
      const kxName = kx ? kx.replace(/[0-9]/g, '').trim() : '';
      const activeIdx = ACS.indexOf(kxName);
      for (let i = 0; i < 8; i++) {
        const a1 = (i * 45 + 345 - 22.5 - 90) * Math.PI / 180;
        const a2 = (i * 45 + 345 + 22.5 - 90) * Math.PI / 180;
        const x1 = cx + R_ACS_OUT * Math.cos(a1), y1 = cy + R_ACS_OUT * Math.sin(a1);
        const x2 = cx + R_ACS_OUT * Math.cos(a2), y2 = cy + R_ACS_OUT * Math.sin(a2);
        const x3 = cx + R_ACS_IN * Math.cos(a2), y3 = cy + R_ACS_IN * Math.sin(a2);
        const x4 = cx + R_ACS_IN * Math.cos(a1), y4 = cy + R_ACS_IN * Math.sin(a1);
        const dpath = "M" + x1.toFixed(1) + "," + y1.toFixed(1) + " A" + R_ACS_OUT + "," + R_ACS_OUT + " 0 0 1 " + x2.toFixed(1) + "," + y2.toFixed(1)
          + " L" + x3.toFixed(1) + "," + y3.toFixed(1) + " A" + R_ACS_IN + "," + R_ACS_IN + " 0 0 0 " + x4.toFixed(1) + "," + y4.toFixed(1) + " Z";
        const isActive = (i === activeIdx);
        svg.appendChild(svgEl('path', { d: dpath, fill: isActive ? ACS_ACTIVE : ACS_COLOR[i], stroke: '#8b6f47', 'stroke-width': 1 }));
        const ta = (a1 + a2) / 2, tr = (R_ACS_IN + R_ACS_OUT) / 2;
        const tx = cx + tr * Math.cos(ta), ty = cy + tr * Math.sin(ta);
        const t = svgEl('text', { x: tx, y: ty - 4, 'text-anchor': 'middle', 'dominant-baseline': 'middle', 'font-size': isActive ? 14 : 12, 'font-weight': 'bold', fill: isActive ? '#1e4a3f' : '#2d5a4f' });
        const ts1 = svgEl('tspan', { x: tx, dy: 0 }); ts1.textContent = GUA[i] + GUA_SYM[i];
        const ts2 = svgEl('tspan', { x: tx, dy: 15 }); ts2.textContent = ACS[i];
        t.appendChild(ts1); t.appendChild(ts2); svg.appendChild(t);
      }
      // 5. 九宫 3x3 中心
      const JG = [[4,9,2],[3,5,7],[8,1,6]];
      for (let r = 0; r < 3; r++) for (let c = 0; c < 3; c++) {
        const x = cx - 30 + c * 30, y = cy - 30 + r * 30;
        svg.appendChild(svgEl('circle', { cx: x, cy: y, r: 9, fill: '#fdebd0', stroke: '#8b6f47' }));
        const t = svgEl('text', { x, y, 'text-anchor': 'middle', 'dominant-baseline': 'middle', 'font-size': 12, 'font-weight': 'bold', fill: '#2d5a4f' });
        t.textContent = JG[r][c]; svg.appendChild(t);
      }
      // 6. 当前时间指针（红箭头指向当前时辰）
      const curPos = (h * 2 + 1) % 24;
      const pp = pos(curPos, R_HOUR - 20);
      svg.appendChild(svgEl('line', { x1: cx, y1: cy, x2: pp.x, y2: pp.y, stroke: '#c0392b', 'stroke-width': 3, 'marker-end': 'url(#lg-arrowhead)' }));
      // 7. 中心当前开穴文字
      const center = svgEl('text', { x: cx, y: cy + 70, 'text-anchor': 'middle', 'font-size': 14, 'font-weight': 'bold', fill: '#c0392b' });
      center.textContent = '开穴：' + kx; svg.appendChild(center);
    }

    // ===== 月历（用服务端 /api/renji/lbg_calendar，cnlunar 阴历/节气） =====
    function drawCal(y, m, curD) {
      document.getElementById('lg-cal-ym').textContent = y + '年' + m + '月';
      getJSON("/api/renji/lbg_calendar?y=" + y + "&m=" + m).then(cal => {
        let html = "<tr>";
        let cell = 0;
        for (let i = 0; i < cal.first_sun; i++) { html += "<td class='empty'></td>"; cell++; }
        cal.days.forEach(day => {
          const isCur = (day.d === curD);
          let h2 = "<div class='solar'>" + day.d + "</div>";
          if (day.term) h2 += "<span class='jq'>" + esc(day.term) + "</span>";
          h2 += "<div class='lun'>" + esc(day.lunar || '') + "</div>";
          html += "<td class='" + (isCur ? 'cur' : '') + "'>" + h2 + "</td>";
          cell++;
          if (cell % 7 === 0 && day.d !== cal.days[cal.days.length - 1].d) html += "</tr><tr>";
        });
        while (cell % 7 !== 0) { html += "<td class='empty'></td>"; cell++; }
        html += "</tr>";
        document.getElementById('lg-cal-body').innerHTML = html;
      }).catch(() => { document.getElementById('lg-cal-body').innerHTML = "<tr><td colspan='7'>月历加载失败</td></tr>"; });
    }

    // ===== 主渲染（结构与源 HTML render() 一致） =====
    function render() {
      const y = parseInt(document.getElementById('lg-y').value);
      const m = parseInt(document.getElementById('lg-m').value);
      const d = parseInt(document.getElementById('lg-d').value);
      const h = parseInt(document.getElementById('lg-h').value);
      const yy = yearGZ(y, m, d);
      const dd = dayGZ(y, m, d);
      const mm = monthGZ(yy.idx % 10, m);
      const hh = hourGZ(dd.idx % 10, h);
      const dayGZKey = dd.stem + dd.branch;
      const kx = LINGGUI[dayGZKey] ? LINGGUI[dayGZKey][DZ[h]] : '—';
      const nj = NAJIA[DZ[h]] || {};
      document.getElementById('r-sizhu').innerHTML =
        "<div class='row'>"
        + "<div><span class='lbl'>公历</span><span class='val'>" + y + '年' + m + '月' + d + '日' + "</span></div>"
        + "<div><span class='lbl'>年柱</span><span class='val'>" + yy.stem + yy.branch + '年' + "</span></div>"
        + "<div><span class='lbl'>月柱</span><span class='val'>" + mm.stem + mm.branch + '月' + "</span></div>"
        + "<div><span class='lbl'>日柱</span><span class='val'>" + dd.stem + dd.branch + '日' + "</span></div>"
        + "<div><span class='lbl'>时柱</span><span class='val'>" + hh.stem + hh.branch + '时' + "</span></div>"
        + "<div><span class='lbl'>生肖</span><span class='val'>" + SX[yy.idx % 12] + "</span></div>"
        + "<div><span class='lbl'>纳音</span><span class='val'>" + nayin60(yy.idx) + "</span></div>"
        + "</div>";
      document.getElementById('r-nazi').innerHTML =
        "<div class='row'>"
        + "<div><span class='lbl'>流经脏腑经络</span><span class='val'>" + esc(nj['流经脏腑经络'] || '') + "</span></div>"
        + "<div><span class='lbl'>本穴</span><span class='val'>" + esc(nj['流注输穴'] || '') + "</span></div>"
        + "<div><span class='lbl'>源穴</span><span class='val'>" + esc(nj['经原穴'] || '') + "</span></div>"
        + "<div><span class='lbl'>补母穴</span><span class='val'>" + esc(nj['补母穴'] || '') + "</span></div>"
        + "<div><span class='lbl'>泻子穴</span><span class='val'>" + esc(nj['泻子穴'] || '') + "</span></div>"
        + "</div>";
      document.getElementById('r-najia').innerHTML =
        "<div class='row'>"
        + "<div><span class='lbl'>流注时辰</span><span class='val'>" + DZ[h] + '时' + "</span></div>"
        + "<div><span class='lbl'>流经脏腑经络</span><span class='val'>" + esc(nj['流经脏腑经络'] || '') + "</span></div>"
        + "<div><span class='lbl'>流注输穴</span><span class='val'>" + esc(nj['流注输穴'] || '') + "</span></div>"
        + "<div><span class='lbl'>经原穴</span><span class='val'>" + esc(nj['经原穴'] || '') + "</span></div>"
        + "<div><span class='lbl'>补母穴</span><span class='val'>" + esc(nj['补母穴'] || '') + "</span></div>"
        + "<div><span class='lbl'>泻子穴</span><span class='val'>" + esc(nj['泻子穴'] || '') + "</span></div>"
        + "</div>";
      document.getElementById('r-lgb').innerHTML =
        "<div class='row'>"
        + "<div><span class='lbl'>日干支</span><span class='val'>" + dayGZKey + "</span></div>"
        + "<div><span class='lbl'>时辰</span><span class='val'>" + DZ[h] + '时' + "</span></div>"
        + "<div><span class='lbl'>灵龟八法开穴</span><span class='val'>" + esc(kx) + "</span></div>"
        + "</div>";
      try { drawDisc(h, dd.idx); } catch (e) { console.error('[灵龟八法] 圆盘绘制失败：', e); }
      const yz = yy.stem + yy.branch;
      const st = SITIAN[yy.branch + ''] || SITIAN[yy.branch] || '';
      const zy = ZHONGYUN[yy.stem] || '';
      const zq = ZAIQUAN[yy.branch] || '';
      document.getElementById('lg-yq-y').textContent = yz + '年';
      document.getElementById('lg-yq-zy').textContent = zy;
      document.getElementById('lg-yq-sq').textContent = st + ' / ' + zq;
      const { name: jq, step } = getStep(y, m, d);
      document.getElementById('lg-yq-jq').textContent = jq;
      document.getElementById('lg-yq-zq').textContent = ZHUQI_PRIMARY[step - 1];
      document.getElementById('lg-yq-kq').textContent = keqi(st, step);
      drawCal(y, m, d);
    }

    ['lg-y','lg-m','lg-d','lg-h'].forEach(id => document.getElementById(id).addEventListener('change', render));
    document.getElementById('lg-now').addEventListener('click', () => {
      const dt = new Date();
      document.getElementById('lg-y').value = dt.getFullYear();
      document.getElementById('lg-m').value = dt.getMonth() + 1;
      document.getElementById('lg-d').value = dt.getDate();
      document.getElementById('lg-h').value = Math.floor((dt.getHours() + 1) / 2) % 12;
      render();
    });
    document.getElementById('lg-prev').addEventListener('click', () => {
      let m = parseInt(document.getElementById('lg-m').value);
      let y = parseInt(document.getElementById('lg-y').value);
      m--; if (m < 1) { m = 12; y--; }
      document.getElementById('lg-m').value = m;
      document.getElementById('lg-y').value = y;
      render();
    });
    document.getElementById('lg-next').addEventListener('click', () => {
      let m = parseInt(document.getElementById('lg-m').value);
      let y = parseInt(document.getElementById('lg-y').value);
      m++; if (m > 12) { m = 1; y++; }
      document.getElementById('lg-m').value = m;
      document.getElementById('lg-y').value = y;
      render();
    });
    render();
  }

// ---------- 汉唐取穴（临床取穴图表 + 针刺手法） ----------
  // ---------- 汉唐取穴（文档式：分类 → 主题 → 条文 + 取穴图表；针刺手法章节树） ----------
  function renderHantang(s) {
    if (s.method === "shoufa") return renderHantangShoufa();
    const catLabel = esc(s.method);
    // 左侧目录改为层级（组标题 + 嵌套条目）；顶部仅显示面包屑路径
    filterBar.innerHTML = "<div class='ht-crumb'>汉唐取穴 › " + catLabel + "</div>";
    resultList.innerHTML = "<div class='loading'>加载中…</div>";
    detailPane.innerHTML = "<div class='hint'>请从左侧目录选择条目，查看详细辩证选穴条文与取穴图表。</div>";
    getJSON("/api/renji/hantang/" + s.method + "/all").then(d => {
      const catName = d.name || s.method;
      const groups = d.tree || [];
      resultList.innerHTML = "";
      if (!groups.length) {
        resultList.innerHTML = "<div class='hint'>该分类暂无可归类条目。</div>";
        return;
      }
      let firstLeaf = null;
      // 递归渲染层级树：组(经脉/系/腑/病症分类/子分类)为二级标签，条目为可点叶节点
      function walk(nodes, path, charts) {
        (nodes || []).forEach(node => {
          if (node.children && node.children.length) {
            const gh = el("div", "ht-group-h", esc(node.name));
            const gc = node.charts || [];
            gh.onclick = () => {
              resultList.querySelectorAll(".active-row").forEach(x => x.classList.remove("active-row"));
              resultList.querySelectorAll(".ht-group-h").forEach(x => x.classList.remove("active-group"));
              gh.classList.add("active-group");
              showHantangGroup(node, catName);
            };
            resultList.appendChild(gh);
            walk(node.children, path.concat(node.name), gc.length ? gc : charts);
          } else {
            const li = el("div", "result-item ht-leaf", "<div class=\"t\">" + esc(node.name) + "</div>");
            li.dataset.label = path.concat(node.name).join(" / ");
            li.onclick = () => {
              resultList.querySelectorAll(".result-item").forEach(x => x.classList.remove("active-row"));
              li.classList.add("active-row");
              showHantangItem(node, catName, charts);
            };
            resultList.appendChild(li);
            if (!firstLeaf) firstLeaf = li;
          }
        });
      }
      walk(groups, [], null);
      if (firstLeaf) firstLeaf.onclick();
    }).catch(() => {
      resultList.innerHTML = "<div class='hint'>目录加载失败，请重试。</div>";
    });
  }

  function showHantangItem(t, catName, groupCharts) {
    let h = "<div class='ht-bread'>汉唐取穴 › " + esc(catName) + "</div>";
    h += "<h2 class='ht-title'>" + esc(t.name) + "</h2>";
    h += "<div class='ht-intro'>辩证选穴条文自人纪软件 EXE（导航树）+ LILUN.mdb 提取；取穴图表取自人纪 MDB <b>nishitu</b> 表（倪师取穴图）。点击图表可放大查看。</div>";
    if (t.text && t.text.trim()) {
      h += "<div class='ht-text'>" + esc(t.text) + "</div>";
    } else {
      h += "<div class='ht-empty'>（暂无辩证选穴条文）</div>";
    }
    const charts = (groupCharts && groupCharts.length) ? groupCharts : (t.charts || []);
    if (!charts.length) {
      h += "<div class='ht-empty'>（暂无匹配图表）</div>";
    } else {
      h += "<div class='ht-sec-ttl'>取穴图表（" + charts.length + "）</div>";
      h += "<div class='ht-grid'>";
      charts.forEach(c => {
        h += "<div class='ht-cell' data-img=\"/renji/img?name=" + encodeURIComponent(c) + "\" data-cap=\"" + esc(c) + "\">"
           + "<div class='imgbox'><img src=\"/renji/img?name=" + encodeURIComponent(c) + "\" loading=\"lazy\" alt=\"" + esc(c) + "\"></div>"
           + "<div class='nm'>" + esc(c) + "</div></div>";
      });
      h += "</div>";
    }
    detailPane.innerHTML = h;
  }

  function showHantangGroup(g, catName) {
    let h = "<div class='ht-bread'>汉唐取穴 › " + esc(catName) + "</div>";
    h += "<h2 class='ht-title'>" + esc(g.name) + "</h2>";
    h += "<div class='ht-intro'>以下为该分类的取穴图表；点击下方具体条目可查看对应辩证选穴条文。</div>";
    const charts = g.charts || [];
    if (!charts.length) {
      h += "<div class='ht-empty'>（该分类暂无配套取穴图表）</div>";
    } else {
      h += "<div class='ht-sec-ttl'>取穴图表（" + charts.length + "）</div>";
      h += "<div class='ht-grid'>";
      charts.forEach(c => {
        h += "<div class='ht-cell' data-img=\"/renji/img?name=" + encodeURIComponent(c) + "\" data-cap=\"" + esc(c) + "\">"
           + "<div class='imgbox'><img src=\"/renji/img?name=" + encodeURIComponent(c) + "\" loading=\"lazy\" alt=\"" + esc(c) + "\"></div>"
           + "<div class='nm'>" + esc(c) + "</div></div>";
      });
      h += "</div>";
    }
    detailPane.innerHTML = h;
  }

  function renderHantangShoufa() {
    filterBar.innerHTML = "";
    resultList.innerHTML = "<div class='loading'>加载中…</div>";
    detailPane.innerHTML = "<div class='hint'>请从左侧目录选择手法，查看说明与演示图。</div>";
    getJSON("/static/shoufa.json?v=1").then(d => {
      const sf = d.shoufa || [];
      const gallery = d.gallery || [];
      const imgUrl = (b) => "/img/shoufa/" + encodeURIComponent(b);
      const showItem = (s) => {
        let h = "<h2 class='ht-title'>" + esc(s.name) + "</h2>";
        if (s.text && s.text.trim()) h += "<div class='ht-text'>" + esc(s.text) + "</div>";
        if (s.imgs && s.imgs.length) {
          h += "<div class='ht-sec-ttl'>手法图（" + s.imgs.length + "）</div>";
          h += "<div class='ht-grid'>";
          s.imgs.forEach(im => {
            h += "<div class='ht-cell' data-img=\"" + imgUrl(im) + "\" data-cap=\"" + esc(s.name) + " 手法图\">"
               + "<div class='imgbox'><img src=\"" + imgUrl(im) + "\" loading='lazy' alt=\"" + esc(s.name) + "\"></div>"
               + "<div class='nm'>" + esc(s.name) + " 手法图</div></div>";
          });
          h += "</div>";
        }
        detailPane.innerHTML = h;
      };
      const showGallery = () => {
        let h = "<h2 class='ht-title'>针刺手法总览图</h2>";
        h += "<div class='ht-grid'>";
        gallery.forEach(im => {
          h += "<div class='ht-cell' data-img=\"" + imgUrl(im) + "\" data-cap='手法演示图'>"
             + "<div class='imgbox'><img src=\"" + imgUrl(im) + "\" loading='lazy' alt='手法图'></div>"
             + "<div class='nm'>手法演示图</div></div>";
        });
        h += "</div>";
        detailPane.innerHTML = h;
      };
      resultList.innerHTML = "";
      let first = null;
      sf.forEach((s) => {
        const li = el("div", "result-item", "<div class=\"t\">" + esc(s.name) + "</div>");
        li.dataset.label = s.name;
        li.onclick = () => {
          resultList.querySelectorAll(".result-item").forEach(x => x.classList.remove("active-row"));
          li.classList.add("active-row");
          showItem(s);
        };
        resultList.appendChild(li);
        if (!first) first = li;
      });
      if (gallery.length) {
        const li = el("div", "result-item", "<div class=\"t\">针刺手法总览图</div>");
        li.dataset.label = "针刺手法总览图";
        li.onclick = () => {
          resultList.querySelectorAll(".result-item").forEach(x => x.classList.remove("active-row"));
          li.classList.add("active-row");
          showGallery();
        };
        resultList.appendChild(li);
      }
      if (first) first.onclick();
    }).catch(() => {
      resultList.innerHTML = "<div class='hint'>目录加载失败，请重试。</div>";
      detailPane.innerHTML = "<div class='hint'>针刺手法数据载入失败，请重试。</div>";
    });
  }

  // 汉唐取穴 图片点击放大（复用 style.css .lightbox）
  let _lb = null;
  function openLb(src, cap) {
    if (!_lb) {
      _lb = document.createElement("div");
      _lb.className = "lightbox";
      _lb.setAttribute("role", "dialog");
      _lb.setAttribute("aria-label", "图片放大查看");
      _lb.addEventListener("click", () => { if (_lb) { _lb.remove(); _lb = null; } });
      document.body.appendChild(_lb);
    }
    _lb.innerHTML = "";
    const im = document.createElement("img");
    im.src = src; im.alt = cap || "";
    im.onerror = () => { if (_lb) { _lb.remove(); _lb = null; } };
    _lb.appendChild(im);
  }
  document.addEventListener("click", (ev) => {
    if (ev.target && ev.target.closest) {
      const btn = ev.target.closest(".bi-btn");
      if (btn) {
        const ref = btn.closest(".body-ref");
        if (ref) {
          const view = btn.getAttribute("data-bi");
          const img = ref.querySelector(".body-ref-img img");
          if (img && BODY_VIEWS[view]) img.src = "/renji/img?name=" + encodeURIComponent(BODY_VIEWS[view]);
          ref.querySelectorAll(".bi-btn").forEach(b => b.classList.toggle("active", b === btn));
        }
        return;
      }
      const cell = ev.target.closest(".ht-cell");
      if (cell && cell.dataset.img) {
        ev.preventDefault();
        openLb(cell.dataset.img, cell.dataset.cap);
      }
    }
  });
  document.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape" && _lb) { _lb.remove(); _lb = null; }
  });

  // ---------- 跨系统：中药 / 药图 ----------
  function renderCross(s) {
    filterBar.innerHTML = "";
    getJSON(s.endpoint + "?size=2000").then(d => {
      resultList.innerHTML = "";
      const items = d.items || [];
      items.slice(0, 2000).forEach((it, i) => {
        // herbs 接口用 MZ 命名字段，yaotu 接口用 name；统一取名称（修复下拉/列表项空白）
        const name = it.name || it.MZ || it.title || "";
        const li = el("li", "result-item", "<div class=\"t\">" + esc(name) + "</div>");
        li.onclick = () => {
          let h = "<div class='point-card'><h4>" + esc(name) + "</h4>";
          Object.keys(it).forEach(k => {
            // name/MZ 已作标题；_image/_rel/_folder 为内部字段，均不展示为原始键名
            if (k === "name" || k === "MZ" || k === "_image" || k === "_rel" || k === "_folder") return;
            if (it[k] && typeof it[k] === "string")
              h += "<div class='sec'><b>" + esc(k) + "：</b><br>" + esc(it[k]) + "</div>";
          });
          // 药图：MDB 派生（原态/药材/饮片）走 /api/herb_image；本草/中药图片 文件夹图走 /extimg（已随站部署）
          const imgName = it._image || name;
          if (imgName) {
            const imgSrc = it._folder
              ? ("/extimg?p=" + encodeURIComponent(it._rel))
              : ("/api/herb_image/" + encodeURIComponent(imgName));
            h += "<img src='" + imgSrc + "' style='max-width:160px;margin:4px;background:#fff;border-radius:6px' onerror=\"this.style.display='none'\">";
          }
          h += "</div>";
          detailPane.innerHTML = h;
        };
        resultList.appendChild(li);
      });
    });
  }

  // ---------- 药图画廊（药图列表.html 内容：467 张图鉴）----------
  let _ytKeyHandler = null;
  const YT_PAGE = 20;
  function renderYaotuGallery() {
    filterBar.className = "yt-filterbar";
    filterBar.innerHTML =
      '<div class="yt-cats" id="ytCats"></div>' +
      '<div class="yt-search"><input id="ytSearch" placeholder="搜索药名…" autocomplete="off"></div>';
    resultList.className = "result-list";
    detailPane.className = "detail-pane yt-pane";
    detailPane.innerHTML =
      '<div class="yt-preview"><img id="ytBig" alt=""></div>' +
      '<div class="yt-pname" id="ytPname"></div>' +
      '<div class="yt-phint">点击左侧缩略图查看大图 · ← / → 键切换</div>';
    const catsWrap = $("#ytCats"), big = $("#ytBig"), pname = $("#ytPname");
    const CATS = ["上经", "中经", "下经", "增补", "其他"];
    const ytLabel = (c) => (c.num != null ? c.num + "、" : "") + c.n;
    let charts = [], view = [], cur = -1, page = 0, curCat = "", curQ = "";
    const pageOf = (pos) => Math.floor(pos / YT_PAGE);

    function buildCats() {
      const counts = {};
      charts.forEach(c => { const k = c.c || "其他"; counts[k] = (counts[k] || 0) + 1; });
      let html = '<button class="yt-cat' + (curCat === "" ? " active" : "") + '" data-c="">全部 <i>' + charts.length + '</i></button>';
      CATS.forEach(ct => {
        if (counts[ct]) html += '<button class="yt-cat' + (curCat === ct ? " active" : "") + '" data-c="' + ct + '">' + ct + ' <i>' + counts[ct] + '</i></button>';
      });
      catsWrap.innerHTML = html;
      catsWrap.querySelectorAll(".yt-cat").forEach(b => {
        b.onclick = () => { curCat = b.dataset.c; applyFilter(); };
      });
    }

    function applyFilter() {
      view = [];
      charts.forEach((c, i) => {
        if (curCat && (c.c || "其他") !== curCat) return;
        if (curQ && c.n.indexOf(curQ) < 0) return;
        view.push(i);
      });
      page = 0;
      renderPage();
    }

    function renderPage() {
      const total = view.length;
      const pages = Math.max(1, Math.ceil(total / YT_PAGE));
      if (page >= pages) page = pages - 1;
      if (page < 0) page = 0;
      const start = page * YT_PAGE;
      const slice = view.slice(start, start + YT_PAGE);
      let html = '<div class="yt-count">共 ' + total + ' 张 · 第 ' + (page + 1) + ' / ' + pages + ' 页</div>';
      html += '<div class="yt-grid" id="ytGrid">';
      if (!slice.length) {
        html += '<div class="yt-empty">未找到匹配的药图</div>';
      } else {
        slice.forEach((idx, k) => {
          const c = charts[idx];
          const pos = start + k;
          html += '<div class="yt-item' + (idx === cur ? " active" : "") + '" data-pos="' + pos + '" data-idx="' + idx + '">' +
            '<div class="yt-thumb"><img loading="lazy" src="' + c.f + '" alt="' + esc(c.n) + '"></div>' +
            '<div class="yt-cap">' + esc(ytLabel(c)) + '</div></div>';
        });
      }
      html += '</div>';
      html += '<div class="yt-pager">' +
        '<button class="yt-pbtn" id="ytPrev"' + (page <= 0 ? " disabled" : "") + '>‹ 上一页</button>' +
        '<span class="yt-pinfo">' + (total ? (start + 1) + '–' + Math.min(start + YT_PAGE, total) : 0) + ' / ' + total + '</span>' +
        '<button class="yt-pbtn" id="ytNext"' + (page >= pages - 1 ? " disabled" : "") + '>下一页 ›</button>' +
        '</div>';
      resultList.innerHTML = html;
      const g = $("#ytGrid");
      if (g) g.querySelectorAll(".yt-item").forEach(it => {
        it.onclick = () => show(Number(it.dataset.idx), Number(it.dataset.pos));
      });
      const pv = $("#ytPrev"), nx = $("#ytNext");
      if (pv) pv.onclick = () => { if (page > 0) { page--; renderPage(); } };
      if (nx) nx.onclick = () => { if (page < pages - 1) { page++; renderPage(); } };
    }

    function show(idx, pos) {
      cur = idx;
      const np = pageOf(pos);
      if (np !== page) { page = np; renderPage(); }
      const c = charts[idx];
      big.src = c.f; pname.textContent = ytLabel(c);
      const g = $("#ytGrid");
      if (g) g.querySelectorAll(".yt-item").forEach(e => e.classList.toggle("active", Number(e.dataset.idx) === idx));
    }

    getJSON("/static/yaotu_gallery.json?v=2").then(d => {
      charts = d || [];
      const CATI = {"上经":0,"中经":1,"下经":2,"增补":3,"其他":4};
      charts.sort((a,b)=>{
        const ca = CATI[a.c]!=null?CATI[a.c]:9, cb = CATI[b.c]!=null?CATI[b.c]:9;
        if(ca!==cb) return ca-cb;
        const na = a.num==null?1e9:a.num, nb = b.num==null?1e9:b.num;
        return na-nb;
      });
      buildCats();
      applyFilter();
      if (view.length) show(view[0], 0);
    }).catch(() => {
      detailPane.innerHTML = '<div class="hint">药图清单加载失败，请刷新重试。</div>';
    });

    const box = $("#ytSearch");
    if (box) box.oninput = () => {
      curQ = box.value.trim();
      applyFilter();
      if (view.length) show(view[0], 0);
    };

    if (_ytKeyHandler) document.removeEventListener("keydown", _ytKeyHandler);
    _ytKeyHandler = (e) => {
      if (!view.length) return;
      const i = view.indexOf(cur);
      if (e.key === "ArrowRight") { const ni = Math.min(i + 1, view.length - 1); show(view[ni], ni); }
      else if (e.key === "ArrowLeft") { const ni = Math.max(i - 1, 0); show(view[ni], ni); }
    };
    document.addEventListener("keydown", _ytKeyHandler);
  }

  // ---------- 中药查询（中药查询.html 内容接入，替换原 cross/herbs）----------
  let _zyState = null;
  let _zyKeyHandler = null;
  function renderZhongyao() {
    filterBar.innerHTML = "";
    resultList.innerHTML = "";
    if (listHint) listHint.style.display = "none";
    if (pager) pager.style.display = "";
    detailPane.innerHTML = "<div class='hint'>载入中…</div>";
    getJSON("/static/zhongyao_herbs_meta.json?v=3").then(meta => {
      const CATS = ["上经", "中经", "下经", "增补", "其他"];
      const QIS = ["热", "温", "平", "凉", "寒"];
      const ZY_PAGE = 20;
      const VER = "?v=3";
      const CAT_FILE = { "上经":"zhongyao_herbs_shang.json", "中经":"zhongyao_herbs_zhong.json", "下经":"zhongyao_herbs_xia.json", "增补":"zhongyao_herbs_zeng.json", "其他":"zhongyao_herbs_qita.json" };
      const _cache = {};      // cat -> 已加载数组（缓存复用）
      const _loading = {};    // cat -> 进行中的 Promise
      let _meta = meta || null;
      function loadCat(cat) {
        if (_cache[cat]) return Promise.resolve(_cache[cat]);
        if (_loading[cat]) return _loading[cat];
        const p = getJSON("/static/" + CAT_FILE[cat] + VER).then(arr => { _cache[cat] = arr; return arr; });
        _loading[cat] = p;
        return p;
      }
      function loadCats(cats) {
        if (cats.length === 1 && cats[0] === "") return Promise.all(CATS.map(loadCat)).then(a => [].concat(...a));
        return Promise.all(cats.map(loadCat)).then(a => [].concat(...a));
      }
      const st = { HERBS: [], curCat: "", curQi: "", curQ: "", activeIdx: null, page: 1 };
      _zyState = st;

      function countCat(c) {
        if (c === "") return _meta ? _meta.total : st.HERBS.length;
        return _meta ? (_meta.counts[c] || 0) : st.HERBS.filter(h => h.c === c).length;
      }
      function countQi(q) {
        const base = (st.curCat === "" ? st.HERBS : st.HERBS.filter(h => h.c === st.curCat));
        return q === "" ? base.length : base.filter(h => h.qi === q).length;
      }
      function hl(s, q) {
        s = s || "";
        if (!q) return esc(s);
        try {
          return esc(s).replace(new RegExp("(" + q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "gi"), "<span class='hl'>$1</span>");
        } catch (e) { return esc(s); }
      }
      function filtered() {
        const q = st.curQ.trim().toLowerCase();
        return st.HERBS.filter(h => {
          if (st.curCat && h.c !== st.curCat) return false;
          if (st.curQi && h.qi !== st.curQi) return false;
          if (q) {
            const hay = (h.n + " " + (h.g || "") + " " + (h.x || "") + " " + (h.b || "") + " " + (h.bj || "")).toLowerCase();
            if (!hay.includes(q)) return false;
          }
          return true;
        });
      }
      function zyLabel(h) { return (h.num != null ? (h.num + "、") : "") + h.n; }

      function renderTags() {
        let tb = "<div class='zy-toolbar'>";
        tb += "<input class='zy-search' id='zySearch' placeholder='搜索药名 / 功效 / 性味 / 本经原文…' value='" + esc(st.curQ) + "'>";
        tb += "<div class='zy-ftitle'>《神农本草经》分类</div><div class='zy-ftags'>";
        [["", "全部"]].concat(CATS.map(c => [c, c])).forEach(([k, label]) => {
          tb += "<button class='zy-ftag" + (k === st.curCat ? " active" : "") + "' data-cat='" + k + "'>" + label + "<span class='ct'>" + countCat(k) + "</span></button>";
        });
        tb += "</div><div class='zy-ftitle'>性味（气）</div><div class='zy-ftags'>";
        [["", "全部"]].concat(QIS.map(q => [q, q])).forEach(([k, label]) => {
          tb += "<button class='zy-ftag" + (k === st.curQi ? " active" : "") + "' data-qi='" + k + "'>" + label + "<span class='ct'>" + countQi(k) + "</span></button>";
        });
        tb += "</div></div>";
        filterBar.innerHTML = tb;
        const se = document.getElementById("zySearch");
        se.addEventListener("input", () => { st.curQ = se.value; st.page = 1; renderList(); });
        filterBar.querySelectorAll("[data-cat]").forEach(b => {
          b.onclick = () => applyCat(b.getAttribute("data-cat"));
        });
        filterBar.querySelectorAll("[data-qi]").forEach(b => {
          b.onclick = () => { st.curQi = b.getAttribute("data-qi"); st.page = 1; applyCat(st.curCat); };
        });
      }

      function renderList() {
        const data = filtered();
        const isMB = isMobile();
        const total = data.length;
        const pages = Math.max(1, Math.ceil(total / ZY_PAGE));
        if (st.page > pages) st.page = pages;
        if (st.page < 1) st.page = 1;
        const q = st.curQ.trim();
        resultList.innerHTML = "";
        if (!total) {
          resultList.innerHTML = "<li class='hint'>无匹配结果</li>";
          if (pager) pager.innerHTML = "";
          return;
        }
        const view = isMB ? data : data.slice((st.page - 1) * ZY_PAGE, st.page * ZY_PAGE);
        view.forEach(h => {
          const li = el("li", "result-item zy-item" + (st.activeIdx !== null && st.HERBS[st.activeIdx] === h ? " active" : ""));
          li.dataset.label = zyLabel(h);
          const badgeCls = h.sh ? "zy-badge fill" : (h.c === "其他" ? "zy-badge other" : "zy-badge");
          const badgeTxt = h.sh ? "神农·补全" : (h.c === "其他" ? "后世本草" : h.c);
          li.innerHTML =
            (h.num != null ? "<span class='zy-num'>" + h.num + "、</span>" : "") +
            "<span class='zy-nm'>" + esc(h.n) + "</span>" +
            "<span class='" + badgeCls + "'>" + badgeTxt + "</span>" +
            (h.qi ? "<span class='zy-qi'>" + esc(h.qi) + "</span>" : "");
          li.onclick = () => show(h);
          resultList.appendChild(li);
        });
        if (!isMB) renderPager(total, pages);
        else if (pager) pager.innerHTML = "";
      }

      function renderPager(total, pages) {
        if (!pager) return;
        pager.innerHTML = "";
        const mk = (label, page, dis) => {
          const b = document.createElement("button");
          b.textContent = label; b.disabled = dis;
          b.onclick = () => { st.page = page; renderList(); };
          return b;
        };
        pager.appendChild(mk("上一页", st.page - 1, st.page <= 1));
        const info = document.createElement("span");
        info.style.cssText = "align-self:center;font-size:13px;color:#5b5246";
        info.textContent = "第 " + st.page + " / " + pages + " 页（共 " + total + " 条）";
        pager.appendChild(info);
        pager.appendChild(mk("下一页", st.page + 1, st.page >= pages));
      }

      function show(h) {
        st.activeIdx = st.HERBS.indexOf(h);
        const data = filtered();
        const idx = data.indexOf(h);
        if (idx >= 0 && !isMobile()) {
          const pg = Math.floor(idx / ZY_PAGE) + 1;
          if (pg !== st.page) st.page = pg;
        }
        renderList();
        const seqLine = (h.c !== "其他" && h.cs != null)
          ? "《神农本草经》· " + esc(h.c) + " · 本经第 " + h.cs + " 味（全书总第 " + h.s + " 味）"
          : (h.c !== "其他" ? "《神农本草经》· " + esc(h.c) : (h.sh ? "神农本草经 · 补全（仅存本经原文与倪师注解）" : "后世本草（非神农本经收录）"));
        const rows = [
          ["性能（性味归经）", h.x],
          ["功效", h.g],
          ["用法用量", h.y],
          ["使用注意", h.z],
          ["神农本经原文", h.bj],
          ["倪师注解", h.nt],
          ["古籍摘要", h.j],
          ["现代研究", h.m],
          ["简述", h.b],
        ];
        let html = "<div class='zy-detail'><div class='zy-ph'><div class='nm'>" + esc(h.n) + "</div><div class='zy-seq'>" + seqLine + "</div>";
        rows.forEach(([k, v]) => {
          if (v && v.trim()) html += "<div class='zy-row'><span class='k'>" + k + "</span><div class='v'>" + hl(v, st.curQ.trim()) + "</div></div>";
        });
        if (h.img) {
          html += "<img class='zy-herb' src='" + esc(h.img) + "' alt='" + esc(h.n) + "' onerror=\"this.style.display='none'\">";
        }
        html += "</div></div>";
        detailPane.innerHTML = html;
        const li = resultList.querySelector(".result-item.active");
        if (li) li.scrollIntoView({ block: "nearest" });
      }

      function applyCat(cat) {
        st.curCat = cat;
        st.page = 1;
        st.activeIdx = null;
        detailPane.innerHTML = "<div class='hint'>载入中…</div>";
        renderTags();
        loadCats([cat]).then(arr => {
          st.HERBS = arr;
          renderList();
          renderTags();
        }).catch(err => {
          detailPane.innerHTML = "<div class='hint'>中药数据载入失败：" + esc(String(err)) + "</div>";
        });
      }

      // 初始：meta 已载入（含分类计数），按需懒加载具体分类数据，避免一次性下载全量
      renderTags();
      resultList.innerHTML = "<li class='hint'>请选择上方《神农本草经》分类查看（点『全部』载入全部 " + (_meta ? _meta.total : "") + " 味）</li>";
      if (pager) pager.innerHTML = "";

      if (_zyKeyHandler) document.removeEventListener("keydown", _zyKeyHandler);
      _zyKeyHandler = (e) => {
        if (e.target && e.target.tagName === "INPUT") return;
        const data = filtered();
        if (!data.length) return;
        let i = st.activeIdx === null ? -1 : data.indexOf(st.HERBS[st.activeIdx]);
        if (e.key === "ArrowDown") { i = Math.min(i + 1, data.length - 1); show(data[i]); e.preventDefault(); }
        else if (e.key === "ArrowUp") { i = Math.max(i - 1, 0); show(data[i]); e.preventDefault(); }
      };
      document.addEventListener("keydown", _zyKeyHandler);
    }).catch(err => {
      detailPane.innerHTML = "<div class='hint'>中药数据载入失败：" + esc(String(err)) + "</div>";
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

  // ---------- 动画演示：穴位走向（依 穴位走向动画.html + SELFDATA 真实坐标重建）----------
  // 真实坐标见 /static/meridian_flow.json（viewBox 0 0 1278 2304，与全身背面经络穴位图像素一致）。
  const SHIER = ["肺经","大肠经","胃经","脾经","心经","小肠经","膀胱经","肾经","心包经","三焦经","胆经","肝经"];
  const QIJING = ["督脉","任脉","冲脉","带脉","阴维脉","阳维脉","阳跷脉","阴跷脉"];

  // 真人全身经络穴位图（自 EXE 提取，2026-08-09 集成进 /renji）
  // 膀胱经 / 督脉 行于背后 → 默认背面图；其余正面图。
  const BODY_VIEWS = {
    "正面": "全身正面经络穴位图",
    "背面": "全身背面经络穴位图",
    "侧面": "全身侧面经络穴位图"
  };
  function bodyRefBlock(view) {
    let h = "<div class='body-ref'>";
    h += "<div class='body-ref-bar'>";
    Object.keys(BODY_VIEWS).forEach(k => {
      h += "<button type='button' class='bi-btn" + (k === view ? " active" : "") + "' data-bi='" + k + "'>" + k + "</button>";
    });
    h += "</div>";
    h += "<div class='body-ref-img'><img src='/renji/img?name=" + encodeURIComponent(BODY_VIEWS[view]) +
         "' alt='" + view + "经络穴位图' loading='lazy'></div>";
    h += "</div>";
    return h;
  }
  // 短名 → meridian_flow.json 的 key（原软件全称）
  const FLOW_KEY_MAP = {
    "肺经":"手太阴肺经","大肠经":"手阳明大肠经","胃经":"足阳明胃经","脾经":"足太阴脾经",
    "心经":"手少阴心经","小肠经":"手太阳小肠经","膀胱经":"足太阳膀胱经","肾经":"足少阴肾经",
    "心包经":"手厥阴心包经","三焦经":"手少阳三焦经","胆经":"足少阳胆经","肝经":"足厥阴肝经",
    "督脉":"督脉经穴","任脉":"任脉经穴"
  };
  function FLOW_KEY_OF(short) { return FLOW_KEY_MAP[short] || null; }
  // 每条经络对应的正确人体方位图（解剖学：膀胱经/督脉行于背后→背面；胆经行于体侧→侧面；其余正面）
  const MERIDIAN_VIEW = {
    "膀胱经": "背面", "督脉": "背面", "胆经": "侧面"
  };
  // 三张人体图真实像素尺寸（取自图片文件），用于按图设定 SVG viewBox，使坐标按比例贴合
  const BODY_IMG_DIMS = {
    "正面": [1793, 3200], "背面": [1278, 2304], "侧面": [1283, 2304]
  };
  function flowViewOf(name) { return MERIDIAN_VIEW[name] || "正面"; }
  function flowImgOf(view) { return "/renji/img?name=" + encodeURIComponent(BODY_VIEWS[view]); }
  let FLOW_DATA = null;
  let FLOW_ACTIVE = 0;
  function flowGetData() {
    if (FLOW_DATA) return Promise.resolve(FLOW_DATA);
    return getJSON("/static/meridian_flow.json?v=1").then(d => (FLOW_DATA = d));
  }

  // （已删除原有的示意人体 bodyShapes，改由真实人体图 + SELFDATA 坐标叠加）
  function renderAnimation(s) {
    const list = s.group === "shier" ? SHIER : QIJING;
    // 经络切换按钮放进 #filterBar（与 #resultList 平级），不再把 <div> 塞进 <ul>
    filterBar.innerHTML = "";
    list.forEach(m => {
      const b = el("button", "filter-tab", m);
      b.onclick = () => playMeridian(m);
      filterBar.appendChild(b);
    });
    // #resultList 只承载 #flowPtsHost（穴位顺序列表），playMeridian 仍按此查询
    resultList.innerHTML = "<div id='flowPtsHost' class='flow-pts-host'></div>";
    const art = s.group === "shier" ? ART_SHIER : ART_QIJING;
    const pv = "正面", pvImg = flowImgOf(pv);
    detailPane.innerHTML =
      "<div class='flow-placeholder'>" +
        "<img src='" + pvImg + "' alt='全身正面经络穴位图' onerror=\"this.style.display='none'\">" +
        "<div class='flow-phcap'>点击左侧经络，查看其穴位循行走向（基于 SELFDATA 真实坐标叠加；按经络自动切换正/背/侧人体图）</div>" +
      "</div>" +
      "<div class='anim-art'>" + esc(art) + "</div>";
  }
  function playMeridian(name) {
    if (!FLOW_DATA) { flowGetData().then(() => playMeridian(name)); return; }
    const key = FLOW_KEY_OF(name);
    const info = FLOW_DATA[key];
    FLOW_ACTIVE = 0;
    if (!info) {
      // 无 SELFDATA 独立坐标的奇经（冲/带/维/跷）：仅文字说明
      detailPane.innerHTML =
        "<div class='anim-cap'>" + esc(name) + " · 穴位走向</div>" +
        "<div class='hint'>该奇经（冲 / 带 / 维 / 跷）无 SELFDATA 独立穴位坐标，无法绘制循行路径；以下为循行说明。</div>" +
        "<div class='anim-art'>" + esc(ART_QIJING) + "</div>";
      return;
    }
    const pts = info.points.filter(p => p.x != null);
    const d = pts.map((p, i) => (i === 0 ? "M" : "L") + p.x + "," + p.y).join(" ");
    let dots = "";
    info.points.forEach((p, idx) => {
      if (p.x == null) return;
      const act = idx === FLOW_ACTIVE;
      dots += "<g class='flow-dot" + (act ? " active" : "") + "' data-idx='" + idx + "'>" +
                "<circle cx='" + p.x + "' cy='" + p.y + "' r='" + (act ? 9 : 6) + "'></circle>" +
                "<text class='flow-num' x='" + p.x + "' y='" + p.y + "'>" + p.i + "</text>" +
                "<text class='flow-name' x='" + p.x + "' y='" + (p.y - 14) + "'>" + esc(p.name) + "</text>" +
              "</g>";
    });
    const view = flowViewOf(name), vd = BODY_IMG_DIMS[view], vimg = flowImgOf(view);
    const svg = "<svg class='flow-svg' viewBox='0 0 " + vd[0] + " " + vd[1] + "' preserveAspectRatio='xMidYMid meet'>" +
        "<image class='flow-img' href='" + vimg + "' xlink:href='" + vimg + "' x='0' y='0' width='" + vd[0] + "' height='" + vd[1] + "'/>" +
        "<path class='flow-line' d='" + d + "'></path>" +
        "<path class='flow-anim' d='" + d + "'></path>" +
        dots + "</svg>";
    const meta = "<div class='flow-meta'>" +
        "<span><b>" + esc(name) + "</b>（" + esc(info.code) + "）</span>" +
        "<span>人体视图：<b>" + view + "</b></span>" +
        "<span>阴阳：<b>" + (info.yin === "yin" ? "阴经" : "阳经") + "</b></span>" +
        "<span>五行：<b>" + esc(info.element) + "</b></span>" +
        "<span>走向：<b>" + esc(info.direction) + "</b></span>" +
        "<span>穴位：<b>" + info.points.length + "</b></span>" +
      "</div>";
    let plist = "<div class='flow-pts'><div class='flow-pttl'>穴位顺序（点击联动高亮）</div>";
    info.points.forEach((p, idx) => {
      const cur = idx === FLOW_ACTIVE ? " cur" : "";
      const miss = p.x == null ? " miss" : "";
      const xy = p.x == null ? "坐标缺" : "(" + p.x + "," + p.y + ")";
      plist += "<div class='flow-pt" + cur + miss + "' data-idx='" + idx + "'>" +
          "<span class='fp-num'>" + p.i + ".</span>" +
          "<span class='fp-name'>" + esc(p.name) + "</span>" +
          "<span class='fp-xy'>" + xy + "</span></div>";
    });
    plist += "</div>";
    const host = resultList.querySelector("#flowPtsHost");
    if (host) host.innerHTML = plist;
    detailPane.innerHTML =
      "<div class='flow-wrap'>" +
        "<div class='flow-body'>" + svg + "</div>" +
        "<div class='flow-detail'>" + meta + flowLegend() + "</div>" +
      "</div>";
    detailPane.querySelectorAll(".flow-dot").forEach(g => {
      g.style.cursor = "pointer";
      g.addEventListener("click", () => setFlowActive(parseInt(g.getAttribute("data-idx"), 10)));
    });
    resultList.querySelectorAll(".flow-pt").forEach(el => {
      el.addEventListener("click", () => setFlowActive(parseInt(el.getAttribute("data-idx"), 10)));
    });
  }
  function flowLegend() {
    return "<div class='flow-legend'>" +
      "<span><i class='sw' style='background:#c0392b'></i>穴位</span>" +
      "<span><i class='sw' style='background:#e67e22'></i>当前选中</span>" +
      "<span><i class='sw sw-flow'></i>流动路径</span></div>";
  }
  function setFlowActive(idx) {
    FLOW_ACTIVE = idx;
    detailPane.querySelectorAll(".flow-dot").forEach(g => {
      const i = parseInt(g.getAttribute("data-idx"), 10);
      g.classList.toggle("active", i === idx);
      const c = g.querySelector("circle");
      if (c) c.setAttribute("r", i === idx ? 9 : 6);
    });
    resultList.querySelectorAll(".flow-pt").forEach(el => {
      el.classList.toggle("cur", parseInt(el.getAttribute("data-idx"), 10) === idx);
    });
    const cur = resultList.querySelector(".flow-pt.cur");
    if (cur && cur.scrollIntoView) cur.scrollIntoView({ block: "nearest" });
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
      observeMobileList();
      if (BOARDS[0]) {
        selectBoard(BOARDS[0], true);
      }
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
