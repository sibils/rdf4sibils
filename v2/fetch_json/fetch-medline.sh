#!/bin/bash

set -e

echo "fetching annotated publications from medline collection..."

scripts_dir="$(dirname $0)"
base_dir=$scripts_dir/..
input_file=$base_dir/out/colls/merged-mapping.txt
out_dir=$base_dir/out/fetch/medline

mkdir -p $out_dir

python $scripts_dir/fetch-medline.py $input_file $out_dir

echo "end"
