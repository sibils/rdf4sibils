#!/bin/bash

if [ "$1" == "" ] || [ "$2" == "" ] || [ "$3" == "" ]; then 
  echo "ERROR, usage is $0 <max_process> <max_task> <max_cycle>"
  exit 1
fi

max_proc=$1
max_task=$2
max_cycl=$3

for ((i=1; i<=max_cycl; i++)); do
  echo "$(date) - Load Program - Cycle $i"
  python3 multi_fetcher.py $max_proc $max_task load_chunk
done

echo "$(date) - Load Program - Done"

