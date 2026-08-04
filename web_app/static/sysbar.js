// -*- coding: utf-8 -*-
// 顶部「系统切换器」：倪海厦三套学习系统相互独立，各自为一个独立页面。
// 当前系统由所在页面的 window.SYSTEM 决定（lilun / renji / tianji）。
const SYS_SYSTEMS = [
  { key: "lilun",  name: "医学论文医案查询系统", url: "/" },
  { key: "renji",  name: "人纪学习系统",          url: "/renji" },
  { key: "tianji", name: "天纪学习系统",          url: "/tianji" },
];

function renderSysBar() {
  const bar = document.getElementById("sysBar");
  if (!bar) return;
  const cur = window.SYSTEM || "lilun";
  const tabs = SYS_SYSTEMS.map((s) =>
    `<a class="sys-tab${s.key === cur ? " active" : ""}" href="${s.url}">${s.name}</a>`
  ).join("");
  bar.innerHTML =
    `<div class="sysbar-inner">` +
      `<div class="sysbar-suite">倪海厦 · 三套学习系统</div>` +
      `<nav class="sysbar-tabs">${tabs}</nav>` +
    `</div>`;
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", renderSysBar);
} else {
  renderSysBar();
}
