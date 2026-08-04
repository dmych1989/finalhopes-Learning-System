# -*- coding: utf-8 -*-
"""Scan the external 《中医》 GitHub repo and build an in-memory index of
acupoint (穴位) and herb-image (中药图片) material for the web app.

Two data sources:
  1. <BASE>/穴位  — acupoints grouped by 经络 (meridian). Each meridian folder
     holds `<穴名>.md` (text) + `<穴名>.png` (image) per point. Top-level
     `<经络>.gif` files are whole-meridian pathway diagrams (used as banners).
     Auxiliary folders: 董氏奇穴 (.txt), 治疗法 (会郄/俞募/原络/子母 .txt),
     图谱 (腹针 / 人体全息投影图 / 经络总图, images only).
  2. <BASE>/本草/中药图片 — herb photos grouped by function folder
     (e.g. `2-清热药`). Each folder holds `<药名>.jpg/.png`.

The result is a plain dict (JSON-serializable) so server.py can serve it
directly. Image bytes are NOT embedded — only relative paths under BASE,
resolved at request time by the `/extimg` route.
"""
import os
import re

BASE = r"E:/Soft/GitHub/中医"
XUEWEI_DIR = os.path.join(BASE, "穴位")
HERB_DIR = os.path.join(BASE, "本草", "中药图片")

# Ordered meridian definition: (key, 显示名, 文件夹名)
MERIDIANS = [
    ("fei",     "肺经",   "手太阴 肺经 寅时 3-5点"),
    ("chang",   "大肠经", "手阳明 大肠经 卯时 5-7点"),
    ("wei",     "胃经",   "足阳明 胃经 辰时 7-9点"),
    ("pi",      "脾经",   "足太阴 脾经 已时 9-11点"),
    ("xin",     "心经",   "手少阴 心经 午时 11-13点"),
    ("xiao",    "小肠经", "手太阳 小肠经 未时 13-15点"),
    ("pang",    "膀胱经", "足太阳 膀胱经 申时 15-17点"),
    ("shen",    "肾经",   "足少阴 肾经 酉时 17-19点"),
    ("bao",     "心包经", "手厥阴 心包经 戌时 19-21点"),
    ("jiao",    "三焦经", "手少阳 三焦经 亥时 21-23点"),
    ("dan",     "胆经",   "足少阳 胆经 子时 23-1点"),
    ("gan",     "肝经",   "足厥阴 肝经 丑时 1-3点"),
    ("ren",     "任脉",   "任脉"),
    ("du",      "督脉",   "督脉"),
    ("jingwai", "经外奇穴", "经外奇穴"),
    ("buchong", "补充",   "补充"),
]
# Auxiliary (non-meridian) categories, appended after meridians.
AUX_CATS = [
    ("dongshi", "董氏奇穴"),
    ("zhiliao", "治疗法"),
    ("tupu",    "图谱"),
]

IMG_EXTS = (".jpg", ".jpeg", ".png", ".gif", ".bmp")


def _read_text(path):
    try:
        with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
            return f.read().strip()
    except Exception:
        return ""


def _rel(path):
    """Relative path under BASE, using forward slashes for URLs."""
    return os.path.relpath(path, BASE).replace("\\", "/")


def _list_img(folder):
    out = []
    if not os.path.isdir(folder):
        return out
    for fn in sorted(os.listdir(folder)):
        if fn.lower().endswith(IMG_EXTS):
            out.append(fn)
    return out


def _build_xuewei():
    points = []
    cats = []

    # ---- meridian categories (md + png per point) ----
    for key, label, folder in MERIDIANS:
        fdir = os.path.join(XUEWEI_DIR, folder)
        diagram = None
        gif = os.path.join(XUEWEI_DIR, label + ".gif")
        if os.path.isfile(gif):
            diagram = _rel(gif)
        count = 0
        if os.path.isdir(fdir):
            # md files define the points; pair with optional png
            mds = [f for f in sorted(os.listdir(fdir)) if f.lower().endswith(".md")]
            for fn in mds:
                name = fn[:-3]
                png = os.path.join(fdir, name + ".png")
                imgs = [_rel(png)] if os.path.isfile(png) else []
                content = _read_text(os.path.join(fdir, fn))
                points.append({
                    "name": name, "cat": key, "cat_name": label,
                    "sub": "", "content": content, "images": imgs,
                })
                count += 1
        cats.append({"key": key, "label": label, "count": count, "diagram": diagram})

    # ---- 董氏奇穴: nested .txt, no images ----
    dong_dir = os.path.join(XUEWEI_DIR, "董氏奇穴")
    dcount = 0
    if os.path.isdir(dong_dir):
        for root, _dirs, files in os.walk(dong_dir):
            for fn in sorted(files):
                if fn.lower().endswith(".txt"):
                    name = fn[:-4]
                    sub = os.path.relpath(root, dong_dir).replace("\\", "/")
                    if sub == ".":
                        sub = ""
                    points.append({
                        "name": name, "cat": "dongshi", "cat_name": "董氏奇穴",
                        "sub": sub, "content": _read_text(os.path.join(root, fn)),
                        "images": [],
                    })
                    dcount += 1
    cats.append({"key": "dongshi", "label": "董氏奇穴", "count": dcount, "diagram": None})

    # ---- 治疗法: 会郄/俞募/原络/子母 folders, each .txt ----
    zhiliao_dirs = ["会郄治疗", "俞募治疗", "原络治疗法", "子母补泻"]
    zcount = 0
    for zdir in zhiliao_dirs:
        fdir = os.path.join(XUEWEI_DIR, zdir)
        if not os.path.isdir(fdir):
            continue
        for fn in sorted(os.listdir(fdir)):
            if fn.lower().endswith(".txt"):
                name = fn[:-4]
                points.append({
                    "name": name, "cat": "zhiliao", "cat_name": "治疗法",
                    "sub": zdir, "content": _read_text(os.path.join(fdir, fn)),
                    "images": [],
                })
                zcount += 1
    cats.append({"key": "zhiliao", "label": "治疗法", "count": zcount, "diagram": None})

    # ---- 图谱: 腹针 / 人体全息投影图 / 经络总图 (images only) ----
    tcount = 0
    tupu_subs = [
        ("腹针", "腹针"),
        ("人体全息投影图", "人体全息投影图"),
    ]
    for subdir, sublabel in tupu_subs:
        fdir = os.path.join(XUEWEI_DIR, subdir)
        for fn in _list_img(fdir):
            name = os.path.splitext(fn)[0]
            points.append({
                "name": name, "cat": "tupu", "cat_name": "图谱",
                "sub": sublabel, "content": "",
                "images": [_rel(os.path.join(fdir, fn))],
            })
            tcount += 1
    # general charts at XUEWEI_DIR root
    for fn in ["子午流注图.jpg", "经络.jpg"]:
        fp = os.path.join(XUEWEI_DIR, fn)
        if os.path.isfile(fp):
            points.append({
                "name": os.path.splitext(fn)[0], "cat": "tupu", "cat_name": "图谱",
                "sub": "经络总图", "content": "",
                "images": [_rel(fp)],
            })
            tcount += 1
    cats.append({"key": "tupu", "label": "图谱", "count": tcount, "diagram": None})

    return {"cats": cats, "points": points, "total": len(points)}


def _natural_key(s):
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", s)]


def _build_herb_imgs():
    items = []
    cats = []
    if not os.path.isdir(HERB_DIR):
        return {"cats": cats, "items": items, "total": 0}
    folders = sorted(os.listdir(HERB_DIR), key=_natural_key)
    for folder in folders:
        fdir = os.path.join(HERB_DIR, folder)
        if not os.path.isdir(fdir):
            continue
        # group images by base name (strip trailing digits/underscore)
        groups = {}
        for fn in sorted(os.listdir(fdir)):
            if not fn.lower().endswith(IMG_EXTS):
                continue
            stem = os.path.splitext(fn)[0]
            base = re.sub(r"[\d_]+$", "", stem)
            if not base:
                base = stem
            groups.setdefault(base, []).append(_rel(os.path.join(fdir, fn)))
        count = 0
        for name, imgs in groups.items():
            items.append({
                "name": name, "cat": folder, "cat_label": folder,
                "images": imgs, "_folder": True,
                "_rel": imgs[0],
            })
            count += 1
        cats.append({"key": folder, "label": folder, "count": count})
    return {"cats": cats, "items": items, "total": len(items)}


def build():
    return {
        "xuewei": _build_xuewei(),
        "herb_imgs": _build_herb_imgs(),
    }


if __name__ == "__main__":
    import json
    data = build()
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "extra_data.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    print("xuewei points:", data["xuewei"]["total"],
          "categories:", len(data["xuewei"]["cats"]))
    print("herb_imgs items:", data["herb_imgs"]["total"],
          "categories:", len(data["herb_imgs"]["cats"]))
    for c in data["xuewei"]["cats"]:
        print("  xw", c["key"], c["label"], c["count"])
    for c in data["herb_imgs"]["cats"]:
        print("  hi", c["key"], c["count"])
