#!/bin/bash

# load the ontology and the terminologies

export DBA_PW=Gx3DWCyHsj3bVY3MU2nR

echo "$(date) - Making a checkpoint"
isql-vt 1111 dba $DBA_PW "EXEC=checkpoint;"
echo "$(date) - Done"

