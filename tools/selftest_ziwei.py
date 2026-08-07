"""紫微斗数引擎自测：用 APK(mingli-master) 的 buildChart 产出真值，
逐盘比对后端 ziwei.ziwei_chart 的辅星/杂曜落宫是否一致（对齐 APK）。

比对规则：
  - 以 APK 输出的 minor+adjective 星集合为基准（真值）。
  - APK 有而 Python 缺失/错位 -> FAIL（必须修复）。
  - Python 有而 APK 没有 -> INFO（多为补充完整性星，如月解，可接受）。
  - 额外校验 命宫地支 与 五行局 是否一致（决定长生十二神定点）。

运行：python tools/selftest_ziwei.py
fixture: tools/ziwei_fixture.json（由 APK 生成，已随仓库存档）。
"""
import json
import os
import sys
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
WEB_APP = os.path.join(os.path.dirname(HERE), "web_app")
sys.path.insert(0, WEB_APP)

from ziwei import ziwei_chart, ZHI  # noqa: E402

FIXTURE = os.path.join(HERE, "ziwei_fixture.json")

# (公历日期, 时辰地支序 0-11, 性别) —— 与 fixture 生成器保持一致
CASES = [
    ("1989-11-05", 6, "男"),
    ("1989-11-05", 6, "女"),
    ("1985-06-15", 2, "男"),
    ("1992-03-20", 10, "女"),
    ("2000-12-25", 4, "男"),
    ("1976-07-04", 8, "女"),
    ("1984-02-02", 1, "男"),
    ("1995-09-09", 3, "女"),
    ("2001-05-01", 9, "男"),
    ("1978-10-10", 0, "女"),
]


def build_python(date_str, hb, gender):
    y, mo, d = map(int, date_str.split("-"))
    hour = 2 * hb  # 子0->0, 丑1->2 ... 与 APK hourIndex 同支
    dt = datetime.datetime(y, mo, d, hour)
    chart = ziwei_chart(dt, gender)
    py = {}
    for z in range(12):
        stars = [s["name"] for s in chart["palace"][z]["stars"]
                 if s["kind"] in ("minor", "adjective")]
        py[ZHI[z]] = sorted(stars)
    return py, chart["ming_gong"]["zhi"], chart["ju"]


def main():
    with open(FIXTURE, encoding="utf-8") as f:
        fixture = json.load(f)

    fails = 0
    infos = 0
    meta_bad = 0
    for date_str, hb, gender in CASES:
        key = f"{date_str} h{hb} {gender}"
        apk = fixture[key]["stars"]
        apk_soul = fixture[key]["soul"]
        apk_five = fixture[key]["five"]
        py, py_soul, py_five = build_python(date_str, hb, gender)

        # 命宫 / 五行局 一致性
        if apk_soul != py_soul:
            print(f"META FAIL {key}: 命宫 APK={apk_soul} PY={py_soul}")
            meta_bad += 1
        if apk_five != py_five:
            print(f"META FAIL {key}: 五行局 APK={apk_five} PY={py_five}")
            meta_bad += 1

        for branch in sorted(set(py) | set(apk)):
            ps = set(py.get(branch, []))
            aset = set(apk.get(branch, []))
            missing = aset - ps
            extra = ps - aset
            if missing:
                print(f"FAIL {key} {branch}宫: 缺失/错位 {sorted(missing)} "
                      f"(APK该宫={sorted(aset)})")
                fails += len(missing)
            if extra:
                print(f"INFO {key} {branch}宫: Python多出 {sorted(extra)}")
                infos += len(extra)

    print("-" * 60)
    print(f"命宫/五行局不一致: {meta_bad}")
    print(f"辅星杂曜 FAIL(APK有而Python缺失/错位): {fails}")
    print(f"Python 多出星 INFO: {infos}")
    if meta_bad or fails:
        print("结果: 不通过，需修复。")
        sys.exit(1)
    print("结果: 全部对齐 APK（含补充完整性星）。")


if __name__ == "__main__":
    main()
