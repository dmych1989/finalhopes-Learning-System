# -*- coding: utf-8 -*-
"""把天纪目录树 TIANJI_TREE 由单一「斗数」根，拆分为「斗数」+「四柱」两个根。

规则（2026-08-06，与用户确认）：
- 斗数根：紫微斗数星曜与卦象 —— 基础理论(甲级星/乙级星及神煞/基础概念)、
          断法细则(十二宫)、天纪卦象查询(原样保留)。
- 四柱根：八字（四柱）理论 —— 断法分类(新建空)、基础理论(八字·十神/六亲/格局)、
          断法细则(原 断法细则 全部内容)、时辰效验、子女、案例查询。
所有叶子节点原样保留，仅重新分组，不丢失任何数据。
"""
import io
import json
import sys

WEB = r"E:\Soft\倪海夏三套学习系统\QQ频道号talktyph0id\finalhopes-Learning-System\web_app"
sys.path.insert(0, WEB)
import tianji_tree as T

OLD = T.TIANJI_TREE


def find(nodes, title):
    for n in nodes:
        if n.get("t") == title:
            return n
        if "children" in n:
            r = find(n["children"], title)
            if r:
                return r
    return None


dou = find(OLD, "斗数")
old_basic = find([dou], "基础理论")
old_jiefa = find([dou], "断法细则")
old_gua = find([dou], "天纪卦象查询")
old_zinv = find([dou], "子女")
old_shichen = find([dou], "时辰效验")
old_anli = find([dou], "案例查询")

jiaji = find([old_basic], "甲级星")
yiji = find([old_basic], "乙级星及神煞")
jichu = find([old_basic], "基础概念")
shier = find([old_basic], "十二宫")
bazi_ss = find([old_basic], "八字·十神")
bazi_lq = find([old_basic], "八字·六亲")
bazi_gj = find([old_basic], "八字·格局与基础")

assert all([dou, old_basic, old_jiefa, old_gua, old_zinv, old_shichen, old_anli,
            jiaji, yiji, jichu, shier, bazi_ss, bazi_lq, bazi_gj]), "源节点查找不完整"

new_dou = {
    "t": "斗数",
    "children": [
        {"t": "基础理论", "children": [jiaji, yiji, jichu]},
        {"t": "断法细则", "children": [shier]},
        old_gua,
    ],
}

new_sizhu = {
    "t": "四柱",
    "children": [
        {"t": "断法分类", "children": []},
        {"t": "基础理论", "children": [bazi_ss, bazi_lq, bazi_gj]},
        {"t": "断法细则", "children": old_jiefa["children"]},
        old_shichen,
        old_zinv,
        old_anli,
    ],
}

new_tree = [new_dou, new_sizhu]


def count_leaves(nodes):
    n = 0
    for nd in nodes:
        if "children" in nd:
            # 空 children 视为占位节点（如「断法分类」），不计为内容叶子
            if nd["children"]:
                n += count_leaves(nd["children"])
        else:
            n += 1
    return n


old_cnt = count_leaves(OLD)
new_cnt = count_leaves(new_tree)
print("源叶子数=%d  新叶子数=%d" % (old_cnt, new_cnt))
assert old_cnt == new_cnt, "叶子数不一致，数据可能丢失！"

header = '''# -*- coding: utf-8 -*-
"""天纪目录树（由 tools/gen_tianji_tree.py 依据 列表.txt 生成）。

每个叶子节点带 src(数据源) 与 idx(在 _DATA[src] 中的序号)，
前端点击叶子调用 /api/tianji/item?sub=<src>&i=<idx> 取详情。

2026-08-06 重构：原单一「斗数」根拆分为「斗数」与「四柱」两个根，
八字（四柱）相关分支（基础理论 / 断法细则 / 时辰效验 / 子女 / 案例查询）
移入四柱根；斗数根保留紫微斗数星曜（甲级星 / 乙级星及神煞 / 基础概念 /
十二宫）与天纪卦象查询。顶部「斗数理论 / 四柱理论」下拉菜单跳转对应根下分区。
"""

'''

body = "TIANJI_TREE = " + json.dumps(new_tree, ensure_ascii=False, indent=2) + "\n"

out_path = WEB + r"\tianji_tree.py"
with io.open(out_path, "w", encoding="utf-8") as f:
    f.write(header + body)
print("已写出:", out_path)
