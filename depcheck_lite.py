#!/usr/bin/env python3
"""depcheck-lite: find unused and undeclared dependencies in JS (package.json) and Python (requirements.txt) projects."""
import argparse, json, os, re, sys

__version__ = "0.1.0"
SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build", ".next", "site-packages"}
JS_EXT = (".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".vue", ".svelte")
JS_IMPORT = re.compile(r"""(?:from\s*|require\s*\(\s*|import\s*\(\s*|import\s+)['"]([^'"]+)['"]""")
PY_IMPORT = re.compile(r"^\s*(?:from\s+([A-Za-z_][\w]*)|import\s+([A-Za-z_][\w]*(?:\s*,\s*[A-Za-z_][\w]*)*))", re.M)
PY_ALIASES = {"PIL": "pillow", "yaml": "pyyaml", "cv2": "opencv-python", "sklearn": "scikit-learn",
              "bs4": "beautifulsoup4", "dateutil": "python-dateutil", "dotenv": "python-dotenv",
              "jwt": "pyjwt", "serial": "pyserial", "attr": "attrs", "git": "gitpython", "OpenSSL": "pyopenssl"}
STDLIB = getattr(sys, "stdlib_module_names", frozenset())


def walk(root, exts):
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            if f.endswith(exts):
                yield os.path.join(d, f)


def js_pkg(spec):
    """'lodash/fp' -> 'lodash'; '@scope/x/y' -> '@scope/x'; relative/builtin -> None."""
    if spec.startswith((".", "/", "node:", "~", "#")):
        return None
    parts = spec.split("/")
    return "/".join(parts[:2]) if spec.startswith("@") else parts[0]


def scan_js(root):
    used = set()
    for path in walk(root, JS_EXT):
        try:
            text = open(path, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        used.update(p for p in map(js_pkg, JS_IMPORT.findall(text)) if p)
    return used


def check_js(root):
    with open(os.path.join(root, "package.json"), encoding="utf-8") as fh:
        pj = json.load(fh)
    deps, dev = set(pj.get("dependencies", {})), set(pj.get("devDependencies", {}))
    used = scan_js(root)
    scripts = " ".join(pj.get("scripts", {}).values())
    cfg_text = " ".join(str(v) for k, v in pj.items() if k not in ("dependencies", "devDependencies", "scripts"))

    def is_used(name):
        if name in used or (name.startswith("@types/") and name[7:] in used):
            return True
        return bool(re.search(r"(?<![\w@/-])" + re.escape(name) + r"(?![\w-])", scripts + " " + cfg_text)) \
            or (name.startswith("@types/") and name[7:] in deps | dev)
    return {
        "unused": sorted(n for n in deps if not is_used(n)),
        "unused_dev": sorted(n for n in dev if not is_used(n)),
        "undeclared": sorted(n for n in used if n not in deps | dev),
    }


def norm(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_requirements(text):
    out = set()
    for line in text.splitlines():
        line = line.split("#")[0].strip()
        if line and not line.startswith(("-", "git+", "http")):
            m = re.match(r"[A-Za-z0-9][A-Za-z0-9._-]*", line)
            if m:
                out.add(norm(m.group(0)))
    return out


def scan_py(root):
    used, local = set(), set()
    for entry in os.listdir(root):
        if entry.endswith(".py"):
            local.add(entry[:-3])
        elif os.path.isdir(os.path.join(root, entry)) and entry not in SKIP_DIRS:
            local.add(entry)
    for path in walk(root, (".py",)):
        with open(path, encoding="utf-8", errors="ignore") as fh:
            text = fh.read()
        for frm, imp in PY_IMPORT.findall(text):
            for mod in ([frm] if frm else [m.strip() for m in imp.split(",")]):
                if mod and mod not in STDLIB and mod not in local:
                    used.add(mod)
    return used


def check_py(root):
    with open(os.path.join(root, "requirements.txt"), encoding="utf-8") as fh:
        req = parse_requirements(fh.read())
    used = {norm(PY_ALIASES.get(m, m)) for m in scan_py(root)}
    return {"unused": sorted(req - used), "unused_dev": [], "undeclared": sorted(used - req)}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--json", action="store_true")
    p.add_argument("--version", action="version", version=__version__)
    a = p.parse_args(argv)
    results = {}
    if os.path.exists(os.path.join(a.path, "package.json")):
        results["javascript"] = check_js(a.path)
    if os.path.exists(os.path.join(a.path, "requirements.txt")):
        results["python"] = check_py(a.path)
    if not results:
        print("depcheck-lite: no package.json or requirements.txt found", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(results, indent=2))
    else:
        for lang, r in results.items():
            print(f"[{lang}]")
            for key, label in (("unused", "unused dependencies"), ("unused_dev", "unused devDependencies"),
                               ("undeclared", "used but not declared")):
                for n in r[key]:
                    print(f"  {label}: {n}")
            if not any(r.values()):
                print("  ✓ no problems found")
    return 1 if any(v for r in results.values() for v in r.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
