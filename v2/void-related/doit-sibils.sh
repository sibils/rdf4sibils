#!/bin/bash

set -e

script_dir="$(dirname $0)"
cd $script_dir

java -jar void-generator.jar \
    --user=dba \
    --password=dba \
    --virtuoso-jdbc=jdbc:virtuoso://localhost:1112/charset=UTF-8 \
    -r "http://localhost/sparql/sparql"  \
    -s void-sibils.ttl \
    -i "http://localhost/sparql/.well-known/void"
