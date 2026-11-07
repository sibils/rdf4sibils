set -e

this_dir="$(dirname $0)"
cd $this_dir
output_dir=sibils.html

rm -rf $output_dir

echo "concat relevant files into sibils.ttl"

cat ontology.ttl > sibils.ttl

echo -e "#\n# Citing sources\n#" >> sibils.ttl
grep -v "@prefix" citing-sources.ttl >> sibils.ttl

echo -e "#\n# Terminologies\n#" >> sibils.ttl
grep -v "@prefix" data_terminologies.ttl >> sibils.ttl


echo "make sure sibils.ttl has 'local' prefixes"

local_pattern="http:\/\/local.sibils.org\/rdf"
test_pattern="https:\/\/test.sibils.org\/rdf"
prod_pattern="https:\/\/purl.expasy.org\/sibils\/rdf"
sed -i "s/$test_pattern/$local_pattern/g" sibils.ttl
sed -i "s/$prod_pattern/$local_pattern/g" sibils.ttl

echo "generate widoco documentation files"

# NOTE: if we omit annotation properties we hide skos:altLabel and skos:prefLabel
java -jar ./widoco.jar -ontFile sibils.ttl -rewriteAll -webVowl -includeAnnotationProperties -uniteSections -noPlaceHolderText -outFolder $output_dir
#java -jar ./widoco.jar -ontFile sibils.ttl -rewriteAll -webVowl  -uniteSections -noPlaceHolderText -outFolder $output_dir


echo "fixing widoco JSON output"

python fix_sibils_webowl_data_ontology_header.py

echo "fixing widoco HTML output"

python ./fix_widoco_output.py $output_dir/doc/index-en.html
mv $output_dir/doc/index-en.html $output_dir/doc/index-en.html.ori
mv $output_dir/doc/index-en.html.fixed $output_dir/doc/index-en.html

echo "get rid of some extra spaces created by widoco"

sed -i 's/N C I T C/NCIT_C/g' $output_dir/doc/index-en.html
sed -i 's/O B I 0/OBI_0/g' $output_dir/doc/index-en.html
sed -i 's/G E N O 0/GENO_0/g' $output_dir/doc/index-en.html
sed -i 's/C A R O 0/CARO_0/g' $output_dir/doc/index-en.html
sed -i 's/C L 0/CL_0/g' $output_dir/doc/index-en.html
sed -i 's/C H E B I/CHEBI/g' $output_dir/doc/index-en.html

if [[ "$1" == "test" ]]; then
  sed -i "s/$local_pattern/$test_pattern/g" $output_dir/doc/index-en.html
fi

if [[ "$1" == "prod" ]]; then
  sed -i "s/$local_pattern/$prod_pattern/g" $output_dir/doc/index-en.html
fi


echo "end"


