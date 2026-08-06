// 通过 Vercel REST API 触发生产部署（CLI 已坏，走 API）。
// 沙箱出网到 api.vercel.com 偶发 ~9s 延迟，连接超时 10s 临界，故加自动重试。
const fs = require("fs");
const os = require("os");

const authPath = `${os.homedir()}/.vercel/auth.json`;
let token = JSON.parse(fs.readFileSync(authPath, "utf8").replace(/^\uFEFF/, "")).token;

const TEAM = "team_AUEOwID6emZlHoTjyvmre3gV";
const SHA = process.argv[2];
const BASE = "https://api.vercel.com";

const headers = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };

async function fetchWithRetry(url, opts, attempts = 4) {
  let lastErr;
  for (let i = 0; i < attempts; i++) {
    try {
      const r = await fetch(url, { ...opts, signal: AbortSignal.timeout(55000) });
      return r;
    } catch (e) {
      lastErr = e;
      console.log(`  fetch attempt ${i + 1} failed: ${e.cause && e.cause.code || e.message}; retrying...`);
      await new Promise((res) => setTimeout(res, 2000));
    }
  }
  throw lastErr;
}

async function postDeploy() {
  const body = {
    name: "finalhopes-learning-system",
    target: "production",
    gitSource: {
      type: "github",
      repoId: 1322853738,
      org: "dmych1989",
      slug: "finalhopes-Learning-System",
      ref: "main",
      sha: SHA,
    },
  };
  const r = await fetchWithRetry(`${BASE}/v13/deployments?teamId=${TEAM}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  const j = await r.json();
  if (!r.ok) { console.log("DEPLOY CREATE FAILED", r.status, JSON.stringify(j)); process.exit(1); }
  return j;
}

async function poll(id) {
  for (let i = 0; i < 60; i++) {
    let j;
    try {
      const r = await fetchWithRetry(`${BASE}/v13/deployments/${id}?teamId=${TEAM}`, { headers });
      j = await r.json();
    } catch (e) {
      console.log(`  poll ${i} fetch error, will retry next loop`);
      await new Promise((res) => setTimeout(res, 5000));
      continue;
    }
    const st = j.status;
    console.log(`[${i}] status=${st}`);
    if (st === "READY") { console.log("READY url=", j.url); return j; }
    if (st === "ERROR" || st === "CANCELED") { console.log("FAILED", JSON.stringify(j).slice(0, 800)); process.exit(1); }
    await new Promise((res) => setTimeout(res, 5000));
  }
  console.log("timeout"); process.exit(1);
}

(async () => {
  const created = await postDeploy();
  console.log("created id=", created.id);
  await poll(created.id);
})();
