#!/bin/bash

set -e

if [[ "$1" != "local" && "$1" != "test" && "$1" != "prod" ]]; then
  echo "Error, invalid platorm name, expected local, test or prod"
  exit 3
fi

platform=$1
echo "platform: $platform"

this_dir=$(dirname $0)
cd $this_dir

virt_dir="../virt"

echo "$(date) - Clearing and reinit'ing virtuoso database"
python rdfbuilder.py --platform=$platform LOAD_RDF clear

echo "$(date) - Loading RDF data files into virtuoso"
python rdfbuilder.py --platform=$platform LOAD_RDF sources
python rdfbuilder.py --platform=$platform LOAD_RDF terminology
python rdfbuilder.py --platform=$platform LOAD_RDF medline
python rdfbuilder.py --platform=$platform LOAD_RDF pmc
python rdfbuilder.py --platform=$platform LOAD_RDF ontology
python rdfbuilder.py --platform=$platform LOAD_RDF queries
python rdfbuilder.py --platform=$platform LOAD_RDF void


echo "$(date) - Performing a vistuoso checkpoint and restarting virtuoso"
$virt_dir/sparql_service.sh stop
sleep 10
$virt_dir/sparql_service.sh start
sleep 10

echo "$(date) - end"


