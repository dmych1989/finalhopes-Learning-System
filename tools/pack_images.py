# -*- coding: utf-8 -*-
"""把 public/img/** 下全部图片打包进按子目录拆分的 SQLite 库 web_app/images_<sub>.db。

动机：Vercel 部署包若含 2239 张独立图片（public/img/*），HOBBY 拥塞下
「Downloading 2315 deployment files」会超时 → 部署 state=ERROR。把这些图塞进
少数几个 SQLite 单文件（每子目录一个，最大 ~26MB，远低于 Vercel 单文件 ~100MB 上限），
部署文件数从 2315 降到 ~78，根治下载超时。

打包后由 server.py 的 GET /api/img/<name> 端点按 key 读取返回；前端 /img/* 引用
统一改为 /api/img/*（见 server.py 与前端改造）。

key 规则：相对 public/ 的路径，例如 img/yaotu_list/桂枝-药材.jpg。
"""
import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_ROOT = os.path.join(ROOT, "public", "img")
DB_DIR = os.path.join(ROOT, "web_app")
SUBS = ["renji", "shoufa", "tianji", "xuewei", "yaotu", "yaotu_list", "zhongyi"]
MIME = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
    "gif": "image/gif", "webp": "image/webp", "bmp": "image/bmp",
}


def mime_of(fn):
    ext = os.path.splitext(fn)[1].lower().lstrip(".")
    return MIME.get(ext, "application/octet-stream")


def main():
    total_files = 0
    total_bytes = 0
    for sub in SUBS:
        base = os.path.join(IMG_ROOT, sub)
        dbp = os.path.join(DB_DIR, "images_%s.db" % sub)
        if os.path.isfile(dbp):
            os.remove(dbp)
        if not os.path.isdir(base):
            print("  skip (missing subdir): %s" % sub)
            continue
        con = sqlite3.connect(dbp)
        con.execute(
            "CREATE TABLE IF NOT EXISTS images("
            "name TEXT PRIMARY KEY, data BLOB, mime TEXT)"
        )
        n = 0
        b = 0
        for dp, _, fns in os.walk(base):
            for fn in fns:
                full = os.path.join(dp, fn)
                if not os.path.isfile(full):
                    continue
                rel = os.path.relpath(full, base).replace(os.sep, "/")
                key = "img/%s/%s" % (sub, rel)
                with open(full, "rb") as f:
                    data = f.read()
                con.execute(
                    "INSERT OR REPLACE INTO images(name, data, mime) VALUES(?,?,?)",
                    (key, data, mime_of(fn)),
                )
                n += 1
                b += len(data)
        con.commit()
        con.close()
        dbsize = os.path.getsize(dbp)
        total_files += n
        total_bytes += b
        print("  %-12s %6d files  %9.2f MB data  -> images_%s.db (%8.2f MB)"
              % (sub, n, b / 1048576.0, sub, dbsize / 1048576.0))
    print("TOTAL %d files  %.2f MB  across %d sqlite dbs (in %s)"
          % (total_files, total_bytes / 1048576.0, len(SUBS), DB_DIR))


if __name__ == "__main__":
    main()
