#!/bin/bash

set -e

echo "getting all pmids..."

scripts_dir="$(dirname $0)"
base_dir=$scripts_dir/..
out_dir=$base_dir/out/pmids

echo "saving previous output..."

mkdir -p $out_dir
mkdir -p $out_dir.old
rm -rf $out_dir.old
mv $out_dir $out_dir.old
mkdir -p $out_dir

echo "fetching pmids from sources..."

python $scripts_dir/cello-pmid-getter.py $out_dir
python $scripts_dir/rhea-pmid-getter.py $out_dir
python $scripts_dir/swisslipid-pmid-getter.py $out_dir
python $scripts_dir/swissprot-pmid-getter.py $out_dir

echo "concatenating pmids in $out_dir/all-pmids.txt..."

cat $out_dir/*.txt | sort -u > $out_dir/all-pmids.txt

echo "end"

