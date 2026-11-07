# Fixes and benchmarks: QLever vs Virtuoso on the v2 data

**After tuning, QLever doesn't clearly outperform Virtuoso on this data, but it's a credible replacement.** The benchmarks you mentioned hold up on large joins and aggregates and on memory use, but not on index size. Load time is a tie once both stores are tuned, and Virtuoso stays faster on small lookups and simple scans. QLever also returned correct counts where Virtuoso silently returned wrong ones.

| | Virtuoso (v2 settings) | QLever (tuned) | Better |
|---|---|---|---|
| **Load time** | 59.2 min (1 loader), 20.9 min (8 loaders) | 50.3 min untuned, **21.9 min** tuned | Tie once both are tuned |
| **Disk size** | **about 20 GB** | 28.9 GB | Virtuoso, by about 45% |
| **Peak memory, load** | 13.9 GB (1 loader), 17.3 GB (8 loaders) | **8.6 GB** | QLever |
| **Peak memory, queries** | 19.7 GB | **10.6 GB** | QLever |
| **Large joins and aggregates** | 45 s for `sibilo:ordinal` domain | **6.5 s** | QLever, 4–10× |
| **Repeated queries** | No result cache | **Under 10 ms for most** | QLever |
| **Small lookups** | **3 ms** | 5–17 ms | Virtuoso, though both are fast |
| **Simple whole-store counts** | **1.3 s** for main graph triples | 3.3 s | Virtuoso, 2–3× |
| **Data model build** | 33 min | **12 min** | QLever |
| **Correct results** | Silent undercount on subquery aggregates | No errors found | QLever |
| **Queries too big for 11 GB** | Runs them, using more memory | Fails with an out of memory error unless rewritten | Virtuoso |

Steps 1–4 are done. The data model and VoID both now work on QLever at 11 GB. All timings are from `lin-202` (16 CPUs, 30 GB RAM), on identical data of 1,386,335,507 triples in the main graph. No run was affected by suspend.

## What needs a decision

1. **Whether the QLever trade-offs are acceptable for v3.** It needs about 45% more disk, and very large queries must be written to fit in memory. In return you get half the memory, faster analytics and a result cache.
2. **Whether to correct the published `void-sibils.ttl`.** It has a wrong `void:entities` value on 73 classes (details under step 3).
3. **What to do about `/describe/model` on QLever.** It runs out of memory at 11 GB and takes 450 s at 18 GB. I recommend building it ahead of time, from the same per-class results as the data model.

## What I did

### Step 1: v2 fixes

| Fix | File | Checked by |
|---|---|---|
| ISO dates are no longer reversed | `v2/rdfize/publi_rdfizer.py` | Re-rdfizing a PMC chunk gives the same 1,044,783 lines as the corrected data (blank node IDs normalised) |
| Date filter gives correct results | Data | `>= 2020-01-01` gives 11,262 results, as on Virtuoso |
| `term_query` select fixed | `v2/rdfize/sparql_client.py` | Only the equivalent regex query ran, not this function |
| Example 101 has its `group by` | `v2/sparql_queries/query-list.txt` | Same 13 rows on both stores |
| `describe_iri` supports QLever | `v2/serve/main.py`, `v2/rdfize/api_platform.py` | FastAPI against QLever: `ttl`, `n3`, `jsonld` and `rdf` work; `html` returns 501, because there's no replacement yet |
| QLever nginx config | `v2/nginx/nginx-rdf4sibils-qlever.conf` (new) | Temporary container: `GET /sparql` redirects to the editor, queries work with one set of CORS headers, `OPTIONS` works |

Two QLever points to keep in mind:
- **Unprotected cache clearing:** `?cmd=clear-cache` works through nginx without a token, while changing settings returns 403. Anyone could clear the cache, so this should be blocked before going public. Blocking it only in the URL wouldn't be enough, because the command can also be sent by POST.
- **Prefixes:** the v2 examples rely on prefixes that Virtuoso defines itself. QLever needs them declared in the query, and the benchmarks add them.

### Step 2: data model queries

`datamodel_builder.py` now completes on QLever at 11 GB, in **729 s**. Its output is **identical to the existing `datamodel.json`**: 137 entities, 744 definitions and 1,182 usage statements. Getting there took three changes:
- **Aggregate first:** QLever then sees one row per distinct value instead of one row per triple.
- **One query per property:** the biggest classes still needed over 11 GB when all their properties were in one query.
- **Listing properties with `group by`:** this takes 0.8 s, where `select distinct` ran out of memory.

**Set `SIBILS_SPARQL_ENGINE=qlever` when building against QLever.** The default is Virtuoso, which gets a different query form, for the reason below.

**Virtuoso silently returns wrong counts for the aggregate-first query:**

| `oa:hasTarget` on `sibilo:NexAnnotation` | Virtuoso | QLever |
|---|---|---|
| Plain count | 115,333,425 | 115,333,426 |
| Sum over `group by ?o` subquery | **52,001,528** (same on both repeats) | 115,333,426 |

There is no error or warning, and I didn't find the cause. `MaxQueryMem` or `ResultSetMaxRows` could be involved, but I didn't test either. With the plain form, Virtuoso builds the model in 1,986 s and only one statement differs from the existing file, by the off-by-one shown above. On Virtuoso, the same triple count is 115,333,426 without the type join and 115,333,425 with it, and no subject lacks the type, so that's an inconsistency inside Virtuoso, also unexplained.

### Step 3: VoID generator

The generator now completes on QLever: **9,714 queries in 10m20s at 11 GB, with no errors**, where it previously failed with 433 null pointer errors. There were three causes:
- **Two generator bugs:** on the group-by path, `IsSourceClassLinkedToTargetClasses` loaded the wrong query file and discarded the count. I patched this in a private copy, `~/work/tools/qlever/bench/void-gen`. Your clone is unchanged, so the patch still has to be applied there or sent upstream.
- **Wrong mode:** the run needs `--optimize-for=Qlever`.
- **Too much concurrency:** I used `--max-concurrency=2`, down from the default 5, so queries don't compete for memory.

This run had `group-by-hash-map-enabled` on, because it came before I found that setting slows things down. I didn't time Virtuoso's VoID run on the same day, so there's no time comparison.

**The published Virtuoso file has an error:** in `void-sibils.ttl`, 73 classes have `void:entities` set to 378,046,300, which is the total number of subjects. For example, `fabio:NewsItem` has 19 instances, which QLever's file gives correctly and a direct query confirms. I didn't check whether the JDBC path or Virtuoso causes this. For property partitions, 70 of the 75 shared properties have the same triple count in both files. The 5 others reflect different contents: Virtuoso's file includes its system graphs, and QLever's data includes the old VoID file.

### Step 4: load tuning

All these QLever runs use 1 stream for the plain files plus the gz streams shown, and all completed runs produced the same triple count.

| Run | Gz streams | Sort memory | Other | Time | Parse | Size | Peak memory |
|---|--:|--:|---|--:|--:|--:|--:|
| `L0-base` | 1 | 10G | | 50.3 min | 2,372 s | 30.76 GB | 12.57 GB |
| `L1-s2` | 2 | 10G | | 33.4 min | 1,357 s | 30.40 GB | 12.39 GB |
| `L1-s4` | 4 | 10G | | 26.7 min | 951 s | 29.92 GB | 12.32 GB |
| `L1-s8` | 8 | 10G | | 23.3 min | 749 s | 29.43 GB | 13.06 GB |
| `L1-s16` | 16 | 10G | | 22.2 min | 693 s | 28.91 GB | 12.73 GB |
| `L2-m20` | 16 | 20G | | 22.3 min | 689 s | 28.91 GB | 21.24 GB |
| `L2-m8` | 16 | 8G | | 21.8 min | 686 s | 28.91 GB | 12.07 GB |
| `L2-m6` | 16 | 6G | | 23.3 min | 787 s | 28.91 GB | 11.45 GB |
| **`L2-m6-b5` (chosen)** | 16 | 6G | 5M triples per batch | **21.9 min** | 697 s | 28.91 GB | **8.62 GB** |
| `L2-b125k` | 16 | 8G | 125k rows per block | 21.9 min | 693 s | 28.81 GB | 11.58 GB |
| `L2-b500k` | 16 | 8G | 500k rows per block | 23.9 min | 697 s | 28.79 GB | 11.78 GB |
| `L2-batch30` | 16 | 8G | 30M triples per batch | Failed after 4 min | | | 28.81 GB, out of RAM |
| `L2-par4` | 4 | 8G | Parallel parser | Failed at the start | | | |

| Virtuoso run | Loaders | Time | Size right after load | Peak memory |
|---|--:|--:|--:|--:|
| `V1-1loader` (v2 default) | 1 | 59.2 min | 15.72 GB | 13.9 GB |
| `V2-8loaders` | 8 | 20.9 min | 22.02 GB | 17.3 GB |

- **Streams are what matter:** going from 1 to 16 cuts load time by 56%. The gain flattens after 8, because the sort and vocabulary phases take a fixed 10 minutes or so.
- **Sort memory doesn't affect time:** 6G and 20G take about the same, so there's no need to give it more.
- **Batch size sets peak memory:** 5M brought the peak under 11 GB at no cost in time. 30M used all the RAM.
- **Index size is hard to reduce:** 26 GB of the 28.9 GB is the six permutations, 2 GB is the vocabulary and 0.9 GB is patterns. Larger blocks save only 0.3%. Removing permutations (`-o`) would break predicate-variable queries, and `--iri-as-blank-node-regexes` would make IRIs unaddressable, so I didn't run either.
- **The parallel parser needs the Turtle changed:** both MEDLINE and PMC contain multi-line literals. Writing single-line literals in v3 would let you test it.
- **Virtuoso's size:** `virtuoso.db` measured 15.72 GB just after the 1-loader load, but 19.98 GB after the benchmarks and shutdown, close to the earlier 19–20 GB. I didn't find out why it grew, so I use about 20 GB as the comparable figure. The 22.02 GB for 8 loaders was measured just after load, so it may also have grown.

## Query tuning

Each run has 34 short queries and, except for `qlever-threads16`, 25 heavy ones, on the `L2-m6-b5` index.

| Run | Memory limit | Settings changed | Peak memory | Effect |
|---|--:|---|--:|---|
| `qlever-default` | 11 GB | None | 10.5 GB | Baseline |
| `qlever-hash` | 11 GB | `group-by-hash-map-enabled=true` | 10.8 GB | **Worse**: `hasSelector` 117 s vs 32 s, `hasTarget` 114 s vs 35 s. Leave it off |
| `qlever-threads16` | 11 GB | `max-num-threads-per-query=16` | 6.5 GB, short queries only | **Better for scans**: main graph count 6.9 s to 3.4 s, DESCRIBE 57 ms to 37 ms |
| `qlever-recommended` | 11 GB | `max-num-threads-per-query=16` | 10.6 GB | Used in the tables below |
| `qlever-mem18` | 18 GB | None | 15.2 GB | All original queries now finish, short queries barely change |

The 18 GB run tests fairness, because Virtuoso actually used 19.7 GB. More memory only helps queries that otherwise fail. Raising simultaneous queries (`-j`) from 8 to 32 gave no gain.

**Recommended QLever config:**
```
qlever-index   --stxxl-memory 6G  --vocabulary-type on-disk-compressed
               16 gz input streams, settings {"num-triples-per-batch": 5000000}
qlever-server  -m 11G -c 2G -j 8
at runtime     max-num-threads-per-query=16
```
Runtime settings didn't survive a server restart here, so set this one again after each start.

## Query results by type

Virtuoso has v2's settings. QLever has the recommended config. **Cold** is the first pass after evicting the page cache and restarting, so later queries still benefit from pages read by earlier ones. **Warm** is the median of two more passes, with QLever's result cache cleared before each query. **Repeat** is QLever's time with its result cache in use, and Virtuoso has no equivalent. A ratio above 1 means QLever is faster.

| Group | Queries | Faster warm on Virtuoso | Faster warm on QLever | Total warm V | Total warm Q |
|---|--:|--:|--:|--:|--:|
| examples | 5 | 3 | 2 | 66.3 s | 20.3 s |
| counts | 4 | 4 | 0 | 5.9 s | 16.0 s |
| describe | 4 | 3 | 1 | 2.2 s | 1.4 s |
| lookup | 4 | 4 | 0 | 15 ms | 38 ms |
| joins | 4 | 3 | 1 | 45.4 s | 7.3 s |
| text | 3 | 1 | 2 | 42.4 s | 35.2 s |
| filters | 3 | 2 | 1 | 118 ms | 60 ms |
| paths | 3 | 2 | 1 | 44 ms | 36 ms |
| model | 3 | 3 | 0 | 28 ms | 69 ms |

#### Example queries shipped with v2

| Query | Rows | Virtuoso cold | Virtuoso warm | QLever cold | QLever warm | QLever repeat (result cache) | Warm ratio V/Q |
|---|--:|--:|--:|--:|--:|--:|--:|
| example 101 | 13 | 49 ms | 8 ms | 55 ms | 30 ms | 5 ms | 0.3 |
| example 102 | 4 | 89 ms | 8 ms | 15 ms | 12 ms | 5 ms | 0.6 |
| example 103 | 2 | 63 ms | 8 ms | 17 ms | 12 ms | 6 ms | 0.7 |
| example 104 | 47 | 61.4 s | 57.9 s | 14.2 s | 14.4 s | 4 ms | 4.0 |
| example 105 | 2214 | 14.8 s | 8.3 s | 24.6 s | 5.8 s | 283 ms | 1.4 |

#### Whole-store counts

| Query | Rows | Virtuoso cold | Virtuoso warm | QLever cold | QLever warm | QLever repeat (result cache) | Warm ratio V/Q |
|---|--:|--:|--:|--:|--:|--:|--:|
| triples in main graph | 1 | 1.4 s | 1.3 s | 4.8 s | 3.3 s | 4 ms | 0.4 |
| triples per predicate | 106 | 3.6 s | 3.5 s | 10.5 s | 9.9 s | 4 ms | 0.4 |
| instances per class | 78 | 1.0 s | 1.1 s | 2.4 s | 2.6 s | 5 ms | 0.4 |
| annotations | 1 | 110 ms | 110 ms | 209 ms | 236 ms | 4 ms | 0.5 |

#### DESCRIBE

| Query | Rows | Virtuoso cold | Virtuoso warm | QLever cold | QLever warm | QLever repeat (result cache) | Warm ratio V/Q |
|---|--:|--:|--:|--:|--:|--:|--:|
| describe PMC publication | 286 | 98 ms | 6 ms | 49 ms | 38 ms | 3 ms | 0.2 |
| describe MEDLINE publication | 933 | 95 ms | 14 ms | 145 ms | 112 ms | 5 ms | 0.1 |
| describe GO concept | 11 | 18 ms | 2 ms | 13 ms | 14 ms | 3 ms | 0.1 |
| describe largest publication | 127073 | 2.3 s | 2.2 s | 1.4 s | 1.2 s | 156 ms | 1.8 |

#### Point lookups

| Query | Rows | Virtuoso cold | Virtuoso warm | QLever cold | QLever warm | QLever repeat (result cache) | Warm ratio V/Q |
|---|--:|--:|--:|--:|--:|--:|--:|
| properties of one publication | 41 | 4 ms | 3 ms | 7 ms | 7 ms | 7 ms | 0.5 |
| subjects of one concept | 2 | 4 ms | 3 ms | 6 ms | 6 ms | 5 ms | 0.5 |
| publication by year literal | 476 | 42 ms | 6 ms | 164 ms | 8 ms | 7 ms | 0.7 |
| annotations of one publication | 24 | 4 ms | 3 ms | 18 ms | 17 ms | 7 ms | 0.2 |

#### Joins and grouping

| Query | Rows | Virtuoso cold | Virtuoso warm | QLever cold | QLever warm | QLever repeat (result cache) | Warm ratio V/Q |
|---|--:|--:|--:|--:|--:|--:|--:|
| concepts of one publication with labels | 24 | 5 ms | 3 ms | 25 ms | 24 ms | 6 ms | 0.1 |
| top concepts | 20 | 438 ms | 440 ms | 794 ms | 774 ms | 5 ms | 0.6 |
| annotated publications per source | 0 | 3 ms | 2 ms | 18 ms | 14 ms | 7 ms | 0.2 |
| domain of sibilo:ordinal | 7 | 46.5 s | 45.0 s | 6.3 s | 6.5 s | 7 ms | 7.0 |

#### Text filters (no text index)

| Query | Rows | Virtuoso cold | Virtuoso warm | QLever cold | QLever warm | QLever repeat (result cache) | Warm ratio V/Q |
|---|--:|--:|--:|--:|--:|--:|--:|
| contains over sentences | 1 | 42.8 s | 41.7 s | 51.6 s | 34.4 s | 3 ms | 1.2 |
| regex on concept labels | 1 | 231 ms | 229 ms | 395 ms | 380 ms | 3 ms | 0.6 |
| prefix on concept labels | 27 | 434 ms | 476 ms | 381 ms | 434 ms | 3 ms | 1.1 |

#### Value filters, sorting, paging

| Query | Rows | Virtuoso cold | Virtuoso warm | QLever cold | QLever warm | QLever repeat (result cache) | Warm ratio V/Q |
|---|--:|--:|--:|--:|--:|--:|--:|
| date range | 1 | 22 ms | 2 ms | 7 ms | 5 ms | 3 ms | 0.4 |
| publications per year | 83 | 22 ms | 6 ms | 7 ms | 8 ms | 5 ms | 0.8 |
| latest publications | 10 | 235 ms | 110 ms | 60 ms | 48 ms | 5 ms | 2.3 |
| deep paging | 100 | error | error | 1.7 s | 1.7 s | 5 ms | - |

#### Property paths

| Query | Rows | Virtuoso cold | Virtuoso warm | QLever cold | QLever warm | QLever repeat (result cache) | Warm ratio V/Q |
|---|--:|--:|--:|--:|--:|--:|--:|
| ancestors of a GO term | 9 | 24 ms | 3 ms | 10 ms | 8 ms | 5 ms | 0.4 |
| ancestors up to depth 3 | 9 | 2 ms | 3 ms | 12 ms | 10 ms | 5 ms | 0.3 |
| descendants of a broad GO term | 1 | 42 ms | 38 ms | 18 ms | 17 ms | 5 ms | 2.2 |

#### Data model definitions

| Query | Rows | Virtuoso cold | Virtuoso warm | QLever cold | QLever warm | QLever repeat (result cache) | Warm ratio V/Q |
|---|--:|--:|--:|--:|--:|--:|--:|
| class definitions | 403 | 111 ms | 18 ms | 32 ms | 30 ms | 14 ms | 0.6 |
| property definitions | 241 | 13 ms | 8 ms | 26 ms | 28 ms | 13 ms | 0.3 |
| prefixes | 26 | 29 ms | 2 ms | 11 ms | 11 ms | 7 ms | 0.2 |

Query results matched on both stores, except in these cases:
- **`triples per predicate` and `instances per class`:** Virtuoso's default graph includes its system graphs, so it returns 207 and 92 rows against QLever's 106 and 78. These two aren't like for like.
- **`deep paging`:** Virtuoso refuses it (error SR353, more than the allowed rows to sort).

### Heavy queries

Each ran once, so treat small differences as noise. "As first written" means the query as it was before my rewrite.

| Query | Virtuoso | QLever 11 GB, 16 threads | QLever 18 GB, 6 threads |
|---|--:|--:|--:|
| class_use fabio:JournalArticle properties | 822 ms | 11 ms | 11 ms |
| class_use fabio:JournalArticle rdf:type | 12 ms | 217 ms | 213 ms |
| class_use fabio:JournalArticle as first written | 26.4 s | 38.1 s | 38.5 s |
| class_use oa:TextPositionSelector properties | 50.6 s | 893 ms | 1.1 s |
| class_use oa:TextPositionSelector rdf:type | 1.8 s | 6.5 s | 6.5 s |
| class_use oa:TextPositionSelector as first written | 1097.3 s | error | 174.1 s |
| class_use sibilo:AnnotationTarget properties | 66.4 s | 849 ms | 932 ms |
| class_use sibilo:AnnotationTarget rdf:type | 2.3 s | 6.8 s | 6.3 s |
| class_use sibilo:AnnotationTarget oa:hasSelector | 403.8 s | 39.2 s | 40.5 s |
| class_use sibilo:AnnotationTarget oa:hasSource | 29.7 s | 12.2 s | 13.7 s |
| class_use sibilo:AnnotationTarget as first written | 300.6 s | error | 103.0 s |
| class_use sibilo:NexAnnotation properties | 67.7 s | 851 ms | 902 ms |
| class_use sibilo:NexAnnotation rdf:type | 2.8 s | 6.6 s | 6.5 s |
| class_use sibilo:NexAnnotation oa:hasBody | 3.5 s | 7.2 s | 8.3 s |
| class_use sibilo:NexAnnotation oa:hasTarget | 99.6 s | 40.6 s | 42.5 s |
| class_use sibilo:NexAnnotation as first written | 261.7 s | error | 96.8 s |
| prop_use oa:hasBody as first written | 64.4 s | error | 692.2 s |
| prop_use oa:hasBody count | 106 ms | 367 ms | 940 ms |
| prop_use oa:hasBody domain | 351.4 s | 40.6 s | 40.8 s |
| prop_use oa:hasBody range | 531 ms | 1.0 s | 1.3 s |
| prop_use sibilo:ordinal as first written | 59.7 s | error | 655.3 s |
| prop_use sibilo:ordinal count | 24 ms | 126 ms | 211 ms |
| prop_use sibilo:ordinal domain | 38.8 s | 10.2 s | 9.3 s |
| prop_use sibilo:ordinal range | 103 ms | 181 ms | 239 ms |
| /describe/model | 1248.1 s | error | 450.4 s |

- **The rewrites:** on `hasBody` domain, QLever takes 41 s against Virtuoso's 351 s. On `class_use ... hasSelector`, it's 39 s against 404 s.
- **The originals:** Virtuoso wins at 18 GB on `prop_use`, 64 s against 692 s. QLever wins on the `class_use` originals, for example 174 s against 1,097 s.
- **`class_use sibilo:NexAnnotation oa:hasTarget`:** Virtuoso's result here is the undercount described in step 2. Its time isn't a valid comparison.
- **`/describe/model`:** all 511 class and property counts match between the stores. The 24 differing rows are type labels only: `xsd:int` against `xsd:long` or `xsd:integer`, and `langString` against `IRI`.

### Concurrent short queries

A mix of 9 short queries (DESCRIBE, lookup, sort), 30 s at each client count, run from the same machine.

| Run | Metric | 1 client | 4 clients | 16 clients | 64 clients |
|---|---|--:|--:|--:|--:|
| Virtuoso | Queries per second | 11.0 | 36.0 | 47.8 | 44.0 |
| | Median / p95 | 20 / 323 ms | 25 / 456 ms | 203 / 1,127 ms | 1,074 / 2,176 ms |
| QLever, 2 GB cache, `-j 8` | Queries per second | 25.1 | 109.8 | 295.1 | 289.1 |
| | Median / p95 | 21 / 103 ms | 23 / 107 ms | 45 / 154 ms | 115 / 750 ms |
| QLever, 2 GB cache, `-j 32` | Queries per second | 25.0 | 105.6 | 259.3 | 255.9 |
| | Median / p95 | 22 / 102 ms | 24 / 109 ms | 48 / 177 ms | 131 / 836 ms |
| QLever, no cache, 16 threads | Queries per second | 4.6 | 20.8 | 36.2 | 37.3 |
| | Median / p95 | 53 / 920 ms | 54 / 932 ms | 285 / 1,355 ms | 1,453 / 3,344 ms |

These bracket the real behaviour rather than measure it. Repeating 9 queries suits the cache perfectly, while `-c 0` removes more caching than a real deployment would. The cached and no-cache QLever runs also differ in thread setting (6 and 16). A real workload should land somewhere in between, depending on how often queries repeat.

## Why this differs from published benchmarks

I don't know for sure, and I didn't test the reasons. Some possibilities:
- **The data shape:** 378M subjects are mostly blank nodes with random-looking IDs, which compress poorly in the permutations.
- **The workload:** many of these queries are point lookups, which suit Virtuoso's mature row-level access.
- **The machine:** most published runs use bigger servers and bigger datasets, and QLever's strengths may show more with scale. The whole-collection v3 data may look different.

## Limits of this comparison

- **QLever got more tuning than Virtuoso:** Virtuoso's query settings stayed at v2's values, with only the loader count varied. Tuning `MaxQueryMem` or `ThreadsPerQuery` could improve its results.
- **Memory isn't equal:** both were configured for about 11 GB, but Virtuoso peaked at 19.7 GB and QLever at 10.6 GB. The 18 GB QLever run covers this.
- **Few repetitions:** short queries have one cold and two warm runs, and heavy queries one run. Small differences mean little. `L2-m6` was 7% slower than similar runs, which gives an idea of the noise.
- **The 8-loader Virtuoso database wasn't query-tested:** the query benchmarks used the 1-loader database.

**Not tested:**
- QLever's full-text index, which could change the text results; `contains` here scans all sentences
- Materialized views
- The rest of the FastAPI app against QLever, including the HTML `describe` replacement
- Heavy and light queries running together
- SPARQL Update
- A whole-collection dataset

## Corrections to my earlier reports

- **The date bug:** `README-compare-virtuoso-qlever.md` said the source dates were day-month. All 40,045 source PMC dates are ISO, and `date_to_yyyy_mm_dd` reversed them. I've corrected that file.
- **The hash group-by:** I expected it to help on QLever. It only helped the whole-class query form, which I ended up replacing, and it slows the final one.
- **Virtuoso's size:** I told you mid-run that its database was 24% smaller than QLever's. That used the 22.02 GB measured right after the 8-loader load. Comparing the settled 20 GB, QLever's index is about 45% larger.
- **QLever's index size:** the "29 GB" in my earlier report was the 30.76 GB index measured in GiB. This report uses GB throughout.

## Where things are

| What | Where |
|---|---|
| Scripts and raw results | `benchmarks/`, with results in `benchmarks/results/` |
| Data models and VoID file from QLever | `benchmarks/results/artifacts/` |
| Best QLever index | `~/work/tools/qlever/bench/runs/L2-m6-b5` |
| Private Virtuoso database (1 loader) | `~/work/tools/qlever/bench/virtuoso/` |
| Corrected data | `~/work/tools/qlever/bench/data-iso/` |
| Earlier trial index, no longer needed | `~/work/tools/qlever/sibils-v2` |

Your production Virtuoso database and `v2/out/ttl` weren't touched. All the servers I started are stopped.

To rerun: `benchmarks/load_matrix.sh`, `benchmarks/load_virtuoso.sh LABEL LOADERS`, `benchmarks/bench.py`, then `benchmarks/tables_md.py` for the tables.
