#!/usr/bin/env python3
"""Throughput of short queries with N clients. usage: concurrency.py URL 'describe-prefix' label"""
import json, os, random, statistics as st, sys, threading, time
import requests
url, desc, label = sys.argv[1:4]
J = "application/sparql-results+json"
B = "https://purl.expasy.org/sibils/rdf/data/"
ids = ["PMC10002150", "PMC10006513", "PMC10007211", "1000501"]
Q = [(desc + f"describe <{B}{i}>", "application/n-triples") for i in ids] + \
    [(f"select ?p ?o where {{ <{B}{i}> ?p ?o }}", J) for i in ids] + \
    [("select ?x ?d where { ?x <http://prismstandard.org/namespaces/basic/2.0/publicationDate> ?d } order by desc(?d) ?x limit 10", J)]
out = []
for n in (1, 4, 16, 64):
    lat, errs, stop = [], [0], time.time() + 30
    def work():
        s = requests.Session(); r = random.Random()
        while time.time() < stop:
            q, a = r.choice(Q); t = time.time()
            x = s.post(url, data={"query": q}, headers={"Accept": a}, timeout=120)
            lat.append(time.time() - t)
            if x.status_code != 200: errs[0] += 1
    th = [threading.Thread(target=work) for _ in range(n)]
    [t.start() for t in th]; [t.join() for t in th]
    lat.sort()
    rec = dict(label=label, clients=n, qps=round(len(lat) / 30, 1), median_ms=round(st.median(lat) * 1e3, 1), p95_ms=round(lat[int(len(lat) * .95)] * 1e3, 1), errors=errs[0])
    print(rec, flush=True); out.append(rec)
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "concurrency.jsonl"), "a") as f:
    for r in out: f.write(json.dumps(r) + "\n")
