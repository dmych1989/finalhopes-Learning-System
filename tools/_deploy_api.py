# 直连 Vercel REST API 部署（不依赖 GitHub，针对 github.com 出网被封的场景）。
# 把 git 跟踪的文件（除 data.db / exe_strings.txt）以 base64 inline 上传，
# 由项目 vercel.json 触发 @vercel/python 构建 api/index.py。
import os, sys, json, base64, subprocess, time, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEAM = "team_AUEOwID6emZlHoTjyvmre3gV"
PROJECT = "prj_5FqANpHobhjTmTTGWWM39bhhRmHY"
BASE = "https://api.vercel.com"

EXCLUDE = {"tools/exe_strings.txt"}  # data.db 现在单独哈希上传（体积大，不能 inline）

def tracked_files():
    # -z emits NUL-delimited, UNQUOTED paths so non-ASCII filenames
    # (e.g. Chinese hexagram images) aren't mangled by git's quotePath.
    out = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT, text=True).split("\0")
    res = []
    for f in out:
        if f in EXCLUDE or f.startswith(".git/") or "__pycache__" in f:
            continue
        p = os.path.join(ROOT, f)
        if os.path.isfile(p):
            res.append(f)
    return res

def build_files():
    files = []
    for f in tracked_files():
        if f == "web_app/data.db":
            continue  # 大数据文件走哈希上传
        with open(os.path.join(ROOT, f), "rb") as fh:
            data = fh.read()
        files.append({"file": f, "data": base64.b64encode(data).decode("ascii"), "encoding": "base64"})
    return files

def upload_data_db(token):
    """Vercel 超过 inline 上限的大文件用 /v2/files 哈希上传，部署时按 sha 引用。"""
    import hashlib
    p = os.path.join(ROOT, "web_app", "data.db")
    data = open(p, "rb").read()
    sha = hashlib.sha1(data).hexdigest()
    size = len(data)
    print(f"uploading data.db sha={sha} size={size}")
    url = f"{BASE}/v2/files?teamId={TEAM}"
    last = None
    for i in range(5):
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Content-Type", "application/octet-stream")
        req.add_header("x-vercel-digest", sha)
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                print("  upload status", r.status)
                return {"file": "web_app/data.db", "sha": sha, "size": size}
        except Exception as e:
            last = e
            print(f"  upload attempt {i+1} failed: {e}; retrying...")
            time.sleep(3)
    raise last

def auth_token():
    p = os.path.expanduser("~/.vercel/auth.json")
    with open(p, encoding="utf-8-sig") as fh:
        return json.load(fh)["token"]

def http_json(method, url, token, body=None, attempts=5, timeout=120):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    last = None
    for i in range(attempts):
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last = e
            try:
                txt = e.read().decode("utf-8", "replace")
            except Exception:
                txt = ""
            print(f"  HTTPError {e.code} attempt {i+1}: {txt[:500]}")
            if e.code < 500:
                raise
        except Exception as e:
            last = e
            print(f"  attempt {i+1} failed: {e}; retrying...")
        time.sleep(3)
    raise last

def main():
    token = auth_token()
    files = build_files()
    db_ref = upload_data_db(token)
    files.append(db_ref)
    total = sum(len(f.get("data", "")) for f in files)
    print(f"deploying {len(files)} files, inline base64 ~{total/1024/1024:.2f} MB (+ data.db via hash)")
    body = {
        "name": "finalhopes-learning-system",
        "target": "production",
        "project": PROJECT,
        "files": files,
    }
    # forceNew: 绕过文件哈希去重，确保重新构建；skipAutoDetectionConfirmation: 跳过框架自动探测确认
    url = f"{BASE}/v13/deployments?teamId={TEAM}&forceNew=1&skipAutoDetectionConfirmation=1"
    st, j = http_json("POST", url, token, body)
    if st != 200 and st != 201:
        print("CREATE FAILED", st, json.dumps(j)[:800]); sys.exit(1)
    dep_id = j["id"]
    print("created deployment id =", dep_id, " url =", j.get("url"))
    # poll
    for i in range(80):
        try:
            st2, j2 = http_json("GET", f"{BASE}/v13/deployments/{dep_id}?teamId={TEAM}", token,
                                attempts=3, timeout=30)
        except Exception as e:
            print(f"  poll {i} error {e}; retry next loop")
            time.sleep(6); continue
        status = j2.get("status")
        print(f"[{i}] status={status}")
        if status == "READY":
            print("READY  url=", j2.get("url"), "  inspector=", j2.get("inspectorUrl"))
            return
        if status in ("ERROR", "CANCELED"):
            print("FAILED", json.dumps(j2)[:1200]); sys.exit(1)
        time.sleep(6)
    print("poll timeout"); sys.exit(1)

if __name__ == "__main__":
    main()
