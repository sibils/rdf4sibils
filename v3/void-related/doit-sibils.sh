#!/bin/bash

set -e

script_dir="$(dirname $0)"
cd $script_dir

# SIBILS_SPARQL_ENGINE selects the store the VoID generator queries: qlever (default) or virtuoso
# QLEVER_URL is optional, it defaults to the QLever port used in nginx-rdf4sibils-qlever.conf
case "${SIBILS_SPARQL_ENGINE:-qlever}" in
  virtuoso)
    engine_opts=(--user=dba
                 --password=dba
                 --virtuoso-jdbc=jdbc:virtuoso://localhost:1112/charset=UTF-8
                 -r "http://localhost/sparql/sparql")
    ;;
  qlever)
    # the generator's group by queries need --optimize-for=Qlever,
    # a lower concurrency keeps them from competing for memory
    engine_opts=(-r "${QLEVER_URL:-http://localhost:7019}"
                 --optimize-for=Qlever
                 --max-concurrency=2)
    ;;
  *)
    echo "ERROR: unknown SIBILS_SPARQL_ENGINE '$SIBILS_SPARQL_ENGINE' (expected: virtuoso or qlever)" >&2
    exit 1
    ;;
esac

java -jar void-generator.jar \
    "${engine_opts[@]}" \
    -s void-sibils.ttl \
    -i "http://localhost/sparql/.well-known/void"
