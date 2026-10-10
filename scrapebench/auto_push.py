import os
import sys
import time
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_URL = "https://github.com/Hyyyyyyy999/ScrapeBench.git"


def find_pat():
    env = os.environ.get("SCRAPEBENCH_PAT")
    if env and len(env) > 20:
        return env.strip()
    for p in [os.path.expanduser("~/.scrapebench_pat"), os.path.join(os.path.dirname(ROOT), "PAT")]:
        if p and os.path.isfile(p):
            tok = open(p).read().strip()
            if len(tok) > 20:
                return tok
    return None


def run(cmd, env=None, check=False):
    return subprocess.run(cmd, env=env, cwd=ROOT, capture_output=True, text=True, check=check)


def main():
    msg = " ".join(sys.argv[1:]) or f"results update {time.strftime('%Y%m%d-%H%M%S')}"
    pat = find_pat()
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    if pat:
        cache = os.path.expanduser("~/.cache/scrapebench")
        os.makedirs(cache, exist_ok=True)
        askpass = os.path.join(cache, "askpass.sh")
        with open(askpass, "w") as f:
            f.write("#!/bin/sh\ncase \"$1\" in *Username*) echo \"$SCRAPEBENCH_USER\" ;; *) echo \"$SCRAPEBENCH_PASS\" ;; esac\n")
        os.chmod(askpass, 0o700)
        env.update(GIT_ASKPASS=askpass, SCRAPEBENCH_USER="x-access-token", SCRAPEBENCH_PASS=pat)
    run(["git", "add", "-A", "runs", "report", "figures", "logs"])
    st = run(["git", "status", "--porcelain"])
    if st.stdout.strip():
        run(["git", "-c", "user.name=ScrapeBench", "-c",
             "user.email=scrapebench@users.noreply.github.com", "commit", "-m", msg])
    else:
        ahead = run(["git", "rev-list", "--count", "origin/main..HEAD"])
        if ahead.stdout.strip() == "0":
            print("nothing to commit or push")
            return 0
    target = "origin" if run(["git", "remote", "get-url", "origin"]).returncode == 0 else REPO_URL
    push = run(["git", "push", target, "HEAD:main"], env=env)
    out = (push.stdout + push.stderr).replace(pat, "***") if pat else (push.stdout + push.stderr)
    print(out.strip())
    return push.returncode


if __name__ == "__main__":
    sys.exit(main())
