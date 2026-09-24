// -*- coding: utf-8 -*-
// 顶部「系统切换器」：倪海厦各学习系统相互独立，各自为一个独立页面。
// 当前系统由所在页面的 window.SYSTEM 决定（lilun / renji / tianji）。
// 若页面内含 #sysInline 容器，则把切换按钮内联到该处（如人纪 topbar 右侧）；
// 否则回退到 #sysBar 独立渐变条（lilun / tianji / mingli 默认）。
// 注：命理系统（/mingli）已从顶部切换器移除，仅作独立页面（直链访问）。
const SYS_SYSTEMS = [
  { key: "lilun",  name: "论文医案查询系统", url: "/" },
  { key: "renji",  name: "人纪学习系统",          url: "/renji" },
  { key: "tianji", name: "天纪学习系统",          url: "/tianji" },
];

function renderSysBar() {
  const cur = window.SYSTEM || "lilun";
  const tabs = SYS_SYSTEMS.map((s) =>
    `<a class="sys-tab${s.key === cur ? " active" : ""}" href="${s.url}">${s.name}</a>`
  ).join("");

  const inline = document.getElementById("sysInline");
  if (inline) {
    inline.innerHTML = `<nav class="sysbar-tabs sysbar-tabs-inline">${tabs}</nav>`;
    return;
  }
  const bar = document.getElementById("sysBar");
  if (!bar) return;
  bar.innerHTML =
    `<div class="sysbar-inner">` +
      `<div class="sysbar-suite">倪海厦 · 学习系统</div>` +
      `<nav class="sysbar-tabs">${tabs}</nav>` +
    `</div>`;
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", renderSysBar);
} else {
  renderSysBar();
}

// ---- 安全：对 /api 请求自动附加 HMAC 时间戳签名（与 Vercel API_SIGN_SECRET 一致）----
// 说明：前端密钥可被提取，仅能阻挡「裸调接口」的朴素爬虫；真正的防护是服务端
// 限流 + 算法不出服务端 + 私有仓库。生产请在服务端设 API_SIGN_SECRET 启用校验。
// 注意：crypto.subtle 仅在 HTTPS/安全上下文可用；本地 http 开发环境自动跳过签名。
(function () {
  var API_SIGN_SECRET = "c914330990";
  if (!API_SIGN_SECRET) return;
  var _fetch = window.fetch ? window.fetch.bind(window) : null;
  if (!_fetch) return;
  function bufToHex(buf) {
    return Array.prototype.map.call(new Uint8Array(buf),
      function (b) { return ("0" + b.toString(16)).slice(-2); }).join("");
  }
  async function hmacSha256(key, msg) {
    if (!window.crypto || !window.crypto.subtle) return "";
    var enc = new TextEncoder();
    var ck = await crypto.subtle.importKey("raw", enc.encode(key),
      { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
    var sig = await crypto.subtle.sign("HMAC", ck, enc.encode(msg));
    return bufToHex(sig);
  }
  window.fetch = async function (input, init) {
    init = init || {};
    var url = typeof input === "string" ? input : (input && input.url) || "";
    if (url.indexOf("/api") !== -1 && window.crypto && window.crypto.subtle) {
      var ts = String(Math.floor(Date.now() / 1000));
      var q = url.indexOf("?");
      var path = q >= 0 ? url.slice(0, q) : url;
      var sig = await hmacSha256(API_SIGN_SECRET, ts + path);
      init.headers = Object.assign({}, init.headers, { "X-Ts": ts, "X-Sig": sig });
    }
    return _fetch(input, init);
  };
})();

// ---- 布局守卫：下拉菜单视口夹紧（默认左对齐；右溢出→右对齐；仍左溢出→钳制进视口）----
// 修复：靠右的板块（汉唐取穴/动画演示/金匮要略）在窄屏下 left:0 锚定的下拉溢出页面右侧。
window.__clampDD = function (dd) {
  if (!dd || !dd.style) return;
  dd.style.left = ""; dd.style.right = "";
  var vw = document.documentElement.clientWidth;
  var w = dd.offsetWidth;
  if (!w) return;
  var hr = dd.parentElement.getBoundingClientRect();
  if (hr.right + w <= vw - 8) return;              // 默认左对齐放得下
  dd.style.left = "auto"; dd.style.right = "0";    // 翻转为右对齐
  if (hr.left - w >= 8) return;
  var want = Math.max(8, vw - w - 8);              // 两侧都放不下：钳制进视口
  dd.style.left = (want - hr.left) + "px";         // left 相对宿主 tab，需减其视口偏移
  dd.style.right = "auto";
};
