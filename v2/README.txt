# -----------------------------
# Building RDF for subils - v2
# -----------------------------


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Step 1 - Collect pmids relevant for SIB resources
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

./pmid_queries/get-all-pmids.sh

=> produces

./out/pmids/all-pmids.txt


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Step 2 - Identify SIBiLS collection (medline, pmc) to get each pmid data
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

./coll_queries/search-collections.sh

=> produces

./out/colls/merged-mapping.txt

Note:
The output fine contains 1 line for each pmid present in ./out/pmids/all-pmids.txt
The 1st column contains a pmid
The 2nd column contains a pmcid if a correspondance was found in medline collection
The 3rd column contains a pmcid if a correspondance was found in pmc collection


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Step 3 - Fetch annotated publications from sibils collections
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

./fetch_json/fetch-pmc.sh 
./fetch_json/fetch-medline.sh 

Caution: the sh scripts are to be run in this order

=> produces a collection of json.gz files in ./out/fetch

Each line of ./out/colls/merged-mapping.txt produces a file 
either in ./out/fetch/pmc subtree or in ./out/fetch/medline subtree


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Step 4 - Build RDF from sibils collections and terminologies
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# get a tar.gz from server and decompresses it to ./out/terminologies
# NOTE: current-version.txt needs to be manually edited cos contains inconsistencies
./rdfize/get_terminologies.sh


# generate RDF data files in ./out/ttl/

python ./rdfize/rdfbuilder.py --platform=prod BUILD_RDF terminology
python ./rdfize/rdfbuilder.py --platform=prod BUILD_RDF medline
python ./rdfize/rdfbuilder.py --platform=prod BUILD_RDF pmc

# FIX: 
# removes triples with is_more_specific_than cos parent field is 
# inconsistent and makes errors during virtuoso loading
./rdfize/fix_concept_mdd_ttl.sh

# clear and reinit virtuoso database

python ./rdfize/rdfbuilder.py --platform=prod LOAD_RDF clear

# load RDF data files into virtuoso 

python ./rdfize/rdfbuilder.py --platform=prod LOAD_RDF terminology
python ./rdfize/rdfbuilder.py --platform=prod LOAD_RDF medline
python ./rdfize/rdfbuilder.py --platform=prod LOAD_RDF pmc

# generate RDF ontology file and load it into virtuoso
python ./rdfize/rdfbuilder.py --platform=prod BUILD_RDF ontology
python ./rdfize/rdfbuilder.py --platform=prod LOAD_RDF ontology

# generate RDF example queries file and load it into virtuoso
python ./rdfize/rdfbuilder.py --platform=prod BUILD_RDF queries
python ./rdfize/rdfbuilder.py --platform=prod LOAD_RDF queries

# python cellapi_builder.py --platform=prod MODEL     # not implemented
# python cellapi_builder.py --platform=prod INFERRED  # not implemented

# generate RDF void metadata file and load it into virtuoso
python ./rdfize/rdfbuilder.py --platform=prod BUILD_RDF void
python ./rdfize/rdfbuilder.py --platform=prod LOAD_RDF void

# generate widoco documentation for ontology




