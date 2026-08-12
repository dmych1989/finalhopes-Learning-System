# 倪海厦三套学习系统（论文医案 · 人纪 · 天纪）

倪海厦中医学习系统的网页版，包含三大板块：**论文医案查询系统**、**人纪学习系统**、**天纪学习系统**。后端为 FastAPI，数据存放在 SQLite 数据库与 JSON 数据中，前端为纯静态 HTML/CSS/JS。

## 功能模块

### 一、论文医案查询系统（首页 `/`）
- **医案查询**：按分类浏览与检索临床医案。
- **论文 / 文章查询**：按分类检索医学论文与文章。
- **中药查询**：中药条目检索，含药图。
- **伤寒论条文**（sspl）：条文按分类浏览。
- **黄帝内经条文**（hdwj）：条文检索。
- **八字（四柱）相关内容**（bz）。
- **全文搜索**：按关键词（症状 / 中药 / 医案 / 文章 …）跨板块检索。

### 二、人纪学习系统（`/renji`）
- **十四经络与穴位详解**：含经络走向动画、按时辰取穴。
- **时辰取穴工具**：子午流注 / 灵龟八法 / 纳甲法 / 纳子法。
- **汉唐方剂与取穴**。
- **针灸手法**。
- **药图**：中药图谱。
- **病症取穴**：按病症查阅对应取穴。
- **针灸穴位图表**。

### 三、天纪学习系统（`/tianji`，旧路径 `/mingli` 重定向至此）
- **易经卦象与经文查询**。
- **干支 / 四柱（八字）排盘**。
- **紫微斗数**。
- **命理案例**。
- **目录树浏览与全文搜索**。

### 接口与服务
- 所有数据通过 `/api/...` 以 REST JSON 形式提供（如 `/api/renji/meridians`、`/api/tianji/search`、`/api/cases`、`/api/herbs` 等）。
- 前端静态资源挂载于 `/static`，图片资源挂载于 `/img`。
- 页面：首页 `/`（论文医案）、`/renji`（人纪）、`/tianji`（天纪）；`/mingli` 重定向至 `/tianji`。

## 目录结构

```
finalhopes-Learning-System/
├── web_app/                  # 应用主目录（后端 + 前端 + 数据）
│   ├── server.py             # FastAPI 主程序：所有 API 路由与页面渲染
│   ├── api/
│   │   └── index.py          # Serverless 入口，导出 app（供部署平台调用）
│   ├── static/               # 前端资源（HTML / CSS / JS 与静态数据 JSON）
│   │   ├── index.html        # 论文医案查询系统首页
│   │   ├── renji.html        # 人纪学习系统
│   │   ├── tianji.html       # 天纪学习系统
│   │   ├── app.js            # 论文医案 / 天纪 前端逻辑
│   │   ├── renji_app.js      # 人纪 前端逻辑
│   │   ├── sysbar.js         # 顶部系统切换栏
│   │   ├── style.css         # 全局样式
│   │   └── *.json            # 前端静态数据（经络走向、灵龟八法、子午流注、药图、汉唐取穴等）
│   ├── data.db               # SQLite 主数据库（已精简版入库）
│   ├── renji_db.py           # 人纪数据访问层
│   ├── tianji_db.py          # 天纪数据访问层（懒加载）
│   ├── tianji_tree.py        # 天纪目录树
│   ├── common.py             # 通用工具
│   ├── img_index.py          # 图片索引
│   ├── extra_index.py        # 扩展内容索引
│   ├── lbg_calc.py           # 灵龟八法算法
│   ├── paipan.py             # 排盘算法
│   ├── bazi.py               # 八字算法
│   ├── ziwei.py              # 紫微斗数算法
│   ├── start.py              # 本地启动脚本（自动装依赖 + 启动 uvicorn）
│   └── *.json                # 后端数据（汉唐取穴、神农本草、黄帝内经、八字/伤寒论映射、文章分类、扩展数据等）
├── api/
│   └── index.py              # Serverless 入口（与 web_app/api/index.py 对应）
├── public/img/               # 图片资源（穴位图 renji/、药图 yaotu_list/ 等），由部署脚本上传
├── tools/                    # 构建与部署脚本（MDB→SQLite 转换、目录树生成、部署等）
├── requirements.txt          # Python 依赖：fastapi / uvicorn / cnlunar
└── vercel.json               # 部署平台配置
```

## 本地运行

```bash
cd web_app
python start.py        # 自动安装依赖并启动，访问 http://127.0.0.1:8000
```

或使用虚拟环境手动启动：

```bash
cd web_app
pip install -r requirements.txt
python -m uvicorn server:app --host 127.0.0.1 --port 8000
```
