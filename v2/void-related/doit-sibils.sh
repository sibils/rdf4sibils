#!/bin/bash

set -e

script_dir="$(dirname $0)"
cd $script_dir

java -jar target/void-generator-0.1-SNAPSHOT.jar --user=dba --password=dba  \
    -r jdbc:virtuoso://localhost:1112/charset=UTF-8  \
    -s void-sibils.ttl \
    -i "http://localhost:8891/sparql/.well-known/void"
#    -i "https://sparql.cellosaurus.org/.well-known/void"
