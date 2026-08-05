# -*- coding: utf-8 -*-
"""生成 web_app/tianji_tree.py：按 天纪学习系统/列表.txt 重组天纪目录树。

每个叶子节点解析到天纪数据源 (gua/rendao/lilun/mingli/jingdu) 的 (src, idx)，
直接复用既有 /api/tianji/item?sub=<src>&i=<idx> 端点渲染详情，无需新后端逻辑。

规则：
  * 天纪卦象查询 > 六十四卦       -> gua（按卦名）
  * 天纪卦象查询 > 人间道         -> rendao（按卦名）
  * 案例查询                      -> mingli（按命例名）
  * 时辰效验                      -> lilun 优先，否则 jingdu（按名）
  * 斗数>基础理论 / 断法细则 / 子女 -> lilun（按名）
  * 某个 ### 组若没有任何叶子（如 验证方法/验证时辰法/子女/地脉道），
    则把该组标题本身当作一个叶子解析（解析不到则 src=None，前端显示「暂无内容」）。
"""
import json
import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIST_TXT = r"E:\Soft\倪海夏三套学习系统\QQ频道号talktyph0id\天纪学习系统\列表.txt"
DATA_DB = os.path.join(ROOT, "web_app", "data.db")
OUT = os.path.join(ROOT, "web_app", "tianji_tree.py")


def load_names(db, key):
    con = sqlite3.connect(db)
    row = con.execute("SELECT v FROM tianji_data WHERE k=?", (key,)).fetchone()
    con.close()
    data = json.loads(row[0]) if row else []
    return {x.get("name", ""): i for i, x in enumerate(data)}


def main():
    gua = load_names(DATA_DB, "gua")
    rendao = load_names(DATA_DB, "rendao")
    lilun = load_names(DATA_DB, "lilun")
    mingli = load_names(DATA_DB, "mingli")
    jingdu = load_names(DATA_DB, "jingdu")

    def resolve(name, sec, grp):
        if sec == "天纪卦象查询":
            if grp == "六十四卦":
                return ("gua", gua[name]) if name in gua else (None, None)
            if grp == "人间道":
                return ("rendao", rendao[name]) if name in rendao else (None, None)
            return ("lilun", lilun[name]) if name in lilun else (None, None)
        if sec == "案例查询":
            return ("mingli", mingli[name]) if name in mingli else (None, None)
        if sec == "时辰效验":
            if name in lilun:
                return ("lilun", lilun[name])
            if name in jingdu:
                return ("jingdu", jingdu[name])
            return (None, None)
        # 斗数 > 基础理论 / 断法细则 / 子女
        return ("lilun", lilun[name]) if name in lilun else (None, None)

    def make_leaf(name, sec, grp):
        src, idx = resolve(name, sec, grp)
        node = {"t": name}
        if src:
            node["src"] = src
            node["idx"] = idx
        return node

    txt = open(LIST_TXT, encoding="utf-8").read()
    lines = [l.rstrip("\n") for l in txt.split("\n")]

    root = {"t": "斗数", "children": []}
    cur_sec = None
    cur_grp = None
    for l in lines:
        if l.startswith("# "):
            continue  # 顶层「斗数」已作为 root
        if l.startswith("## "):
            cur_sec = {"t": l[3:].strip(), "children": []}
            root["children"].append(cur_sec)
            cur_grp = None
        elif l.startswith("### "):
            cur_grp = {"t": l[4:].strip(), "children": []}
            cur_sec["children"].append(cur_grp)
        elif l.strip():
            leaf = make_leaf(l.strip(), cur_sec["t"],
                              cur_grp["t"] if cur_grp else None)
            if cur_grp:
                cur_grp["children"].append(leaf)
            else:
                cur_sec["children"].append(leaf)

    # 后处理：把没有任何叶子的 ### 组转为「以自身标题为叶子」的节点；
    # 再把单子节点且与自身同名的组折叠掉（如 子女>子女）。
    def finalize(node):
        if "src" in node:
            return node
        kids = node.get("children", [])
        if not kids:
            # 空组 -> 自身当叶子解析
            src, idx = resolve(node["t"],
                                node.get("_sec", ""), node.get("_grp", ""))
            leaf = {"t": node["t"]}
            if src:
                leaf["src"] = src
                leaf["idx"] = idx
            return leaf
        newkids = [finalize(c) for c in kids]
        node["children"] = newkids
        # 折叠：仅一个子节点且该子节点是同名叶子
        if (len(newkids) == 1 and "src" in newkids[0]
                and newkids[0]["t"] == node["t"]):
            return newkids[0]
        return node

    # 记录每个组的上下文（用于空组解析）
    def tag(node, sec, grp):
        if "src" in node:
            return
        node["_sec"] = sec
        node["_grp"] = grp
        for c in node.get("children", []):
            tag(c, sec, grp if "src" not in c else c.get("t", grp))

    for sec in root["children"]:
        for grp in sec["children"]:
            tag(grp, sec["t"], grp["t"])

    root = finalize(root)

    # 统计
    leaf_count = {"gua": 0, "rendao": 0, "lilun": 0, "mingli": 0, "jingdu": 0, "none": 0}

    def walk(n):
        if "src" in n:
            leaf_count[n["src"] if n["src"] else "none"] += 1
        for c in n.get("children", []):
            walk(c)

    walk(root)

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("# -*- coding: utf-8 -*-\n")
        f.write('"""天纪目录树（由 tools/gen_tianji_tree.py 依据 列表.txt 生成）。\n\n')
        f.write("每个叶子节点带 src(数据源) 与 idx(在 _DATA[src] 中的序号)，\n")
        f.write('前端点击叶子调用 /api/tianji/item?sub=<src>&i=<idx> 取详情。\n"""\n')
        f.write("TIANJI_TREE = ")
        f.write(json.dumps([root], ensure_ascii=False, indent=2))
        f.write("\n")

    print("written:", OUT)
    print("per-source leaf counts:", leaf_count)
    total = sum(leaf_count.values())
    print("total leaves:", total)


if __name__ == "__main__":
    main()
