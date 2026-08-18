# -*- coding: utf-8 -*-
"""Organize all text + images from 人纪针灸 EXE/MDB into 人纪学习系统/.

Sources:
  EXE  = 倪海厦汉唐中医馆人纪针灸内部学习系统V2022.exe  (images, menu text)
  MDB  = Data/LILUN.mdb  (pwd JiSkS92A30; ciphered XOR-0x0F + GBK RTF)
         tables used:
           - nishixuewei (357 穴 · 14 经 · 文字)  → 十二经络与奇经八脉/<经>/
           - nishitu (63 倪师图表)                  → 倪师傅经验/针灸穴位总结图表/

Outputs (under ROOT):
  十二经络与奇经八脉/
    目录.txt (existing)
    <14 经>/
      穴位列表.txt
      <穴名>.txt
      穴位图.txt
    人体穴位图/  (EXE 全身经络穴位图)
    十四经络穴位.json
  倪师傅经验/
    目录.txt (existing)
    针刺手法/   (EXE 手法图 + 倪师照片)
    针灸穴位总结图表/  (MDB nishitu 63 图)
  README.md
"""
import os, sys, re, json, struct

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "web_app"))
import common

ROOT = r"E:/Soft/倪海夏三套学习系统/QQ频道号talktyph0id/人纪学习系统"
MDB  = os.path.join(ROOT, "Data", "LILUN.mdb")
EXE  = os.path.join(ROOT, "倪海厦汉唐中医馆人纪针灸内部学习系统V2022.exe")
PWD  = "JiSkS92A30"

common.DB = MDB
common.PWD = PWD
common.USE_SQLITE = False

# 14 经目录顺序（与用户 目录.txt 一致：任脉经穴/督脉经穴/十二正经）
DIR_ORDER = [
    "手太阴肺经","手阳明大肠经","足阳明胃经","足太阴脾经",
    "手少阴心经","手太阳小肠经","足太阳膀胱经","足少阴肾经",
    "手厥阴心包经","手少阳三焦经","足少阳胆经","足厥阴肝经",
    "任脉经穴","督脉经穴",
]

# 标准 361 穴 → 经脉（国标）
MERIDIANS = {
 "手太阴肺经": ["中府","云门","天府","侠白","尺泽","孔最","列缺","经渠","太渊","鱼际","少商"],
 "手阳明大肠经": ["商阳","二间","三间","合谷","阳溪","偏历","温溜","下廉","上廉","手三里","曲池","肘髎","手五里","臂臑","肩髃","巨骨","天鼎","扶突","口禾髎","迎香"],
 "足阳明胃经": ["承泣","四白","巨髎","地仓","大迎","颊车","下关","头维","人迎","水突","气舍","缺盆","气户","库房","屋翳","膺窗","乳中","乳根","不容","承满","梁门","关门","太乙","滑肉门","天枢","外陵","大巨","水道","归来","气冲","髀关","伏兔","阴市","梁丘","犊鼻","足三里","上巨虚","条口","下巨虚","丰隆","解溪","冲阳","陷谷","内庭","厉兑"],
 "足太阴脾经": ["隐白","大都","太白","公孙","商丘","三阴交","漏谷","地机","阴陵泉","血海","箕门","冲门","府舍","腹结","大横","腹哀","食窦","天溪","胸乡","周荣","大包"],
 "手少阴心经": ["极泉","青灵","少海","灵道","通里","阴郄","神门","少府","少冲"],
 "手太阳小肠经": ["少泽","前谷","后溪","腕骨","阳谷","养老","支正","小海","肩贞","臑俞","天宗","秉风","曲垣","肩外俞","肩中俞","天窗","天容","颧髎","听宫"],
 "足太阳膀胱经": ["睛明","攒竹","眉冲","曲差","五处","承光","通天","络却","玉枕","天柱","大杼","风门","肺俞","厥阴俞","心俞","督俞","膈俞","肝俞","胆俞","脾俞","胃俞","三焦俞","肾俞","气海俞","大肠俞","关元俞","小肠俞","膀胱俞","中膂俞","白环俞","上髎","次髎","中髎","下髎","会阳","承扶","殷门","浮郄","委阳","委中","附分","魄户","膏肓","神堂","譩譆","膈关","魂门","阳纲","意舍","胃仓","肓门","志室","胞肓","秩边","合阳","承筋","承山","飞扬","跗阳","昆仑","仆参","申脉","金门","京骨","束骨","足通谷","至阴"],
 "足少阴肾经": ["涌泉","然谷","太溪","大钟","水泉","照海","复溜","交信","筑宾","阴谷","横骨","大赫","气穴","四满","中注","肓俞","商曲","石关","阴都","通谷","幽门","步廊","神封","灵墟","神藏","彧中","俞府"],
 "手厥阴心包经": ["天池","天泉","曲泽","郄门","间使","内关","大陵","劳宫","中冲"],
 "手少阳三焦经": ["关冲","液门","中渚","阳池","外关","支沟","会宗","三阳络","四渎","天井","清冷渊","消泺","臑会","肩髎","天髎","天牖","翳风","瘈脉","颅息","角孙","耳门","耳和髎","丝竹空"],
 "足少阳胆经": ["瞳子髎","听会","上关","颔厌","悬颅","悬厘","曲鬓","率谷","天冲","浮白","头窍阴","完骨","本神","阳白","头临泣","目窗","正营","承灵","脑空","风池","肩井","渊腋","辄筋","日月","京门","带脉","五枢","维道","居髎","环跳","风市","中渎","膝阳关","阳陵泉","阳交","外丘","光明","阳辅","悬钟","丘墟","足临泣","地五会","侠溪","足窍阴"],
 "足厥阴肝经": ["大敦","行间","太冲","中封","蠡沟","中都","膝关","曲泉","阴包","足五里","阴廉","急脉","章门","期门"],
 "任脉": ["会阴","曲骨","中极","关元","石门","气海","阴交","神阙","水分","下脘","建里","中脘","上脘","巨阙","鸠尾","中庭","膻中","玉堂","紫宫","华盖","璇玑","天突","廉泉","承浆"],
 "督脉": ["长强","腰俞","腰阳关","命门","悬枢","脊中","中枢","筋缩","至阳","灵台","神道","身柱","陶道","大椎","哑门","风府","脑户","强间","后顶","百会","前顶","囟会","上星","神庭","素髎","水沟","兑端","龈交"],
}

# 别名（DB 简称 → 标准穴名→经脉）
ALIASES = {
    "和髎": "手少阳三焦经",   # DB「（耳）和髎」= 耳和髎
    "腹通": "足少阴肾经",     # 腹通谷
    "足窍": "足少阳胆经",     # 足窍阴
}

# 目录.txt → 经脉键
DIR_TO_MER = {
    "手太阴肺经":"手太阴肺经","手阳明大肠经":"手阳明大肠经","足阳明胃经":"足阳明胃经",
    "足太阴脾经":"足太阴脾经","手少阴心经":"手少阴心经","手太阳小肠经":"手太阳小肠经",
    "足太阳膀胱经":"足太阳膀胱经","足少阴肾经":"足少阴肾经","手厥阴心包经":"手厥阴心包经",
    "手少阳三焦经":"手少阳三焦经","足少阳胆经":"足少阳胆经","足厥阴肝经":"足厥阴肝经",
    "任脉经穴":"任脉","督脉经穴":"督脉",
}

def safe_fn(name):
    """safe filename (Windows)."""
    s = re.sub(r'[\\/:*?"<>|]', '_', name)
    return s.strip() or "_"

def norm(name):
    n = name.strip()
    n = re.sub(r"[（(].*?[)）]", "", n)
    return n.strip()

def build_rev():
    rev = {}
    for mer, pts in MERIDIANS.items():
        for p in pts:
            rev.setdefault(p, mer)
    for k, v in ALIASES.items():
        rev.setdefault(k, v)
    return rev

# ============== 1. 解密穴位文字，按 14 经整理 ==============
def decrypt_acupoints(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM [nishixuewei]")
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    recs = []
    for r in rows:
        d = {cols[i]: common.text_of(cols[i], r[i], "nishixuewei") for i in range(len(cols))}
        d["_MZ"] = d.get("MZ", "")
        d["_norm"] = norm(d["_MZ"])
        recs.append(d)
    return recs

def group_by_meridian(recs, rev):
    groups = {m: [] for m in MERIDIANS}
    orphans = []
    for r in recs:
        key = r["_norm"]
        mer = rev.get(key)
        if mer is None:
            orphans.append(r)
            continue
        # ensure ordered list of fields kept
        groups[mer].append(r)
    # sort each meridian by standard sequence
    for mer in groups:
        order = {p: i for i, p in enumerate(MERIDIANS[mer])}
        groups[mer].sort(key=lambda x: order.get(x["_norm"], 9999))
    return groups, orphans

def write_meridian_folders(groups):
    jingluo_root = os.path.join(ROOT, "十二经络与奇经八脉")
    os.makedirs(jingluo_root, exist_ok=True)
    # body image paths (relative to jingluo_root)
    body_dir = os.path.join(jingluo_root, "人体穴位图")
    body_imgs = ["人体穴位图/全身背面经络穴位图.jpg",
                 "人体穴位图/全身侧面经络穴位图.jpg",
                 "人体穴位图/背部经络图.jpg"]
    body_text = ("人体穴位图（EXE 提取，全身经络穴位图，置于右侧栏）：\n"
                 + "\n".join(f"  - {p}" for p in body_imgs) + "\n")

    summary = {}
    for dir_name in DIR_ORDER:
        mer = DIR_TO_MER[dir_name]
        acupoints = groups.get(mer, [])
        if not acupoints: continue
        d = os.path.join(jingluo_root, dir_name)
        os.makedirs(d, exist_ok=True)
        # 穴位列表.txt
        with open(os.path.join(d, "穴位列表.txt"), "w", encoding="utf-8") as f:
            f.write(f"{dir_name} · 穴位列表（{len(acupoints)} 穴，按经脉循行顺序）\n")
            f.write("=" * 50 + "\n")
            for i, a in enumerate(acupoints, 1):
                f.write(f"  {i:2d}. {a['_MZ']}\n")
        # 每个穴位 .txt
        # 字段顺序（人纪软件原书格式）
        FIELDS = ["【别名】","【定位】","【解剖】","【主治】","【穴义】","【刺灸】",
                  "【备注】","【配伍】","【特征】","【规律】","【名词解析】","【倪师注解】","【治法】"]
        for a in acupoints:
            fn = safe_fn(a["_MZ"]) + ".txt"
            with open(os.path.join(d, fn), "w", encoding="utf-8") as f:
                f.write(f"{a['_MZ']}（{dir_name}）\n")
                f.write("=" * 50 + "\n\n")
                for k in FIELDS:
                    v = a.get(k, "").strip()
                    if v:
                        f.write(f"{k}\n{v}\n\n")
                # 若所有字段空，保留空文本
        # 穴位图.txt
        with open(os.path.join(d, "穴位图.txt"), "w", encoding="utf-8") as f:
            f.write(body_text)
        summary[dir_name] = len(acupoints)
    return summary, body_imgs

# ============== 2. 主索引 JSON ==============
def write_master_json(groups, body_imgs):
    jingluo_root = os.path.join(ROOT, "十二经络与奇经八脉")
    out = {
        "meta": {
            "title": "十四经络穴位",
            "source": "倪海厦汉唐中医馆人纪针灸内部学习系统V2022",
            "extracted_from": {"MDB": "Data/LILUN.mdb · table nishixuewei",
                                "EXE": "倪海厦汉唐中医馆人纪针灸内部学习系统V2022.exe"},
            "encoding": "XOR-0x0F cipher + GBK RTF (decrypted via common.py)",
            "total_meridians": 14,
            "total_acupoints_in_db": sum(len(v) for v in groups.values()),
            "layout": "左=穴位列表 · 中=穴位详情 · 右=人体穴位图",
        },
        "meridians": [],
        "body_images": body_imgs,
    }
    for dir_name in DIR_ORDER:
        mer = DIR_TO_MER[dir_name]
        acs = groups.get(mer, [])
        out["meridians"].append({
            "name": dir_name,
            "folder": dir_name,
            "count": len(acs),
            "acupoints": [
                {"name": a["_MZ"],
                 "list_path": f"{dir_name}/穴位列表.txt",
                 "detail_path": f"{dir_name}/{safe_fn(a['_MZ'])}.txt",
                 **{k.strip("【】"): a.get(k, "").strip() for k in [
                     "【别名】","【定位】","【解剖】","【主治】","【穴义】","【刺灸】",
                     "【备注】","【配伍】","【特征】","【规律】","【名词解析】","【倪师注解】","【治法】"]
                    }}
                for a in acs
            ],
        })
    with open(os.path.join(jingluo_root, "十四经络穴位.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    return out

# ============== 3. EXE 图片抽取 ==============
def parse_jpeg(buf):
    if buf[:3] != b'\xff\xd8\xff': return None
    i = 2; w = h = None
    while i < len(buf)-1:
        if buf[i] != 0xFF: i += 1; continue
        m = buf[i+1]
        if m in (0xD8,0xD9) or 0xD0 <= m <= 0xD7: i += 2; continue
        if m == 0xDA:
            e = buf.find(b'\xff\xd9', i)
            if e < 0: return None
            return (2, e+2, w, h)
        if m in (0xC0,0xC1,0xC2,0xC3):
            h = struct.unpack('>H', buf[i+5:i+7])[0]
            w = struct.unpack('>H', buf[i+7:i+9])[0]
            seg = struct.unpack('>H', buf[i+2:i+4])[0]; i += 2 + seg; continue
        if m == 0xD9: break
        seg = struct.unpack('>H', buf[i+2:i+4])[0]
        if seg <= 0: break
        i += 2 + seg
    return None

def extract_all_jpgs(exe_data):
    out = []
    start = 0
    while True:
        i = exe_data.find(b'\xff\xd8\xff', start)
        if i < 0: break
        r = parse_jpeg(exe_data[i:i+800000])
        if r:
            out.append((i, r[1], r[2], r[3]))
        start = i + 1
    return out

def extract_exe_images():
    """Extract body diagrams → 人体穴位图/; technique + photo → 倪师傅经验/."""
    body_dir = os.path.join(ROOT, "十二经络与奇经八脉", "人体穴位图")
    os.makedirs(body_dir, exist_ok=True)
    tech_dir = os.path.join(ROOT, "倪师傅经验", "针刺手法")
    os.makedirs(tech_dir, exist_ok=True)

    data = open(EXE, "rb").read()
    jpgs = extract_all_jpgs(data)

    # 全身图（高≥1000px）：去重，按尺寸排序
    big = sorted({(w,h,off,ln) for off,ln,w,h in jpgs if (h and h>=1000)}, key=lambda x:(x[0],x[1]))
    # 已知 2 张唯一：1278x2304（背面）+ 1283x2304（侧面）；其他为重复
    body_map = {
        (1278,2304): "全身背面经络穴位图.jpg",
        (1283,2304): "全身侧面经络穴位图.jpg",
    }
    seen_body = set()
    for (w,h,off,ln) in big:
        key = (w,h)
        if key in body_map and key not in seen_body:
            open(os.path.join(body_dir, body_map[key]), "wb").write(data[off:off+ln])
            seen_body.add(key)

    # 背部经络图（89x160）也归人体穴位图（首个实例）
    for off,ln,w,h in jpgs:
        if w==89 and h==160:
            open(os.path.join(body_dir, "背部经络图.jpg"), "wb").write(data[off:off+ln])
            break

    # 针刺手法图（中等尺寸，非全身） + 倪师照片（178x178）
    # 已识别：220x130, 300x168, 330x164, 334x148, 178x178
    tech_map = {
        (220,130): "痰闭针孔针刺图.jpg",
        (300,168): "山火透天凉手法图.jpg",
        (330,164): "眼针呼气手法图.jpg",
        (334,148): "进针手法图(呼气吸气).jpg",
    }
    seen_tech = set()
    for off,ln,w,h in jpgs:
        key = (w,h)
        if key in tech_map and key not in seen_tech:
            open(os.path.join(tech_dir, tech_map[key]), "wb").write(data[off:off+ln])
            seen_tech.add(key)
        if w==178 and h==178:
            open(os.path.join(ROOT, "倪师傅经验", "倪海厦师父照片.jpg"), "wb").write(data[off:off+ln])

    return {
        "body": sorted(os.listdir(body_dir)),
        "technique": sorted(os.listdir(tech_dir)),
        "photo": "倪海厦师父照片.jpg" if os.path.exists(os.path.join(ROOT, "倪师傅经验", "倪海厦师父照片.jpg")) else None,
    }

# ============== 4. MDB nishitu → 倪师傅经验/针灸穴位总结图表/ ==============
def extract_nishitu_charts(conn):
    target = os.path.join(ROOT, "倪师傅经验", "针灸穴位总结图表")
    os.makedirs(target, exist_ok=True)
    cur = conn.cursor()
    cur.execute("SELECT MZ, NR FROM [nishitu]")
    saved = []
    failed = []
    # read row-by-row to avoid fetchall() choking on large blobs; skip bad rows
    while True:
        try:
            row = cur.fetchone()
        except Exception as e:
            failed.append(("FETCH", str(e)[:80]))
            break
        if row is None:
            break
        mz, nr = row[0], row[1]
        if not isinstance(nr, (bytes, bytearray)) or len(nr) < 100:
            continue
        try:
            plain = common.decrypt_bytes(nr)
        except Exception as e:
            failed.append((mz, "decrypt:"+str(e)[:60]))
            continue
        if plain[:3] != b'\xff\xd8\xff':
            failed.append((mz, "not-jpeg-after-decrypt"))
            continue
        fn = safe_fn(mz) + ".jpg"
        path = os.path.join(target, fn)
        try:
            open(path, "wb").write(plain)
            saved.append((mz, fn))
        except Exception as e:
            failed.append((mz, "write:"+str(e)[:60]))
    # 索引
    with open(os.path.join(target, "索引.txt"), "w", encoding="utf-8") as f:
        f.write(f"针灸穴位总结图表（倪师图，来自 MDB nishitu 表）  成功 {len(saved)} / 失败 {len(failed)}\n")
        f.write("=" * 60 + "\n\n")
        for mz, fn in saved:
            f.write(f"  {mz}  →  {fn}\n")
        if failed:
            f.write(f"\n失败 {len(failed)} 项：\n")
            for mz, why in failed:
                f.write(f"  ! {mz}  ({why})\n")
    return saved

# ============== 5. README ==============
def write_readme(stats, imgs, charts):
    readme = os.path.join(ROOT, "README.md")
    with open(readme, "w", encoding="utf-8") as f:
        f.write("# 人纪学习系统 · 内容整理索引\n\n")
        f.write("> 自动从 `倪海厦汉唐中医馆人纪针灸内部学习系统V2022.exe` 与 `Data/LILUN.mdb` 解密提取，按用户已建子目录整理。\n\n")
        f.write("## 一、十二经络与奇经八脉（十四经络穴位 · 主线）\n\n")
        f.write("布局：**左 = 穴位列表 · 中 = 穴位详情 · 右 = 人体穴位图**\n\n")
        f.write("| 经脉 | 穴位数 | 列表 | 详情 | 经络图 |\n|---|---|---|---|---|\n")
        body_imgs = ["人体穴位图/全身背面经络穴位图.jpg",
                     "人体穴位图/全身侧面经络穴位图.jpg",
                     "人体穴位图/背部经络图.jpg"]
        for dir_name, cnt in stats.items():
            f.write(f"| {dir_name} | {cnt} | `穴位列表.txt` | `<穴名>.txt` | {', '.join(body_imgs)} |\n")
        total = sum(stats.values())
        f.write(f"\n合计 {len(stats)} 经 · **{total} 穴**（MDB 含 {total}；国标 361，差 {361-total} 个标准穴未在本软件库中）\n\n")
        f.write("- 主索引 JSON：`十二经络与奇经八脉/十四经络穴位.json`（含全部字段，可直接驱动三栏网页）\n")
        f.write("- 每穴位字段：别名 / 定位 / 解剖 / 主治 / 穴义 / 刺灸 / 备注 / 配伍 / 特征 / 规律 / 名词解析 / 倪师注解 / 治法\n")
        f.write("- 加密：MDB 字段 `XOR-0x0F` 后为 GBK RTF，用 `web_app/common.py` 的 `text_of` 还原\n\n")
        f.write("## 二、倪师傅经验\n\n")
        f.write("### 针刺手法（EXE 提取图）\n\n")
        f.write("| 图 | 尺寸 | 说明 |\n|---|---|---|\n")
        f.write("| `痰闭针孔针刺图.jpg` | 220×130 | 痰闭针孔针刺手法 |\n")
        f.write("| `山火透天凉手法图.jpg` | 300×168 | 热补/凉泻手法（山火/透天凉）|\n")
        f.write("| `眼针呼气手法图.jpg` | 330×164 | 眼针 · 呼气 |\n")
        f.write("| `进针手法图(呼气吸气).jpg` | 334×148 | 进针与呼气/吸气配合 |\n")
        f.write("\n> 针刺手法的**文字**（倪师讲解）原 EXE 内未以明文嵌入单独段落；EXE 主要承载这些**手法示意图**。如需配套文字，可对照现行网页版（已在 web_app 中转写部分）。\n\n")
        f.write(f"### 针灸穴位总结图表（MDB nishitu 提取，{len(charts)} 张 JPEG）\n\n")
        f.write("每张图均来自 MDB `nishitu` 表（NR 字段经 XOR-0x0F 解密后为 JPEG）：\n\n")
        for mz, fn in charts[:20]:
            f.write(f"- {mz} → `{fn}`\n")
        if len(charts) > 20:
            f.write(f"- ... 共 {len(charts)} 张（详见 `倪师傅经验/针灸穴位总结图表/索引.txt`）\n")
        f.write("\n")
        f.write("### 倪海厦师父照片\n\n")
        f.write("- `倪师傅经验/倪海厦师父照片.jpg`（EXE 内 178×178 嵌入图）\n\n")
        f.write("## 三、未提取栏目（说明）\n\n")
        f.write("- **汉唐取穴**（经络/脏腑辩证取穴·对症取穴·辩病取穴法）：MDB 无独立结构化表，原文可能在 EXE 资源/字符串中，需按节提取；本次未触及。\n")
        f.write("- **动画演示 / 穴位走向动画**：原为 Delphi 运行时矢量绘制（web 端已用 SVG 重建替代），EXE 内无可独立抽取的动画帧，故未放置矢量/帧文件。`目录.txt` 已保留目录。\n")
        f.write("- **人体正面全身经络穴位图**：本 EXE 内未发现独立的正面视图（仅背面 1278×2304 + 侧面 1283×2304 + 竖裁背面 89×160），已提取并标注。如需正面图，建议参考外部中医图谱。\n\n")
        f.write("## 四、解密与抽取工具\n\n")
        f.write("所有内容由 `finalhopes-Learning-System/tools/build_renji_content.py` 一键构建：\n\n")
        f.write("```bash\n")
        f.write(f".venv/Scripts/python.exe tools/build_renji_content.py\n")
        f.write("```\n\n")
        f.write("- MDB 解密：复用 `web_app/common.py`（`XOR-0x0F` + `rtf_to_text` + GBK 解码）\n")
        f.write("- EXE 图片：JPEG 魔术字扫描 + 尺寸校验去重\n")
        f.write("- 经脉归属：国标 361 穴对照 + 3 个别名（和髎/腹通/足窍）补齐 357 穴全覆盖\n")
    return readme

# ============== MAIN ==============
def main():
    print("[1/6] 连接 MDB（单连接查询 nishixuewei + nishitu）...")
    conn = common.connect()
    print("      已连接")

    print("[2/6] 解密 nishixuewei ...")
    recs = decrypt_acupoints(conn)
    print(f"      → {len(recs)} 个穴位")
    rev = build_rev()
    groups, orphans = group_by_meridian(recs, rev)
    print(f"      → 归属 {sum(len(v) for v in groups.values())} 穴，未归属 {len(orphans)}")
    if orphans:
        print("      未归属穴：", [o["_MZ"] for o in orphans])

    print("[3/6] 写出十四经络穴位（按目录.txt）...")
    stats, body_imgs = write_meridian_folders(groups)
    for k,v in stats.items(): print(f"      {k}: {v}")
    write_master_json(groups, body_imgs)

    print("[4/6] 抽取 EXE 图片 ...")
    imgs = extract_exe_images()
    print(f"      人体穴位图: {imgs['body']}")
    print(f"      针刺手法: {imgs['technique']}")
    print(f"      倪师照片: {imgs['photo']}")

    print("[5/6] 解密 nishitu 图表 ...")
    charts = extract_nishitu_charts(conn)
    print(f"      → {len(charts)} 张图表")

    conn.close()
    print("      MDB 关闭")

    print("[6/6] 写 README ...")
    write_readme(stats, imgs, charts)

    print("\n✅ 完成。请查看：")
    print(f"  - {ROOT}\\十二经络与奇经八脉\\")
    print(f"  - {ROOT}\\倪师傅经验\\")
    print(f"  - {ROOT}\\README.md")

if __name__ == "__main__":
    main()