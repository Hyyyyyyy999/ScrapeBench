import argparse
import fnmatch
import hashlib
import json
import re
import sys
from datetime import date

USE_TOKENS = {
    "recognition-accuracy", "research-aggregate", "security-fraud", "editorial",
    "personalization", "customization", "fine-tuning", "embedding-extraction",
    "training-generative", "any",
}


def parse_manifest(text):
    manifest = {"version": None, "contact": None, "applies_to": [], "default": "deny", "blocks": []}
    block = None
    errors = []
    for ln, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if not line.startswith("  ") and ":" in line:
            key, _, val = line.partition(":")
            key, val = key.strip(), val.strip()
            lk = key.lower()
            if lk == "consent-version":
                manifest["version"] = val
            elif lk == "contact":
                manifest["contact"] = val
            elif lk == "applies-to":
                manifest["applies_to"].append(val)
            elif lk == "default-policy":
                manifest["default"] = val.lower()
            elif lk == "identity-block":
                block = {"id": val, "line": ln, "images": [], "allowed": [], "denied": [],
                         "subject_hash": None, "expiry": None, "revocation": None, "signature": None}
                manifest["blocks"].append(block)
            else:
                errors.append(f"line {ln}: unknown top-level key {key!r}")
            continue
        if block is None:
            errors.append(f"line {ln}: indented directive outside a block")
            continue
        key, _, val = line.strip().partition(":")
        key, val = key.strip().lower(), val.strip()
        if key == "images":
            block["images"].append(val)
        elif key == "allowed-uses":
            block["allowed"] = [u.strip().lower() for u in val.split(",") if u.strip()]
        elif key == "denied-uses":
            block["denied"] = [u.strip().lower() for u in val.split(",") if u.strip()]
        elif key == "subject-hash":
            block["subject_hash"] = val
        elif key == "expiry":
            block["expiry"] = val
        elif key == "revocation":
            block["revocation"] = val
        elif key == "signature":
            block["signature"] = val
        else:
            errors.append(f"line {ln}: unknown block key {key!r}")
    return manifest, errors


def validate(manifest, errors):
    problems = list(errors)
    if manifest["version"] != "1.0":
        problems.append("missing or unsupported Consent-Version")
    if not manifest["contact"]:
        problems.append("missing Contact")
    for b in manifest["blocks"]:
        if not b["images"]:
            problems.append(f"block {b['id']} (line {b['line']}): no Images glob")
        for u in b["allowed"] + b["denied"]:
            if u not in USE_TOKENS:
                problems.append(f"block {b['id']}: unknown use token {u!r}")
        if b["expiry"]:
            try:
                date.fromisoformat(b["expiry"])
            except ValueError:
                problems.append(f"block {b['id']}: bad expiry {b['expiry']!r}")
        if b["subject_hash"] and not re.fullmatch(r"sha256-[0-9a-f]{64}", b["subject_hash"]):
            problems.append(f"block {b['id']}: malformed Subject-Hash")
    return problems


def active(block, today):
    if not block["expiry"]:
        return True
    try:
        return date.fromisoformat(block["expiry"]) >= today
    except ValueError:
        return False


def decide(manifest, path, use, today=None):
    today = today or date.today()
    hit = None
    for b in manifest["blocks"]:
        if not active(b, today):
            continue
        for g in b["images"]:
            if fnmatch.fnmatch(path, g):
                hit = b
                break
        if hit:
            break
    if hit is None:
        return manifest["default"], "default-policy"
    if use in hit["denied"] or "any" in hit["denied"]:
        return "deny", f"block:{hit['id']}:denied-uses"
    if use in hit["allowed"] or "any" in hit["allowed"]:
        return "allow", f"block:{hit['id']}:allowed-uses"
    return manifest["default"], f"block:{hit['id']}:default-policy"


def main():
    ap = argparse.ArgumentParser(description="face-consent.txt validator")
    ap.add_argument("--file", required=True)
    ap.add_argument("--check", help="use token to query")
    ap.add_argument("--path", default="/", help="image path to query")
    ap.add_argument("--audit", action="store_true", help="audit a directory of images against the manifest")
    args = ap.parse_args()
    text = open(args.file, encoding="utf-8").read()
    manifest, errors = parse_manifest(text)
    problems = validate(manifest, errors)
    digest = hashlib.sha256(text.encode()).hexdigest()[:16]
    if problems:
        for p in problems:
            print(f"ERROR: {p}", file=sys.stderr)
        sys.exit(2)
    if args.audit:
        import os
        covered, denied_by_default, total = 0, 0, 0
        for root, _, files in os.walk(os.path.dirname(os.path.abspath(args.file)) or "."):
            for fn in files:
                if not fn.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                    continue
                total += 1
                rel = os.path.relpath(os.path.join(root, fn), os.path.dirname(os.path.abspath(args.file)))
                rel = "/" + rel.replace(os.sep, "/")
                decision, source = decide(manifest, rel, args.check.lower() if args.check else "personalization")
                if decision == "allow":
                    covered += 1
                elif source == "default-policy":
                    denied_by_default += 1
        print(json.dumps({"images_scanned": total, "allowed": covered,
                          "denied_by_default": denied_by_default,
                          "explicitly_denied": total - covered - denied_by_default,
                          "use": args.check or "personalization"}))
        sys.exit(0)
    if args.check:
        decision, source = decide(manifest, args.path, args.check.lower())
        print(json.dumps({"decision": decision, "source": source, "manifest_sha256": digest,
                          "use": args.check, "path": args.path}))
        sys.exit(0 if decision == "allow" else 1)
    print(json.dumps({"manifest_sha256": digest, "blocks": len(manifest["blocks"]),
                      "default": manifest["default"], "contact": manifest["contact"], "status": "valid"}))


def os_walk_cwd():
    import os
    return os.walk(os.getcwd())


if __name__ == "__main__":
    main()
