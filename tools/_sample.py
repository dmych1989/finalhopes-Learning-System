import sys, re, json
sys.path.insert(0, "web_app")
import common

rows = common.load_table("nhxlwj")

# sspl (时事评论) & general articles: find bodies that look like reports
def show(tag, rec):
    print("="*70)
    print(tag, "| MZ:", rec.get("MZ"))
    print("-"*70)
    print((rec.get("NR") or "")[:1500])
    print()

# Sample a few sspl-ish (contain 报道/来源/媒体) bodies
cnt = 0
for r in rows:
    nr = r.get("NR") or ""
    mz = r.get("MZ") or ""
    if ("报道" in nr or "来源" in nr or "媒体" in nr or "记者" in nr) and cnt < 6:
        show("REPORT-LIKE", r)
        cnt += 1

# Scan all for date-like and platform-like lines
date_re = re.compile(r"^\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}|\d{2,4}[.、]\d{1,2}([.、]\d{1,2})?|\d{4}年\d{1,2}月\d{1,2}日)")
plat_hits = {}
date_hits = 0
for r in rows:
    nr = r.get("NR") or ""
    for line in nr.split("\n"):
        s = line.strip()
        if not s: continue
        if date_re.match(s):
            date_hits += 1
        for kw in ["中国时报","联合报","民视","TVBS","中视","台视","三立","东森","新浪","搜狐","网易","腾讯","央视","凤凰","人民网","新华","联合新闻网","苹果日报","自由时报","年代","华视","中天","YouTube","脸书","Facebook","微博","博客","转载","來源","来源","记者","報導","报道","刊於","刊于","本文轉載","轉載自"]:
            if kw in s:
                plat_hits[kw] = plat_hits.get(kw, 0) + 1

print("="*70)
print("DATE-LIKE standalone lines:", date_hits)
print("PLATFORM/SOURCE keyword hits (top):")
for k,v in sorted(plat_hits.items(), key=lambda x:-x[1])[:40]:
    print(f"  {k}: {v}")
