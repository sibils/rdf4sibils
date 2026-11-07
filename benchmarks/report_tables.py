#!/usr/bin/env python3
"""Print per-query comparison tables from results/queries_<label>.json. usage: report_tables.py label1 label2 ..."""
import json, os, statistics as st, sys
HERE = os.path.dirname(os.path.abspath(__file__))
labels = sys.argv[1:]
D = {l: json.load(open(f"{HERE}/results/queries_{l}.json")) for l in labels}
for l, d in D.items():
    print(l, "mem", d["mem"], "cache", d["cache"], "set", d.get("set"), "extra", d.get("extra"), "start", d["start_s"], "peak", d.get("peak_rss_gb"), "susp", d["suspended_s"], "total", d["total_s"])
base = D[labels[0]]["queries"]
def cell(q):
    r = q["runs"]
    if not r: return "-"
    if q["heavy"]:
        return "ERR" if r[0].get("error") else f"{r[0]['s']:.2f}"
    cold = "ERR" if r[0].get("error") else f"{r[0]['s']:.3f}"
    w = [x["s"] for x in r[1:] if not x.get("error")]
    return f"{cold}/{(st.median(w) if w else float('nan')):.3f}"
print("| group | query | rows | " + " | ".join(labels) + " | same |")
for q in base:
    qs = [next((x for x in D[l]["queries"] if x["name"] == q["name"]), {"runs": [], "heavy": False}) for l in labels]
    ok = [x["runs"][0] for x in qs if x["runs"] and not x["runs"][0].get("error")]
    digs = {(r.get("digest"), r.get("rows")) if r.get("digest") else r.get("rows") for r in ok}
    print("|", q["group"], "|", q["name"], "|", (ok[0].get("rows") if ok else "-"), "|", " | ".join(cell(x) for x in qs), "|", "yes" if len(digs) == 1 else f"NO {[ (r.get('rows'),r.get('digest')) for r in ok]}", "|")
errs = [(l, q["name"], r["error"][:110]) for l in labels for q in D[l]["queries"] for r in q["runs"][:1] if r.get("error")]
for e in errs: print("ERR", *e)
