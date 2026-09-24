# -*- coding: utf-8 -*-
"""Vercel 构建期把核心排盘算法编译为 C 扩展（第四道锁：源码二进制化）。

挂载方式：根 requirements.txt 中的 `-e ./buildtools`，由 @vercel/python 在
Linux 构建容器内执行（本机 Windows 无 WSL/Docker，无法交叉编译 manylinux .so）。

设计原则——失败安全（任何环节失败都不影响部署）：
  * cythonize / C 编译任一步失败 -> 保留 .py 源码，运行时走纯 Python；
  * 只有 paipan / bazi / ziwei 三个模块的 .so 全部生成成功后，才把 .py 覆写为
    桩文件（import 优先级：扩展模块 > .py，桩永不执行，仅防打包器漏收 .so）。

server.py 中的 _NFT_BUNDLED 显式引用 .so 精确文件名
（paipan.cpython-312-x86_64-linux-gnu.so 等，Vercel Python 固定 3.12 x86_64）。
"""
import glob
import os
import traceback

from setuptools import setup
from setuptools.command.build_ext import build_ext as _build_ext

try:
    from Cython.Build import cythonize
except Exception:                                    # cython 不可用 -> 纯 .py
    cythonize = None

WEB = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "..", "web_app"))
TARGETS = ["paipan.py", "bazi.py", "ziwei.py"]
ABI_SO = ".cpython-312-x86_64-linux-gnu.so"

STUB = (
    "# -*- coding: utf-8 -*-\n"
    "# 构建期已把本模块源码编译为 C 扩展并移除源码（防逆向）。\n"
    "# import 优先级为 扩展模块 > .py，本桩仅在 .so 缺失时被加载（异常兜底提示）。\n"
    'raise ImportError("compiled module %s expected; .so missing in bundle")\n'
)


def _so_exists(base):
    return bool(glob.glob(os.path.join(WEB, base + ".*.so")))


class _inplace_build_ext(_build_ext):
    """强制就地生成 .so 到 web_app/，且失败不抛出（回退 .py）。"""

    def run(self):
        self.inplace = True
        try:
            _build_ext.run(self)
        except Exception:
            print("[buildtools] C 扩展编译失败，运行时回退 .py 源码")
            traceback.print_exc()
            return
        ok = [t for t in TARGETS
              if _so_exists(os.path.splitext(t)[0])]
        if len(ok) == len(TARGETS):                  # 全部成功 -> 桩化源码
            for t in TARGETS:
                p = os.path.join(WEB, t)
                try:
                    with open(p, "w", encoding="utf-8") as f:
                        f.write(STUB % os.path.splitext(t)[0])
                    print("[buildtools] stubbed %s (source stripped)" % t)
                except Exception:
                    traceback.print_exc()
        else:
            print("[buildtools] .so 不全 (%d/%d)，保留 .py 源码" % (len(ok), len(TARGETS)))


def _targets():
    if cythonize is None:
        return []
    out = []
    for t in TARGETS:
        base = os.path.splitext(t)[0]
        p = os.path.join(WEB, t)
        # 幂等：同一容器内 setup.py 可能被多次调用（元数据准备 + 实际构建），
        # .so 已存在时跳过，避免把上一轮生成的桩文件再编译一轮。
        if os.path.isfile(p) and not _so_exists(base):
            out.append(p)
    return out


setup(
    name="buildtools",
    version="0.1.0",
    py_modules=[],
    ext_modules=cythonize(_targets(), language_level=3) if _targets() else [],
    cmdclass={"build_ext": _inplace_build_ext},
)
