#!/bin/bash

set -e

echo "searching pmids incollections..."

scripts_dir="$(dirname $0)"
base_dir=$scripts_dir/..
input_file=$base_dir/out/pmids/all-pmids.txt
out_dir=$base_dir/out/colls

echo "saving previous output..."

mkdir -p $out_dir
mkdir -p $out_dir.old
rm -rf $out_dir.old
mv $out_dir $out_dir.old
mkdir -p $out_dir

echo "checking presence of pmids in collections..."

python $scripts_dir/search-collections.py $input_file $out_dir

echo "end"

