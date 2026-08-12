# 把「完整文件列表」以 target=production 创建部署（所有 blob 已存在，秒级），自动 promotion 为线上版本。
import os, sys, json, base64, subprocess, time, urllib.request, urllib.error, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEAM = "team_AUEOwID6emZlHoTjyvmre3gV"
PROJECT = "prj_5FqANpHobhjTmTTGWWM39bhhRmHY"
BASE = "https://api.vercel.com"
EXCLUDE = {"tools/exe_strings.txt"}
SKIP_PREFIXES = ("public/img/yaotu_list/",)


def auth_token():
    return json.load(open(os.path.expanduser("~/.vercel/auth.json"), encoding="utf-8-sig"))["token"]


def apiget(path, token):
    req = urllib.request.Request("https://api.vercel.com" + path)
    req.add_header("Authorization", "Bearer %s" % token)
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read().decode("utf-8")
    return json.loads(raw)


def apipost(path, token, body, attempts=5, timeout=120):
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
            last = e
            txt = e.read().decode("utf-8", "replace")
            print("  HTTPError %s attempt %d: %s" % (e.code, i + 1, txt[:400]))
            if e.code < 500:
                raise
        except Exception as e:
            last = e
            print("  attempt %d failed: %s" % (i + 1, e))
        time.sleep(3)
    raise last


def get_prev_paths(token):
    j = apiget("/v6/deployments?teamId=%s&projectId=%s&limit=1" % (TEAM, PROJECT), token)
    uid = j["deployments"][0].get("uid")
    tree = apiget("/v13/deployments/%s/files?teamId=%s" % (uid, TEAM), token)
    prev = set()
    prev_shas = {}

    def walk(n, p=""):
        nm = n.get("name", "")
        path = (p + "/" + nm) if p else nm
        if n.get("type") == "directory":
            for c in n.get("children", []):
                walk(c, path)
        else:
            key = path[4:] if path.startswith("src/") else path
            prev.add(key)
            s = n.get("sha")
            if s:
                prev_shas[key] = s

    for t in tree:
        walk(t)
    return prev, prev_shas


def tracked_files():
    out = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT, text=True).split("\0")
    res = []
    for f in out:
        if not f or f in EXCLUDE or f.startswith(".git/") or "__pycache__" in f:
            continue
        if os.path.isfile(os.path.join(ROOT, f)):
            res.append(f)
    return res


def modified_files():
    a = subprocess.check_output(["git", "diff", "--name-only"], cwd=ROOT, text=True).splitlines()
    b = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True).splitlines()
    return set(a) | set(b)


def build_files(token, prev_paths, prev_shas, force=set()):
    tracked = set(tracked_files())
    mod = modified_files()
    overlay = set()
    for f in tracked:
        if any(f.startswith(s) for s in SKIP_PREFIXES):
            continue
        if f not in prev_paths or f in mod:
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
        if f in prev_paths and f not in overlay and prev_shas.get(f) == sha:
            files.append({"file": f, "sha": sha, "size": size})
        else:
            if f.startswith("public/img/") or size > 4 * 1024 * 1024:
                for i in range(5):
                    req = urllib.request.Request("%s/v2/files?teamId=%s" % (BASE, TEAM), data=data, method="POST")
                    req.add_header("Authorization", "Bearer %s" % token)
                    req.add_header("Content-Type", "application/octet-stream")
                    req.add_header("x-vercel-digest", sha)
                    try:
                        with urllib.request.urlopen(req, timeout=60) as r:
                            print("  hashed %s (%dKB)" % (f, size // 1024)); break
                    except Exception as e:
                        print("  upload attempt %d %s failed: %s" % (i + 1, f, e)); time.sleep(3)
                else:
                    raise RuntimeError("upload failed %s" % f)
                files.append({"file": f, "sha": sha, "size": size})
            else:
                files.append({"file": f, "data": base64.b64encode(data).decode("ascii"), "encoding": "base64"})
    print("files total:", len(files))
    return files


def main():
    token = auth_token()
    prev_paths, prev_shas = get_prev_paths(token)
    files = build_files(token, prev_paths, prev_shas)
    inline = sum(len(f.get("data", "")) for f in files) / 1024 / 1024
    print("inline ~%.2f MB" % inline)
    for attempt in range(4):
        body = {"name": "finalhopes-learning-system", "target": "production", "project": PROJECT, "files": files}
        st, j = apipost("/v13/deployments?teamId=%s&forceNew=1&skipAutoDetectionConfirmation=1" % TEAM, token, body)
        if st not in (200, 201):
            # 400 missing_files: some referenced blobs are not on Vercel's store.
            # Map the missing hashes back to current tracked files and force-upload them.
            err = (j or {}).get("error", {})
            if st == 400 and err.get("code") == "missing_files":
                missing = set(err.get("missing", []))
                if missing and attempt < 3:
                    print("  missing_files: %s — remapping & force-uploading" % missing)
                    cur = {}
                    for f in set(tracked_files()):
                        if any(f.startswith(s) for s in SKIP_PREFIXES):
                            continue
                        cur[hashlib.sha1(open(os.path.join(ROOT, f), "rb").read()).hexdigest()] = f
                    force = set()
                    for h in missing:
                        if h in cur:
                            force.add(cur[h])
                        else:
                            print("  WARN unmatched missing hash:", h)
                    if force:
                        files = build_files(token, prev_paths, prev_shas, force=force)
                        inline = sum(len(f.get("data", "")) for f in files) / 1024 / 1024
                        print("  retry inline ~%.2f MB (forced %d files)" % (inline, len(force)))
                        continue
            print("CREATE FAILED", st, json.dumps(j)[:800]); sys.exit(1)
        did = j["id"]
        print("production id=", did)
        for i in range(160):
            d = apiget("/v13/deployments/%s?teamId=%s" % (did, TEAM), token)
            status = d.get("status")
            print("[%d] status=%s aliasAssigned=%s" % (i, status, d.get("aliasAssigned")))
            if status == "READY":
                print("READY url=", d.get("url")); return
            if status in ("ERROR", "CANCELED"):
                print("FAILED", json.dumps(d)[:800]); sys.exit(1)
            time.sleep(6)
        print("poll timeout (but deployment may still be finalizing)")
        return


if __name__ == "__main__":
    main()
