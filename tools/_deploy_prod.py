# 把「完整文件列表」以 target=production 创建部署（所有 blob 已存在，秒级），自动 promotion 为线上版本。
import os, sys, json, base64, subprocess, time, urllib.request, urllib.error, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEAM = "team_AUEOwID6emZlHoTjyvmre3gV"
PROJECT = "prj_5FqANpHobhjTmTTGWWM39bhhRmHY"
BASE = "https://api.vercel.com"
EXCLUDE = {"tools/exe_strings.txt"}
SKIP_PREFIXES = ("public/img/yaotu_list/",)
STATE_FILE = os.path.join(ROOT, ".vercel_deploy_state.json")


def auth_token():
    return json.load(open(os.path.expanduser("~/.vercel/auth.json"), encoding="utf-8-sig"))["token"]


def apiget(path, token):
    req = urllib.request.Request("https://api.vercel.com" + path)
    req.add_header("Authorization", "Bearer %s" % token)
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read().decode("utf-8")
    return json.loads(raw)


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
    """public/img 下所有磁盘文件（排除 SKIP_PREFIXES），不依赖 git 追踪状态。
    防止新增/未强追踪的图片漏部署（如 public/img/shoufa）。"""
    res = []
    base = os.path.join(ROOT, "public", "img")
    if not os.path.isdir(base):
        return res
    for dp, _, fns in os.walk(base):
        for fn in fns:
            full = os.path.join(dp, fn)
            rel = "public/img/" + os.path.relpath(full, base).replace(os.sep, "/")
            if any(rel.startswith(s) for s in SKIP_PREFIXES):
                continue
            res.append(rel)
    return res


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
    req = urllib.request.Request("%s/v13/deployments/%s?teamId=%s" % (BASE, did, TEAM), method="DELETE")
    req.add_header("Authorization", "Bearer %s" % token)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print("  deleted deployment", did, "status", r.status)
    except Exception as e:
        print("  delete failed", did, e)


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
    files, cur_shas = build_files(token, prev_paths, changed)
    inline = sum(len(f.get("data", "")) for f in files) / 1024 / 1024
    print("inline ~%.2f MB" % inline)

    # 最多 3 次完整部署尝试；每次内部对 400 missing_files 自愈，对平台级
    # post-build 卡死（HOBBY 偶发）自动 DELETE 后重试。
    for deploy_attempt in range(3):
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
        for i in range(160):
            d = apiget("/v13/deployments/%s?teamId=%s" % (did, TEAM), token)
            status = d.get("status")
            print("[%d] status=%s aliasAssigned=%s" % (i, status, d.get("aliasAssigned")))
            if status == "READY":
                print("READY url=", d.get("url"))
                # 部署成功：持久化本次 commit + 全部 sha，供下次精准检测内容变化。
                save_deploy_state(head_commit(), cur_shas)
                return
            if status in ("ERROR", "CANCELED"):
                print("FAILED", json.dumps(d)[:800]); break
            # 平台级 post-build 卡死（HOBBY 偶发）：BUILDING 超过 ~8 分钟无进展即删掉重试。
            if i >= 80 and status in (None, "BUILDING", "QUEUED"):
                print("  freeze suspected (%d polls, ~%.0f min) — deleting and retrying" % (i, i * 6 / 60))
                delete_deployment(token, did)
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
