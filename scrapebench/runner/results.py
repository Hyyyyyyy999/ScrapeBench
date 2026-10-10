import csv
import os
import time

FIELDS = ["run", "stage", "pid", "method", "tier", "attack", "n_gallery", "n_samples",
          "mean_id", "ci_lo", "ci_hi", "p_lo", "p_hi", "pos_rate", "gen_sec", "sec_per_img", "ts"]


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def ensure_csv(path, fields=FIELDS):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", newline="") as f:
            csv.writer(f).writerow(fields)
    return path


def append_row(path, row):
    with open(path, "a", newline="") as f:
        csv.DictWriter(f, fieldnames=FIELDS).writerow(row)


def load_done(path):
    done = set()
    if not os.path.exists(path):
        return done
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            done.add((r["stage"], r["pid"], r["method"], r["tier"], r["attack"]))
    return done


def log(msg, log_path=None):
    line = f"[{now()}] {msg}"
    print(line, flush=True)
    if log_path:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a") as f:
            f.write(line + "\n")
