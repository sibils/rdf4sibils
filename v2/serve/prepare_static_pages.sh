#!/bin/bash

set -e

base_dir="$(dirname $0)"
cd $base_dir 
base_dir=$(pwd)

# echo "base_dir: $base_dir"

echo "copying widoco output to static"

rm -rf $base_dir/static/sparql
mkdir $base_dir/static/sparql
cp -r $base_dir/../../../sibils-widoco/sibils.html/doc $base_dir/static/sparql/

echo "clean useless files"
cd $base_dir/static/sparql
rm doc/index-en.html.ori doc/webvowl/data/ontology.json.ori

echo "copying rdf_data to static"
cd $base_dir
rm -rf $base_dir/static/downloads
mkdir -p $base_dir/static/downloads

tar cvf data_pmc_ttl_gz.tar ../out/ttl/data_pmc*.ttl.gz
mv data_pmc_ttl_gz.tar static/downloads/

tar cvf data_medline_ttl_gz.tar ../out/ttl/data_medline*.ttl.gz
mv data_medline_ttl_gz.tar static/downloads/

tar cvf terminologies_ttl.tar ../out/ttl/termino*.ttl ../out/ttl/concept_*.ttl
mv terminologies_ttl.tar static/downloads/

cp ../out/ttl/ontology.ttl ../out/ttl/void-sibils.ttl ../out/ttl/queries.ttl static/downloads/

echo "done"


