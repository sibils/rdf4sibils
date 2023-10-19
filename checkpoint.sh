#!/bin/bash

# load the ontology and the terminologies

export DBA_PW=Gx3DWCyHsj3bVY3MU2nR

echo "$(date) - Listing loaf file status"
isql-vt 1111 dba $DBA_PW "EXEC=select * from DB.DBA.load_list;"
echo "$(date) - Counting loaded files"
isql-vt 1111 dba $DBA_PW "EXEC=select count(*) as LOADED_COUNT from DB.DBA.load_list where ll_state=2;"
echo "$(date) - Counting load errors"
isql-vt 1111 dba $DBA_PW "EXEC=select count(*) as ERROR_COUNT from DB.DBA.load_list where ll_error is not null;"
echo "$(date) - Making a checkpoint"
isql-vt 1111 dba $DBA_PW "EXEC=checkpoint;"
echo "$(date) - Done"

