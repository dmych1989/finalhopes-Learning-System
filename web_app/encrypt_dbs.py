# -*- coding: utf-8 -*-
"""AES 加密 web_app 的 SQLite 数据库，生成 *.db.enc（供 Vercel 安全部署）。

用法：
    python encrypt_dbs.py <passphrase>

会从脚本所在目录（web_app）加密 data.db 与 images_*.db。
解密密钥仅保存在 Vercel 环境变量 DB_DECRYPT_KEY，切勿提交到仓库。

算法：Fernet（AES-128-CBC + HMAC-SHA256），密钥由 passphrase 经 SHA-256 派生。
与 server.py / common.py 中的 _maybe_decrypt / _decrypt_to 配套。
"""
import os
import sys
import base64
import hashlib
from cryptography.fernet import Fernet

HERE = os.path.dirname(os.path.abspath(__file__))
TARGETS = ["data.db"] + [
    "images_%s.db" % s for s in
    ["renji", "shoufa", "tianji", "xuewei", "yaotu_list", "yaotu", "zhongyi"]
]


def derive_key(passphrase):
    return base64.urlsafe_b64encode(hashlib.sha256(passphrase.encode("utf-8")).digest())


def main():
    if len(sys.argv) < 2:
        print("用法: python encrypt_dbs.py <passphrase>")
        return
    f = Fernet(derive_key(sys.argv[1]))
    for name in TARGETS:
        src = os.path.join(HERE, name)
        if not os.path.isfile(src):
            print("跳过(不存在):", name)
            continue
        dst = src + ".enc"
        with open(src, "rb") as fh:
            blob = fh.read()
        enc = f.encrypt(blob)
        with open(dst, "wb") as fh:
            fh.write(enc)
        print("已加密: %s -> %s (%d KB)" % (name, dst, len(enc) // 1024))


if __name__ == "__main__":
    main()
