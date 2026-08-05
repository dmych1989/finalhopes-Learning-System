// -*- coding: utf-8 -*-
const state = { module: null, page: 1, size: 20, items: [], total: 0, herbCat: "", caseCat: "", articleCat: "", bzCat: "" };
const REF_TABLES = { bbxx: "BBXX", bzdz: "BZDZ", zfbz: "ZFBZ", zjdcjl: "ZJDCJL", hantang: "hantang" };
const ACU_TABLES = [
  { key: "lingui", name: "灵龟八法", tbl: "lingui" },
  { key: "najia", name: "纳甲法", tbl: "najia" },
  { key: "nazi", name: "纳子法", tbl: "nazi" },
];
// 子午流注各表列名 → 中文标头（源库列名 nazi_1…、naja_1…、time 均为英文/数字，需映射）
const ACU_COL_LABELS = {
  lingui: { time: "日干支" },                                  // 其余列本就是 子丑寅… 十二时辰，无需映射
  najia:  { time: "时辰", nazi_1: "当令经脉", nazi_2: "补母穴", nazi_3: "泻子穴", nazi_4: "本穴", nazi_5: "原穴" },
  nazi:   { time: "日干时辰", naja_1: "开穴一", naja_2: "开穴二", naja_3: "开穴三" },
};
function acuColLabel(tbl, col) {
  const m = ACU_COL_LABELS[tbl];
  return (m && m[col]) || col;
}

// Request sequence guard: only the latest navigation may render, so switching
// modules can never let a stale in-flight response blank or corrupt the list.
let loadSeq = 0;
let currentSearchQ = "";
let lastSearchData = null;
let yaotuQ = "", yaotuCat = "";
let casesCatsCache = null;                 // 医案证型分类（缓存）
let articleCatsCache = null;               // 论文栏目分类（缓存）
let bzCatsCache = null;                    // 病症研究病种目录（缓存）
let ARTICLE_TOTAL = 0;                     // 论文总数（全部）
let xueweiCatsCache = null, xueweiTotal = 0; // 穴位分类（含经络走向动画计数）
// 子系统（人纪 / 天纪）：子模块列表 / 当前子模块 / 当前子模块的元数据 / 子模块内搜索词
let subSubs = [], subKey = "", subMeta = null, subQ = "", subTotal = 0;

const $ = (s) => document.querySelector(s);

// 当前所属系统：lilun（医学论文医案查询系统）/ renji（人纪学习系统）/ tianji（天纪学习系统）。
// 三个系统是完全独立的不同页面，由各自 HTML 的 window.SYSTEM 决定，互不在对方侧栏出现。
const SYSTEM = window.SYSTEM || "lilun";

// 子系统配置：人纪 / 天纪 共用一套「左侧即子模块」渲染逻辑，仅 API 前缀 / 图片路由 /
// 表格端点 / 是否显示卦象(卦图) 不同。lilun 系统无此项（值为 undefined）。
const SYS_CFG = {
  renji: {
    api: "/api/renji", img: "/renji/img", modulesUrl: "/api/renji/modules",
    tablesUrl: "/api/renji/ziwwu", showDD: false,
  },
  tianji: {
    api: "/api/tianji", img: "/tianji/img", modulesUrl: "/api/tianji/modules",
    tablesUrl: "/api/tianji/tables", showDD: true,
  },
};
const sysCfg = SYS_CFG[SYSTEM];   // 仅 renji / tianji 有值

// fetch JSON with a hard timeout: if the server stalls (e.g. a stuck worker),
// the request is aborted so navigation/tab-switching can never freeze forever.
async function api(path, opts) {
  // 稳定性：对网络层错误（含超时中止 / 连接被拒）自动重试，吸收服务端偶发
  // 不可达（重启、瞬时连接闪断），避免一闪而过的故障让用户看到"加载失败"。
  const o = opts || {};
  const maxTries = o.retries != null ? o.retries : 2;
  const perTimeout = o.timeoutMs || 15000;
  let lastErr;
  for (let attempt = 0; attempt <= maxTries; attempt++) {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), perTimeout);
    try {
      const r = await fetch(path, { ...o, signal: ctrl.signal });
      if (!r.ok) throw new Error("HTTP " + r.status);
      return await r.json();
    } catch (e) {
      lastErr = e;
      clearTimeout(timer);
      // 仅网络层错误（中止 / 连接失败）可重试；HTTP 4xx/5xx 不重试
      const retryable = e.name === "AbortError" || e instanceof TypeError;
      if (!retryable || attempt === maxTries) throw e;
      await new Promise((res) => setTimeout(res, 400 * (attempt + 1)));
    } finally {
      clearTimeout(timer);
    }
  }
  throw lastErr;
}

function buildSidebar(modules) {
  const bar = $("#boardTabs");
  const side = $("#sidebar");
  if (bar) {
    // lilun：模块标签横向排在顶部（与 renji 顶栏一致）
    bar.innerHTML = "";
    modules.forEach((m) => {
      const d = document.createElement("div");
      d.className = "board-tab";
      d.innerHTML = `<span>${esc(m.name)}</span>`;
      m._el = d;
      d.onclick = () => selectModule(m, d);
      bar.appendChild(d);
    });
  } else if (side) {
    // tianji：模块列表保留在左侧，但 tool 类（排盘系统/命理系统）提升到顶部横向菜单
    side.innerHTML = "";
    modules.forEach((m) => {
      if (m.kind === "tool") return;   // 排盘/命理 移到顶部 #tjTools，左侧不再重复
      const d = document.createElement("div");
      d.className = "nav-item";
      d.innerHTML = `${esc(m.name)}<small>${esc(m.desc || "")}</small>`;
      m._el = d;
      d.onclick = () => selectModule(m, d);
      side.appendChild(d);
    });
    buildTianjiTools(modules);
  }
}

function setActive(el) {
  document.querySelectorAll(".board-tab, .nav-item, .tj-tool").forEach((n) => n.classList.remove("active"));
  if (el) el.classList.add("active");
}

// 天纪：把 tool 类模块（排盘系统/命理系统）渲染为顶部横向菜单
function buildTianjiTools(modules) {
  const box = document.getElementById("tjTools");
  if (!box) return;
  const tools = modules.filter((m) => m.kind === "tool");
  box.innerHTML = "";
  if (!tools.length) return;
  const label = document.createElement("span");
  label.className = "tj-tools-label";
  label.textContent = "工具";
  box.appendChild(label);
  tools.forEach((m) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "tj-tool" + (m.key === state.module ? " active" : "");
    b.textContent = m.name;
    m._toolEl = b;
    b.onclick = () => selectModule(m, b);
    box.appendChild(b);
  });
}

function setHead(m) {
  $("#moduleHead").innerHTML = `<div class="mh-left"><h2>${m.name}</h2><p>${m.desc}</p></div>`;
}

function clearFilterBar() {
  const fb = $("#filterBar");
  if (fb) { fb.innerHTML = ""; fb.style.display = "none"; }
}

// Render the switchable category tab bar at the top of the list pane.
function renderFilterBar(tabs, activeKey, onSelect) {
  const fb = $("#filterBar");
  if (!fb) return;
  fb.innerHTML = "";
  if (!tabs || !tabs.length) { fb.style.display = "none"; return; }
  fb.style.display = "flex";
  tabs.forEach((t) => {
    const b = document.createElement("button");
    b.className = "filter-tab" + (t.key === activeKey ? " active" : "");
    b.textContent = t.label + (t.count != null ? "（" + t.count + "）" : "");
    b.onclick = () => onSelect(t.key);
    fb.appendChild(b);
  });
}

// 中药查询：按神农本草经类别（上经/中经/下经/增补/其他）筛选。
function renderHerbTabs(cats) {
  const tabs = (cats || []).map((c) => ({ key: c.key, label: c.label, count: c.count }));
  tabs.unshift({ key: "", label: "全部" });
  renderFilterBar(tabs, state.herbCat || "", (key) => {
    state.herbCat = key; state.page = 1; loadList($("#search").value);
  });
}

function selectModule(m, el) {
  setActive(el);
  setHead(m);
  if (m.key !== "acu" && lgTimer) { clearInterval(lgTimer); lgTimer = null; }
  state.module = m.key;
  try { localStorage.setItem("nihai_active_module_" + SYSTEM, m.key); } catch (e) {}
  state.page = 1;
  state.herbCat = "";
  state.caseCat = "";
  state.articleCat = "";
  state.bzCat = "";
  const catNav = $("#casesCatNav");
  if (catNav) catNav.style.display = "none";
  const artNav = $("#articleCatNav");
  if (artNav) artNav.style.display = "none";
  $("#detailPane").innerHTML = '<div class="hint">点击左侧条目查看详情。</div>';
  // 子系统（人纪 / 天纪）：左侧模块即各子模块，选中后直接加载该子模块列表。
  // 注：herbs / yaotu / xuewei 三项原属主系统、现已并入人纪，但复用主系统接口
  // 与渲染逻辑，故在 renji 模式下也走下方主系统分支（跨系统调用 /api/herbs 等）。
  if (sysCfg && m.key !== "herbs" && m.key !== "yaotu" && m.key !== "xuewei") {
    subKey = m.key;
    clearFilterBar();
    subQ = "";
    loadSubList();
    return;
  }
  if (m.key === "acu") {
    let tbl = "lingui";
    try { tbl = localStorage.getItem("nihai_acu_table") || "lingui"; } catch (e) {}
    renderAcu(tbl);
    return;
  }
  if (m.key === "yaotu") { loadYaotu("", "", 1); return; }
  if (m.key === "xuewei") { loadXuewei("", "", 1); return; }
  loadList("");
}

function endpointFor(q) {
  const k = state.module;
  if (k === "cases") return `/api/cases?cat=${enc(state.caseCat || "")}&q=${enc(q)}&page=${state.page}&size=${state.size}`;
  if (k === "herbs") return `/api/herbs?q=${enc(q)}&cat=${enc(state.herbCat)}&page=${state.page}&size=${state.size}`;
  if (k === "articles") return `/api/articles?cat=${enc(state.articleCat || "")}&q=${enc(q)}&page=${state.page}&size=${state.size}`;
  if (k === "hdwj") return `/api/hdwj?q=${enc(q)}&page=${state.page}&size=${state.size}`;
  if (k === "bz") return `/api/bz?cat=${enc(state.bzCat || "")}&q=${enc(q)}&page=${state.page}&size=${state.size}`;
  if (REF_TABLES[k]) return `/api/ref/${REF_TABLES[k]}?q=${enc(q)}&page=${state.page}&size=${state.size}`;
  return null;
}
const enc = (s) => encodeURIComponent(s || "");

async function loadList(q) {
  const ep = endpointFor(q);
  if (!ep) return;
  const my = ++loadSeq;
  if (state.module === "cases" && !casesCatsCache) {
    try { casesCatsCache = await api("/api/cases/cats"); } catch (e) { casesCatsCache = { cats: [] }; }
  }
  if (state.module === "articles" && !articleCatsCache) {
    try { articleCatsCache = await api("/api/articles/cats"); } catch (e) { articleCatsCache = { cats: [] }; }
  }
  if (state.module === "bz" && !bzCatsCache) {
    try { bzCatsCache = await api("/api/bz/cats"); } catch (e) { bzCatsCache = { cats: [] }; }
  }
  clearFilterBar();
  let data;
  try {
    data = await api(ep);
  } catch (e) {
    if (my !== loadSeq) return;
    const ul = $("#resultList");
    if (ul) ul.innerHTML = "";
    const hint = $("#listHint");
    if (hint) { hint.style.display = "block"; hint.textContent = "加载失败，请重试。"; }
    return;
  }
  if (my !== loadSeq) return; // a newer navigation superseded this request
  state.items = data.items; state.total = data.total;
  if (state.module === "articles") ARTICLE_TOTAL = data.total;
  renderList();
  renderPager();
  if (state.module === "cases" && casesCatsCache) {
    renderCasesCatNav(casesCatsCache.cats, state.caseCat || "all");
  } else if (state.module === "articles" && articleCatsCache) {
    renderArticleCatNav(articleCatsCache.cats, state.articleCat || "");
  } else if (state.module === "bz" && bzCatsCache) {
    renderBzCatNav(bzCatsCache.cats, state.bzCat || "");
  } else if (state.module === "herbs" && data.cats) {
    renderHerbTabs(data.cats);
  }
}

// 医案「按证型浏览」左侧分类侧栏
function renderCasesCatNav(cats, activeKey) {
  const nav = $("#casesCatNav");
  if (!nav) return;
  nav.style.display = "block";
  nav.innerHTML = "";
  const title = document.createElement("div");
  title.className = "catnav-title";
  title.textContent = "按证型浏览";
  nav.appendChild(title);
  (cats || []).forEach((c) => {
    const b = document.createElement("button");
    b.className = "catnav-item" + (c.key === activeKey ? " active" : "");
    b.innerHTML = `<span class="cn-label">${esc(c.label)}</span><em class="cn-count">${c.count}</em>`;
    b.onclick = () => { state.caseCat = c.key; state.page = 1; loadList($("#search").value); };
    nav.appendChild(b);
  });
}

// 论文「栏目」左侧分类侧栏（13 个栏目，近似归类）
function renderArticleCatNav(cats, activeKey) {
  const nav = $("#articleCatNav");
  if (!nav) return;
  nav.style.display = "block";
  nav.innerHTML = "";
  const title = document.createElement("div");
  title.className = "catnav-title";
  title.textContent = "论文栏目";
  nav.appendChild(title);
  const all = document.createElement("button");
  all.className = "catnav-item" + (activeKey === "" ? " active" : "");
  all.innerHTML = `<span class="cn-label">全部论文</span><em class="cn-count">${ARTICLE_TOTAL || ""}</em>`;
  all.onclick = () => { state.articleCat = ""; state.page = 1; loadList($("#search").value); };
  nav.appendChild(all);
  (cats || []).forEach((c) => {
    const b = document.createElement("button");
    b.className = "catnav-item" + (c.key === activeKey ? " active" : "");
    b.innerHTML = `<span class="cn-label">${esc(c.name)}</span><em class="cn-count">${c.count}</em>`;
    b.onclick = () => { state.articleCat = c.key; state.page = 1; loadList($("#search").value); };
    nav.appendChild(b);
  });
}

// 病症研究「按疾病专论浏览」左侧目录侧栏（22 个病种），复用论文栏目的 #articleCatNav 容器。
function renderBzCatNav(cats, activeKey) {
  const nav = $("#articleCatNav");
  if (!nav) return;
  nav.style.display = "block";
  nav.innerHTML = "";
  const title = document.createElement("div");
  title.className = "catnav-title";
  title.textContent = "病症分类";
  nav.appendChild(title);
  const all = document.createElement("button");
  all.className = "catnav-item" + (activeKey === "" ? " active" : "");
  all.innerHTML = `<span class="cn-label">全部病症</span>`;
  all.onclick = () => { state.bzCat = ""; state.page = 1; loadList($("#search").value); };
  nav.appendChild(all);
  (cats || []).forEach((c) => {
    const b = document.createElement("button");
    b.className = "catnav-item" + (c.key === activeKey ? " active" : "");
    b.innerHTML = `<span class="cn-label">${esc(c.name)}</span><em class="cn-count">${c.count}</em>`;
    b.onclick = () => { state.bzCat = c.key; state.page = 1; loadList($("#search").value); };
    nav.appendChild(b);
  });
}

// Pick a sensible title / subtitle for a record, regardless of which columns
// the table actually has (e.g. hantang uses ID/zygn, others use MZ/NR).
function refTitleSub(rec) {
  let title = "", sub = "";
  // 汉唐方剂（补全后带 _name）：标题显示「编号 · 方名」
  if (rec._name) title = (rec.ID || "") + " · " + rec._name;
  else if (rec.MZ != null) title = rec.MZ;
  else if (rec.ID != null) title = rec.ID;
  else title = rec.XM || "";
  if (rec.NR != null) sub = rec.NR;
  else if (rec.zygn != null) sub = rec.zygn;
  else if (rec._obs && rec._obs.body) sub = rec._obs.body.slice(0, 80);
  return [title, sub];
}

// Unified title/subtitle for a list item, by module.
function itemTitleSub(k, rec) {
  if (k === "cases") return [rec._title || rec.MZ || "(无名)", ""];
  if (k === "herbs") return [rec.MZ || "", rec["【功效】"] || rec["【古籍摘要】"] || rec["【简述】"] || ""];
  if (k === "articles") return [rec.MZ || "(无标题)", ""];
  // 黄帝外经：左侧列表只显示篇名（不显示正文摘要），篇次序号由列表渲染单独加。
  if (k === "hdwj") return [rec.MZ || "(无标题)", ""];
  if (k === "bz") return [rec.MZ || "(无标题)", (rec.NR || "").slice(0, 80)];
  if (k === "yaotu") return [rec.name, ""];
  if (k === "xuewei") return [rec.name, [rec.cat_name, rec.sub].filter(Boolean).join(" · ")];
  return refTitleSub(rec);
}

function renderList() {
  const ul = $("#resultList");
  if (!ul) return;
  ul.className = "result-list";
  ul.innerHTML = "";
  if (!state.items.length) {
    const hint = $("#listHint");
    hint.style.display = "block";
    hint.textContent = "没有匹配结果。";
    return;
  }
  $("#listHint").style.display = "none";
  const k = state.module;
  state.items.forEach((rec) => {
    const li = document.createElement("li");
    li.className = "result-item";
    const [title, sub] = itemTitleSub(k, rec);
    // 序号徽标：中药用 _seq，《外经微言》用 _idx（原书第 N 篇）。
    const seqNum = (rec._idx != null) ? rec._idx : (rec._seq != null ? rec._seq : null);
    const seqBadge = (seqNum != null)
      ? `<span class="seq-badge">${seqNum}</span>` : "";
    const subHtml = sub ? `<div class="s">${esc(sub)}</div>` : "";
    li.innerHTML = `<div class="t">${seqBadge}${esc(title)}</div>${subHtml}`;
    li.onclick = () => showDetail(k, rec);
    ul.appendChild(li);
  });
}

function renderPager() {
  const p = $("#pager");
  if (!p) return;
  p.innerHTML = "";
  const totalPages = Math.max(1, Math.ceil(state.total / state.size));
  const mk = (label, page, dis) => {
    const b = document.createElement("button");
    b.textContent = label; b.disabled = dis;
    b.onclick = () => { state.page = page; loadList($("#search").value); };
    return b;
  };
  p.appendChild(mk("上一页", state.page - 1, state.page <= 1));
  const info = document.createElement("span");
  info.style.cssText = "align-self:center;font-size:13px;color:#5b5246";
  info.textContent = `第 ${state.page} / ${totalPages} 页（共 ${state.total} 条）`;
  p.appendChild(info);
  p.appendChild(mk("下一页", state.page + 1, state.page >= totalPages));
}

function showDetail(k, rec) {
  if (k === "cases") return showCase(rec);
  if (k === "herbs") return showHerb(rec);
  if (k === "articles") return showArticle(rec);
  if (k === "hdwj") return showArticle(rec);
  if (k === "bz") return showArticle(rec);
  if (k === "hantang") return showHantang(rec);
  return showGeneric(rec, k);
}

// Used by global search results, where each item already knows its module.
function showUniversal(module, rec) {
  if (module === "ref" && rec._table) module = rec._table.toLowerCase(); // 搜索结果里的参考表
  if (module === "cases") return showCase(rec);
  if (module === "herbs") return showHerb(rec);
  if (module === "articles") return showArticle(rec);
  if (module === "yaotu") return showYaotuDetail(rec);
  if (module === "xuewei") return showXueweiDetail(rec);
  if (module === "hantang") return showHantang(rec);
  return showGeneric(rec, module);
}

const ORDER_CASES = ["MZ", "【姓名】", "【性别】", "【年龄及体型】", "【来诊日期】",
  "【来诊原因】", "【问诊】", "【脉诊】", "【望诊】", "【诊断】", "【中药处方】",
  "【解说】", "【备注】", "【针灸处方】"];

function fieldRow(k, v) {
  if (v === "" || v == null) return "";
  return `<div class="field"><span class="k">${esc(k)}</span><span class="v">${esc(v)}</span></div>`;
}

function showCase(rec) {
  let h = `<div class="detail-card"><h3>${esc(rec._title || rec.MZ || "(无名)")}</h3>`;
  ORDER_CASES.slice(1).forEach((k) => { h += fieldRow(k, rec[k]); });
  h += `</div>`;
  $("#detailPane").innerHTML = h;
}

function showHerb(rec) {
  let img = rec._image
    ? `<img class="herb-img" src="/api/herb_image/${enc(rec._image)}" alt="${esc(rec.MZ)}" onerror="this.style.display='none'">`
    : "";
  let badge = rec._shennong ? `<span class="shennong-badge">神农本草经 · 补全</span>` : "";
  let seqLine = rec._seq != null
    ? `<div class="seq-line">《神农本草经》· ${esc(rec._cat)} · 本经第 ${rec._cat_seq} 味（全书总第 ${rec._seq} 味）</div>`
    : "";
  let h = `<div class="detail-card">${img}<h3>${esc(rec.MZ || "")} ${badge}</h3>${seqLine}`;
  ["【出自】", "【简述】", "【性能】", "【功效】", "【用法用量】", "【使用注意】",
   "【古籍摘要】", "【现代研究】"].forEach((k) => { h += fieldRow(k, rec[k]); });
  if (rec._shennong && rec.note) {
    h += `<div class="article-body" style="margin-top:12px"><div class="field"><span class="k">倪师注解</span></div>${esc(rec.note)}</div>`;
  }
  h += `</div>`;
  $("#detailPane").innerHTML = h;
}

// 汉唐方剂：源数据仅含「编号 + 主治(zygn) + 规格/价格编码(XB/XM)」。
// 已按编号合并「倪师100方剂」Obsidian 笔记（_obs：名称/组成/用法/注意/全文）。
// 渲染时突出主治与倪师解说，补全字段置顶高亮，规格置底。
function showHantang(rec) {
  const id = rec.ID || "";
  const name = rec._name || "";
  const zygn = (rec.zygn || "").trim();
  const spec = (rec.XB || rec.XM || "").trim();
  const obs = rec._obs || {};
  const badge = rec._extra
    ? `<span class="shennong-badge">倪师100方剂 · 补全</span>`
    : `<span class="shennong-badge">汉唐方剂</span>`;
  let h = `<div class="detail-card"><h3>${esc(id)}${name ? " · " + esc(name) : ""} ${badge}</h3>`;
  if (zygn) h += `<div class="field"><span class="k">源库主治</span><span class="v">${esc(zygn)}</span></div>`;
  if (obs.composition) h += `<div class="field"><span class="k">组成</span><span class="v">${esc(obs.composition)}</span></div>`;
  if (obs.usage) h += `<div class="field"><span class="k">用法</span><span class="v">${esc(obs.usage)}</span></div>`;
  if (obs.caution) h += `<div class="field"><span class="k">注意</span><span class="v">${esc(obs.caution)}</span></div>`;
  if (obs.body) {
    h += `<div class="article-body" style="margin-top:10px"><div class="field"><span class="k">倪师解说</span></div>${esc(obs.body)}</div>`;
  }
  if (spec) h += `<div class="field"><span class="k">规格</span><span class="v">${esc(spec)}</span></div>`;
  if (!zygn && !obs.body && !spec) h += `<div class="hint">本条源数据为空（原库未录入内容）。</div>`;
  h += `</div>`;
  $("#detailPane").innerHTML = h;
}

function showArticle(rec) {
  let body = rec.NR || "";
  const title = (rec.MZ || "").trim();
  // The article body usually repeats the title as its first line; drop it.
  if (title && body.startsWith(title)) {
    body = body.slice(title.length).replace(/^\s*[\r\n]+/, "");
  }
  // 《外经微言》标注原书篇次（第 N 篇），其余文章无 _idx 则不加。
  const idxTag = (rec._idx != null) ? `<span class="seq-badge">第 ${rec._idx} 篇</span> ` : "";
  let h = `<div class="detail-card"><h3>${idxTag}${esc(rec.MZ || "(无标题)")}</h3>`;
  h += `<div class="article-body">${esc(body)}</div>`;
  h += `</div>`;
  $("#detailPane").innerHTML = h;
}

// 参考类表（辨证论治/正副辨证/针灸记录等）字段的中文标签。
// 源库列名本身就是 No1 / NR / NR1 / NR2，需转成可读小标题，并隐藏纯序号 No1。
const FIELD_LABELS = {
  bbxx:   { NR: "对应方剂 / 处方" },
  bzdz:   { NR: "针灸处方 / 治法" },
  zfbz:   { NR1: "辨证要点", NR2: "取穴治法" },
  zjdcjl: { NR1: "临床表现", NR2: "取穴治法" },
};

function showGeneric(rec, module) {
  const labels = FIELD_LABELS[module] || {};
  let h = `<div class="detail-card"><h3>${esc(rec.MZ || rec.ID || rec.XM || "")}</h3>`;
  Object.keys(rec).forEach((k) => {
    if (k.startsWith("_")) return;
    if (k === "MZ" || k === "ID" || k === "XM") return; // 已用作标题
    if (k === "No1") return;                              // 纯序号，非内容
    const v = rec[k];
    if (v === "" || v == null) return;
    // 源库列名是 No1/NR/NR1/NR2 这类编码，按内容写成可读的中文小节标题。
    const lbl = labels[k] || k;
    h += `<div class="sec-h">${esc(lbl)}</div><div class="sec-b">${esc(v)}</div>`;
  });
  h += `</div>`;
  $("#detailPane").innerHTML = h;
}

function showYaotuDetail(rec) {
  const imgSrc = rec._folder ? `/extimg?p=${enc(rec._rel)}` : `/api/herb_image/${enc(rec.name)}`;
  const badge = rec.cat_label ? `<span class="shennong-badge">${esc(rec.cat_label)}</span>` : "";
  $("#detailPane").innerHTML =
    `<div class="detail-card"><h3>${esc(rec.name)} ${badge}</h3>` +
    `<img class="herb-img" style="float:none;max-width:100%;max-height:72vh" ` +
    `src="${imgSrc}" alt="${esc(rec.name)}" onerror="this.style.display='none'"></div>`;
}

// ---- 穴位查询 (xuewei)：按经络分类的穴位图文（来自《中医》仓库） ----
let xueweiQ = "", xueweiCat = "";
async function loadXuewei(cat, q, page) {
  page = page || 1;
  xueweiQ = q || ""; xueweiCat = cat || "";
  // 「经络走向动画」为独立可视化视图，不走穴位列表
  if (xueweiCat === "jingluo") { renderJingluoAnim(); return; }
  const my = ++loadSeq;
  const data = await api(`/api/xuewei?cat=${enc(xueweiCat)}&q=${enc(xueweiQ)}&page=${page}&size=60`);
  if (my !== loadSeq) return;
  xueweiCatsCache = data.cats || [];
  xueweiTotal = data.total;
  const ul = $("#resultList");
  if (ul) { ul.className = "result-list"; ul.innerHTML = ""; }
  const hint = $("#listHint");
  hint.style.display = "block";
  hint.textContent = "点击左侧穴位查看定位 / 主治 / 针刺方法与配图；上方可按经络筛选。";
  const cats = (data.cats || []);
  const tabs = [{ key: "jingluo", label: "经络走向动画" }]
    .concat([{ key: "", label: "全部经络", count: data.total }])
    .concat(cats.map((c) => ({ key: c.key, label: c.label + (c.count ? ` (${c.count})` : "") })));
  renderFilterBar(tabs, xueweiCat, (k) => loadXuewei(k, xueweiQ, 1));
  data.items.forEach((r) => {
    const li = document.createElement("li");
    li.className = "result-item";
    const sub = [r.cat_name, r.sub].filter(Boolean).join(" · ");
    li.innerHTML = `<div class="t">${esc(r.name)}</div><div class="s">${esc(sub)}</div>`;
    li.onclick = () => showXueweiDetail(r);
    ul.appendChild(li);
  });
  renderXueweiPager(data);
  showXueweiBanner(data, xueweiCat);
}

// ---- 经络走向动画：十二正经 + 任督二脉 循行示意（流光 + 行针小球） ----
// 经络 key 与 extra_index.py 的 MERIDIANS 一致，便于跳转「查看本经穴位」。
const JINGLUO = [
  // 手三阴：从胸走手（右手内侧）
  { key: "fei", name: "手太阴肺经", type: "yin", time: "寅时 3-5点", flow: "从胸走手", d: "M216,150 C232,180 250,210 262,240 S286,310 298,360" },
  { key: "bao", name: "手厥阴心包经", type: "yin", time: "戌时 19-21点", flow: "从胸走手", d: "M220,180 C236,210 252,240 264,268 S288,318 294,360" },
  { key: "xin", name: "手少阴心经", type: "yin", time: "午时 11-13点", flow: "从胸走手", d: "M224,205 C240,235 254,262 266,290 S286,322 290,362" },
  // 手三阳：从手走头（右手外侧）
  { key: "chang", name: "手阳明大肠经", type: "yang", time: "卯时 5-7点", flow: "从手走头", d: "M300,360 C292,312 280,252 266,212 S246,150 232,118 C226,100 224,86 222,74" },
  { key: "jiao", name: "手少阳三焦经", type: "yang", time: "亥时 21-23点", flow: "从手走头", d: "M296,362 C290,316 278,258 264,218 S244,156 230,120 C224,102 222,88 220,76" },
  { key: "xiao", name: "手太阳小肠经", type: "yang", time: "未时 13-15点", flow: "从手走头", d: "M292,364 C286,320 274,264 260,224 S240,162 226,122 C220,104 218,90 216,78" },
  // 足三阳：从头走足
  { key: "wei", name: "足阳明胃经", type: "yang", time: "辰时 7-9点", flow: "从头走足", d: "M222,74 C226,120 232,200 236,300 C240,400 244,500 248,632" },
  { key: "dan", name: "足少阳胆经", type: "yang", time: "子时 23-1点", flow: "从头走足", d: "M220,76 C236,140 256,220 262,300 C268,400 262,500 258,632" },
  { key: "pang", name: "足太阳膀胱经", type: "yang", time: "申时 15-17点", flow: "从头走足", d: "M218,78 C206,150 202,240 204,320 C208,420 212,510 216,632" },
  // 足三阴：从足走胸/腹
  { key: "pi", name: "足太阴脾经", type: "yin", time: "巳时 9-11点", flow: "从足走胸", d: "M246,632 C244,560 242,470 240,380 C238,320 230,270 222,230 C218,205 216,190 214,178" },
  { key: "gan", name: "足厥阴肝经", type: "yin", time: "丑时 1-3点", flow: "从足走腹", d: "M250,632 C252,560 252,470 250,380 C248,330 238,310 224,300" },
  { key: "shen", name: "足少阴肾经", type: "yin", time: "酉时 17-19点", flow: "从足走胸", d: "M254,632 C254,560 252,470 250,380 C246,320 232,270 220,235 C214,212 212,200 210,188" },
  // 任督二脉：皆自下而上
  { key: "ren", name: "任脉（前正中）", type: "ren", time: "—", flow: "从下（会阴）走上（承浆）", d: "M196,392 C196,300 196,200 196,110" },
  { key: "du", name: "督脉（后正中）", type: "du", time: "—", flow: "从下（长强）走上（龈交）", d: "M204,396 C204,300 204,200 204,104" },
];

const JL_BODY = `<g class="jl-body">`+
  `<circle cx="200" cy="56" r="30"/>`+
  `<path d="M172,92 Q200,84 228,92 L236,300 Q200,322 164,300 Z"/>`+
  `<path class="jl-limb" d="M182,108 C158,180 142,260 132,352"/>`+
  `<path class="jl-limb" d="M218,108 C242,180 258,260 268,352"/>`+
  `<path class="jl-limb" d="M180,300 C174,470 170,560 168,632"/>`+
  `<path class="jl-limb" d="M220,300 C226,470 230,560 232,632"/>`+
  `</g>`;

// 经络 key → 仓库里真实动画 GIF 文件名（原版「经络走向动画」本体，640×960 逐帧动画）
const JL_GIF = { fei: "肺经", bao: "心包经", xin: "心经", chang: "大肠经", jiao: "三焦经", xiao: "小肠经",
  wei: "胃经", dan: "胆经", pang: "膀胱经", pi: "脾经", gan: "肝经", shen: "肾经", ren: "任脉", du: "督脉" };
let jlIndex = 0;

function jlGifUrl(m) {
  const c = (xueweiCatsCache || []).find((x) => x.key === m.key);
  const rel = (c && c.diagram) ? c.diagram : `穴位/${JL_GIF[m.key] || m.name}.gif`;
  return `/extimg?p=${enc(rel)}`;
}

function renderJingluoAnim() {
  const dp = $("#detailPane"); if (!dp) return;
  const ul = $("#resultList"); if (ul) ul.innerHTML = "";
  const hint = $("#listHint");
  if (hint) { hint.style.display = "block"; hint.textContent = "点击左侧经络名称播放其走向动画；「查看本经穴位」跳转到穴位列表。"; }

  const tabs = [{ key: "jingluo", label: "经络走向动画" }]
    .concat([{ key: "", label: "全部经络", count: xueweiTotal }])
    .concat((xueweiCatsCache || []).map((c) => ({ key: c.key, label: c.label + (c.count ? ` (${c.count})` : "") })));
  renderFilterBar(tabs, "jingluo", (k) => loadXuewei(k, xueweiQ, 1));

  // 14 条经络 → 左侧「穴位查询 / 经络走向动画」列表（切换图片标签）
  const listHtml = JINGLUO.map((m, i) => {
    const c = (xueweiCatsCache || []).find((x) => x.key === m.key);
    const cnt = c ? c.count : 0;
    return `<li class="jl-item mer-${m.type}" data-i="${i}">` +
      `<span class="jl-dot mer-${m.type}"></span>` +
      `<span class="jl-name">${m.name}</span>` +
      `<span class="jl-meta">${m.time} · ${m.flow}</span>` +
      `<span class="jl-cnt">${cnt} 穴</span>` +
      `</li>`;
  }).join("");

  if (ul) {
    ul.className = "result-list jl-result-list";
    ul.innerHTML =
      `<li class="jl-switch"><button id="jlPrev" class="jl-navbtn">‹ 上一条</button>` +
      `<span class="jl-switch-tip">切换经络</span>` +
      `<button id="jlNext" class="jl-navbtn">下一条 ›</button></li>` +
      listHtml;
  }

  dp.innerHTML = `<div class="detail-card jl-card">` +
    `<div class="jl-top"><h3>十二经络 · 穴位走向动画</h3></div>` +
    `<p class="jl-desc">原版即以人体图为底，逐帧描绘每条经脉的循行线路与经气运行方向（手三阴从胸走手、手三阳从手走头、足三阳从头走足、足三阴从足走胸；任督自下而上）。点击左侧经络即可在上方播放对应动画。</p>` +
    `<div class="jl-gifwrap"><img class="jl-gif" id="jlGif" alt="经络走向动画"></div>` +
    `<div class="jl-info" id="jlInfo"></div>` +
    `</div>`;

  if (ul) {
    ul.querySelectorAll(".jl-item").forEach((li) => {
      li.onclick = () => selectJingluo(parseInt(li.dataset.i, 10));
    });
    const prev = ul.querySelector("#jlPrev");
    const next = ul.querySelector("#jlNext");
    if (prev) prev.onclick = () => selectJingluo((jlIndex - 1 + JINGLUO.length) % JINGLUO.length);
    if (next) next.onclick = () => selectJingluo((jlIndex + 1) % JINGLUO.length);
  }

  selectJingluo(jlIndex || 0);
}

function selectJingluo(i) {
  jlIndex = i;
  const dp = $("#detailPane"); if (!dp) return;
  const m = JINGLUO[i];
  document.querySelectorAll(".jl-item").forEach((x) => x.classList.toggle("active", parseInt(x.dataset.i, 10) === i));
  const gif = dp.querySelector("#jlGif");
  if (gif) { gif.src = jlGifUrl(m) + "&_=" + Date.now(); gif.alt = m.name + " 走向动画"; }
  const c = (xueweiCatsCache || []).find((x) => x.key === m.key);
  const cnt = c ? c.count : 0;
  const plain = m.name.replace(/（.*?）/g, "");
  const info = dp.querySelector("#jlInfo");
  if (info) {
    info.innerHTML = `<div class="jl-det-name"><span class="jl-dot mer-${m.type}"></span>${m.name}</div>` +
      `<div class="jl-det-row"><b>时辰</b>　${m.time}</div>` +
      `<div class="jl-det-row"><b>循行走向</b>　${m.flow}</div>` +
      `<div class="jl-det-row"><b>本经穴位</b>　${cnt} 个</div>` +
      (cnt ? `<button class="jl-gobtn" onclick="loadXuewei('${m.key}','',1)">查看本经「${plain}」穴位 →</button>` : "");
  }
}

function formatXueweiContent(text) {
  const lines = (text || "").split(/\r?\n/);
  let html = "", buf = [];
  const flush = () => {
    if (buf.length) {
      html += `<div class="xw-body">${esc(buf.join("\n")).replace(/\n/g, "<br>")}</div>`;
      buf = [];
    }
  };
  for (const ln of lines) {
    const m = ln.match(/^\s*\[([^\]]+)\]\s*$/);
    if (m) { flush(); html += `<div class="xw-sec">${esc(m[1])}</div>`; }
    else if (ln.trim() === "") { flush(); }
    else buf.push(ln);
  }
  flush();
  return html || `<div class="hint">（暂无文字说明）</div>`;
}

function showXueweiDetail(rec) {
  const badge = rec.cat_name ? `<span class="shennong-badge">${esc(rec.cat_name)}</span>` : "";
  const sub = rec.sub ? `<span class="xw-sub">${esc(rec.sub)}</span>` : "";
  const imgs = (rec.images && rec.images.length)
    ? `<div class="xw-imgs">` + rec.images.map((rel) =>
        `<a class="xw-img" href="/extimg?p=${enc(rel)}" target="_blank">` +
        `<img src="/extimg?p=${enc(rel)}" alt="${esc(rec.name)}" loading="lazy" onerror="this.style.display='none'"></a>`
      ).join("") + `</div>`
    : "";
  const body = formatXueweiContent(rec.content);
  $("#detailPane").innerHTML =
    `<div class="detail-card"><h3>${esc(rec.name)} ${badge} ${sub}</h3>${body}${imgs}</div>`;
}

function showXueweiBanner(data, catKey) {
  const dp = $("#detailPane"); if (!dp) return;
  const cat = (data.cats || []).find((c) => c.key === catKey);
  if (catKey && cat) {
    if (cat.diagram) {
      dp.innerHTML =
        `<div class="detail-card xw-banner">` +
        `<h3>${esc(cat.label)} · 经络示意图</h3>` +
        `<img class="xw-diagram" src="/extimg?p=${enc(cat.diagram)}" alt="${esc(cat.label)}" onerror="this.style.display='none'">` +
        `<div class="hint">本经共 ${cat.count} 个穴位，点击左侧列表查看每个穴位的定位、主治与配图。</div>` +
        `</div>`;
    } else {
      dp.innerHTML =
        `<div class="detail-card"><h3>${esc(cat.label)}</h3>` +
        `<div class="hint">本类共 ${cat.count} 条，点击左侧列表查看详情。</div></div>`;
    }
  } else {
    dp.innerHTML =
      `<div class="detail-card"><h3>穴位查询</h3>` +
      `<div class="hint">按经络分类的穴位图文资料。先在上方选择一条经络，再点击左侧穴位查看定位、主治、针刺方法与配图；图谱类（腹针 / 全息 / 经络总图）以图片为主。</div></div>`;
  }
}

function renderXueweiPager(data) {
  const p = $("#pager");
  if (!p) return;
  p.innerHTML = "";
  const totalPages = Math.max(1, Math.ceil(data.total / data.size));
  const mk = (label, page, dis) => {
    const b = document.createElement("button");
    b.textContent = label; b.disabled = dis;
    b.onclick = () => loadXuewei(xueweiCat, xueweiQ, page);
    return b;
  };
  p.appendChild(mk("上一页", data.page - 1, data.page <= 1));
  const info = document.createElement("span");
  info.style.cssText = "align-self:center;font-size:13px;color:#5b5246";
  info.textContent = `第 ${data.page} / ${totalPages} 页（共 ${data.total} 条）`;
  p.appendChild(info);
  p.appendChild(mk("下一页", data.page + 1, data.page >= totalPages));
}

// ---- 灵龟八法 实时开穴（依据 finalhopes.com/tortoise 权威算法 +《针灸大成》八法歌） ----
const LG_GAN = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"];
const LG_ZHI = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"];
const LG_DAY_GAN  = {"甲":10,"己":10,"乙":9,"庚":9,"丁":8,"壬":8,"戊":7,"癸":7,"丙":7,"辛":7};
const LG_DAY_ZHI  = {"辰":10,"戌":10,"丑":10,"未":10,"申":9,"酉":9,"寅":8,"卯":8,"子":7,"巳":7,"午":7,"亥":7};
const LG_HOUR_GAN = {"甲":9,"己":9,"乙":8,"庚":8,"丙":7,"辛":7,"丁":6,"壬":6,"戊":5,"癸":5};
const LG_HOUR_ZHI = {"子":9,"午":9,"丑":8,"未":8,"寅":7,"申":7,"卯":6,"酉":6,"辰":5,"戌":5,"巳":4,"亥":4};
const LG_REM2ACU  = {1:"申脉",2:"照海",3:"外关",4:"足临泣",5:"照海",6:"公孙",7:"后溪",8:"内关",9:"列缺"};
// 八穴：八卦 / 九宫 / 通脉 / 定位 / 主治 / 配穴 / 下针顺序 / 共治（据 finalhopes 与八法歌）
const LG_ACU = {
  "申脉":  {gua:"坎", gong:1, mai:"阳跷脉", desc:"足太阳膀胱经穴，通阳跷脉，位于足外侧，外踝直下方凹陷中", treat:"头痛、眩晕、腰腿痛、失眠、癫痫", pair:"后溪", order:"先针申脉，后针后溪", scope:"目内眦、颈项、耳、肩膊、小肠、膀胱"},
  "照海":  {gua:"坤", gong:2, mai:"阴跷脉", desc:"足少阴肾经穴，通阴跷脉，位于足内侧，内踝尖下方凹陷处", treat:"咽喉肿痛、失眠、月经不调、小便频数", pair:"列缺", order:"先针照海，后针列缺", scope:"肺系、咽喉、胸膈"},
  "外关":  {gua:"震", gong:3, mai:"阳维脉", desc:"手少阳三焦经穴，通阳维脉，位于前臂背侧，腕背横纹上2寸，尺骨与桡骨之间", treat:"头痛、耳鸣、目痛、上肢痹痛、热病", pair:"足临泣", order:"先针外关，后针足临泣", scope:"目锐眦、耳后、颈项、肩"},
  "足临泣":{gua:"巽", gong:4, mai:"带脉",   desc:"足少阳胆经穴，通带脉，位于足背外侧，第四跖骨间隙后方凹陷处", treat:"头痛、目赤、目痛、足跗肿痛、月经不调", pair:"外关", order:"先针足临泣，后针外关", scope:"目锐眦、耳后、颈项、肩"},
  "公孙":  {gua:"乾", gong:6, mai:"冲脉",   desc:"足太阴脾经穴，通冲脉，位于足内侧缘，第一跖骨基底部前下方", treat:"胃痛、呕吐、腹痛、泄泻、月经不调", pair:"内关", order:"先针公孙，后针内关", scope:"心、胃、胸"},
  "后溪":  {gua:"兑", gong:7, mai:"督脉",   desc:"手太阳小肠经穴，通督脉，位于手尺侧，微握拳，第五掌指关节后远侧掌横纹头赤白肉际", treat:"头痛、项强、腰背痛、手指挛痛", pair:"申脉", order:"先针后溪，后针申脉", scope:"目内眦、颈项、耳、肩膊、小肠、膀胱"},
  "内关":  {gua:"艮", gong:8, mai:"阴维脉", desc:"手厥阴心包经穴，通阴维脉，位于前臂掌侧，腕横纹上2寸，掌长肌腱与桡侧腕屈肌腱之间", treat:"心痛、心悸、胃痛、呕吐、失眠", pair:"公孙", order:"先针内关，后针公孙", scope:"心、胃、胸"},
  "列缺":  {gua:"离", gong:9, mai:"任脉",   desc:"手太阴肺经穴，通任脉，位于前臂桡侧缘，桡骨茎突上方，腕横纹上1.5寸", treat:"头痛、咳嗽、气喘、咽喉肿痛", pair:"照海", order:"先针列缺，后针照海", scope:"肺系、咽喉、胸膈"}
};
const LG_HOUR_DESC = {'子':'23:00-1:00','丑':'1:00-3:00','寅':'3:00-5:00','卯':'5:00-7:00','辰':'7:00-9:00','巳':'9:00-11:00','午':'11:00-13:00','未':'13:00-15:00','申':'15:00-17:00','酉':'17:00-19:00','戌':'19:00-21:00','亥':'21:00-23:00'};

function lgJDN(y,m,d){ if(m<=2){y-=1;m+=12;} const A=Math.floor(y/100); const B=2-A+Math.floor(A/4); return Math.floor(365.25*(y+4716))+Math.floor(30.6001*(m+1))+d+B-1524; }
function lgDayGZ(y,m,d){ const j=lgJDN(y,m,d); const idx=((j+49)%60+60)%60; return {gan:LG_GAN[idx%10], zhi:LG_ZHI[idx%12], idx}; }
function lgHourZhiIdx(h){ return Math.floor(((h+1)%24)/2); }
function lgHourGZ(dayGanIdx, hzIdx){ const start=[0,2,4,6,8,0,2,4,6,8][dayGanIdx]; return LG_GAN[(start+hzIdx)%10]; }
function lgCompute(date, gender){
  gender = gender || "男";
  const dg = lgDayGZ(date.getFullYear(), date.getMonth()+1, date.getDate());
  const hzIdx = lgHourZhiIdx(date.getHours());
  const hz = LG_ZHI[hzIdx];
  const hg = lgHourGZ(dg.idx%10, hzIdx);
  const sum = LG_DAY_GAN[dg.gan] + LG_DAY_ZHI[dg.zhi] + LG_HOUR_GAN[hg] + LG_HOUR_ZHI[hz];
  const yang = ["甲","丙","戊","庚","壬"].includes(dg.gan);
  const div = yang ? 9 : 6;
  let rem = sum % div; if (rem === 0) rem = yang ? 9 : 6;
  // 余数5：男取照海、女取内关（finalhopes.com/tortoise 算法修正说明）
  let acu = LG_REM2ACU[rem];
  if (rem === 5) acu = (gender === "女") ? "内关" : "照海";
  return {date, day:{gan:dg.gan,zhi:dg.zhi,yang}, hour:{gan:hg,zhi:hz}, gender,
          hourRange:LG_HOUR_DESC[hz], sum, div, rem, acu, info:LG_ACU[acu]};
}
function fmt2(n){ return n<10 ? ("0"+n) : (""+n); }
let lgTimer = null;
let lgGender = "男";
try { const g = localStorage.getItem("lg_gender"); if (g === "男" || g === "女") lgGender = g; } catch(e){}
// 四组固定“夫妻配对”（据 finalhopes.com/tortoise 穴位配对关系）：开穴为主、配偶为辅、先主后配
const LG_PAIRS = [
  {a:"内关",   b:"公孙",   scope:"心、胃、胸"},
  {a:"足临泣", b:"外关",   scope:"目锐眦、耳后、颈项、肩"},
  {a:"后溪",   b:"申脉",   scope:"目内眦、颈项、耳、肩膊、小肠、膀胱"},
  {a:"列缺",   b:"照海",   scope:"肺系、咽喉、胸膈"},
];
function renderPairs(){
  const el = document.getElementById("lgPairs"); if (!el) return;
  el.innerHTML = LG_PAIRS.map((p,i)=>
    `<div class="pair-card" id="pair-${i}" data-a="${p.a}" data-b="${p.b}">`+
      `<div class="pair-card-head">`+
        `<span class="pair-x">${p.a}</span>`+
        `<span class="pair-link">⇄</span>`+
        `<span class="pair-x">${p.b}</span>`+
      `</div>`+
      `<div class="pair-scope"><span class="pair-scope-k">共治</span>${p.scope}</div>`+
      `<div class="pair-now"></div>`+
    `</div>`).join("");
}
function tickLingGui(){
  const inner = document.getElementById("lgLiveInner"); if (!inner) return;
  const r = lgCompute(new Date(), lgGender);
  const dt = r.date, ds = `${dt.getFullYear()}-${fmt2(dt.getMonth()+1)}-${fmt2(dt.getDate())} ${fmt2(dt.getHours())}:${fmt2(dt.getMinutes())}:${fmt2(dt.getSeconds())}`;
  const dayType = r.day.yang ? "阳日" : "阴日";
  const i = r.info;
  let fm = `${LG_DAY_GAN[r.day.gan]}+${LG_DAY_ZHI[r.day.zhi]}+${LG_HOUR_GAN[r.hour.gan]}+${LG_HOUR_ZHI[r.hour.zhi]}=${r.sum}，<b>${dayType}</b> ÷ ${r.div} 余 <b>${r.rem}</b>`;
  if (r.rem === 5) fm += ` → 男取照海 / 女取内关（<b>${r.gender}</b>取 <b>${r.acu}</b>）`;
  else fm += ` → <b>${r.acu}</b>`;
  inner.innerHTML =
    `<div class="lg-live-head">`+
      `<span class="lg-live-title"><span class="lg-live-dot"></span>灵龟八法 · 实时开穴</span>`+
      `<span class="lg-live-clock">${ds}</span>`+
    `</div>`+
    `<div class="lg-live-main">`+
      `<div class="lg-live-acu-wrap">`+
        `<div class="lg-live-acu">${r.acu}</div>`+
        `<div class="lg-live-sub">${i.gua}卦 · ${i.gong}宫 · 通${i.mai}</div>`+
      `</div>`+
      `<div class="lg-live-gz">`+
        `<div class="gz"><span class="gz-k">日干支</span><span class="gz-v">${r.day.gan}${r.day.zhi}<em>${dayType}</em></span></div>`+
        `<div class="gz"><span class="gz-k">时干支</span><span class="gz-v">${r.hour.gan}${r.hour.zhi}<em>${r.hour.zhi}时 ${r.hourRange}</em></span></div>`+
      `</div>`+
    `</div>`+
    `<div class="lg-live-chips">`+
      `<div class="chip"><span class="chip-k">定位</span><span class="chip-v">${i.desc}</span></div>`+
      `<div class="chip"><span class="chip-k">主治</span><span class="chip-v">${i.treat}</span></div>`+
      `<div class="chip"><span class="chip-k">共治</span><span class="chip-v">${i.scope}</span></div>`+
    `</div>`+
    `<div class="lg-live-formula">取穴算式　${fm}</div>`;
  // 高亮当前开穴所在的配对组，并标出“先主后配”
  LG_PAIRS.forEach((p,idx)=>{
    const card = document.getElementById("pair-"+idx); if (!card) return;
    const now = card.querySelector(".pair-now");
    if (r.acu === p.a || r.acu === p.b){
      card.classList.add("active");
      const info = LG_ACU[r.acu];
      now.innerHTML = `当前开 <b>${r.acu}</b> → 配 <b>${info.pair}</b>　${info.order}`;
    } else {
      card.classList.remove("active");
      if (now) now.innerHTML = "";
    }
  });
}
function setupAcuRight(tbl){
  if (lgTimer){ clearInterval(lgTimer); lgTimer = null; }
  if (tbl !== "lingui") return;   // 实时开穴与穴位配对关系仅灵龟八法页展示
  renderPairs();
  tickLingGui();
  lgTimer = setInterval(tickLingGui, 1000);
}
function lgRefTables(){
  const mk = (title, rows) => {
    let t = `<div class="lg-tbl"><div class="lg-tbl-t">${title}</div><table>`;
    rows.forEach(r => { t += `<tr>` + r.map(c => `<td>${c}</td>`).join("") + `</tr>`; });
    return t + `</table></div>`;
  };
  const dayGan  = [["甲己","10"],["乙庚","9"],["丁壬","8"],["戊癸丙辛","7"]];
  const dayZhi  = [["辰戌丑未","10"],["申酉","9"],["寅卯","8"],["子巳午亥","7"]];
  const hourGan = [["甲己","9"],["乙庚","8"],["丙辛","7"],["丁壬","6"],["戊癸","5"]];
  const hourZhi = [["子午","9"],["丑未","8"],["寅申","7"],["卯酉","6"],["辰戌","5"],["巳亥","4"]];
  const gong    = [["1 坎","申脉"],["2/5 坤","照海"],["3 震","外关"],["4 巽","临泣"],["6 乾","公孙"],["7 兑","后溪"],["8 艮","内关"],["9 离","列缺"]];
  return mk("日干代数",dayGan)+mk("日支代数",dayZhi)+mk("时干代数",hourGan)+mk("时支代数",hourZhi)+mk("九宫配穴",gong);
}
function lgConfluenceCard(){
  const order = ["申脉","照海","外关","足临泣","公孙","后溪","内关","列缺"];
  const cards = order.map(k=>{
    const a = LG_ACU[k];
    return `<div class="cf-card">`+
      `<div class="cf-top"><span class="cf-name">${k}</span><span class="cf-mai">通${a.mai}</span></div>`+
      `<div class="cf-g">${a.gua}卦 · ${a.gong}宫</div>`+
      `<div class="cf-desc">${a.desc}</div>`+
      `<div class="cf-treat"><span>主治</span>${a.treat}</div>`+
      `<div class="cf-pair">配 ${a.pair} · ${a.order}</div>`+
    `</div>`;
  }).join("");
  return `<div class="detail-card lg-conf"><h3>八脉交会穴</h3>`+
    `<p class="lg-note">十二正经与奇经八脉交会的八个腧穴，为灵龟八法取穴之本。八穴两两相配（<b>夫妻配对</b>），开穴为主、配偶为辅，<b>先针主穴、后针配穴</b>。</p>`+
    `<div class="cf-grid">${cards}</div></div>`;
}

// ---- Acu (子午流注) ----
async function renderAcu(tbl) {
  const my = ++loadSeq;
  clearFilterBar();
  const data = await api(`/api/acu/${tbl}`);
  if (my !== loadSeq) return;
  setupAcuRight(tbl);
  try { localStorage.setItem("nihai_acu_table", tbl); } catch (e) {}
  const ul = $("#resultList");
  if (ul) {
    ul.className = "result-list";
    ul.innerHTML = "";
    $("#pager").innerHTML = "";
    ACU_TABLES.forEach((a) => {
      const li = document.createElement("li");
      li.className = "result-item" + (a.tbl === tbl ? " active-row" : "");
      li.innerHTML = `<div class="t">${esc(a.name)}</div>`;
      li.onclick = () => renderAcu(a.tbl);
      ul.appendChild(li);
    });
  }
  const hint = $("#listHint");
  hint.style.display = "block";
  hint.textContent = "子午流注开穴表：点击左侧方法或上方标签切换，详见右侧表格。";
  const cols = Object.keys(data[0] || {});
  let h = "";
  if (tbl === "lingui") {
    h += `<div id="lgLiveCard" class="lg-live-card">`+
           `<div class="lg-gender" id="lgGender" role="group" aria-label="性别">`+
             `<span class="lg-gender-k">性别</span>`+
             `<button type="button" data-g="男" class="${lgGender==='男'?'on':''}">男</button>`+
             `<button type="button" data-g="女" class="${lgGender==='女'?'on':''}">女</button>`+
           `</div>`+
           `<div id="lgLiveInner"></div>`+
         `</div>`;
    h += `<div class="detail-card lg-pairs">`+
           `<h3 class="lg-pairs-h"><span class="lg-pairs-ico">⚭</span> 穴位配对关系</h3>`+
           `<p class="lg-pairs-note">八脉交会穴分四组“夫妻配对”：开穴为主、配偶为辅，<b>先针主穴、后针配穴</b>。当前实时开穴所在的配对组会自动高亮（见上方实时开穴卡）。</p>`+
           `<div id="lgPairs" class="lg-pairs-grid"></div>`+
         `</div>`;
  }
  h += `<div class="tabs">`;
  ACU_TABLES.forEach((a) => {
    h += `<button class="${a.tbl === tbl ? "active" : ""}" data-tbl="${a.tbl}">${a.name}</button>`;
  });
  h += `</div>`;
  h += `<div class="detail-card"><table class="acu"><thead><tr>`;
  cols.forEach((c) => h += `<th>${esc(acuColLabel(tbl, c))}</th>`);
  h += `</tr></thead><tbody>`;
  data.forEach((row) => {
    h += "<tr>";
    cols.forEach((c) => h += `<td>${esc(row[c])}</td>`);
    h += "</tr>";
  });
  h += `</tbody></table></div>`;
  if (tbl === "lingui") {
    h += lgConfluenceCard();
    h += `<div class="detail-card lg-ref"><h3>灵龟八法 · 算法说明</h3>` +
      `<p class="lg-song">八法歌：坎一连申脉，照海坤二五，震三属外关，巽四临泣数，乾六是公孙，兑七后溪府，艮八系内关，离九列缺主。</p>` +
      `<p class="lg-note">取穴法则：日干、日支、时干、时支四数相加，<b>阳日（甲丙戊庚壬）除以 9</b>、<b>阴日（乙丁己辛癸）除以 6</b>，其余数对应九宫数开穴；恰除尽时阳日余 9、阴日余 6。</p>` +
      `<div class="lg-tables">${lgRefTables()}</div></div>`;
  }
  $("#detailPane").innerHTML = h;
  if (tbl === "lingui") {
    renderPairs();
    document.querySelectorAll("#lgGender button").forEach((b) => {
      b.onclick = () => {
        lgGender = b.dataset.g;
        try { localStorage.setItem("lg_gender", lgGender); } catch(e){}
        document.querySelectorAll("#lgGender button").forEach((x) => x.classList.toggle("on", x.dataset.g === lgGender));
        tickLingGui();
      };
    });
    const lc = document.getElementById("lgLiveCard"); if (lc) tickLingGui();
  }
  document.querySelectorAll(".tabs button").forEach((b) => {
    b.onclick = () => renderAcu(b.dataset.tbl);
  });
}

// ---- Search category tabs (top of list) ----
function renderSearchTabs(activeKey) {
  const groups = lastSearchData ? lastSearchData.groups : [];
  const total = groups.reduce((a, g) => a + g.total, 0);
  const tabs = [{ key: "all", label: "全部", count: total }]
    .concat(groups.map((g) => ({ key: g.module, label: g.name, count: g.total })));
  renderFilterBar(tabs, activeKey, (key) => {
    if (key === "all") { renderSearch(lastSearchData, "all"); }
    else { selectSearchCategory(key, 1); }
  });
}

function renderSearchItem(module, rec) {
  const ul = $("#resultList");
  const li = document.createElement("li");
  li.className = "result-item";
  const [title, sub] = itemTitleSub(module, rec);
  li.innerHTML = `<div class="t">${esc(title)}</div><div class="s">${esc(sub)}</div>`;
  li.onclick = () => showUniversal(module, rec);
  ul.appendChild(li);
}

function renderSearch(data, activeKey) {
  lastSearchData = data;
  const ul = $("#resultList");
  if (!ul) return;
  ul.className = "result-list";
  ul.innerHTML = "";
  $("#pager").innerHTML = "";
  const groups = data.groups || [];
  const total = groups.reduce((a, g) => a + g.total, 0);
  const hint = $("#listHint");
  if (!total) {
    hint.style.display = "block";
    hint.textContent = `未找到与 “${data.q}” 相关的内容`;
    renderFilterBar(null);
    return;
  }
  hint.style.display = "none";
  renderSearchTabs("all");
  groups.forEach((g) => {
    const gh = document.createElement("li");
    gh.className = "result-group-head";
    gh.textContent = `${g.name}（${g.total}）`;
    ul.appendChild(gh);
    g.items.forEach((rec) => renderSearchItem(g.module, rec));
  });
}

async function selectSearchCategory(module, page) {
  page = page || 1;
  const q = currentSearchQ;
  const my = ++loadSeq;
  let data;
  try {
    data = await api(`/api/search?q=${enc(q)}&module=${module}&page=${page}&size=50`);
  } catch (e) {
    if (my !== loadSeq) return;
    const ul = $("#resultList"); if (ul) ul.innerHTML = "";
    const hint = $("#listHint");
    if (hint) { hint.style.display = "block"; hint.textContent = "加载失败，请重试。"; }
    return;
  }
  if (my !== loadSeq) return;
  const g = (data.groups && data.groups[0]) || null;
  const ul = $("#resultList");
  ul.innerHTML = "";
  const hint = $("#listHint");
  if (!g || !g.items.length) {
    hint.style.display = "block";
    hint.textContent = "没有匹配结果。";
  } else {
    hint.style.display = "none";
    g.items.forEach((rec) => renderSearchItem(g.module, rec));
  }
  renderSearchTabs(module);
  renderSearchPager(data, module);
}

function renderSearchPager(data, module) {
  const p = $("#pager");
  if (!p) return;
  p.innerHTML = "";
  const g = (data.groups && data.groups[0]) || { total: 0 };
  const totalPages = Math.max(1, Math.ceil(g.total / data.size));
  const mk = (label, pg, dis) => {
    const b = document.createElement("button");
    b.textContent = label; b.disabled = dis;
    b.onclick = () => selectSearchCategory(module, pg);
    return b;
  };
  p.appendChild(mk("上一页", data.page - 1, data.page <= 1));
  const info = document.createElement("span");
  info.style.cssText = "align-self:center;font-size:13px;color:#5b5246";
  info.textContent = `第 ${data.page} / ${totalPages} 页（共 ${g.total} 条）`;
  p.appendChild(info);
  p.appendChild(mk("下一页", data.page + 1, data.page >= totalPages));
}

// ---- Yaotu (药图): square-thumbnail list + category filter ----
async function loadYaotu(q, cat, page) {
  page = page || 1;
  yaotuQ = q || ""; yaotuCat = cat || "";
  const my = ++loadSeq;
  const data = await api(`/api/yaotu?q=${enc(yaotuQ)}&cat=${enc(yaotuCat)}&page=${page}&size=60`);
  if (my !== loadSeq) return;
  const ul = $("#resultList");
  if (ul) {
    ul.className = "result-list thumb-grid";
    ul.innerHTML = "";
  }
  const hint = $("#listHint");
  hint.style.display = "block";
  hint.textContent = "点击下方缩略图查看大图；上方可按「形态 / 功效分类」筛选。";
  const cats = (data.cats || []);
  const tabs = [{ key: "", label: "全部", count: data.total }]
    .concat(cats.map((c) => ({ key: c.key, label: c.label })));
  renderFilterBar(tabs, yaotuCat, (k) => loadYaotu(yaotuQ, k, 1));
  data.items.forEach((r) => {
    const li = document.createElement("li");
    li.className = "thumb-item";
    li.dataset.name = r.name;
    const img = document.createElement("img");
    img.src = r._folder ? ("/extimg?p=" + enc(r._rel)) : ("/api/herb_image/" + enc(r.name));
    img.alt = r.name;
    img.loading = "lazy";
    img.onerror = () => { li.style.display = "none"; };
    const cap = document.createElement("span");
    cap.className = "thumb-cap";
    cap.textContent = r.name;
    li.appendChild(img);
    li.appendChild(cap);
    li.onclick = () => showYaotuDetail(r);
    ul.appendChild(li);
  });
  renderYaotuPager(data);
}

function renderYaotuPager(data) {
  const p = $("#pager");
  if (!p) return;
  p.innerHTML = "";
  const totalPages = Math.max(1, Math.ceil(data.total / data.size));
  const mk = (label, page, dis) => {
    const b = document.createElement("button");
    b.textContent = label; b.disabled = dis;
    b.onclick = () => loadYaotu(yaotuQ, yaotuCat, page);
    return b;
  };
  p.appendChild(mk("上一页", data.page - 1, data.page <= 1));
  const info = document.createElement("span");
  info.style.cssText = "align-self:center;font-size:13px;color:#5b5246";
  info.textContent = `第 ${data.page} / ${totalPages} 页（共 ${data.total} 张）`;
  p.appendChild(info);
  p.appendChild(mk("下一页", data.page + 1, data.page >= totalPages));
}

function esc(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// ===========================================================================
// 人纪学习系统（完整复刻《人纪针灸内部学习系统》）：10 个子模块
//   fields 型：倪师穴位详解 / 针灸医案 / 汉唐方剂 / 病症方剂 / 辨证论治 / 正副辨证 / 针灸记录
//   image  型：倪师图（63 张经络表/脏腑图）
//   points 型：人体穴位图（SELFDATA 348 个坐标）
//   tables 型：子午流注·灵龟八法（灵龟八法 / 纳甲 / 纳子）
// ===========================================================================

// 人体底图：原 EXE 内的真实彩色人体穴位图（1793×3200），存放于 static/img/renji-body.jpg。
// SELFDATA 坐标范围正好落在图片的 (218..1557, 83..3064) 子区域（身体的实际绘制区）。
// 故以"图片真实像素尺寸"作为 SVG viewBox，让穴位圈与原图位置一一对齐。
const RENJI_BODY_W = 1793, RENJI_BODY_H = 3200, RENJI_BODY_IMG = "/static/img/renji-body.jpg";
// 人纪穴位图分组配色：原 EXE 用 SELFDATA.Y 区分背/前/侧三视图组
//   Y=0 督脉/背俞穴（落在左半=背侧）   — 红色
//   Y=1 任脉/腹募穴（落在右半=前侧）   — 蓝色
//   Y=2 侧身/四肢穴（落在外缘/局部图） — 绿色
const RENJI_Y_COLOR = {
  0: { dot: "#e95420", halo: "rgba(233,84,32,.18)", label: "背侧（督脉·背俞）" },
  1: { dot: "#1f6feb", halo: "rgba(31,111,235,.18)", label: "前侧（任脉·腹募）" },
  2: { dot: "#1f9d55", halo: "rgba(31,157,85,.18)", label: "侧身/四肢" },
};

function subKind() {
  subMeta = (subSubs || []).find((m) => m.key === subKey) || null;
  return subMeta ? subMeta.kind : "";
}

function failHint(msg) {
  const hint = $("#listHint");
  if (hint) { hint.style.display = "block"; hint.textContent = msg; }
}

async function loadSubList() {
  const meta = (subSubs || []).find((m) => m.key === subKey);
  if (!meta) return;
  const kind = meta.kind;
  if (kind === "tool") { renderTool(); return; }
  if (kind === "catalog") { renderCatalogTree(); return; }
  const my = ++loadSeq;
  const ul = $("#resultList");
  if (ul) { ul.innerHTML = ""; $("#pager").innerHTML = ""; }
  failHint("加载中…");

  let data;
  try {
    if (kind === "points") {
      data = await api(`${sysCfg.api}/list?sub=points`);
    } else if (kind === "tables") {
      data = await api(sysCfg.tablesUrl + "?sub=" + enc(subKey));
    } else {
      data = await api(`${sysCfg.api}/list?sub=${enc(subKey)}&q=${enc(subQ)}&page=${state.page}&size=60`);
    }
  } catch (e) {
    // 失败也绝不可停留在「加载中…」：超时被 AbortController 中止、网络抖动、
    // 服务端偶发 5xx 都应给用户明确反馈，而不是空白转圈。
    if (my !== loadSeq) return;          // 已被更新的导航取代
    failHint("加载失败，请稍后重试（点击左侧模块可重新加载）。");
    return;
  }
  if (my !== loadSeq) return;            // 已被更新的导航取代

  if (kind === "points") { renderSubPoints(data.items); return; }
  if (kind === "tables") { renderSubTables(data); return; }
  subTotal = data.total;
  if (kind === "image") renderSubImages(data.items);
  else renderSubFields(data.items);
  renderSubPager(data);
}

// ---- fields 型：列表 + 详情 ----
function renderSubFields(items) {
  const ul = $("#resultList");
  if (!ul) return;
  ul.className = "result-list";
  ul.innerHTML = "";
  const hint = $("#listHint");
  hint.style.display = items.length ? "none" : "block";
  if (!items.length) hint.textContent = "没有匹配结果。";
  items.forEach((it) => {
    const li = document.createElement("li");
    li.className = "result-item";
    li.innerHTML = `<div class="t">${esc(it.name)}</div>`;
    li.onclick = () => loadSubItem(it.i);
    ul.appendChild(li);
  });
}

async function loadSubItem(i) {
  let item;
  try { item = await api(`${sysCfg.api}/item?sub=${enc(subKey)}&i=${i}`); }
  catch (e) {
    $("#detailPane").innerHTML = `<div class="hint">详情加载失败，请重试。</div>`;
    return;
  }
  showSubDetail(item);
}

function showSubDetail(item) {
  const meta = subMeta || {};
  const fields = item.fields || {};
  let h = `<div class="detail-card"><h3>${esc(item.name)}</h3>`;
  // 卦图（六十四卦等带 hasImg 的子模块）
  if (meta.hasImg) {
    h += `<div class="gua-img"><img src="${sysCfg.img}?name=${enc(item.name)}" ` +
         `alt="${esc(item.name)}" onerror="this.style.display='none'"></div>`;
  }
  // 卦象（阴阳爻）—— DD 为上→下（上爻在最前，初爻在最后）
  if (sysCfg.showDD && item.dd && /^[01]{6}$/.test(item.dd)) {
    h += `<div class="gua-dd" title="上爻→初爻">`;
    for (let k = 0; k < 6; k++) {
      const yang = item.dd[k] === "1";
      h += `<div class="gua-line ${yang ? "yang" : "yin"}">` +
           (yang ? "" : `<span></span><span></span>`) + `</div>`;
    }
    h += `</div>`;
  }
  const keys = Object.keys(fields);
  if (!keys.length && !meta.hasImg &&
      !(sysCfg.showDD && item.dd)) h += `<div class="hint">（本条暂无内容）</div>`;
  keys.forEach((k) => {
    const v = fields[k];
    if (v == null || v === "") return;
    h += `<div class="sec-h">${esc(k)}</div><div class="sec-b">${esc(v)}</div>`;
  });
  h += `</div>`;
  $("#detailPane").innerHTML = h;
}

// ---- 天纪目录（catalog 模块）：章节树 + 条目文章 ----
const CAT_SUB_META = { gua: { hasImg: true }, rendao: { hasImg: false },
                       lilun: { hasImg: false }, mingli: { hasImg: false } };

async function renderCatalogTree() {
  const ul = $("#resultList");
  if (ul) { ul.innerHTML = ""; ul.className = "catalog-tree"; $("#pager").innerHTML = ""; }
  const hint = $("#listHint"); if (hint) hint.style.display = "none";
  const dp = $("#detailPane");
  if (dp) dp.innerHTML = '<div class="hint">点击左侧章节展开，再点条目查看文章。</div>';
  let data;
  try { data = await api("/api/tianji/catalog"); }
  catch (e) {
    if (hint) { hint.style.display = "block"; hint.textContent = "目录加载失败，请稍后重试。"; }
    return;
  }
  if (!ul) return;
  ul.innerHTML = "";
  data.tree.forEach((cat) => {
    const li = document.createElement("li");
    li.className = "cat-node";
    const head = document.createElement("div");
    head.className = "cat-head";
    const catCnt = cat.subs.reduce((a, s) => a + s.entries.reduce((b, e) => b + e.articles.length, 0), 0);
    head.innerHTML = `<span class="cat-toggle">▸</span>${esc(cat.name)}<small>${catCnt ? " " + catCnt : ""}</small>`;
    head.onclick = () => {
      li.classList.toggle("open");
      head.querySelector(".cat-toggle").textContent = li.classList.contains("open") ? "▾" : "▸";
    };
    li.appendChild(head);
    const subUl = document.createElement("ul");
    subUl.className = "cat-subs";
    cat.subs.forEach((sub) => {
      const sli = document.createElement("li");
      sli.className = "sub-node";
      const sh = document.createElement("div");
      sh.className = "sub-head";
      const subCnt = sub.entries.reduce((a, e) => a + e.articles.length, 0);
      sh.innerHTML = `<span class="sub-toggle">▸</span>${esc(sub.name)}<small>${subCnt ? " " + subCnt : ""}</small>`;
      sh.onclick = (ev) => {
        ev.stopPropagation();
        sli.classList.toggle("open");
        sh.querySelector(".sub-toggle").textContent = sli.classList.contains("open") ? "▾" : "▸";
      };
      sli.appendChild(sh);
      const eUl = document.createElement("ul");
      eUl.className = "cat-entries";
      sub.entries.forEach((e) => {
        const eli = document.createElement("li");
        eli.className = "entry-node";
        const eh = document.createElement("div");
        eh.className = "entry-head";
        eh.innerHTML = `${esc(e.name)}<small>${e.articles.length ? " " + e.articles.length : ""}</small>`;
        eh.onclick = (ev) => { ev.stopPropagation(); showCatalogEntry(e); };
        eli.appendChild(eh);
        eUl.appendChild(eli);
      });
      sli.appendChild(eUl);
      subUl.appendChild(sli);
    });
    li.appendChild(subUl);
    ul.appendChild(li);
  });

  // 未归类（平铺文章，确保全部不丢）
  if (data.uncat && data.uncat.articles.length) {
    const li = document.createElement("li");
    li.className = "cat-node open";
    const head = document.createElement("div");
    head.className = "cat-head";
    head.innerHTML = `<span class="cat-toggle">▾</span>未归类<small> ${data.uncat.articles.length}</small>`;
    li.appendChild(head);
    const wrap = document.createElement("div");
    wrap.className = "cat-uncat";
    data.uncat.articles.forEach((a) => {
      const d = document.createElement("div");
      d.className = "catalog-article";
      d.textContent = a.name;
      d.onclick = () => showCatalogArticle(a);
      wrap.appendChild(d);
    });
    li.appendChild(wrap);
    ul.appendChild(li);
  }
}

function showCatalogEntry(e) {
  const dp = $("#detailPane");
  if (!dp) return;
  if (!e.articles.length) {
    dp.innerHTML = `<div class="detail-card"><h3>${esc(e.name)}</h3><div class="hint">（本条目暂无收录文章）</div></div>`;
    return;
  }
  let h = `<div class="detail-card"><h3>${esc(e.name)}</h3><div class="sec-h">收录文章（${e.articles.length}）</div>`;
  e.articles.forEach((a, idx) => {
    h += `<div class="catalog-article" data-idx="${idx}">${esc(a.name)}</div>`;
  });
  h += `</div>`;
  dp.innerHTML = h;
  dp.querySelectorAll(".catalog-article").forEach((el) => {
    el.onclick = () => showCatalogArticle(e.articles[+el.dataset.idx]);
  });
}

async function showCatalogArticle(a) {
  const dp = $("#detailPane");
  if (!dp) return;
  dp.innerHTML = '<div class="hint">加载中…</div>';
  let item;
  try { item = await api(`${sysCfg.api}/item?sub=${enc(a.src)}&i=${a.i}`); }
  catch (e) { dp.innerHTML = '<div class="hint">加载失败，请重试。</div>'; return; }
  subMeta = CAT_SUB_META[a.src] || {};
  showSubDetail(item);
}

// ---- image 型：缩略图网格 + 大图 ----
function renderSubImages(items) {
  const ul = $("#resultList");
  if (!ul) return;
  ul.className = "result-list thumb-grid";
  ul.innerHTML = "";
  const hint = $("#listHint");
  hint.style.display = "block";
  hint.textContent = "点击下方缩略图查看倪师原图（经络表 / 脏腑生理病理与治疗配穴列表等）。";
  items.forEach((it) => {
    const li = document.createElement("li");
    li.className = "thumb-item";
    const img = document.createElement("img");
    img.src = `${sysCfg.img}?name=${enc(it.name)}`;
    img.alt = it.name; img.loading = "lazy";
    img.onerror = () => { li.style.display = "none"; };
    const cap = document.createElement("span");
    cap.className = "thumb-cap"; cap.textContent = it.name;
    li.appendChild(img); li.appendChild(cap);
    li.onclick = () => showSubImage(it.name);
    ul.appendChild(li);
  });
}

function showSubImage(name) {
  $("#detailPane").innerHTML =
    `<div class="detail-card"><h3>${esc(name)}</h3>` +
    `<img class="herb-img" style="float:none;max-width:100%;max-height:80vh" ` +
    `src="${sysCfg.img}?name=${enc(name)}" alt="${esc(name)}" onerror="this.style.display='none'"></div>`;
}

// ---- points 型：SELFDATA 坐标人体穴位图 ----
function renderSubPoints(items) {
  const ul = $("#resultList");
  if (ul) ul.innerHTML = "";
  const hint = $("#listHint");
  if (hint) hint.style.display = "none";
  if (!items.length) return;
  // 使用原 EXE 抽取的真实人体穴位图（1793×3200）作为底图，穴位圈按 SELFDATA
  // 真实坐标 (left, top) 精确定位，颜色按 Y 字段分背/前/侧三组。
  const vb = `0 0 ${RENJI_BODY_W} ${RENJI_BODY_H}`;
  const pts = items.map((p, idx) => {
    const c = RENJI_Y_COLOR[p.y] || RENJI_Y_COLOR[2];
    return { idx, x: p.left, y: p.top, id: p.id, dot: c.dot, halo: c.halo };
  });
  const halos = pts.map((p) =>
    `<circle class="renji-pt-h" data-i="${p.idx}" cx="${p.x}" cy="${p.y}" r="44" ` +
    `fill="${p.halo}" stroke="none">` +
    `<title>${esc(p.id)}</title></circle>`).join("");
  const dots = pts.map((p) =>
    `<circle class="renji-pt" data-i="${p.idx}" cx="${p.x}" cy="${p.y}" r="18" ` +
    `fill="${p.dot}" stroke="#fff" stroke-width="3">` +
    `<title>${esc(p.id)}</title></circle>`).join("");
  // 统计各组数量
  const counts = { 0: 0, 1: 0, 2: 0 };
  items.forEach((p) => { counts[p.y] = (counts[p.y] || 0) + 1; });
  const legend = Object.keys(RENJI_Y_COLOR).map((k) => {
    const c = RENJI_Y_COLOR[k];
    const n = counts[k] || 0;
    return `<span class="renji-legend-item" data-y="${k}">` +
      `<i style="background:${c.dot}"></i>${c.label}（${n}）</span>`;
  }).join("");
  const svg = `<svg class="renji-svg" viewBox="${vb}" preserveAspectRatio="xMidYMin meet">` +
    `<image href="${RENJI_BODY_IMG}" x="0" y="0" width="${RENJI_BODY_W}" height="${RENJI_BODY_H}" preserveAspectRatio="none"/>` +
    `<g class="renji-pts">${halos}${dots}</g></svg>`;
  $("#detailPane").innerHTML =
    `<div class="detail-card renji-map-card"><h3>人体穴位图（原软件自带彩色图）</h3>` +
    `<p class="hint">共 ${items.length} 个穴位，按原《人纪》软件 SELFDATA 坐标精确定位到原图（${RENJI_BODY_W}×${RENJI_BODY_H}）。` +
    `鼠标悬停查看穴名，点击穴位在下方显示穴位名称与坐标。</p>` +
    `<div class="renji-legend">${legend}</div>` +
    `<div class="renji-map-wrap">${svg}</div>` +
    `<div class="renji-ptinfo" id="renjiPtInfo">点击穴位查看详情。</div></div>`;
  document.querySelectorAll(".renji-pt").forEach((c) => {
    c.style.cursor = "pointer";
    c.addEventListener("click", () => {
      const p = items[parseInt(c.dataset.i, 10)];
      const info = document.getElementById("renjiPtInfo");
      if (info) info.innerHTML = `<b>${esc(p.id)}</b>　坐标（left=${p.left}，top=${p.top}，分组=${RENJI_Y_COLOR[p.y] ? RENJI_Y_COLOR[p.y].label : p.y}）`;
    });
  });
}

// ---- tables 型：子午流注·灵龟八法 / 紫微斗数 / 易经数表 ----
// 复用顶部子模块筛选条做导航；子表（灵龟八法/纳甲/纳子 或 紫微诸星/安世袭卦…）
// 做成详情卡内的内嵌标签，避免覆盖顶层导航。
// renji 返回 {lingui,najia,nazi}；tianji 返回 {tables:[{key,label,cols,rows}]}。
function renderSubTables(data) {
  const hint = $("#listHint");
  if (hint) hint.style.display = "none";
  let groups;
  if (data.tables) {
    groups = data.tables.map((t) => ({ key: t.key, label: t.label, cols: t.cols, rows: t.rows }));
  } else {
    groups = [
      { key: "lingui", label: "灵龟八法", cols: (data.lingui || {}).cols, rows: (data.lingui || {}).rows },
      { key: "najia",  label: "纳甲法",   cols: (data.najia  || {}).cols, rows: (data.najia  || {}).rows },
      { key: "nazi",   label: "纳子法",   cols: (data.nazi   || {}).cols, rows: (data.nazi   || {}).rows },
    ];
  }
  if (groups.length) renderSubTablesBody(groups, groups[0].key);
}

function renderSubTablesBody(groups, key) {
  const g = groups.find((x) => x.key === key) || groups[0];
  const cols = g.cols || [], rows = g.rows || [];
  let h = `<div class="detail-card"><h3>${esc(g.label)}</h3><div class="tabs">`;
  groups.forEach((x) => {
    h += `<button class="${x.key === key ? "active" : ""}" data-k="${x.key}">${esc(x.label)}</button>`;
  });
  h += `</div><table class="acu"><thead><tr>`;
  cols.forEach((c) => h += `<th>${esc(c)}</th>`);
  h += `</tr></thead><tbody>`;
  rows.forEach((r) => {
    h += "<tr>";
    cols.forEach((c, idx) => h += `<td>${esc(r[idx])}</td>`);
    h += "</tr>";
  });
  h += `</tbody></table></div>`;
  $("#detailPane").innerHTML = h;
  document.querySelectorAll(".detail-card .tabs button").forEach((b) => {
    b.onclick = () => renderSubTablesBody(groups, b.dataset.k);
  });
}

// ---- 人纪列表分页 ----
function renderSubPager(data) {
  const p = $("#pager");
  if (!p) return;
  p.innerHTML = "";
  const totalPages = Math.max(1, Math.ceil(data.total / data.size));
  const mk = (label, page, dis) => {
    const b = document.createElement("button");
    b.textContent = label; b.disabled = dis;
    b.onclick = () => { state.page = page; loadSubList(); };
    return b;
  };
  p.appendChild(mk("上一页", data.page - 1, data.page <= 1));
  const info = document.createElement("span");
  info.style.cssText = "align-self:center;font-size:13px;color:#5b5246";
  info.textContent = `第 ${data.page} / ${totalPages} 页（共 ${data.total} 条）`;
  p.appendChild(info);
  p.appendChild(mk("下一页", data.page + 1, data.page >= totalPages));
}

// ---- Global search (top bar): searches ALL modules and shows grouped results ----
async function doGlobalSearch(q) {
  currentSearchQ = q;
  const my = ++loadSeq;
  let data;
  try {
    data = await api(`/api/search?q=${enc(q)}`);
  } catch (e) {
    if (my !== loadSeq) return;
    const ul = $("#resultList"); if (ul) ul.innerHTML = "";
    const hint = $("#listHint");
    if (hint) { hint.style.display = "block"; hint.textContent = "搜索失败，请重试。"; }
    renderFilterBar(null);
    return;
  }
  if (my !== loadSeq) return;
  renderSearch(data, "all");
}

// ---- init ----
(async function init() {
  const modulesUrl = sysCfg ? sysCfg.modulesUrl : "/api/modules";
  const modules = await api(modulesUrl);
  // 子系统（人纪 / 天纪）：左侧模块即各子模块，loadSubList 需据此查 sub 的 kind。
  if (sysCfg) subSubs = modules;
  buildSidebar(modules);
  // 初始默认激活：优先恢复上次停留在的模块（按系统分别记忆），否则激活第一个模块
  let target = modules[0];
  try {
    const saved = localStorage.getItem("nihai_active_module_" + SYSTEM);
    if (saved) {
      const found = modules.find((m) => m.key === saved);
      if (found) target = found;
    }
  } catch (e) {}
  if (target) selectModule(target, target._el);
  const doSearch = () => {
    const q = $("#search").value.trim();
    state.page = 1;
    // 子系统（人纪 / 天纪）是独立页面：无论空查询还是有查询，都走自身的子模块内
    // 搜索/列表（避免与医案系统的同名模块 key 如 xuewei/bbxx 冲突）。
    if (sysCfg) {
      subQ = q;
      return loadSubList();
    }
    if (!q) {
      // empty query: browse the current module (default to cases)
      if (!state.module) state.module = "cases";
      if (state.module === "acu") {
        let tbl = "lingui";
        try { tbl = localStorage.getItem("nihai_acu_table") || "lingui"; } catch (e) {}
        return renderAcu(tbl);
      }
      if (state.module === "yaotu") return loadYaotu("", "", 1);
      if (state.module === "xuewei") return loadXuewei("", "", 1);
      return loadList("");
    }
    doGlobalSearch(q);
  };
  $("#searchBtn").onclick = doSearch;
  $("#search").addEventListener("keydown", (e) => { if (e.key === "Enter") doSearch(); });
})();

// ===== 天纪 · 排盘系统 / 命理系统（tool 型模块，顶层作用域，供 loadSubList 调用） =====
let lastPaipan = null;

function renderTool() {
    const isMing = subKey === "mingli_sys";
    const lm = $("#listMain");
    if (lm) {
      lm.innerHTML =
        '<div class="paipan-form">' +
        '<h3>' + (isMing ? "命理系统 · 出生信息" : "排盘系统 · 出生信息") + '</h3>' +
        '<label>阳历出生日期<input type="date" id="ppDate" value="1985-03-12"></label>' +
        '<label>出生时辰<select id="ppHour">' +
        '<option value="0">子时 23:00–00:59</option>' +
        '<option value="1">丑时 01:00–02:59</option>' +
        '<option value="3" selected>寅时 03:00–04:59</option>' +
        '<option value="5">卯时 05:00–06:59</option>' +
        '<option value="7">辰时 07:00–08:59</option>' +
        '<option value="9">巳时 09:00–10:59</option>' +
        '<option value="11">午时 11:00–12:59</option>' +
        '<option value="13">未时 13:00–14:59</option>' +
        '<option value="15">申时 15:00–16:59</option>' +
        '<option value="17">酉时 17:00–18:59</option>' +
        '<option value="19">戌时 19:00–20:59</option>' +
        '<option value="21">亥时 21:00–22:59</option>' +
        '</select></label>' +
        '<label>性别<select id="ppGender"><option value="男" selected>男</option>' +
        '<option value="女">女</option></select></label>' +
        '<label>出生地（选填）<input type="text" id="ppPlace" placeholder="如 北京"></label>' +
        '<button id="ppBtn">' + (isMing ? "排盘并解读" : "开始排盘") + '</button>' +
        '<div class="pp-tip">时辰按传统 2 小时制；排盘结果仅供学习参考，流派差异以原版为准。</div>' +
        '</div>';
    }
    const fb = $("#filterBar"); if (fb) fb.style.display = "none";
    const lh = $("#listHint"); if (lh) lh.style.display = "none";
    const pg = $("#pager"); if (pg) pg.innerHTML = "";
    const btn = $("#ppBtn"); if (btn) btn.onclick = doPaipan;
    const dp = $("#detailPane");
    if (dp) dp.innerHTML = '<div class="hint">填写左侧出生信息后点击「' +
      (isMing ? "排盘并解读" : "开始排盘") + '」。</div>';
  }

  async function doPaipan() {
    const date = $("#ppDate").value;
    const hour = $("#ppHour").value;
    const gender = $("#ppGender").value;
    const place = ($("#ppPlace").value || "").trim();
    if (!date) { alert("请填写出生日期"); return; }
    const solar = date + " " + String(hour).padStart(2, "0") + ":30";
    const dp = $("#detailPane");
    dp.innerHTML = '<div class="hint">排盘中…</div>';
    let data;
    try {
      data = await api("/api/tianji/paipan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ solar, gender, birthplace: place }),
      });
    } catch (e) {
      dp.innerHTML = '<div class="hint">排盘失败：' + esc(e.message || String(e)) + '</div>';
      return;
    }
    lastPaipan = data;
    if (subKey === "mingli_sys") renderMingli(data);
    else renderPaipan(data);
  }

  const SIHUA_COLOR = { "禄": "var(--c-lu)", "权": "var(--c-quan)",
                         "科": "var(--c-ke)", "忌": "var(--c-ji)" };

  function pillarCell(p, label) {
    return '<div class="bz-cell">' +
      '<div class="bz-label">' + label + '</div>' +
      '<div class="bz-gz">' + esc(p.gz) + '</div>' +
      '<div class="bz-shi">' + esc(p.gan_shi) + '</div>' +
      '<div class="bz-nayin">' + esc(p.nayin) + '</div>' +
      '</div>';
  }

  function renderPaipan(d) {
    const b = d.bazi, z = d.ziwei, g = d.gua;
    let h = '<div class="paipan-result">';
    // 概要
    h += '<div class="pp-summary">' +
      '<span>阳历 <b>' + esc(b.solar) + '</b></span>' +
      '<span>农历 <b>' + esc(b.lunar) + '</b></span>' +
      '<span>生肖 <b>' + esc(b.zodiac) + '</b></span>' +
      '<span>性别 <b>' + esc(b.gender) + '</b></span>' +
      '<span>日主 <b>' + esc(b.ri_gan) + '（' + esc(b.ri_wx) + '）</b></span>' +
      '<span>强弱 <b>' + esc(b.strength) + '</b></span>' +
      '</div>';
    // 八字四柱
    h += '<div class="sec-h">八字四柱</div><div class="bazi-grid">';
    const labels = ["年柱", "月柱", "日柱", "时柱"];
    b.pillars.forEach((p, i) => { h += pillarCell(p, labels[i]); });
    h += '</div>';
    // 五行分布条
    const wx = b.wx_score;
    h += '<div class="sec-h">五行分布</div><div class="wx-bar">';
    const wxc = { "木": "#2e8b57", "火": "#d9534f", "土": "#c79a4b",
                  "金": "#b0b0b0", "水": "#3a7bd5" };
    const maxv = Math.max.apply(null, Object.values(wx));
    Object.keys(wx).forEach((k) => {
      const pct = (wx[k] / maxv * 100).toFixed(0);
      h += '<div class="wx-row"><span class="wx-name">' + k + '</span>' +
        '<span class="wx-track"><span class="wx-fill" style="width:' + pct +
        '%;background:' + wxc[k] + '"></span></span>' +
        '<span class="wx-val">' + wx[k].toFixed(2) + '</span></div>';
    });
    h += '</div>';
    // 大运
    h += '<div class="sec-h">大运（' + (b.dayun.shun ? "顺" : "逆") + '排，' +
      b.dayun.start_age + '岁' + b.dayun.start_mon + '个月起运）</div>' +
      '<div class="dayun-row">';
    b.dayun.list.slice(0, 10).forEach((du) => {
      h += '<div class="dy-cell"><div class="dy-age">' + du.age + '岁</div>' +
        '<div class="dy-gz">' + esc(du.gz) + '</div>' +
        '<div class="dy-shi">' + esc(du.gan_shi) + '</div></div>';
    });
    h += '</div>';
    // 紫微斗数命盘
    h += '<div class="sec-h">紫微斗数命盘（' + esc(z.ju) + ' · 命宫 ' +
      esc(z.ming_gong.gz) + ' · 身宫 ' + esc(z.shen_gong.zhi) + '）</div>';
    h += '<div class="ziwei-grid">';
    z.palace.forEach((pal) => {
      const isMing = pal.gong === "命宫";
      h += '<div class="palace-card' + (isMing ? " ming" : "") + '">';
      h += '<div class="pc-head">' + esc(pal.gong) + ' <span class="pc-zhi">' +
        esc(pal.zhi) + '</span></div><div class="pc-stars">';
      if (!pal.stars.length) h += '<span class="pc-empty">（空宫）</span>';
      pal.stars.forEach((s) => {
        const col = SIHUA_COLOR[s.sihua] || "var(--star)";
        h += '<span class="star-chip" style="color:' + col + '" title="' +
          (ziweiStarTip(s.name)) + '">' + esc(s.name) +
          (s.sihua ? '<i class="sihua">' + s.sihua + '</i>' : '') + '</span>';
      });
      h += '</div></div>';
    });
    h += '</div>';
    // 四化
    const sh = z.sihua;
    h += '<div class="sec-h">生年四化</div><div class="sihua-line">';
    ["禄", "权", "科", "忌"].forEach((k) => {
      h += '<span class="sihua-pill" style="color:' + SIHUA_COLOR[k] + '">' +
        k + '：' + esc(sh[k] || "—") + '</span>';
    });
    h += '</div>';
    // 本命卦
    h += '<div class="sec-h">本命卦（' + esc(g.method) + '）</div>' +
      '<div class="gua-box">本卦 <b>' + esc(g.ben) + '</b>（' + esc(g.up) +
      '上' + esc(g.down) + '下）　动爻 第' + g.dong_yao + '爻　变卦 <b>' +
      esc(g.bian) + '</b><div class="gua-sub">农历 ' + esc(g.lunar) + '</div></div>';
    h += '</div>';
    $("#detailPane").innerHTML = h;
  }

  function ziweiStarTip(name) {
    const M = {
      "紫微": "北斗帝星，主尊贵领导权柄", "天机": "智谋，主思辨机变谋略",
      "太阳": "官禄主，主光明名声父兄", "武曲": "财星，主财富刚毅行动",
      "天同": "福德主，主福气安逸和缓", "廉贞": "次桃花，主权柄才艺情绪",
      "天府": "南斗库星，主财富守成稳重", "太阴": "财星，主内敛情感母妻",
      "贪狼": "桃花星，主欲望交际才艺", "巨门": "口舌星，主是非洞察口才",
      "天相": "印星，主协调服务掌印", "天梁": "荫星，主解厄长辈学术",
      "七杀": "将星，主开创决断孤克", "破军": "先锋星，主破耗变革波折",
    };
    return M[name] || name;
  }

  function renderMingli(d) {
    const a = d.analysis, b = d.bazi, z = d.ziwei;
    let h = '<div class="paipan-result mingli">';
    h += '<div class="sec-h">命主总览</div><div class="pp-summary">' +
      '<span>日主 <b>' + esc(a.day_master) + '</b></span>' +
      '<span>强弱 <b>' + esc(a.strength) + '</b></span>' +
      '<span>命宫主星 <b>' + esc(a.ming_gong_stars.join("、") || "—") + '</b></span>' +
      '<span>五行局 <b>' + esc(z.ju) + '</b></span></div>';
    h += '<div class="sec-h">格局分析</div><div class="sec-b">' +
      esc(a.pattern) + '</div>';
    h += '<div class="sec-h">大运走势</div><div class="sec-b">' +
      esc(a.dayun_note) + '</div>';
    // 十神
    h += '<div class="sec-h">四柱十神</div><div class="tag-row">';
    const labels = ["年", "月", "日", "时"];
    b.pillars.forEach((p, i) => {
      h += '<span class="tag">' + labels[i] + '·' + esc(p.gan) + '→' +
        esc(p.gan_shi) + '</span>';
    });
    h += '</div>';
    // 六亲
    h += '<div class="sec-h">六亲定位（以日干为我）</div><table class="liuqin-tbl">' +
      '<tr><th>来源</th><th>天干</th><th>十神</th><th>六亲含义</th></tr>';
    a.liuqin.forEach((q) => {
      h += '<tr><td>' + esc(q.from) + '</td><td>' + esc(q.gan) + '</td><td>' +
        esc(q.shi) + '</td><td>' + esc(q.meaning) + '</td></tr>';
    });
    h += '</table>';
    // 本命卦
    const g = a.benming_gua;
    h += '<div class="sec-h">本命卦</div><div class="sec-b">本卦 <b>' + esc(g.ben) +
      '</b>（' + esc(g.up) + '上' + esc(g.down) + '下），动第' + g.dong_yao +
      '爻，变卦 <b>' + esc(g.bian) + '</b>。</div>';
    // 相关命例
    if (a.related_cases.length) {
      h += '<div class="sec-h">天纪原有八字命例（日主相同 · ' +
        a.related_cases.length + '）</div><ul class="rel-list">';
      a.related_cases.forEach((c) => {
        h += '<li><b>' + esc(c.name) + '</b>　<span class="rel-zhu">' +
          esc(c.zhu) + '</span><div class="rel-snip">' + esc(c.snippet) +
          '</div></li>';
      });
      h += '</ul>';
    }
    // 相关理论
    if (a.related_lilun.length) {
      h += '<div class="sec-h">相关天纪理论（' + a.related_lilun.length +
        '）</div><div class="tag-row">';
      a.related_lilun.forEach((x) => {
        h += '<span class="tag">' + esc(x.name) + '</span>';
      });
      h += '</div>';
    }
    h += '</div>';
    $("#detailPane").innerHTML = h;
  }
