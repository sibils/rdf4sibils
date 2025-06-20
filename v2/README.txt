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





