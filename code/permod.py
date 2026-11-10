"""A1 runner: each tests/test_*.py module in its own process (no bytecode). Writes <out>.log and <out>.json (no clobber)."""
import json, os, re, subprocess, sys, time, glob
out = sys.argv[1]; env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
res, log = {}, []
for f in sorted(glob.glob("tests/test_*.py")):
    m = "tests." + os.path.basename(f)[:-3]
    p = subprocess.run([".venv/bin/python", "-B", "-m", "unittest", "-v", m], capture_output=True, text=True, env=env)
    t = p.stderr + p.stdout
    ran = re.search(r"^Ran (\d+) test", t, re.M)
    bad = sorted(set(re.findall(r"^(?:FAIL|ERROR): (\S+) \(([^)]+)\)", t, re.M)))
    res[m] = {"rc": p.returncode, "ran": int(ran.group(1)) if ran else None,
              "failed": [f"{cls.rsplit('.',1)[0]}.{name}" if '.' in cls else name for name, cls in bad],
              "kinds": re.findall(r"^(FAIL|ERROR): ", t, re.M), "tail": t.strip().splitlines()[-1] if t.strip() else ""}
    log.append(f"===== {m} rc={p.returncode}\n{t}\n")
with open(out + ".log", "x") as fh: fh.write("".join(log))
with open(out + ".json", "x") as fh: json.dump(res, fh, indent=1, sort_keys=True); fh.write("\n")
tot = sum(r["ran"] or 0 for r in res.values()); nb = sum(len(r["kinds"]) for r in res.values())
print("modules", len(res), "tests", tot, "fail+error entries", nb)
for m, r in res.items():
    if r["rc"] != 0: print(m, r["tail"], r["failed"], r["kinds"])
