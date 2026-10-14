import os
root = os.path.expanduser("~/ScrapeBench/data")
need = ["celeb00025", "celeb00027", "celeb00028", "celeb00029", "celeb00030", "celeb00031"]
for pid in need:
    g = len(os.listdir(os.path.join(root, "raw", pid)))
    r = len(os.listdir(os.path.join(root, "refs", pid)))
    assert g >= 8 and r >= 2, f"{pid}: gallery={g} refs={r}"
print("data ok:", ", ".join(f"{p}={len(os.listdir(os.path.join(root,'raw',p)))}" for p in need))
