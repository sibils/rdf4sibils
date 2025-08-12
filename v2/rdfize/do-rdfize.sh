#!/bin/bash

set -e

if [[ "$1" != "local" && "$1" != "test" && "$1" != "prod" ]]; then
  echo "Error, invalid platorm name, expected local, test or prod"
  exit 3
fi

platform=$1
rdfize_dir=$(dirname $0)
widoco_dir="$rdfize_dir/../../../sibils-widoco/"
virt_dir="$rdfize_dir/../virt"

options=$2
echo "options: $options"


if [[ "$options" =~ "nodata" ]]; then
    echo "$(date) - Skipping generating RDF data files in .../out/ttl/"
else
    echo "$(date) - Generating RDF data files in .../out/ttl/"
    python $rdfize_dir/rdfbuilder.py --platform=$platform BUILD_RDF terminology
    python $rdfize_dir/rdfbuilder.py --platform=$platform BUILD_RDF medline
    python $rdfize_dir/rdfbuilder.py --platform=$platform BUILD_RDF pmc
fi

# FIX: 
# removes triples with is_more_specific_than cos parent field is 
# inconsistent and makes errors during virtuoso loading
echo "$(date) - Fixing $rdfize_dir/fix_concept_mdd_ttl.sh"
$rdfize_dir/fix_concept_mdd_ttl.sh

echo "$(date) - Clearing and reinit'ing virtuoso database"
python $rdfize_dir/rdfbuilder.py --platform=$platform LOAD_RDF clear

echo "$(date) - Loading RDF data files into virtuoso"
python $rdfize_dir/rdfbuilder.py --platform=$platform LOAD_RDF terminology
python $rdfize_dir/rdfbuilder.py --platform=$platform LOAD_RDF medline
python $rdfize_dir/rdfbuilder.py --platform=$platform LOAD_RDF pmc

# Note: useful for further SPARQL queries to run fast
echo "$(date) - Performing a vistuoso checkpoint and restarting virtuoso"
$virt_dir/sparql_service.sh stop
sleep 3
$virt_dir/sparql_service.sh start
sleep 10

echo "$(date) - Generating RDF ontology file and loading it into virtuoso"
python $rdfize_dir/rdfbuilder.py --platform=$platform BUILD_RDF ontology
python $rdfize_dir/rdfbuilder.py --platform=$platform LOAD_RDF ontology

echo "$(date) - Generating RDF example queries file and loading it into virtuoso"
python $rdfize_dir/rdfbuilder.py --platform=$platform BUILD_RDF queries
python $rdfize_dir/rdfbuilder.py --platform=$platform LOAD_RDF queries

# python cellapi_builder.py --platform=$platform MODEL     # not implemented
# python cellapi_builder.py --platform=$platform INFERRED  # not implemented

if [[ "$options" =~ "novoid" ]]; then
    echo "$(date) - Skipped generating RDF void metadata file and loading it into virtuoso"
else
    echo "$(date) - Generating RDF void metadata file and loading it into virtuoso"
    python $rdfize_dir/rdfbuilder.py --platform=$platform BUILD_RDF void
fi

python $rdfize_dir/rdfbuilder.py --platform=$platform LOAD_RDF void

echo "$(date) - Generating widoco documentation for ontology"
$widoco_dir/doit-sibils.sh $platform

echo "$(date) - end"
