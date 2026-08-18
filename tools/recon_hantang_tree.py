# -*- coding: utf-8 -*-
"""Recon v5: clean recursive pre-order tree parse with forward re-sync."""
import struct, sys

EXE = r"E:\Soft\倪海夏三套学习系统\QQ频道号talktyph0id\人纪学习系统\倪海厦汉唐中医馆人纪针灸内部学习系统V2022.exe"

def is_cjk(t):
    if not t:
        return False
    n = sum(1 for c in t if '\u4e00' <= c <= '\u9fff')
    return n >= max(2, len(t) - 2)

def parse_node(data, pos):
    if pos is None or pos + 17 > len(data):
        return None
    img = data[pos:pos+8]
    fa = struct.unpack('<i', data[pos+8:pos+12])[0]
    cc = struct.unpack('<i', data[pos+12:pos+16])[0]
    tl = data[pos+16]
    text = data[pos+17:pos+17+tl]
    try:
        s = text.decode('gbk')
    except Exception:
        return None
    if not (0 <= cc <= 400 and 0 <= fa <= 400):
        return None
    if not (img == b'\xff'*8 or img == b'\x00'*8):
        return None
    if not is_cjk(s):
        return None
    return {'pos': pos, 'cc': cc, 'fa': fa, 'text': s, 'img': img.hex()}

def node_next(data, pos, max_gap=256):
    nd = parse_node(data, pos)
    if nd is None:
        return None
    tlen = len(nd['text'].encode('gbk'))
    search = pos + 17 + tlen
    guard = 0
    while search < len(data) - 16 and guard < max_gap:
        guard += 1
        if parse_node(data, search) is not None:
            return search
        search += 1
    return None

def subtree_end(data, pos):
    """Return offset immediately after the entire subtree rooted at pos."""
    node = parse_node(data, pos)
    if node is None:
        return (pos + 1) if isinstance(pos, int) else None
    p = node_next(data, pos)
    for _ in range(node['cc']):
        if p is None:
            break
        p = subtree_end(data, p)
    return p

def parse_tree(data, pos, max_nodes=5000):
    node = parse_node(data, pos)
    if node is None:
        return None
    children = []
    p = node_next(data, pos)
    for _ in range(node['cc']):
        if p is None:
            break
        child = parse_tree(data, p, max_nodes)
        if child is None:
            break
        children.append(child)
        p = subtree_end(data, p)
    node['children'] = children
    return node

def count_leaves(node):
    tot = 0
    for ch in node['children']:
        if ch['cc'] == 0:
            tot += 1
        tot += count_leaves(ch)
    return tot

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

def main():
    with open(EXE, 'rb') as f:
        data = f.read()
    candidates = {
        '经络辩证取穴': ['经络辩证取穴'],
        '脏腑辩证取穴': ['汉唐脏腑辨证取穴'],
        '汉唐对症取穴': ['汉唐对症取穴'],
        '汉唐辩病取穴法': ['辨病选穴法'],
    }
    # expected leaf counts from MDB (for validation)
    expect = {'经络辩证取穴': (20, 27), '脏腑辩证取穴': (10, 30),
              '汉唐对症取穴': (3, 50), '汉唐辩病取穴法': (11, 206)}
    for cat, anchors in candidates.items():
        print(f"### {cat} ###", file=sys.stderr)
        for a in anchors:
            for bs, cc, fa in find_anchor_nodes(data, a.encode('gbk')):
                tree = parse_tree(data, bs)
                if tree is None:
                    print(f"  anchor='{a}' FAILED", file=sys.stderr)
                    continue
                nt = len(tree['children'])
                nl = count_leaves(tree)
                et, el = expect[cat]
                ok = (nt == et and nl == el)
                print(f"  anchor='{a}' @{bs:x} root='{tree['text']}' topics={nt}(exp{et}) leaves={nl}(exp{el}) {'OK' if ok else 'MISMATCH'}",
                      file=sys.stderr)
                print(f"     topics={[c['text'] for c in tree['children']][:4]}", file=sys.stderr)

if __name__ == '__main__':
    main()
