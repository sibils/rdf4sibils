# Moving from Virtuoso to QLever

This covers step 1 of v3: replacing Virtuoso with QLever while keeping the v2 website, API and SPARQL endpoint. Step 2 (loading whole collections) is out of scope, except where it affects the trial below.

No blocker was found, but **two issues need real design work**: the build pipeline and the limits on the public endpoint.

QLever has not been run yet, so anything marked **test** is unproven. Everything else comes from v2's code, its data or QLever's docs and source.

The v2 data is about 1.4 billion lines of Turtle, estimated from 12 sampled files, and 91–93% of those lines involve blank nodes.

## High difficulty

### 1. The build pipeline assumes a live database that can be loaded step by step

- **Issue:** QLever builds its index in one pass, while `do-rdfize.sh` loads files in stages and queries the store between them. The ontology's domains and ranges (`ontology_builder.py:106,135`), `datamodel.json` and the VoID file all come from the loaded data.
- **Solution:** build in two stages. Index the data and terminologies, generate those derived files against that index, then rebuild with everything. This leaves one clean index to deploy. QLever's update API could add the extra files instead, but it keeps them in a separate updates file.

### 2. Public endpoint limits and performance are unknown (test)

- **Issue:** Virtuoso has a 1M-row cap and a 2-hour limit here (`virtuoso.ini.prod`). QLever works differently, with memory, cache and timeout settings. The likely heavy queries are `/describe/model` (`main.py:536`), which aggregates the whole graph, and example 105, which runs `contains(lcase(...))` over sentence text.
- **Solution:** replay the real queries on the v2 data, then set `MEMORY_FOR_QUERIES`, `CACHE_MAX_SIZE` and `TIMEOUT`, plus nginx rate limits. Serve `/describe/model` from a precomputed file. QLever's text index is an option for sentence search, though those queries would then need its non-standard syntax.

## Medium difficulty

### 3. `/describe` loses RDF/XML and JSON-LD

- **Issue:** QLever's CONSTRUCT/DESCRIBE formats are Turtle, N-Triples, CSV, TSV and its own JSON. The API also offers RDF/XML and JSON-LD, which QLever can't produce.
- **Solution:** fetch Turtle in `describe_iri` and convert it with rdflib. Direct `/sparql` users lose those two formats, so document that.

### 4. `/describe` loses its HTML output

- **Issue:** the HTML view uses Virtuoso's `application/x-nice-microdata` format (`main.py:520`).
- **Solution:** render the page in FastAPI with a small template, reusing `html_builder.py` if it fits. Microdata markup would need rebuilding if we want to keep it.

### 5. Turtle files can't simply be concatenated for indexing

- **Issue:** each of the 1,527 data files repeats its 26 `@prefix` lines, but parallel parsing needs prefixes at the start of the input stream. Long multi-line literals also occur, with 206 lines ending in a period inside them across the 6 sampled MEDLINE files. These may confuse the parallel parser; this is from memory, not the docs (test).
- **Solution:** use `MULTI_INPUT_JSON`, or strip the prefixes and stream one header followed by the data. Set `PARSER_BUFFER_SIZE` and `ULIMIT`, and fall back to sequential parsing if needed.

### 6. One bad line can stop the whole build

- **Issue:** Virtuoso tracks errors per file, but QLever aborts the index build at the first parse error. `is_valid_url` is deliberately loose ("enough for virtuoso"), and `fix_concept_mdd_ttl.sh` already patches around bad data. The sample found no truly invalid IRIs; the 3 hits were table text inside literals, but that was only 12 data files and the 47 concept files.
- **Solution:** tighten IRI checks in the rdfizers and validate all files before indexing.

### 7. Some dates are invalid

- **Issue:** about 7% of sampled `xsd:date` values look like `"04-04-2022"` rather than `YYYY-MM-DD`. How QLever handles them is unknown (test), and date filters or sorting could misbehave.
- **Solution:** normalise them in the rdfizers. First confirm whether the source is day-month or month-day, because a value like this one doesn't show which.

### 8. Internal jobs will hit QLever's default timeout

- **Issue:** the default is 30 seconds, and a longer per-request timeout returns 403 without an access token. The ontology, data model and VoID jobs can all run long.
- **Solution:** run the builds on a private instance with a long timeout, and serve the public one with a short timeout. Using the access token on internal requests also works.

### 9. VoID generation uses a Virtuoso JDBC connection

- **Issue:** `void-related/doit-sibils.sh` connects with `--virtuoso-jdbc`, and the tool's README says this is much faster than HTTP.
- **Solution:** switch to its plain SPARQL mode (`-r`). Expect a slower run with heavy queries (test), so this needs the private instance from item 8.

### 10. Operations scripts need replacing

- **Issue:** these are all Virtuoso-specific:
  - `sparql_service.sh`
  - `load_ttl_files.sh`
  - `copy_virtuoso_db.sh`
  - `virtuoso.ini.*`
  - the `config/*.config` variables
  - `LOAD_RDF` in `rdfbuilder.py`
- **Solution:** use a Qleverfile and the `qlever` CLI, and choose Docker, Podman or native. Deployment becomes copying the index files and swapping the server over, which also makes rollback simpler.

## Low difficulty

| # | Issue | Solution |
|---|---|---|
| 11 | `DEFINE sql:describe-mode "CBD"` is Virtuoso-only (`main.py:517`) | Use plain `DESCRIBE`. QLever follows blank nodes recursively, so results should be close, but compare them on sample entities |
| 12 | `describe_iri` never checks the HTTP status, so a store error is returned as a 200 RDF response (`main.py:523-525`) | Check the status and return a proper error |
| 13 | Virtuoso's built-in prefixes won't exist: `prefix_query` uses `owl:` without declaring it (`datamodel_builder.py:136`), and users' saved queries may do the same | Add the declaration, drop `getSQLforVirtuoso` and the setup SQL, and tell users |
| 14 | Non-standard SPARQL: example 101 has an aggregate without `GROUP BY`, and `sparql_client.py` uses `?c as ?x` and `{2,4}` paths | Fix these and test all examples, including the external `sib-swiss/sparql-examples` SIBiLS set |
| 15 | QLever returns `xsd:int` for `xsd:integer`, which affects `oa:start`, `oa:end` and `sibilo:ordinal`, so `datamodel.json` and the concept hopper will change | Map it back in `datamodel_builder.py`, or accept and document it |
| 16 | Everything must still land in the graph `graphs/main`, because `main.py:538` queries it by name | Set `"graph"` in `MULTI_INPUT_JSON`. Queries with no graph appear to cover all graphs, as they would need to, but the only source is third-party (test) |
| 17 | Opening `/sparql` in a browser gets an error instead of Virtuoso's query page | Redirect requests with no query to `/sparql-editor` in nginx, and update the port. QLever sets its own CORS headers, so remove nginx's to avoid duplicates |
| 18 | `sparql-editor` and example-query discovery must still work | Should be fine with standard SPARQL, but check that the examples and prefixes load (test) |
| 19 | Federated queries rely on Virtuoso grants today | Remove the grants, since QLever supports `SERVICE`. The example list has no `SERVICE` queries, so the risk is low |
| 20 | Updates must not be publicly open | Keep the access token private, and block token parameters and non-query methods at nginx |

## Suggested next step

Before changing any code, run a short trial: index the existing `v2/out/ttl` files in QLever, then replay the example, data model and `/describe` queries against both stores. That settles most **test** items and gives real numbers for step 2, since whole collections will be far larger than this subset.

## Sources

- [QLever repository](https://github.com/ad-freiburg/qlever)
- [Compliance](https://docs.qlever.dev/compliance/)
- [Update](https://docs.qlever.dev/update/)
- [Qleverfile settings](https://docs.qlever.dev/qleverfile/)
- [Troubleshooting](https://docs.qlever.dev/troubleshooting/)
- [FAQ](https://docs.qlever.dev/faq/)
- [`Describe.cpp`](https://raw.githubusercontent.com/ad-freiburg/qlever/master/src/engine/Describe.cpp)
- [`ExportQueryExecutionTrees.h`](https://raw.githubusercontent.com/ad-freiburg/qlever/master/src/engine/ExportQueryExecutionTrees.h)
- [`ExportQueryExecutionTrees.cpp`](https://raw.githubusercontent.com/ad-freiburg/qlever/master/src/engine/ExportQueryExecutionTrees.cpp)
- [`MediaTypes.h`](https://raw.githubusercontent.com/ad-freiburg/qlever/master/src/util/http/MediaTypes.h)
- [`Server.cpp`](https://raw.githubusercontent.com/ad-freiburg/qlever/master/src/engine/Server.cpp)
- [void-generator](https://github.com/sib-swiss/void-generator)
- [Gno QLever adapter (third-party, default graph behaviour)](https://gno.hexdocs.pm/Gno.Store.Adapters.Qlever.html)
