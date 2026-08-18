# -*- coding: utf-8 -*-
"""Gap-fill recovery for 针灸穴位总结图表 (MDB nishitu).

Only writes charts whose file is missing or empty; does NOT touch the other
386 already-built files. Per-row retry to survive the occasional HY000 blob
lock hiccup. Regenerates 索引.txt with the full success/failure list.
"""
import os, sys, re

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "web_app"))
import common

ROOT = r"E:/Soft/倪海夏三套学习系统/QQ频道号talktyph0id/人纪学习系统"
MDB  = os.path.join(ROOT, "Data", "LILUN.mdb")
TARGET = os.path.join(ROOT, "倪师傅经验", "针灸穴位总结图表")

common.DB = MDB
common.PWD = "JiSkS92A30"
common.USE_SQLITE = False


def safe_fn(name):
    s = re.sub(r'[\\/:*?"<>|]', '_', name)
    return s.strip() or "_"


def main():
    os.makedirs(TARGET, exist_ok=True)
    conn = common.connect()
    cur = conn.cursor()
    cur.execute("SELECT MZ, NR FROM [nishitu]")

    saved, failed = [], []
    existing_before = len([f for f in os.listdir(TARGET) if f.lower().endswith(".jpg")])

    while True:
        row = None
        for attempt in range(4):  # retry flaky reads
            try:
                row = cur.fetchone()
                break
            except Exception as e:
                if attempt == 3:
                    failed.append(("FETCH", str(e)[:80]))
                    row = "BREAK"
                continue
        if row == "BREAK":
            break
        if row is None:
            break

        mz, nr = row[0], row[1]
        if not isinstance(nr, (bytes, bytearray)) or len(nr) < 100:
            continue
        try:
            plain = common.decrypt_bytes(nr)
        except Exception as e:
            failed.append((mz, "decrypt:" + str(e)[:60]))
            continue
        if plain[:3] != b'\xff\xd8\xff':
            failed.append((mz, "not-jpeg-after-decrypt"))
            continue

        fn = safe_fn(mz) + ".jpg"
        path = os.path.join(TARGET, fn)
        # skip if already a valid non-trivial jpg of similar size
        if os.path.exists(path) and os.path.getsize(path) >= len(plain) - 64:
            saved.append((mz, fn))  # already present
            continue
        try:
            open(path, "wb").write(plain)
            saved.append((mz, fn))
        except Exception as e:
            failed.append((mz, "write:" + str(e)[:60]))

    existing_after = len([f for f in os.listdir(TARGET) if f.lower().endswith(".jpg")])

    with open(os.path.join(TARGET, "索引.txt"), "w", encoding="utf-8") as f:
        f.write(f"针灸穴位总结图表（倪师图，来自 MDB nishitu 表）  成功 {len(saved)} / 失败 {len(failed)}\n")
        f.write("=" * 60 + "\n\n")
        for mz, fn in saved:
            f.write(f"  {mz}  →  {fn}\n")
        if failed:
            f.write(f"\n失败 {len(failed)} 项：\n")
            for mz, why in failed:
                f.write(f"  ! {mz}  ({why})\n")

    print(f"目录内 jpg 数: 恢复前={existing_before} → 恢复后={existing_after}")
    print(f"本次索引计入成功 {len(saved)} 项, 失败 {len(failed)} 项")
    if failed:
        print("剩余失败:")
        for mz, why in failed:
            print(f"   ! {mz} ({why})")
    conn.close()


if __name__ == "__main__":
    main()
