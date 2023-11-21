#!/bin/bash

query_files=$(ls -1 sparql/*.rq)

for qf in $query_files; do
  echo "$(date) - running $qf"
  python sparql_client.py query $qf
done

echo "$(date) - INFO $0 done"
