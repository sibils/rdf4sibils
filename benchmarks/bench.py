#!/usr/bin/env python3
"""Run the SIBiLS query set against a QLever index or a Virtuoso instance and save timings.

usage:
  bench.py qlever RUN --label L [--mem 11G --cache 2G --threads 8 --extra FLAGS] [--set name=value,...] [--groups a,b] [--no-heavy]
  bench.py virtuoso --label L [--groups a,b] [--no-heavy]

Each store is stopped, its files are evicted from the page cache, and it is restarted, so the first
pass over the queries is cold (later queries still profit from pages read by earlier ones). Two more
passes give warm times, with QLever's result cache cleared before each query. A last pass with the
result cache kept gives QLever's repeat-query time. Heavy queries run once, cold.
"""
import argparse, collections, glob, hashlib, json, os, subprocess, sys, time
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.environ.get("BENCH", "/home/pmichel/work/tools/qlever/bench")
IMAGE = "docker.io/adfreiburg/qlever:commit-7f8b3be50d"
TOKEN = "bench-local-only"
QPORT, VPORT, VISQL = 7121, 8892, 1122
VHOME = "/home/pmichel/work/tools/virtuoso-opensource"
GRAPH = "https://www.sibils.org/rdf/graphs/main"
J = "application/sparql-results+json"
NT = "application/n-triples"
RDFIZE = os.path.join(HERE, "..", "v2", "rdfize")
sys.path.insert(0, RDFIZE)
sys.path.insert(0, HERE)
os.chdir(RDFIZE)
from query_set import build_queries


def suspended():
    return time.clock_gettime(time.CLOCK_BOOTTIME) - time.clock_gettime(time.CLOCK_MONOTONIC)


def evict(files):
    for f in files:
        fd = os.open(f, os.O_RDONLY)
        os.fsync(fd)
        os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
        os.close(fd)


class QLever:
    url = f"http://localhost:{QPORT}"
    name = "qlever"

    def __init__(self, a):
        self.a, self.dir = a, f"{BENCH}/runs/{a.run}"

    def stop(self):
        subprocess.run(["docker", "rm", "-f", "qlever.server.bench"], capture_output=True)
        time.sleep(2)

    def start(self):
        a = self.a
        evict(glob.glob(f"{self.dir}/sibils.*"))
        cmd = (f"exec qlever-server -i sibils -p {QPORT} -m {a.mem} -c {a.cache} -j {a.threads} "
               f"-s 2400s -a {TOKEN} {a.extra} > sibils.server-log.txt 2>&1")
        subprocess.run(["docker", "run", "-d", "--rm", "-u", f"{os.getuid()}:{os.getgid()}", "-v", "/etc/localtime:/etc/localtime:ro",
                        "--mount", f"type=bind,src={self.dir},target=/index", "-w", "/index", "--name", "qlever.server.bench",
                        "--init", "-p", f"{QPORT}:{QPORT}", "--entrypoint", "bash", IMAGE, "-c", cmd], check=True, capture_output=True)
        wait_ready(self.url, "SELECT * WHERE { ?s ?p ?o } LIMIT 1")
        if a.set:
            params = dict(kv.split("=") for kv in a.set.split(","))
            r = requests.get(self.url, params={**params, "access-token": TOKEN}, timeout=60)
            current = requests.get(self.url, params={"cmd": "get-settings"}, timeout=60).json()
            if r.status_code != 200 or any(str(current[k]).lower() != v.lower() for k, v in params.items()):
                raise SystemExit(f"settings not applied: {r.status_code} {r.text[:200]}")

    def clear(self):
        requests.post(self.url, data={"cmd": "clear-cache", "access-token": TOKEN}, timeout=120)

    def pid(self):
        out = subprocess.run(["pgrep", "-f", f"qlever-server -i sibils -p {QPORT}"], capture_output=True, text=True).stdout.split()
        return out[-1] if out else None

    def describe(self, iri):
        return f"describe <{iri}>"


class Virtuoso:
    url = f"http://localhost:{VPORT}/sparql"
    name = "virtuoso"

    def __init__(self, a):
        self.a, self.dir = a, f"{BENCH}/virtuoso"

    def stop(self):
        subprocess.run([f"{VHOME}/bin/isql", str(VISQL), "dba", "dba", "exec=checkpoint; shutdown;"], capture_output=True)
        time.sleep(5)

    def start(self):
        evict(glob.glob(f"{self.dir}/sibils_database/*.db"))
        subprocess.run([f"{VHOME}/bin/virtuoso-t", "+wait", "+configfile", f"{self.dir}/virtuoso.ini"], cwd=f"{self.dir}/bin", check=True, capture_output=True)
        wait_ready(self.url, "SELECT * WHERE { ?s ?p ?o } LIMIT 1")

    def clear(self):
        pass

    def pid(self):
        out = subprocess.run(["pgrep", "-f", f"{self.dir}/virtuoso.ini"], capture_output=True, text=True).stdout.split()
        return out[0] if out else None

    def describe(self, iri):
        return f'DEFINE sql:describe-mode "CBD" describe <{iri}>'


def wait_ready(url, q):
    for _ in range(600):
        try:
            if requests.post(url, data={"query": q}, headers={"Accept": J}, timeout=30).status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(1)
    raise SystemExit("server did not come up")


def norm(c):
    if c is None:
        return None
    if c["type"] == "bnode":
        return "_:b"
    v = c["value"]
    try:
        if c.get("datatype", "").startswith("http://www.w3.org/2001/XMLSchema#"):
            f = float(v)
            if f == int(f):
                return str(int(f))
    except (ValueError, OverflowError):
        pass
    return v.replace("XMLSchema#int", "XMLSchema#integer") if v.endswith("XMLSchema#int") else v


def run_one(store, q):
    text = store.describe(q["describe"]) if "describe" in q else q["sparql"]
    accept = NT if "describe" in q else J
    t0 = time.time()
    try:
        r = requests.post(store.url, data={"query": text}, headers={"Accept": accept}, timeout=2500)
        body = r.content
        dt = round(time.time() - t0, 3)
    except requests.RequestException as e:
        return {"s": round(time.time() - t0, 3), "error": repr(e)[:300]}
    if r.status_code != 200:
        msg = r.text
        try:
            msg = r.json().get("exception", msg)
        except ValueError:
            pass
        return {"s": dt, "error": f"HTTP {r.status_code}: {msg}"[:400]}
    if "describe" in q:
        return {"s": dt, "rows": body.count(b"\n")}
    j = r.json()
    if "results" not in j:
        return {"s": dt, "rows": 1}
    v = j["head"]["vars"]
    rows = [tuple(norm(b.get(k)) for k in v) for b in j["results"]["bindings"]]
    c = collections.Counter(rows)
    return {"s": dt, "rows": len(rows), "distinct": len(c),
            "digest": hashlib.sha1(json.dumps(sorted(map(repr, set(rows)))).encode()).hexdigest()[:12]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("store", choices=["qlever", "virtuoso"])
    ap.add_argument("run", nargs="?")
    ap.add_argument("--label", required=True)
    ap.add_argument("--mem", default="11G")
    ap.add_argument("--cache", default="2G")
    ap.add_argument("--threads", default="8")
    ap.add_argument("--extra", default="")
    ap.add_argument("--set", default="", help="QLever runtime settings, name=value,...")
    ap.add_argument("--groups", default="")
    ap.add_argument("--no-heavy", action="store_true")
    ap.add_argument("--keep-running", action="store_true")
    a = ap.parse_args()
    store = QLever(a) if a.store == "qlever" else Virtuoso(a)
    qs = build_queries()
    if a.groups:
        qs = [q for q in qs if q["group"] in a.groups.split(",")]
    if a.no_heavy:
        qs = [q for q in qs if not q.get("heavy")]
    store.stop()
    s0 = suspended()
    t0 = time.time()
    store.start()
    start_s = round(time.time() - t0, 1)
    out = {"label": a.label, "store": a.store, "run": a.run, "mem": a.mem, "cache": a.cache, "threads": a.threads, "extra": a.extra, "set": a.set,
           "start_s": start_s, "queries": []}
    light = [q for q in qs if not q.get("heavy")]
    res = {q["name"]: {"name": q["name"], "group": q["group"], "heavy": bool(q.get("heavy")), "runs": []} for q in qs}
    path = f"{HERE}/results/queries_{a.label}.json"
    for i, batch in enumerate([light, light, light]):
        for q in batch:
            store.clear()
            o = run_one(store, q)
            res[q["name"]]["runs"].append(o)
            print(a.label, f"pass{i}", q["name"], o.get("s"), o.get("rows"), o.get("error", "")[:120], flush=True)
    if a.store == "qlever":
        for q in light:
            run_one(store, q)   # the earlier passes cleared the cache: this one fills it
            res[q["name"]]["cached"] = run_one(store, q).get("s")
    for q in qs:
        if q.get("heavy"):
            store.clear()
            o = run_one(store, q)
            res[q["name"]]["runs"].append(o)
            print(a.label, "heavy", q["name"], o.get("s"), o.get("rows"), o.get("error", "")[:120], flush=True)
            if a.store == "qlever" and o.get("error"):
                wait_ready(store.url, "SELECT * WHERE { ?s ?p ?o } LIMIT 1")
    pid = store.pid()
    if pid and os.path.exists(f"/proc/{pid}/status"):
        for line in open(f"/proc/{pid}/status"):
            if line.startswith("VmHWM"):
                out["peak_rss_gb"] = round(int(line.split()[1]) / 1048576, 1)
    out["suspended_s"] = round(suspended() - s0)
    out["total_s"] = round(time.time() - t0)
    out["queries"] = list(res.values())
    json.dump(out, open(path, "w"), indent=1)
    print("saved", path, "peak", out.get("peak_rss_gb"), "suspended", out["suspended_s"], flush=True)
    if not a.keep_running:
        store.stop()


main()
