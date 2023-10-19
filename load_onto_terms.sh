#!/bin/bash

# load the ontology and the terminologies

export DBA_PW=Gx3DWCyHsj3bVY3MU2nR

echo "$(date) - Adding files to virtuoso load list"

isql-vt 1111 dba $DBA_PW "EXEC=ld_dir ('/share/rdf/ttl/terminologies', '*.ttl', 'http://sibils.org/rdf/concepts') ;"
isql-vt 1111 dba $DBA_PW "EXEC=ld_dir ('/share/rdf/ttl/ontology', '*.ttl', 'http://sibils.org/rdf/ontology') ;"

isql-vt 1111 dba $DBA_PW "EXEC=select * from DB.DBA.load_list;"

echo "$(date) - Loading files to virtuoso db with 4 processes"
isql-vt 1111 dba $DBA_PW "EXEC=rdf_loader_run();" &
isql-vt 1111 dba $DBA_PW "EXEC=rdf_loader_run();" &
isql-vt 1111 dba $DBA_PW "EXEC=rdf_loader_run();" &
isql-vt 1111 dba $DBA_PW "EXEC=rdf_loader_run();" &
wait

echo "$(date) - Making a checkpoint"
isql-vt 1111 dba $DBA_PW "EXEC=checkpoint;"
echo "$(date) - Done"

