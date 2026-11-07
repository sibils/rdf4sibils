#!/usr/bin/env python3
"""Markdown tables per query group for the report."""
import json, os, statistics as st
H = os.path.dirname(os.path.abspath(__file__))
L = lambda n: {q["name"]: q for q in json.load(open(f"{H}/results/queries_{n}.json"))["queries"]}
V, Q0, Q = L("virtuoso-v2"), L("qlever-default"), L("qlever-recommended")
M18 = L("qlever-mem18")
def warm(q):
    w = [r["s"] for r in q["runs"][1:] if not r.get("error")]
    return st.median(w) if w else None
def f(x):
    return "error" if x is None else (f"{x*1000:.0f} ms" if x < 1 else f"{x:.1f} s")
def cold(q):
    return None if q["runs"][0].get("error") else q["runs"][0]["s"]
titles = dict(examples="Example queries shipped with v2", counts="Whole-store counts", describe="DESCRIBE", lookup="Point lookups", joins="Joins and grouping",
              text="Text filters (no text index)", filters="Value filters, sorting, paging", paths="Property paths", model="Data model definitions")
for g, t in titles.items():
    print(f"\n#### {t}\n\n| Query | Rows | Virtuoso cold | Virtuoso warm | QLever cold | QLever warm | QLever repeat (result cache) | Warm ratio V/Q |\n|---|--:|--:|--:|--:|--:|--:|--:|")
    for n, q in V.items():
        if q["group"] != g: continue
        x = Q[n]; a, b = warm(q), warm(x)
        rows = x["runs"][0].get("rows")
        print(f"| {n} | {rows} | {f(cold(q))} | {f(a)} | {f(cold(x))} | {f(b)} | {f(x.get('cached'))} | {('%.1f' % (a/b)) if a and b else '-'} |")
print("\n#### Heavy queries, run once\n\n| Query | Virtuoso | QLever 11 GB, 16 threads | QLever 18 GB, 6 threads |\n|---|--:|--:|--:|")
for n, q in V.items():
    if not q["heavy"]: continue
    print(f"| {n} | {f(cold(q))} | {f(cold(Q[n]))} | {f(cold(M18[n]))} |")
# group summaries
print("\n| Group | Queries | Faster warm on Virtuoso | Faster warm on QLever | Total warm V | Total warm Q |\n|---|--:|--:|--:|--:|--:|")
for g in titles:
    ns = [n for n, q in V.items() if q["group"] == g and warm(q) and warm(Q[n])]
    print(f"| {g} | {len(ns)} | {sum(warm(V[n]) < warm(Q[n]) for n in ns)} | {sum(warm(V[n]) > warm(Q[n]) for n in ns)} | {f(sum(warm(V[n]) for n in ns))} | {f(sum(warm(Q[n]) for n in ns))} |")
