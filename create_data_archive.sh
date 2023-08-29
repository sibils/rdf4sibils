rm output/*.ttl output/v3.3/*
python get_termino_rdf_new.py onto
cd ontology
./build-sibils-ontology.sh
cd ..
python get_termino_rdf_new.py data
python get_publi_rdf_new.py parse
cd output
mv v3.3/* .
cp ../ontology/sibils-ontology.ttl .
tar cvzf sibils-rdf.tar.gz *.ttl

scp -P10587 sibils-rdf.tar.gz pam@goldorak.hesge.ch:sibils_virtdb/input/
echo "End"

