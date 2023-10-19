#!/bin/bash

if [ "$1" == "" ]; then 
  echo "ERROR, usage is $0 <chunk_name>"
  exit 1
fi

export DBA_PW=Gx3DWCyHsj3bVY3MU2nR

if [ "${DBA_PW}" == "" ]; then
  echo "ERROR, please define and export environment variable DBA_PW"
  exit 2
fi

chunk=$1
chunk_dir=/share/rdf/ttl/${chunk}

echo "$(date) - Decompressing files in $chunk_dir"

msg=""
lz4 -m -d ${chunk_dir}/*.ttl.lz4
if [ "$?" != "0" ]; then 
  msg="ERROR while decompressing files in $chunk_dir"; 
  exit 4
fi
  
echo "$(date) - Adding files to virtuoso load list and loading"

isql-vt 1111 dba $DBA_PW "EXEC=ld_dir ('/share/rdf/ttl/${chunk}', '*.ttl', 'http://sibils.org/rdf') ;"
if [ "$?" != "0" ]; then 
  msg="ERROR while adding files to load list with isql for chunk $chunk";
  exit 5
fi

isql-vt 1111 dba $DBA_PW "EXEC=select * from DB.DBA.load_list where ll_file like '*pmc*' ;"
if [ "$?" != "0" ]; then 
  msg="ERROR while reading list of files to load with isql for chunk $chunk";
  exit 6
fi

isql-vt 1111 dba $DBA_PW "EXEC=rdf_loader_run();"
if [ "$?" != "0" ]; then 
  msg="ERROR while running load with isql for chunk $chunk"; 
  exit 7
fi

echo "$(date) - Deleting decompressed files"

rm ${chunk_dir}/*.ttl

echo "$(date) - Done"

