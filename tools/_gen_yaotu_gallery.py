# -*- coding: utf-8 -*-
"""Generate 人纪学习系统/中药查询/药图列表.html
A herb-image gallery: left = responsive square-thumbnail + name grid (药图列表),
right = enlarged preview that adapts to page width. Mirrors 倪师取穴图表.html
but uses the 467 herb jpgs in 药材图/. Images are referenced by relative path
(药材图/<file>) so the HTML stays tiny.
"""
import os, re, json

BASE = r"E:/Soft/倪海夏三套学习系统/QQ频道号talktyph0id"
SRC_DIR = os.path.join(BASE, "人纪学习系统/中药查询/药材图")
OUT = os.path.join(BASE, "人纪学习系统/中药查询/药图列表.html")

SUFFIX_RE = re.compile(r"[-_ ]?(原态|药材|饮片|植物|花|果实|根|叶|全草|炮制)$")

def clean_name(fn):
    base = fn[:-4]
    base = SUFFIX_RE.sub("", base)
    return base

def main():
    files = [f for f in os.listdir(SRC_DIR) if f.lower().endswith(".jpg")]
    files.sort(key=lambda f: clean_name(f))
    charts = []
    for f in files:
        charts.append({"n": clean_name(f), "f": "药材图/" + f})
    print("images:", len(charts))

    data_json = json.dumps(charts, ensure_ascii=False)

    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>药图列表 · 中药图鉴</title>
<style>
  :root{
    --teal:#0f766e; --teal-d:#115e59; --teal-l:#ccfbf1;
    --bg:#f3f7f6; --card:#fff; --line:#d8e6e3; --txt:#1f2d2b; --mut:#6b7d7a;
  }
  *{box-sizing:border-box}
  body{margin:0;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;
    background:var(--bg);color:var(--txt);}
  header{background:linear-gradient(135deg,var(--teal),var(--teal-d));color:#fff;
    padding:14px 20px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;}
  header h1{margin:0;font-size:19px;letter-spacing:1px}
  header .cnt{font-size:13px;opacity:.85}
  #search{border:0;border-radius:20px;padding:8px 16px;font-size:14px;min-width:200px;
    outline:2px solid transparent;background:#fff;color:var(--txt)}
  #search:focus{outline:2px solid var(--teal-l)}
  .wrap{display:flex;gap:0;align-items:stretch;min-height:calc(100vh - 58px)}
  .left{flex:0 0 62%;max-width:62%;border-right:1px solid var(--line);
    padding:16px;overflow-y:auto;max-height:calc(100vh - 58px)}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(108px,1fr));
    gap:12px}
  .item{background:var(--card);border:1px solid var(--line);border-radius:10px;
    overflow:hidden;cursor:pointer;transition:.15s;display:flex;flex-direction:column}
  .item:hover{transform:translateY(-2px);box-shadow:0 6px 16px rgba(15,118,110,.18);
    border-color:var(--teal)}
  .item.active{border-color:var(--teal);box-shadow:0 0 0 3px var(--teal-l)}
  .item .thumb{aspect-ratio:1/1;width:100%;background:#eef4f3;overflow:hidden}
  .item .thumb img{width:100%;height:100%;object-fit:cover;display:block}
  .item .cap{padding:7px 6px;font-size:13px;line-height:1.3;text-align:center;
    border-top:1px solid var(--line);min-height:38px;display:flex;align-items:center;
    justify-content:center}
  .right{flex:1 1 38%;min-width:0;padding:16px;display:flex;flex-direction:column;
    background:#fff}
  .preview{flex:1;display:flex;align-items:center;justify-content:center;
    background:#0b1f1c;border-radius:12px;overflow:hidden;min-height:320px;padding:14px}
  .preview img{max-width:100%;width:100%;height:auto;display:block;
    border-radius:8px;box-shadow:0 8px 30px rgba(0,0,0,.4)}
  .pname{margin:12px 2px 4px;font-size:18px;font-weight:600;color:var(--teal-d);
    text-align:center}
  .phint{font-size:12px;color:var(--mut);text-align:center}
  .empty{color:var(--mut);text-align:center;padding:40px 0}
  @media (max-width:820px){
    .wrap{flex-direction:column}
    .left,.right{max-width:100%;flex:none;border-right:0}
    .left{max-height:none}
    .right{border-top:1px solid var(--line)}
  }
</style>
</head>
<body>
<header>
  <h1>药图列表 · 中药图鉴</h1>
  <span class="cnt" id="cnt"></span>
  <input id="search" placeholder="搜索药名…" autocomplete="off">
</header>
<div class="wrap">
  <div class="left">
    <div class="grid" id="grid"></div>
    <div class="empty" id="empty" style="display:none">未找到匹配的药图</div>
  </div>
  <div class="right">
    <div class="preview"><img id="big" alt=""></div>
    <div class="pname" id="pname"></div>
    <div class="phint">点击左侧缩略图查看大图 · ← / → 键切换</div>
  </div>
</div>
<script>
const CHARTS = __DATA__;
const grid=document.getElementById('grid');
const big=document.getElementById('big');
const pname=document.getElementById('pname');
const cnt=document.getElementById('cnt');
const empty=document.getElementById('empty');
const search=document.getElementById('search');
let view=[];   // currently visible indices into CHARTS
let cur=-1;

function render(list){
  view=list;
  grid.innerHTML='';
  if(list.length===0){empty.style.display='block';cnt.textContent='';return;}
  empty.style.display='none';
  cnt.textContent='共 '+list.length+' 张';
  list.forEach((i,pos)=>{
    const c=CHARTS[i];
    const d=document.createElement('div');
    d.className='item';
    d.dataset.pos=pos;
    d.innerHTML='<div class="thumb"><img loading="lazy" src="'+c.f+'" alt="'+c.n+'"></div>'
      +'<div class="cap">'+c.n+'</div>';
    d.onclick=()=>show(pos);
    grid.appendChild(d);
  });
}
function show(pos){
  if(pos<0||pos>=view.length)return;
  cur=pos;
  const c=CHARTS[view[pos]];
  big.src=c.f;
  pname.textContent=c.n;
  document.querySelectorAll('.item').forEach(e=>e.classList.remove('active'));
  const el=grid.querySelector('.item[data-pos="'+pos+'"]');
  if(el){el.classList.add('active');el.scrollIntoView({block:'nearest'});}
}
search.oninput=()=>{
  const q=search.value.trim();
  const list=[];
  CHARTS.forEach((c,i)=>{if(!q||c.n.indexOf(q)>=0)list.push(i);});
  render(list);
  if(list.length)show(0);
};
document.addEventListener('keydown',e=>{
  if(e.key==='ArrowRight')show(Math.min(cur+1,view.length-1));
  if(e.key==='ArrowLeft')show(Math.max(cur-1,0));
});
// init
render(CHARTS.map((_,i)=>i));
if(view.length)show(0);
</script>
</body>
</html>
"""
    html = html.replace("__DATA__", data_json)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(html)
    print("wrote:", OUT, "sizeKB=%.1f" % (os.path.getsize(OUT)/1024))

if __name__ == "__main__":
    main()
