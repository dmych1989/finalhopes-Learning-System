# -*- coding: utf-8 -*-
"""生产校验：验证部署后穴位图/药材图可访问 + /renji 页面可加载。
复刻浏览器对图片端点的真实调用：
  - 穴位图(renji 字典)  -> GET /renji/img?name=<key>        (server.py: renji_img, 查询参数)
  - 药材图(yaotu 字典)  -> GET /api/herb_image/<key>        (server.py: herb_image, 路径参数)
图片端点 302 重定向到 CDN 静态路径 /img/{sub}/<file>，这里跟随重定向取最终状态码与 Content-Type。
用法: python tools/verify_prod.py [BASE_URL]
"""
import sys, ssl, urllib.request, urllib.error, urllib.parse

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "https://finalhopes.dynv6.net"
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

RENJI_KEYS = ["八脉交会穴表", "下合六表", "十二经子母补泻表", "丙丁日按时定穴表", "五腧穴表"]
YAOTU_KEYS = ["三七", "丁公藤-原态", "丁香-药材", "龟甲-饮片"]

UA = {"User-Agent": "Mozilla/5.0 prod-verify"}


def head_or_get(path, follow=True):
    url = BASE + path
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=30, context=CTX) as r:
            return r.status, r.headers.get("Content-Type", ""), len(r.read())
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type", ""), 0
    except Exception as e:
        return -1, "ERR:" + str(e), 0


def check_img(label, path):
    st, ct, n = head_or_get(path)
    ok = st == 200 and (ct.startswith("image") or "octet" in ct)
    print(f"  [{'OK' if ok else 'FAIL'}] {label}: {path} -> {st} {ct} ({n}B)")
    return ok


print("BASE =", BASE)
# 1) 页面
st, ct, n = head_or_get("/renji")
page_ok = st == 200 and "text/html" in ct
print(f"  [{'OK' if page_ok else 'FAIL'}] /renji -> {st} {ct} ({n}B)")

# 2) 穴位图(renji, 查询参数)
r_ok = all(check_img(f"renji:{k}", "/renji/img?name=" + urllib.parse.quote(k)) for k in RENJI_KEYS)

# 3) 药材图(yaotu, 路径参数)
y_ok = all(check_img(f"yaotu:{k}", "/api/herb_image/" + urllib.parse.quote(k)) for k in YAOTU_KEYS)

print("PAGE:", "PASS" if page_ok else "FAIL",
      "| RENJI IMG:", "PASS" if r_ok else "FAIL",
      "| YAOTU IMG:", "PASS" if y_ok else "FAIL")
sys.exit(0 if (page_ok and r_ok and y_ok) else 1)
