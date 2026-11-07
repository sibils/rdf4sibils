#!/bin/bash
# The QLever load runs, one after the other. Nothing else heavy should run meanwhile.
cd $(dirname $0)
docker rm -f qlever.server.bench >/dev/null 2>&1
./run_index.py L0-base --streams 1
for s in 2 4 8 16; do ./run_index.py L1-s$s --streams $s; done
./run_index.py L2-m8 --streams 16 --stxxl 8G
./run_index.py L2-m20 --streams 16 --stxxl 20G
./run_index.py L2-par4 --streams 4 --stxxl 8G --parallel true
./run_index.py L2-b125k --streams 16 --stxxl 8G --extra "--index-rows-per-block 125000"
./run_index.py L2-b500k --streams 16 --stxxl 8G --extra "--index-rows-per-block 500000"
./run_index.py L2-batch30 --streams 16 --stxxl 8G --settings '{"num-triples-per-batch": 30000000}'
./run_index.py L2-m6 --streams 16 --stxxl 6G
./run_index.py L2-m6-b5 --streams 16 --stxxl 6G --settings '{"num-triples-per-batch": 5000000}'
