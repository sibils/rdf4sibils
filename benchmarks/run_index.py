#!/usr/bin/env python3
"""Build one QLever index of the SIBiLS data and record what it cost.

usage: run_index.py NAME --streams K [--stxxl 10G] [--extra "qlever-index flags"] [--settings JSON]
The index goes to $BENCH/runs/NAME; one line per run is appended to results/index_runs.jsonl
"""
import argparse, glob, gzip, json, os, re, shutil, subprocess, time

BENCH = os.environ.get("BENCH", "/home/pmichel/work/tools/qlever/bench")
DATA = os.environ.get("BENCH_DATA", f"{BENCH}/data-iso")
IMAGE = "docker.io/adfreiburg/qlever:commit-7f8b3be50d"
GRAPH = "https://www.sibils.org/rdf/graphs/main"
RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "index_runs.jsonl")


def suspended():
    return time.clock_gettime(time.CLOCK_BOOTTIME) - time.clock_gettime(time.CLOCK_MONOTONIC)


def groups(files, k):
    """split files into k groups of similar total size"""
    out = [[0, []] for _ in range(k)]
    for f in sorted(files, key=os.path.getsize, reverse=True):
        g = min(out, key=lambda x: x[0])
        g[0] += os.path.getsize(f)
        g[1].append(os.path.basename(f))
    return [g[1] for g in out if g[1]]


def phases(log):
    marks = [("parse", "Parsing input triples"), ("vocab", "Merging partial vocabularies"), ("ids", "Converting triples from local"),
             ("spo", "Creating permutations SPO"), ("osp", "Creating permutations OSP"), ("pso", "Creating permutations PSO"), ("end", "Index build completed")]
    times = {}
    for line in open(log, errors="replace"):
        for name, text in marks:
            if name not in times and text in line:
                times[name] = time.mktime(time.strptime(line[:19], "%Y-%m-%d %H:%M:%S"))
    names = [m[0] for m in marks]
    return {a: round(times[b] - times[a]) for a, b in zip(names, names[1:]) if a in times and b in times}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--streams", type=int, required=True)
    ap.add_argument("--stxxl", default="10G")
    ap.add_argument("--extra", default="")
    ap.add_argument("--settings", default="{}")
    ap.add_argument("--parallel", default="false")
    a = ap.parse_args()

    run = f"{BENCH}/runs/{a.name}"
    shutil.rmtree(run, ignore_errors=True)
    os.makedirs(f"{run}/input")
    os.makedirs(f"{run}/groups")
    for f in glob.glob(f"{DATA}/*"):
        os.link(f, f"{run}/input/{os.path.basename(f)}")
    plain = sorted(glob.glob(f"{run}/input/*.ttl"))
    gz = sorted(glob.glob(f"{run}/input/*.ttl.gz"))
    # stream command -> parallel parser or not; the plain files and MEDLINE hold multi-line literals
    streams = {f"cat {' '.join('input/' + os.path.basename(f) for f in plain)}": "false"}
    prefix = ""
    if a.parallel == "true":
        # the parallel parser wants a single prefix block, at the start of its stream
        with gzip.open(gz[0], "rt") as f:
            open(f"{run}/prefixes.ttl", "w").write("".join(sorted({l for l in f if l.startswith("@prefix")})))
        prefix = "cat prefixes.ttl; "
        medline = [f for f in gz if "data_medline" in f]
        gz = [f for f in gz if f not in medline]
        open(f"{run}/groups/medline.txt", "w").write("\n".join("input/" + os.path.basename(f) for f in medline) + "\n")
        streams["xargs zcat < groups/medline.txt"] = "false"
    for i, g in enumerate(groups(gz, a.streams)):
        open(f"{run}/groups/g{i}.txt", "w").write("\n".join("input/" + f for f in g) + "\n")
        if prefix:
            streams[f"{{ {prefix}xargs zcat < groups/g{i}.txt | grep -v '^@prefix'; }}"] = "true"
        else:
            streams[f"xargs zcat < groups/g{i}.txt"] = "false"
    flags = " ".join(f"-f <({c}) -g {GRAPH} -F ttl -p {p}" for c, p in streams.items())
    open(f"{run}/sibils.settings.json", "w").write(a.settings)
    cmd = (f"ulimit -Sn 50000 && qlever-index -i sibils -s sibils.settings.json --vocabulary-type on-disk-compressed {flags} "
           f"--stxxl-memory {a.stxxl} {a.extra} 2>&1 | tee sibils.index-log.txt")
    docker = ["docker", "run", "--rm", "-u", f"{os.getuid()}:{os.getgid()}", "-v", "/etc/localtime:/etc/localtime:ro",
              "--mount", f"type=bind,src={run},target=/index", "-w", "/index", "--name", f"qlever.index.{a.name}",
              "--init", "--entrypoint", "bash", IMAGE, "-c", cmd]
    s0, t0 = suspended(), time.time()
    with open(f"{run}/index.out", "w") as out:
        rc = subprocess.call(docker, stdout=out, stderr=subprocess.STDOUT)
    seconds = round(time.time() - t0)
    log = open(f"{run}/sibils.index-log.txt", errors="replace").read()
    ok = "Index build completed" in log   # qlever-index can exit 0 after a failed build
    m = re.findall(r"Triples parsed: ([\d,]+)", log) or re.findall(r"Triples sorted: ([\d,]+)", log)
    rss = 0
    usage = f"{run}/sibils.index.resource-usage-log.tsv"
    if os.path.exists(usage):
        rows = open(usage).read().splitlines()
        h = rows[0].split("\t")
        col = next((i for i, c in enumerate(h) if "rss" in c.lower()), None)
        if col is not None:
            rss = max(float(r.split("\t")[col]) for r in rows[1:] if r.split("\t")[col])
    size = sum(os.path.getsize(f) for f in glob.glob(f"{run}/sibils.*") if not f.endswith((".txt", ".tsv", ".jsonl")))
    rec = {"name": a.name, "streams": a.streams, "stxxl": a.stxxl, "extra": a.extra, "settings": a.settings, "parallel": a.parallel,
           "ok": ok, "rc": rc, "seconds": seconds, "suspended_s": round(suspended() - s0), "size_gb": round(size / 1e9, 2),
           "last_triples": m[-1] if m else None, "peak_rss_raw": rss, "rss_col_header": h[col] if rss else None, "phases": phases(f"{run}/sibils.index-log.txt")}
    with open(RESULTS, "a") as f:
        f.write(json.dumps(rec) + "\n")
    print(json.dumps(rec))


main()
