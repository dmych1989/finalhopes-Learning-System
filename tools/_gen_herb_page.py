# -*- coding: utf-8 -*-
"""Generate 人纪学习系统/中药查询.html — 神农本草经(上/中/下/增补)+后世本草,
表头刷选标签(神农分类 + 四气), 搜索, 列表 + 详情, 药材图.

数据：ZYX(469 味, 全字段) + shennong.json(神农 上/中/下/增补 382 + 补全 250)
图片：public/img/yaotu (IMG_INDEX 映射) 按药名取最佳形态(药材>原态>饮片>基名)
"""
import os, sys, json, re, shutil

ROOT = r"E:/Soft/倪海夏三套学习系统/QQ频道号talktyph0id/finalhopes-Learning-System"
sys.path.insert(0, os.path.join(ROOT, "web_app"))
import common

OUT_DIR = r"E:/Soft/倪海夏三套学习系统/QQ频道号talktyph0id/人纪学习系统/中药查询"
IMG_DIR = os.path.join(OUT_DIR, "药材图")
os.makedirs(IMG_DIR, exist_ok=True)

# ---------- 1. 加载数据 ----------
HERBS = common.load_dict("ZYX")                      # 469 味, 已解密
HERE = os.path.join(ROOT, "web_app")
SN = json.load(open(os.path.join(HERE, "shennong.json"), encoding="utf-8"))
IMG_INDEX = __import__("img_index", fromlist=["IMG_INDEX"]).IMG_INDEX
YT_MAP = IMG_INDEX.get("yaotu", {})

# 神农 benjing/note 查找：order + missing，按 (name) 归并，优先 (name,cat) 精确
sn_text = {}
for o in SN.get("order", []):
    sn_text.setdefault(o["name"], {})[o.get("cat")] = o
for m in SN.get("missing", []):
    sn_text.setdefault(m["name"], {})[m.get("cat")] = m

_SN_LOOKUP = SN["lookup"]

def _herb_key(name):
    d = _SN_LOOKUP.get(name)
    if d:
        return (d[1], d[2], 0, name)
    return (5, 0, 1, name)

# ---------- 2. 四气 ----------
QI_ORDER = ["大热", "微温", "微寒", "热", "温", "凉", "寒", "平"]
QI_BUCKET = {"大热": "热", "热": "热", "微温": "温", "温": "温",
             "平": "平", "凉": "凉", "微寒": "凉", "寒": "寒"}
def extract_qi(xingneng):
    if not xingneng:
        return ""
    for tok in QI_ORDER:
        if tok in xingneng:
            return QI_BUCKET[tok]
    return ""

# ---------- 3. 图片最佳匹配 ----------
TYPES_PREF = ["药材", "原态", "饮片", ""]   # 优先药材
def best_image(name):
    # 1) 精确基名
    if name in YT_MAP:
        return YT_MAP[name]
    # 2) 带形态后缀：收集所有 <name>-<type>
    cands = []
    for k, fn in YT_MAP.items():
        if k == name:
            cands.append(( "", fn))
        elif k.startswith(name + "-"):
            cands.append((k.split("-", 1)[1], fn))
    if not cands:
        return ""
    # 按偏好排序
    def rank(c):
        t = c[0]
        return TYPES_PREF.index(t) if t in TYPES_PREF else 99
    cands.sort(key=rank)
    return cands[0][1]

# ---------- 4. 组装记录 ----------
def build_record(name, rec, is_shennong_fill=False):
    cat = rec.get("_cat", "其他")
    # 神农本经/注解
    bj, nt = "", ""
    entry = sn_text.get(name, {})
    if cat in entry:
        e = entry[cat]
    elif len(entry) == 1:
        e = next(iter(entry.values()))
    else:
        e = {}
    bj = e.get("benjing", "") or ""
    nt = e.get("note", "") or ""
    xingneng = rec.get("【性能】", "") or ""
    qi = extract_qi(xingneng)
    img = best_image(name)
    rec_out = {
        "n": name,
        "c": cat,
        "s": rec.get("_seq"),
        "cs": rec.get("_cat_seq"),
        "sh": is_shennong_fill,
        "x": xingneng,
        "g": rec.get("【功效】", "") or "",
        "y": rec.get("【用法用量】", "") or "",
        "z": rec.get("【使用注意】", "") or "",
        "j": rec.get("【古籍摘要】", "") or "",
        "m": rec.get("【现代研究】", "") or "",
        "b": rec.get("【简述】", "") or "",
        "bj": bj,
        "nt": nt,
        "qi": qi,
        "img": img,
    }
    return rec_out

# ZYX 药 -> 赋 _cat 后排序
_herb_sorted = []
for name, rec in HERBS.items():
    sn = _SN_LOOKUP.get(name)
    rec = dict(rec)
    rec["_cat"] = (sn[0] if sn else "其他")
    _herb_sorted.append((_herb_key(name), rec))
# 补全(仅神农注解)
for m in SN["missing"]:
    name = m["name"]
    rec = {"MZ": name, "【古籍摘要】": m.get("benjing", ""), "【简述】": m.get("note", ""),
           "_shennong": True, "_cat": m["cat"]}
    _herb_sorted.append((_herb_key(name), rec))
_herb_sorted.sort(key=lambda x: x[0])

# 赋全局序号
_seq = 0; _cat_seq = {}; ordered = []
for key, rec in _herb_sorted:
    cat = rec.get("_cat")
    if cat in ("上经", "中经", "下经", "增补"):
        _seq += 1
        rec["_seq"] = _seq
        _cat_seq[cat] = _cat_seq.get(cat, 0) + 1
        rec["_cat_seq"] = _cat_seq[cat]
    else:
        rec["_seq"] = None
        rec["_cat_seq"] = None
    ordered.append(rec)

records = []
img_copied = 0
for rec in ordered:
    name = rec.get("MZ")
    is_fill = bool(rec.get("_shennong"))
    out = build_record(name, rec, is_fill)
    # 复制图片
    if out["img"]:
        src = os.path.join(ROOT, "public", "img", "yaotu", out["img"])
        if os.path.exists(src):
            dst = os.path.join(IMG_DIR, out["img"])
            if not os.path.exists(dst):
                shutil.copyfile(src, dst)
            img_copied += 1
    records.append(out)

# ---------- 5. 统计 ----------
from collections import Counter
cat_counts = Counter(r["c"] for r in records)
qi_counts = Counter(r["qi"] for r in records if r["qi"])
stats = {
    "total": len(records),
    "cats": {c: cat_counts.get(c, 0) for c in ["上经", "中经", "下经", "增补", "其他"]},
    "qi": dict(qi_counts),
    "with_img": sum(1 for r in records if r["img"]),
}
print("records:", len(records))
print("cat counts:", stats["cats"])
print("qi counts:", stats["qi"])
print("with image:", stats["with_img"], "/ copied this run:", img_copied)

# 写出数据 JSON（供核对/二次使用）
json.dump(records, open(os.path.join(OUT_DIR, "herbs.json"), "w", encoding="utf-8"),
          ensure_ascii=False)

# ---------- 6. 生成 HTML ----------
html = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>中药查询 · 神农本草经</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
:root { --teal:#2d5a4f; --teal-d:#1f4038; --bg:#f5f1e8; --card:#fff; --line:#e0d8c0; --ink:#222; --mut:#8a8472; --red:#c0392b; }
body { font-family: -apple-system,"Microsoft YaHei",sans-serif; background: var(--bg); color: var(--ink); }
header { background: var(--teal); color:#fff; padding: 12px 18px; display:flex; align-items:baseline; gap:12px; flex-wrap:wrap; }
header h1 { font-size: 18px; }
header p { font-size: 12px; opacity:.85; }
.wrap { display:grid; grid-template-columns: 1fr 380px; height: calc(100vh - 56px); }
@media (max-width: 880px) { .wrap { grid-template-columns: 1fr; height:auto; } .detail { min-height:60vh; order:-1; } }

/* 表头刷选标签 */
.toolbar { padding: 10px 14px; background:#efe9da; border-bottom:1px solid var(--line); position:sticky; top:0; z-index:5; }
.search { width:100%; padding:8px 10px; border:1px solid var(--line); border-radius:6px; font-size:14px; margin-bottom:8px; }
.ftitle { font-size:11px; color:var(--mut); margin:4px 0 4px; }
.ftags { display:flex; flex-wrap:wrap; gap:6px; }
.ftag { border:1px solid var(--line); background:#fff; color:#444; padding:4px 10px; border-radius:14px; font-size:12px; cursor:pointer; transition:.12s; }
.ftag:hover { border-color:var(--teal); }
.ftag.active { background:var(--teal); color:#fff; border-color:var(--teal); }
.ftag .ct { opacity:.7; margin-left:3px; font-size:11px; }

.list { overflow-y:auto; padding:10px 12px; }
.item { background:var(--card); border:1px solid var(--line); border-radius:6px; padding:9px 11px; margin-bottom:8px; cursor:pointer; transition:.12s; }
.item:hover { box-shadow:0 2px 7px rgba(0,0,0,.1); transform:translateY(-1px); }
.item.active { outline:2px solid var(--teal); }
.item .top { display:flex; align-items:center; gap:8px; }
.item .nm { font-size:15px; font-weight:bold; }
.badge { font-size:10px; padding:1px 6px; border-radius:8px; background:var(--teal); color:#fff; white-space:nowrap; }
.badge.fill { background:var(--red); }
.badge.other { background:#9a9486; }
.item .qi { font-size:11px; color:var(--mut); margin-left:auto; }
.item .gx { font-size:12px; color:#555; margin-top:3px; line-height:1.4; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }

.detail { border-left:1px solid var(--line); background:#26241f; color:#eee; overflow-y:auto; }
.detail .ph { padding:14px; }
.detail .ph .nm { font-size:20px; font-weight:bold; color:#fff; }
.detail .seq { font-size:12px; color:#f0c674; margin:6px 0; }
.detail .row { margin-top:12px; }
.detail .row .k { font-size:12px; color:#9fd3c4; font-weight:bold; margin-bottom:3px; }
.detail .row .v { font-size:13px; line-height:1.7; color:#e7e3d8; white-space:pre-wrap; }
.detail img.herb { max-width:100%; border-radius:6px; margin-top:10px; background:#fff; display:block; }
.detail .empty { color:#9b957a; text-align:center; padding:40px 10px; font-size:14px; line-height:1.8; }
.hl { background:#fff3b0; }
</style>
</head>
<body>
<header>
  <h1>中药查询 · 神农本草经</h1>
  <p>上经 / 中经 / 下经 / 增补（共 __OTAL__ 味）· 表头刷选标签筛选 · 点击查看详情</p>
</header>

<div class="wrap">
  <div class="left">
    <div class="toolbar">
      <input id="search" class="search" type="text" placeholder="搜索药名 / 功效 / 性味…" autocomplete="off">
      <div class="ftitle">神农本草经分类</div>
      <div class="ftags" id="catTags"></div>
      <div class="ftitle">四气（性味）</div>
      <div class="ftags" id="qiTags"></div>
    </div>
    <div class="list" id="list"></div>
  </div>
  <div class="detail" id="detail">
    <div class="empty">点击左侧中药查看详情<br>（神农本经原文 · 倪师注解 · 药材图）</div>
  </div>
</div>

<script>
const HERBS = __HERBS__;
const CATS = ["上经","中经","下经","增补","其他"];
const QIS = ["热","温","平","凉","寒"];

let curCat = "", curQi = "", curQ = "";
let activeIdx = null;

const catTags = document.getElementById('catTags');
const qiTags = document.getElementById('qiTags');
const listEl = document.getElementById('list');
const detailEl = document.getElementById('detail');
const searchEl = document.getElementById('search');

function countCat(c){ return HERBS.filter(h=> c==="" ? true : h.c===c).length; }
function countQi(q){ return HERBS.filter(h=> q==="" ? true : h.qi===q).length; }

function renderTags(){
  catTags.innerHTML = "";
  [["", "全部"]].concat(CATS.map(c=>[c,c])).forEach(([k,label])=>{
    const b=document.createElement('button');
    b.className='ftag'+(k===curCat?' active':'');
    b.innerHTML = label + '<span class="ct">'+countCat(k)+'</span>';
    b.onclick=()=>{ curCat=k; renderTags(); renderList(); };
    catTags.appendChild(b);
  });
  qiTags.innerHTML = "";
  [["", "全部"]].concat(QIS.map(q=>[q,q])).forEach(([k,label])=>{
    const b=document.createElement('button');
    b.className='ftag'+(k===curQi?' active':'');
    b.innerHTML = label + '<span class="ct">'+countQi(k)+'</span>';
    b.onclick=()=>{ curQi=k; renderTags(); renderList(); };
    qiTags.appendChild(b);
  });
}

function esc(s){ return (s||"").replace(/[&<>]/g, m=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[m])); }
function hl(s, q){
  s = s||"";
  if(!q) return esc(s);
  try { return esc(s).replace(new RegExp('('+q.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+')','gi'),'<span class="hl">$1</span>'); }
  catch(e){ return esc(s); }
}

function filtered(){
  const q = curQ.trim().toLowerCase();
  return HERBS.filter(h=>{
    if(curCat && h.c!==curCat) return false;
    if(curQi && h.qi!==curQi) return false;
    if(q){
      const hay = (h.n+' '+(h.g||'')+' '+(h.x||'')+' '+(h.b||'')+' '+(h.bj||'')).toLowerCase();
      if(!hay.includes(q)) return false;
    }
    return true;
  });
}

function renderList(){
  const data = filtered();
  listEl.innerHTML = "";
  if(!data.length){ listEl.innerHTML='<div style="padding:20px;color:#888;text-align:center">无匹配结果</div>'; return; }
  const q = curQ.trim();
  data.forEach((h, i)=>{
    const d=document.createElement('div');
    d.className='item'+(activeIdx!==null && HERBS[activeIdx]===h?' active':'');
    const badgeCls = h.sh ? 'badge fill' : (h.c==='其他' ? 'badge other' : 'badge');
    const badgeTxt = h.sh ? '神农·补全' : (h.c==='其他' ? '后世本草' : h.c);
    d.innerHTML =
      '<div class="top"><span class="nm">'+esc(h.n)+'</span>'+
      '<span class="'+badgeCls+'">'+badgeTxt+'</span>'+
      (h.qi?'<span class="qi">'+esc(h.qi)+'</span>':'')+'</div>'+
      '<div class="gx">'+(h.g? hl(h.g,q) : (h.bj? hl(h.bj,q):''))+'</div>';
    d.onclick=()=> show(h);
    listEl.appendChild(d);
  });
}

function show(h){
  activeIdx = HERBS.indexOf(h);
  document.querySelectorAll('.item').forEach(el=>el.classList.remove('active'));
  // 高亮当前（重新渲染后由 className 处理；这里直接找匹配）
  renderList();
  const seqLine = (h.c!=='其他' && h.s!=null)
    ? '<div class="seq">《神农本草经》· '+esc(h.c)+' · 本经第 '+h.cs+' 味（全书总第 '+h.s+' 味）</div>'
    : (h.sh ? '<div class="seq">神农本草经 · 补全（仅存本经原文与倪师注解）</div>' : '<div class="seq">后世本草（非神农本经收录）</div>');
  let html = '<div class="ph"><div class="nm">'+esc(h.n)+'</div>'+seqLine;
  const rows = [
    ['性能（性味归经）', h.x],
    ['功效', h.g],
    ['用法用量', h.y],
    ['使用注意', h.z],
    ['神农本经原文', h.bj],
    ['倪师注解', h.nt],
    ['古籍摘要', h.j],
    ['现代研究', h.m],
    ['简述', h.b],
  ];
  rows.forEach(([k,v])=>{
    if(v && v.trim()) html += '<div class="row"><div class="k">'+k+'</div><div class="v">'+hl(v, curQ.trim())+'</div></div>';
  });
  if(h.img){
    html += '<img class="herb" src="药材图/'+esc(h.img)+'" alt="'+esc(h.n)+'" onerror="this.style.display=\'none\'">';
  }
  html += '</div>';
  detailEl.innerHTML = html;
}

searchEl.addEventListener('input', ()=>{ curQ = searchEl.value; renderList(); });
renderTags();
renderList();
</script>
</body>
</html>
"""

html = html.replace("__OTAL__", str(stats["total"]))
html = html.replace("__HERBS__", json.dumps(records, ensure_ascii=False))
fp = os.path.join(OUT_DIR, "中药查询.html")
open(fp, "w", encoding="utf-8").write(html)
print("\n生成:", fp, "(", len(html), "chars )")
