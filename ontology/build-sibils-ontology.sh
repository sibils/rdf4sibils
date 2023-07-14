grep -v "@prefix" terminology-individuals.ttl > ti-no-prefix.ttl
cat sibils-schema.ttl ti-no-prefix.ttl > sibils-ontology.ttl
rm ti-no-prefix.ttl
echo done
