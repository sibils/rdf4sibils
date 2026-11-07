# Virtuoso vs QLever: trial on the v2 data

> Later fixes and benchmarks, which supersede some results here, are in `README-fix-and-benchmarks.md`.

**QLever holds exactly the same data as Virtuoso and gives the same answers on most queries, but it isn't a drop-in replacement yet.** Some v2 code needs small fixes, and the main open problem is memory: at the same 11 GB query limit as Virtuoso's buffers, the heaviest aggregation queries fail, which also stops `datamodel.json` and leaves VoID generation incomplete.

This was a first run with almost no tuning, so the timings and memory figures are a baseline, not a final verdict.

## Setup

| | Virtuoso | QLever |
|---|---|---|
| **Version** | Existing v2 database, native | Image `commit-7f8b3be50d`, CLI 0.6.0, in Docker |
| **Data** | Loaded from `v2/out/ttl` | Indexed from the same files |
| **Memory setting** | About 11 GB of buffers (`virtuoso.ini.dev`) | 8 GB in the first pass, 11 GB in the re-run |
| **Machine** | `lin-202`: 16 CPUs, 30 GB RAM | Same |

Each store ran on this machine with both up during the first pass; the 11 GB and 18 GB QLever runs had Virtuoso stopped. Only the single-client behaviour was tested, not concurrent users.

## Load (baseline)

| | Virtuoso | QLever |
|---|---|---|
| **Load time** | 53 and 57 min (October 2025 logs) | 51 min |
| **Size on disk** | 19 GB | 29 GB |
| **Peak memory during load** | Not measured | 12.6 GB |

The QLever run used one main input stream, so tuning and file grouping are still untested. It also needs `"parallel": "false"` because the parallel parser rejects our multi-line literals.

## What works as expected

| Check | Result |
|---|---|
| **Triples in the main graph** | 1,386,335,507 in both |
| **Counts per predicate and per class** | Identical (106 predicates, 78 classes) |
| **Example queries 102–105** | Identical results |
| **`DESCRIBE`** | Same triples for all 9 sampled entities and an unknown IRI, including blank nodes, apart from the two data differences below |
| **Turtle and N-Triples output** | Work |
| **RDF/XML and JSON-LD** | Converted from Turtle with rdflib on a small sample |
| **Ontology domain and range queries** | All 12 match, apart from `xsd:int` |
| **Data model definition and prefix queries** | Identical once `owl:` is declared |
| **Federated `SERVICE`** | Works (tested against Rhea) |
| **Protocol** | GET, POST form and `application/sparql-query` work, as do the `/sparql` path, ASK, CONSTRUCT, CSV, XML and `SPARQLWrapper` |
| **CORS** | QLever sends its own headers |
| **Update without a token** | Refused with HTTP 403 |
| **Queries used by `sparql-editor`** | Same results, using my approximation of its queries; the editor itself wasn't opened |

## What doesn't work as is

| Problem | Evidence | Fix |
|---|---|---|
| **`DEFINE sql:describe-mode` in `/describe`** | HTTP 400 (`main.py:517`) | Remove it; plain `DESCRIBE` gave the results above |
| **RDF/XML and JSON-LD from the store** | HTTP 406 | Convert from Turtle in `describe_iri` |
| **Example 101** | HTTP 400: aggregate without `GROUP BY` | Add `GROUP BY` (fixed query not yet run) |
| **Implicit prefixes** | HTTP 400; breaks `prefix_query` in `datamodel_builder.py` and may break users' queries | Declare `owl:`, tell users |
| **`select ?c as ?x`** in `sparql_client.py` | HTTP 400 | Use `(?c as ?x)` |
| **Regex backreferences** | HTTP 400, because QLever uses RE2 | Document it; no example query uses them |
| **`GET /sparql` with no query** | HTTP 404 instead of Virtuoso's form | Redirect to `/sparql-editor` in nginx |
| **`qlever index` exit code** | Returns 0 even when the build fails | Check the log for `Index build completed` |

## Data differences

| Difference | Virtuoso | QLever | Which is right? |
|---|---|---|---|
| **40,108 invalid dates** such as `"04-04-2022"^^xsd:date` (13% of 300,767) | Kept as dates but compared wrongly: `>= 2020-01-01` gives 10,032 and includes `01-01-1969`; `DESCRIBE` changes the value to `0401-01-01` | Stored as `xsd:string`: the same filter gives 4,898, leaving those dates out | Neither. The answer should be 11,262 (4,898 ISO + 6,364 day-month by string) |
| **Integers** (`oa:start`, `oa:end`, `sibilo:ordinal`) | `xsd:integer` | `xsd:int` | Same values; `datamodel.json` would show the new type |
| **Property paths** (`+`, `{,3}`) | Duplicate rows (18 and 13) | 9 distinct rows | QLever; both give the same set of values |
| **Triple count with no graph clause** | 5,589 more, from system graphs | Main graph only | Expected |

**Correction:** the source dates are ISO, and `date_to_yyyy_mm_dd` wrongly reversed them. The fix is in `v2/rdfize/publi_rdfizer.py`. See `README-fix-and-benchmarks.md`.

## Speed

The two stores vary by query type: QLever was faster on joins and aggregations over annotations, while Virtuoso was faster on simple counts and large `DESCRIBE`s.

Second-run times in seconds, with QLever's result cache cleared and an 8 GB limit:

| Query | Virtuoso | QLever |
|---|---|---|
| Example 104 (annotations by terminology) | 56.5 | **15.4** |
| Domain query on `sibilo:ordinal` | 49.6 | **7.6** |
| Sentence text scan with `contains` | **24.9** | 33.5 |
| Count of the main graph | **1.4** | 7.0 |
| Triples per predicate | **3.5** | 10.0 |
| `DESCRIBE` of the largest publication (11,550 annotations) | **2.1** | 6.4 |
| Regex on concept labels | 0.3 | 0.4 |

Cold-cache runs only:

- **Example 105:** Virtuoso 107 s, QLever 23 s.
- **12 ontology queries in total:** Virtuoso 162 s, QLever 68 s.
- **`DESCRIBE` of a typical entity:** 0.2 s or less on both.

## Memory: the main open problem

| Query | Virtuoso | QLever at 8 GB | QLever at 11 GB | QLever at 18 GB (diagnostic) |
|---|---|---|---|---|
| `class_use` on `fabio:JournalArticle` | 29 s | Out of memory | 41 s, same apart from dates | Not run |
| Graph list | 3 s | Out of memory | 22 s, main graph only | Not run |
| `prop_use` on `oa:hasBody` | 59 s | Out of memory | Out of memory after 345 s | 663 s, identical |
| `prop_use` on `sibilo:ordinal` | 56 s | Out of memory | Out of memory after 344 s | Not run |
| `/describe/model` | 1,158 s | Out of memory | Out of memory after 9 s | 434 s, see below |

Peak memory of the server process:

| Store | Peak |
|---|---|
| Virtuoso | 12.9 GB |
| QLever at 8 GB | 8.0 GB |
| QLever at 11 GB | 13.8 GB |
| QLever at 18 GB | 16.2 GB |

At 18 GB, `/describe/model` returned 681 rows against Virtuoso's 672. The differences I sampled were all date rows, as expected from the invalid dates, but I didn't check all 57 differing rows.

So these failures are at least partly a matter of memory, but `oa:hasBody` was still 11 times slower than on Virtuoso when it succeeded. Tuning or rewriting these queries, which use `OPTIONAL` over very common properties, hasn't been tried.

## Pipeline steps

| Step | Result on QLever at 11 GB |
|---|---|
| **`datamodel_builder.py`** | **Failed.** With `owl:` declared it ran 73 usage queries, then ran out of memory on `oa:TextPositionSelector`. Not retried at 18 GB |
| **VoID generator with `-r`, no JDBC** | **Incomplete.** Finished in 6 min with errors, including out-of-memory errors and 433 `NullPointerException`s. Output has 3,996 lines against 7,113, and about 10 class-partition lines against 139 |

## Not tested

- The FastAPI app, nginx and website running against QLever.
- The HTML output of `/describe`.
- The real `sparql-editor` page.
- Several users at once.
- Load tuning or file grouping.
- Whole collections (step 2).

## Corrections to `README-move-to-qlever.md`

- **Item 5:** confirmed. Multi-line literals do break the parallel parser, so this is no longer from memory.
- **Item 7:** the invalid dates came from an rdfizer bug. Virtuoso also mishandles them.
- **Item 14:** QLever accepts `{,3}` paths. Only `?c as ?x` and the missing `GROUP BY` fail.
- **Item 16:** a query with no graph clause covers the main graph on QLever, as hoped.
- **Item 19:** federation confirmed working.

## Suggested next steps

1. Make the v2 fixes above, starting with ISO dates.
2. Tune and rewrite the failing data model queries, then re-run `datamodel_builder.py` at 11 GB.
3. Find out why the VoID generator fails, and whether it needs QLever-specific settings.
4. Test load tuning with file grouping.
5. Run the FastAPI app against QLever.
