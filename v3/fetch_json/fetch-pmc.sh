#!/bin/bash

set -e

echo "fetching annotated publications from pmc collection..."

scripts_dir="$(dirname $0)"
base_dir=$scripts_dir/..
input_file=$base_dir/out/colls/merged-mapping.txt
out_dir=$base_dir/out/fetch/pmc

mkdir -p $out_dir

python $scripts_dir/fetch-pmc.py $input_file $out_dir

echo "end"
