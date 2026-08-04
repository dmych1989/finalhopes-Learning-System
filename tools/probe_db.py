# -*- coding: utf-8 -*-
import pyodbc, os, re
BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "Data", "LILUN.mdb"); PWD = "JiSkS92A30"
c = pyodbc.connect("Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=%s;PWD=%s;" % (DB, PWD))
cur = c.cursor()
# 第7栏 汉唐方剂: 看 nhxlwj 里有没有 唐-01 / 汉唐
cur.execute("SELECT [ID] FROM [nhxlwj] WHERE [ID] LIKE '%唐-0%' OR [ID] LIKE '%唐-%'")
rows = [r[0] for r in cur.fetchall()]
print("nhxlwj 含'唐-'的ID样例(前20):", rows[:20], "总数:", len(rows))
# hantang 表
cur.execute("SELECT [ID] FROM [hantang]")
print("hantang ID样例:", [r[0] for r in cur.fetchall()][:10])
# 引号差异示例: 找含 十枣汤 的
cur.execute("SELECT [ID] FROM [nhxlwj] WHERE [ID] LIKE '%十枣汤%'")
print("含十枣汤的ID:", [r[0] for r in cur.fetchall()][:10])
# 引号字符
cur.execute("SELECT [ID] FROM [nhxlwj] WHERE [ID] LIKE '%\"%' OR [ID] LIKE '%“%'")
print("含直/弯引号的ID数:", len(cur.fetchall()))
c.close()
