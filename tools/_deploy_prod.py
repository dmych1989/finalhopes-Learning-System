# 把「完整文件列表」以 target=production 创建部署（所有 blob 已存在，秒级），自动 promotion 为线上版本。
import os, sys, json, base64, subprocess, time, urllib.request, urllib.error, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEAM = "team_AUEOwID6emZlHoTjyvmre3gV"
PROJECT = "prj_5FqANpHobhjTmTTGWWM39bhhRmHY"
BASE = "https://api.vercel.com"
EXCLUDE = {"tools/exe_strings.txt"}
# 图片不再作为独立静态文件随站部署：2239 张 public/img/* 会让部署包文件数爆炸
# （HOBBY 拥塞下 Downloading 2315 files 超时 → state=ERROR）。改由 tools/pack_images.py
# 把全部图片打包进按子目录拆分的 SQLite 库 web_app/images_<sub>.db（共 ~96MB、7 个文件），
# 经 server.py 的 /api/img/<name> 端点按需返回。故 public/img/ 整体跳过不部署；
# images_*.db 作为普通文件随 git 追踪、按内容 sha 增量上传（首次上传，之后引用旧 blob）。
SKIP_PREFIXES = ("public/img/",)
STATE_FILE = os.path.join(ROOT, ".vercel_deploy_state.json")


def auth_token():
    return json.load(open(os.path.expanduser("~/.vercel/auth.json"), encoding="utf-8-sig"))["token"]


def apiget(path, token, attempts=5, persist=False):
    """GET JSON with retry on transient network/SSL errors.
    persist=True（只读状态轮询用）：对瞬时网络/SSL 错误无限退避重试、绝不抛异常，
    避免 api.vercel.com 偶发 SSL 抖动（UNEXPECTED_EOF_WHILE_READING）让整个部署进程自杀。
    4xx/5xx 客户端错误始终立即抛出（不重试）。"""
    last = None
    i = 0
    while True:
        req = urllib.request.Request("https://api.vercel.com" + path)
        req.add_header("Authorization", "Bearer %s" % token)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read().decode("utf-8")
            return json.loads(raw)
        except urllib.error.HTTPError as e:
            raise  # 4xx/5xx 客户端错误不重试，直接抛
        except Exception as e:
            last = e
            if not persist and i >= attempts - 1:
                break
            i += 1
            wait = min(30, 3 * (2 ** min(i, 4)))
            print("  apiget attempt %d failed: %s (retry in %ds)" % (i, e, wait))
            time.sleep(wait)
    if last:
        raise last
    raise RuntimeError("apiget exhausted attempts")


def apipost(path, token, body, attempts=3, timeout=120):
    """POST JSON. On network errors, retry. On 4xx client errors, return the
    status+body immediately (caller decides how to recover) instead of raising —
    this is what lets the missing_files recovery in main() actually run."""
    data = json.dumps(body).encode("utf-8")
    last = None
    for i in range(attempts):
        req = urllib.request.Request("https://api.vercel.com" + path, data=data, method="POST")
        req.add_header("Authorization", "Bearer %s" % token)
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            txt = e.read().decode("utf-8", "replace")
            try:
                body_e = json.loads(txt)
            except Exception:
                body_e = {"raw": txt}
            if 400 <= e.code < 500:
                print("  HTTPError %s (client, non-retryable): %s" % (e.code, txt[:400]))
                return e.code, body_e
            print("  HTTPError %s attempt %d: %s" % (e.code, i + 1, txt[:400]))
            last = e
        except Exception as e:
            last = e
            print("  attempt %d failed: %s" % (i + 1, e))
        time.sleep(3)
    if last:
        raise last
    raise RuntimeError("apipost exhausted attempts")


def get_prev_paths(token):
    j = apiget("/v6/deployments?teamId=%s&projectId=%s&limit=1" % (TEAM, PROJECT), token)
    uid = j["deployments"][0].get("uid")
    tree = apiget("/v13/deployments/%s/files?teamId=%s" % (uid, TEAM), token)
    prev = set()

    def walk(n, p=""):
        nm = n.get("name", "")
        path = (p + "/" + nm) if p else nm
        if n.get("type") == "directory":
            for c in n.get("children", []):
                walk(c, path)
        else:
            key = path[4:] if path.startswith("src/") else path
            prev.add(key)

    for t in tree:
        walk(t)
    return prev


def load_deploy_state():
    """Returns (prev_commit, shas). prev_commit = commit of the last successful
    deploy (used to compute git-diff of committed changes); shas is a path->sha
    map kept for diagnostics/future use."""
    try:
        d = json.load(open(STATE_FILE, encoding="utf-8"))
        return d.get("commit"), d.get("shas", {})
    except Exception:
        return None, {}


def save_deploy_state(commit, shas):
    tmp = STATE_FILE + ".tmp"
    json.dump({"commit": commit, "shas": shas}, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
    os.replace(tmp, STATE_FILE)


def head_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception as e:
        print("  git rev-parse HEAD failed:", e)
        return None


def changed_files(prev_commit):
    """Files that differ from the last deployed commit (committed changes) plus
    any uncommitted working-tree changes. These MUST be force-uploaded — referencing
    them by content-sha would point at a blob that does not yet exist on Vercel."""
    res = set()
    if prev_commit:
        try:
            a = subprocess.check_output(
                ["git", "diff", "--name-only", prev_commit, "HEAD"], cwd=ROOT, text=True
            ).splitlines()
            res |= set(a)
        except Exception as e:
            print("  git commit-diff (%s) failed — falling back to retry: %s" % (prev_commit, e))
    try:
        b = subprocess.check_output(["git", "diff", "--name-only", "HEAD"], cwd=ROOT, text=True).splitlines()
        res |= set(b)
    except Exception as e:
        print("  git working-tree diff failed:", e)
    return res


def tracked_files():
    out = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT, text=True).split("\0")
    res = []
    for f in out:
        if not f or f in EXCLUDE or f.startswith(".git/") or "__pycache__" in f:
            continue
        if os.path.isfile(os.path.join(ROOT, f)):
            res.append(f)
    return res


def disk_img_files():
    """历史遗留：早期用于把 public/img 下未强追踪的图片补进部署。
    现图片已统一打包进 web_app/images_<sub>.db 随 git 部署，public/img 整体跳过，
    此函数不再贡献任何文件（保留签名以兼容 build_files 调用）。"""
    return []


def build_files(token, prev_paths, changed, force=set()):
    tracked = set(tracked_files()) | set(disk_img_files())
    overlay = set()
    for f in tracked:
        if any(f.startswith(s) for s in SKIP_PREFIXES):
            continue
        # 新文件（Vercel 上不存在）或相对上次部署有内容变化的文件 → 必须上传。
        if f not in prev_paths or f in changed:
            overlay.add(f)
    overlay |= force
    files = []
    cur_shas = {}
    for f in sorted(tracked):
        if any(f.startswith(s) for s in SKIP_PREFIXES):
            continue
        p = os.path.join(ROOT, f)
        data = open(p, "rb").read()
        sha = hashlib.sha1(data).hexdigest()
        size = len(data)
        cur_shas[f] = sha
        if f in prev_paths and f not in overlay:
            # 内容未变且上次部署已存在 → 直接引用已持久化的 blob（秒级）。
            files.append({"file": f, "sha": sha, "size": size})
        else:
            if f.startswith("public/img/") or size > 4 * 1024 * 1024:
                ok = False
                for i in range(12):
                    req = urllib.request.Request("%s/v2/files?teamId=%s" % (BASE, TEAM), data=data, method="POST")
                    req.add_header("Authorization", "Bearer %s" % token)
                    req.add_header("Content-Type", "application/octet-stream")
                    req.add_header("x-vercel-digest", sha)
                    try:
                        with urllib.request.urlopen(req, timeout=60) as r:
                            print("  hashed %s (%dKB)" % (f, size // 1024)); ok = True; break
                    except Exception as e:
                        print("  upload attempt %d %s failed: %s" % (i + 1, f, e)); time.sleep(2 + i * 2)
                if not ok:
                    raise RuntimeError("upload failed %s" % f)
                files.append({"file": f, "sha": sha, "size": size})
            else:
                files.append({"file": f, "data": base64.b64encode(data).decode("ascii"), "encoding": "base64"})
    print("files total:", len(files), "uploaded:", len(overlay))
    return files, cur_shas


def map_missing_to_paths(missing):
    """Map missing blob hashes back to current local files (tracked + disk img)."""
    cur = {}
    for f in set(tracked_files()) | set(disk_img_files()):
        if any(f.startswith(s) for s in SKIP_PREFIXES):
            continue
        cur[hashlib.sha1(open(os.path.join(ROOT, f), "rb").read()).hexdigest()] = f
    force = set()
    for h in missing:
        if h in cur:
            force.add(cur[h])
        else:
            print("  WARN unmatched missing hash:", h)
    return force


def delete_deployment(token, did):
    # Vercel API 当前 SSL 抖动频繁，删除必须重试，否则冻结重试时 DELETE 静默失败、
    # 留下孤儿部署持续占用 HOBBY 唯一构建槽，导致后续部署无限 QUEUED。
    for _ in range(8):
        req = urllib.request.Request("%s/v13/deployments/%s?teamId=%s" % (BASE, did, TEAM), method="DELETE")
        req.add_header("Authorization", "Bearer %s" % token)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                print("  deleted deployment", did, "status", r.status)
                return True
        except urllib.error.HTTPError as e:
            print("  delete HTTP", e.code, did); return False
        except Exception as e:
            print("  delete attempt failed", did, e)
            time.sleep(6)
    print("  delete giving up", did)
    return False


def create_deployment(token, files):
    body = {"name": "finalhopes-learning-system", "target": "production", "project": PROJECT, "files": files}
    return apipost("/v13/deployments?teamId=%s&forceNew=1&skipAutoDetectionConfirmation=1" % TEAM, token, body)


def main():
    token = auth_token()
    prev_commit, _ = load_deploy_state()
    prev_paths = get_prev_paths(token)
    if prev_commit is None:
        # First deploy with the new state tracking: we cannot git-diff against the
        # last deployed commit, so upload EVERYTHING to guarantee correctness
        # (in particular committed content changes get pushed, not just referenced).
        # Subsequent deploys are incremental via git diff <prev_commit> HEAD.
        changed = set(tracked_files()) | set(disk_img_files())
        print("no deploy state — uploading ALL %d files (one-time, ensures committed changes ship)" % len(changed))
    else:
        changed = changed_files(prev_commit)
        if changed:
            print("committed/working changes since %s: %d files" % (prev_commit, len(changed)))
    # 防御性：除 public/img 图片外的所有文件（代码/静态 JSON/HTML/CSS/JS/DB）永远按当前内容
    # 强制上传，绝不引用旧 blob。增量部署若把旧版 server.py 与新版 data.db/前端错配，会在导入期
    # 崩溃（如旧 server.py 顶层 get_yaotu_images() 引用已删除的 yaotu_img 表）或使前端修复失效。
    # 例外：web_app/images_*.db 是图片包，按 git 追踪内容 sha 增量上传（首次上传、之后引用旧 blob），
    # 不每次强制重传（避免每次部署都重传 ~96MB）。
    force_backend = {f for f in (set(tracked_files()) | set(disk_img_files()))
                     if not f.startswith("public/img/")
                     and not f.startswith("web_app/images_")}
    changed |= force_backend
    print("forced non-image files: %d" % len(force_backend))
    files, cur_shas = build_files(token, prev_paths, changed)
    inline = sum(len(f.get("data", "")) for f in files) / 1024 / 1024
    print("inline ~%.2f MB" % inline)

    # 最多 10 次完整部署尝试；每次内部对 400 missing_files 自愈，对平台级
    # post-build 卡死（HOBBY 偶发，可能持续数十分钟）自动 DELETE 后冷却重试。
    for deploy_attempt in range(10):
        st, j = create_deployment(token, files)
        if st not in (200, 201):
            err = (j or {}).get("error", {})
            if st == 400 and err.get("code") == "missing_files":
                missing = set(err.get("missing", []))
                print("  missing_files: %s — remapping & force-uploading" % missing)
                force = map_missing_to_paths(missing)
                if force:
                    files, cur_shas = build_files(token, prev_paths, changed, force=force)
                    inline = sum(len(f.get("data", "")) for f in files) / 1024 / 1024
                    print("  retry inline ~%.2f MB (forced %d files)" % (inline, len(force)))
                    st, j = create_deployment(token, files)
            if st not in (200, 201):
                print("CREATE FAILED", st, json.dumps(j)[:800]); sys.exit(1)
        did = j["id"]
        print("production id=", did, "(attempt %d)" % (deploy_attempt + 1))
        frozen = False
        for i in range(620):
            d = apiget("/v13/deployments/%s?teamId=%s" % (did, TEAM), token, persist=True)
            status = d.get("status")
            print("[%d] status=%s aliasAssigned=%s" % (i, status, d.get("aliasAssigned")))
            if status == "READY":
                print("READY url=", d.get("url"))
                # 部署成功：持久化本次 commit + 全部 sha，供下次精准检测内容变化。
                save_deploy_state(head_commit(), cur_shas)
                return
            if status in ("ERROR", "CANCELED"):
                print("FAILED/ERROR — deleting, cooling 120s, retrying", json.dumps(d)[:400])
                delete_deployment(token, did)
                time.sleep(120)
                frozen = True
                break
            # 平台级 post-build 卡死（HOBBY 偶发）：BUILDING 超过 ~30 分钟无进展才删掉重试。
            # 阈值调高（原 18 分钟）：当前 HOBBY 负载下 Python 构建常需 20-30 分钟，
            # 避免把「缓慢推进但正常」的构建误判为冻结而反复删除重来（每次删除还需占槽冷却）。
            if i >= 500 and status in (None, "BUILDING", "QUEUED"):
                print("  freeze suspected (%d polls, ~%.0f min) — deleting, cooling 120s, retrying" % (i, i * 6 / 60))
                delete_deployment(token, did)
                time.sleep(120)  # 给 Vercel 拥塞的构建槽恢复时间，降低下一轮再次卡死概率
                frozen = True
                break
            time.sleep(6)
        if frozen:
            continue
        # 走到这里说明 poll 超时（160 轮 ≈ 16 分钟）仍未 READY/ERROR。
        print("poll timeout (deployment may still be finalizing) — deleting and retrying")
        delete_deployment(token, did)
    print("deploy failed after retries")
    sys.exit(1)


if __name__ == "__main__":
    main()
