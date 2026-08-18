# -*- coding: utf-8 -*-
"""Extract 汉唐取穴 text from EXE (navigation tree) + LILUN.mdb (body),
organized exactly per 目录.txt. Also extracts 针刺手法 name index from EXE.

Output:
  <汉唐取穴>/导出/汉唐取穴_导出.txt
  <汉唐取穴>/导出/汉唐取穴_导出.html
"""
import struct, os, sys, html, json
from collections import defaultdict

EXE = r"E:\Soft\倪海夏三套学习系统\QQ频道号talktyph0id\人纪学习系统\倪海厦汉唐中医馆人纪针灸内部学习系统V2022.exe"
MDB = r"E:\Soft\倪海夏三套学习系统\QQ频道号talktyph0id\人纪学习系统\Data\LILUN.mdb"
OUTDIR = r"E:\Soft\倪海夏三套学习系统\QQ频道号talktyph0id\人纪学习系统\汉唐取穴\导出"
DIRTXT = r"E:\Soft\倪海夏三套学习系统\QQ频道号talktyph0id\人纪学习系统\汉唐取穴\目录.txt"

# (display_category, exe_anchor, mdb_table, content_cols)
CATS = [
    ('经络辩证取穴', '经络辩证取穴', 'ZJDCJL', ('NR1', 'NR2')),
    ('脏腑辩证取穴', '汉唐脏腑辨证取穴', 'ZFBZ', ('NR1', 'NR2')),
    ('汉唐对症取穴', '汉唐对症取穴', 'BZDZ', ('NR',)),
    ('汉唐辩病取穴法', '辨病选穴法', 'BBXX', ('NR',)),
]

# 辨病: EXE fine topic -> 目录.txt coarse topic
BIANBING_MAP = {
    '消化系病选穴': '消化系病选穴',
    '胃肠病症': '消化系病选穴',
    '肝胆胰脏病症': '消化系病选穴',
    '呼吸系病选穴': '呼吸系病选穴',
    '心脑血管系病症选穴': '心脑血管系病症选穴',
    '精神神经系统辩病取穴': '精神神经系统辩病取穴',
    '泌尿生殖系统辩病取穴': '泌尿生殖系统辩病取穴',
    '运动系统辩证选穴': '运动系统辩证取穴',
    '腰椎、颈椎病症': '腰椎、颈椎病症',
    '五官病辩选穴': '五官病辩选穴',
    '皮肤病辩证取穴': '皮肤病辩证取穴',
}

def is_cjk(t):
    if not t:
        return False
    n = sum(1 for c in t if '\u4e00' <= c <= '\u9fff')
    return n >= max(2, len(t) - 2)

def is_cjk_loose(t):
    """Lenient CJK gate for the 针刺手法/针灸治症 navigation tree (a known,
    childCount-driven subtree at a fixed offset). Titles there contain several
    punctuation marks / spaces (e.g. '耳针治疗：醒酒、肾结石、心脏、消炎'),
    which the strict rule rejects. Requiring >= 2 CJK chars still filters out
    random binary false-positives while accepting these legit titles."""
    if not t:
        return False
    return sum(1 for c in t if '\u4e00' <= c <= '\u9fff') >= 2

def _node_text(data, pos, tl):
    """Decode the GBK text field. Some EXE nodes (e.g. the 针刺手法 chapter
    header) store a len byte that is 1 short of the real byte count; fall back
    to len+1 / len+2 so the trailing character is not dropped. The strict decode
    still succeeds first for well-formed nodes, so this only triggers on the
    off-by-one entries and cannot spuriously accept garbage (is_cjk + cc/fa/img
    filters in parse_node reject anything invalid)."""
    for dl in (0, 1, 2):
        end = pos + 17 + tl + dl
        if end > len(data):
            break
        frag = data[pos+17:end]
        try:
            return frag.decode('gbk')
        except Exception:
            continue
    return None

def parse_node(data, pos, cjk=is_cjk):
    if pos is None or pos + 17 > len(data):
        return None
    img = data[pos:pos+8]
    fa = struct.unpack('<i', data[pos+8:pos+12])[0]
    cc = struct.unpack('<i', data[pos+12:pos+16])[0]
    tl = data[pos+16]
    s = _node_text(data, pos, tl)
    if s is None:
        return None
    if not (0 <= cc <= 400 and 0 <= fa <= 400):
        return None
    if not (img == b'\xff'*8 or img == b'\x00'*8):
        return None
    if not cjk(s):
        return None
    return {'pos': pos, 'cc': cc, 'text': s.strip()}

def node_next(data, pos, max_gap=256, cjk=is_cjk):
    nd = parse_node(data, pos, cjk)
    if nd is None:
        return None
    tlen = len(nd['text'].encode('gbk'))
    search = pos + 17 + tlen
    g = 0
    while search < len(data) - 16 and g < max_gap:
        g += 1
        if parse_node(data, search, cjk) is not None:
            return search
        search += 1
    return None

def subtree_end(data, pos, cjk=is_cjk):
    node = parse_node(data, pos, cjk)
    if node is None:
        return (pos + 1) if isinstance(pos, int) else None
    p = node_next(data, pos, cjk=cjk)
    for _ in range(node['cc']):
        if p is None:
            break
        p = subtree_end(data, p, cjk=cjk)
    return p

def parse_tree(data, pos, cjk=is_cjk):
    node = parse_node(data, pos, cjk)
    if node is None:
        return None
    children = []
    p = node_next(data, pos, cjk=cjk)
    for _ in range(node['cc']):
        if p is None:
            break
        child = parse_tree(data, p, cjk=cjk)
        if child is None:
            break
        children.append(child)
        p = subtree_end(data, p, cjk=cjk)
    node['children'] = children
    return node

def find_anchor_nodes(data, anchor_gbk):
    res = []
    start = 0
    while True:
        i = data.find(anchor_gbk, start)
        if i < 0:
            break
        p = i - 1
        bs = p - 16
        if bs >= 0 and bs + 17 <= len(data):
            img = data[bs:bs+8]
            fa = struct.unpack('<i', data[bs+8:bs+12])[0]
            cc = struct.unpack('<i', data[bs+12:bs+16])[0]
            if (img == b'\xff'*8 or img == b'\x00'*8) and 0 <= cc <= 400 and 0 <= fa <= 400:
                res.append((bs, cc, fa))
        start = i + 1
    return res

def read_mdb(table, cols):
    import pyodbc
    conn = pyodbc.connect(
        r"Driver={Microsoft Access Driver (*.mdb, *.accdb)};"
        r"Dbq=" + MDB + ";Pwd=JiSkS92A30;")
    cur = conn.cursor()
    rows = cur.execute(f"SELECT MZ, {', '.join(cols)} FROM [{table}]").fetchall()
    conn.close()
    out = {}
    for r in rows:
        mz = r[0]
        if isinstance(mz, bytes):
            mz = mz.decode('gbk', errors='replace')
        parts = []
        for ci in range(1, len(r)):
            v = r[ci]
            if isinstance(v, bytes):
                v = v.decode('gbk', errors='replace')
            elif v is not None:
                v = str(v)
            parts.append(v or "")
        content = "\n".join(p for p in parts if p).strip()
        out[mz.strip()] = content
    return out

def read_mdb_rows(table, cols):
    """Return MDB rows as a list of (mz, body) in table row order. Unlike
    read_mdb (a name->body dict that collapses duplicate MZ), this preserves
    every row, so tables with duplicate 病机/证型 names (e.g. ZJDCJL has
    风寒痹阻 x3 and 外邪痹阻 x3 with DIFFERENT bodies) can be assigned
    one-by-one via pop-in-order."""
    import pyodbc
    conn = pyodbc.connect(
        r"Driver={Microsoft Access Driver (*.mdb, *.accdb)};"
        r"Dbq=" + MDB + ";Pwd=JiSkS92A30;")
    cur = conn.cursor()
    rows = cur.execute(f"SELECT MZ, {', '.join(cols)} FROM [{table}]").fetchall()
    conn.close()
    out = []
    for r in rows:
        mz = r[0]
        if isinstance(mz, bytes):
            mz = mz.decode('gbk', errors='replace')
        parts = []
        for ci in range(1, len(r)):
            v = r[ci]
            if isinstance(v, bytes):
                v = v.decode('gbk', errors='replace')
            elif v is not None:
                v = str(v)
            parts.append(v or "")
        content = "\n".join(p for p in parts if p).strip()
        out.append((mz.strip(), content))
    return out

def parse_shoufa_tree(data):
    """Parse the 针刺手法 / 针灸治症 navigation as TWO sibling chapters.

    Real structure (verified by a full node survey of the region 0x45d37b..):
      · '第五章 奇经八脉与针刺法' @0x45d37b (childCount=19)
          -> 19 leaf titles (针刺手法: 十二经络与十五络脉歌 … 九针之使用时机)
      · '第六章 针灸治症系列' @0x45d712 (childCount=36)
          -> 33 leaf titles found in-region (针灸治症: 梅花针 … 十三鬼穴)
    These are SIBLING top-level trees, NOT parent/child. The detailed bodies
    live in EXE Lines.Strings as encoded/compressed binary and cannot be
    decoded to plain text, so only the navigation titles (preserving the tree
    hierarchy) are exported. A lenient CJK gate is used so punctuation-heavy
    titles (e.g. '耳针治疗：醒酒、肾结石、心脏、消炎') are not rejected.
    """
    may = parse_tree(data, 0x45d37b, cjk=is_cjk_loose)
    june = parse_tree(data, 0x45d712, cjk=is_cjk_loose)
    children = [c for c in (may, june) if c]
    return {'text': '针刺手法与针灸治症（EXE 导航索引）', 'children': children, 'cc': len(children)}

def _count_leaves(node):
    if node is None:
        return 0
    if not node.get('children'):
        return 1
    return sum(_count_leaves(c) for c in node['children'])

def clean_body(text):
    # normalize whitespace; keep newlines
    lines = [ln.strip() for ln in text.split('\n')]
    return '\n'.join(l for l in lines if l)

def build():
    with open(EXE, 'rb') as f:
        data = f.read()
    result = {}  # category -> list of (topic, items)  ; items: list of dict
    report = []

    # read 目录.txt topic order
    dir_topics = {}
    cur_cat = None
    with open(DIRTXT, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('《') and line.endswith('》'):
                cur_cat = line[1:-1]
                dir_topics[cur_cat] = []
            elif cur_cat:
                dir_topics[cur_cat].append(line)

    for disp, anchor, table, cols in CATS:
        tree = None
        for bs, cc, fa in find_anchor_nodes(data, anchor.encode('gbk')):
            tree = parse_tree(data, bs)
            if tree:
                break
        rows = read_mdb_rows(table, cols)
        # pop-in-order map: name -> list of bodies in row order (handles duplicate
        # MZ with different bodies; each tree leaf pops the next unused body).
        by_name = defaultdict(list)
        for mz, body in rows:
            by_name[mz].append(body)
        name_set = set(by_name.keys())
        if tree is None:
            report.append(f"[FAIL] {disp}: tree not parsed")
            result[disp] = []
            continue
        topics = []
        if disp != '汉唐辩病取穴法':
            # simple 2-level: topic -> disease leaves with body
            for topic in tree['children']:
                tname = topic['text'].strip()
                items = []
                for leaf in topic['children']:
                    if leaf['cc'] != 0:
                        continue
                    name = leaf['text'].strip()
                    lst = by_name.get(name)
                    body = lst.pop(0) if lst else ''
                    items.append({'type': 'entry', 'name': name, 'body': clean_body(body)})
                topics.append((tname, items))
        else:
            # 辨病: 3-level; map fine topics to coarse 目录 topics; add MDB-only
            # group EXE tree by coarse topic
            coarse_map = {}  # coarse -> list of fine-topic structures
            for fine in tree['children']:
                fname = fine['text'].strip()
                coarse = BIANBING_MAP.get(fname, fname)
                # within fine topic: build subgroups (diseases carry body)
                subgroups = []  # (header_or_None, [{'name','body'}, ...])
                cur_header = None
                cur_list = []
                for ch in fine['children']:
                    nm = ch['text'].strip()
                    if ch['cc'] == 0 and nm not in name_set:
                        # group header
                        if cur_list:
                            subgroups.append((cur_header, cur_list))
                        cur_header = nm
                        cur_list = []
                    else:
                        lst = by_name.get(nm)
                        body = lst.pop(0) if lst else ''
                        cur_list.append({'name': nm, 'body': clean_body(body)})
                if cur_list:
                    subgroups.append((cur_header, cur_list))
                coarse_map.setdefault(coarse, []).append((fname, subgroups))
            # MDB-only diseases -> 传染 / 内分泌
            tree_leaves = set()
            def collect(n):
                for c in n['children']:
                    if c['cc'] == 0:
                        tree_leaves.add(c['text'].strip())
                    collect(c)
            collect(tree)
            mdb_only = sorted(name_set - tree_leaves)
            chuan, nei = [], []
            for m in mdb_only:
                if any(k in m for k in ['甲状腺', '糠尿', '糖尿病', '内分泌', '垂体', '肾上腺', '肥胖']):
                    nei.append(m)
                else:
                    chuan.append(m)
            # build topics following 目录.txt order
            for coarse in dir_topics.get(disp, []):
                if coarse in ('传染性疾病辩病取穴',):
                    items = [{'type': 'entry', 'name': m, 'body': clean_body(by_name.get(m, [''])[0])} for m in chuan]
                    topics.append((coarse, items, 'fine:_传染'))
                elif coarse in ('内分泌病辩选穴',):
                    items = [{'type': 'entry', 'name': m, 'body': clean_body(by_name.get(m, [''])[0])} for m in nei]
                    topics.append((coarse, items, 'fine:_内分泌'))
                else:
                    # fine topics for this coarse
                    fines = coarse_map.get(coarse, [])
                    topics.append((coarse, fines, 'coarse'))
        result[disp] = topics
        # report
        if disp != '汉唐辩病取穴法':
            ntopics = len(topics)
            nentries = sum(len(it) for _, it in topics)
            # leftover bodies (duplicate MZ not fully consumed) — should be 0
            leftover = sum(len(v) for v in by_name.values())
            report.append(f"{disp}: topics={ntopics} entries={nentries} mdb_rows={len(rows)} unused_bodies={leftover}")
        else:
            report.append(f"{disp}: coarse_topics={len(topics)} mdb_rows={len(rows)} mdb_only={len(mdb_only)} (传染{len(chuan)}/内分泌{len(nei)})")

    # 针刺手法 / 针灸治症 navigation tree (EXE offset 0x45d37b)
    shoufa_tree = parse_shoufa_tree(data)
    n_leaves = _count_leaves(shoufa_tree)
    report.append(f"针刺手法/针灸治症导航树: root={shoufa_tree['text']!r} leaves={n_leaves}")
    return result, report, shoufa_tree, dir_topics

def write_txt(result, shoufa_tree, dir_topics, path):
    lines = []
    lines.append("汉唐取穴 · 文字导出（按 目录.txt 整理）")
    lines.append("=" * 60)
    lines.append("")
    lines.append("来源：倪海厦汉唐中医馆人纪针灸内部学习系统V2022.exe（导航树）")
    lines.append("      + 配套 LILUN.mdb（正文：ZJDCJL/ZFBZ/BZDZ/BBXX，GBK 明文）")
    lines.append("")
    for disp, topics in result.items():
        lines.append("")
        lines.append(f"【{disp}】")
        lines.append("-" * 50)
        for t in topics:
            if len(t) == 3:
                coarse, payload, kind = t
            else:
                coarse, payload, kind = t[0], t[1], 'simple'
            lines.append("")
            lines.append(f"● {coarse}")
            if kind in ('simple',):
                for it in payload:
                    lines.append(f"  ○ {it['name']}")
                    if it['body']:
                        for bl in it['body'].split('\n'):
                            lines.append(f"      {bl}")
            elif kind == 'coarse':
                # payload = list of (fine_name, subgroups)
                for fine_name, subgroups in payload:
                    lines.append(f"  ▶ {fine_name}")
                    for header, diseases in subgroups:
                        if header:
                            lines.append(f"    ◇ {header}")
                        for d in diseases:
                            lines.append(f"      ○ {d['name']}")
                            if d['body']:
                                for bl in d['body'].split('\n'):
                                    lines.append(f"          {bl}")
            elif kind in ('fine:_传染', 'fine:_内分泌'):
                for it in payload:
                    lines.append(f"  ○ {it['name']}")
                    if it['body']:
                        for bl in it['body'].split('\n'):
                            lines.append(f"      {bl}")
    # 针刺手法 / 针灸治症导航树
    lines.append("")
    lines.append("【第五章 奇经八脉与针刺法 · 针刺手法/针灸治症】（EXE 导航索引）")
    lines.append("-" * 50)
    lines.append("注：本系统针刺手法及针灸治症的详细正文存于 EXE 的 Lines.Strings，为编码/压缩")
    lines.append("    二进制格式，无法直接解码为明文；以下为 EXE 内可识别的章节导航标题（保留层级）：")
    def _render(node, depth):
        pad = '  ' * depth
        lines.append(f"{pad}● {node['text']}")
        for ch in node.get('children', []):
            if ch.get('children'):
                _render(ch, depth + 1)
            else:
                lines.append(f"{pad}  ○ {ch['text']}")
    if shoufa_tree:
        _render(shoufa_tree, 0)
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

def write_html(result, shoufa_tree, path):
    parts = []
    parts.append("""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>汉唐取穴 · 文字导出</title>
<style>
:root{--teal:#0f766e;--teal-d:#0b5750;--bg:#f3f7f6;--card:#fff;--ink:#1f2a28;--mut:#5b6b68;}
*{box-sizing:border-box}
body{margin:0;font-family:"PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--ink);line-height:1.7}
header{background:linear-gradient(135deg,var(--teal),var(--teal-d));color:#fff;padding:26px 20px}
header h1{margin:0;font-size:22px}
header p{margin:6px 0 0;opacity:.9;font-size:13px}
.wrap{max-width:980px;margin:0 auto;padding:18px}
.cat{background:var(--card);border-radius:12px;margin:16px 0;box-shadow:0 2px 10px rgba(15,118,110,.08);overflow:hidden}
.cat>h2{margin:0;background:var(--teal);color:#fff;padding:12px 16px;font-size:17px}
.topic{padding:10px 16px;border-top:1px solid #eef3f2}
.topic>h3{margin:6px 0;color:var(--teal-d);font-size:15px}
.fine{margin:6px 0 6px 14px}
.fine>h4{margin:4px 0;color:#0d9488;font-size:14px;font-weight:600}
.group{margin:4px 0 4px 14px;color:#7c2d12;font-size:13px;font-weight:600}
.entry{margin:3px 0 3px 22px}
.entry .nm{font-weight:600;color:var(--ink)}
.entry .bd{margin:2px 0 6px 18px;color:var(--mut);font-size:13px;white-space:pre-wrap}
.src{font-size:12px;color:var(--mut);padding:6px 16px 12px}
code{background:#eef3f2;padding:1px 5px;border-radius:4px}
</style></head><body>
<header><h1>汉唐取穴 · 文字导出</h1>
<p>按 目录.txt 整理 · 来源：人纪针灸内部学习系统V2022.exe（导航树）+ LILUN.mdb（正文）</p></header>
<div class="wrap">""")
    for disp, topics in result.items():
        parts.append(f'<section class="cat"><h2>《{html.escape(disp)}》</h2>')
        for t in topics:
            if len(t) == 3:
                coarse, payload, kind = t
            else:
                coarse, payload, kind = t[0], t[1], 'simple'
            parts.append(f'<div class="topic"><h3>● {html.escape(coarse)}</h3>')
            if kind == 'simple':
                for it in payload:
                    parts.append(f'<div class="entry"><span class="nm">{html.escape(it["name"])}</span>')
                    if it['body']:
                        parts.append(f'<div class="bd">{html.escape(it["body"])}</div>')
                    parts.append('</div>')
            elif kind == 'coarse':
                for fine_name, subgroups in payload:
                    parts.append(f'<div class="fine"><h4>▸ {html.escape(fine_name)}</h4>')
                    for header, diseases in subgroups:
                        if header:
                            parts.append(f'<div class="group">◇ {html.escape(header)}</div>')
                        for d in diseases:
                            parts.append(f'<div class="entry"><span class="nm">{html.escape(d["name"])}</span>')
                            if d['body']:
                                parts.append(f'<div class="bd">{html.escape(d["body"])}</div>')
                            parts.append('</div>')
                    parts.append('</div>')
            else:  # 传染/内分泌
                for it in payload:
                    parts.append(f'<div class="entry"><span class="nm">{html.escape(it["name"])}</span>')
                    if it['body']:
                        parts.append(f'<div class="bd">{html.escape(it["body"])}</div>')
                    parts.append('</div>')
            parts.append('</div>')
        parts.append('</section>')
    # 针刺手法 / 针灸治症导航树
    parts.append('<section class="cat"><h2>第五章 奇经八脉与针刺法 · 针刺手法/针灸治症（EXE 导航索引）</h2>')
    parts.append('<div class="src">注：详细正文存于 EXE 的 <code>Lines.Strings</code>，为编码/压缩二进制格式，无法直接解码为明文；以下为 EXE 内可识别的章节导航标题（保留层级）。</div>')
    def _render_html(node, depth):
        if depth == 0:
            parts.append(f'<div class="topic"><h3>● {html.escape(node["text"])}</h3></div>')
        else:
            parts.append(f'<div class="fine"><h4>▸ {html.escape(node["text"])}</h4></div>')
        for ch in node.get('children', []):
            if ch.get('children'):
                _render_html(ch, depth + 1)
            else:
                parts.append(f'<div class="entry"><span class="nm">{html.escape(ch["text"])}</span></div>')
    if shoufa_tree:
        _render_html(shoufa_tree, 0)
    parts.append('</section>')
    parts.append('</div></body></html>')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(parts))

def main():
    result, report, shoufa_tree, dir_topics = build()
    os.makedirs(OUTDIR, exist_ok=True)
    txt_path = os.path.join(OUTDIR, '汉唐取穴_导出.txt')
    html_path = os.path.join(OUTDIR, '汉唐取穴_导出.html')
    write_txt(result, shoufa_tree, dir_topics, txt_path)
    write_html(result, shoufa_tree, html_path)
    print('\n'.join(report), file=sys.stderr)
    print(f"\nTXT -> {txt_path}", file=sys.stderr)
    print(f"HTML-> {html_path}", file=sys.stderr)
    # dump json for inspection
    with open(os.path.join(OUTDIR, '_dump.json'), 'w', encoding='utf-8') as f:
        json.dump({k: [(t[0], len(t[1]) if len(t) == 3 else len(t[1])) for t in v] for k, v in result.items()}, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
