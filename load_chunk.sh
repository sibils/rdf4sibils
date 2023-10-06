#!/bin/bash

if [ "$1" == "" ]; then 
  echo "ERROR, usage is $0 <chunk_name>"
  exit 1
fi

#echo "DBA_PW: ${DBA_PW}"

if [ "${DBA_PW}" == "" ]; then
  echo "ERROR, please define and export environment variable DBA_PW"
  exit 2
fi

chunk=$1
chunk_dir=/share/rdf/ttl/${chunk}

echo "$(date) - Decompressing files in $chunk_dir"

lz4 -m -d ${chunk_dir}/*.ttl.lz4

echo "$(date) - Adding files to virtuoso load list and loading"

isql-vt 1111 dba $DBA_PW "EXEC=ld_dir ('/share/rdf/ttl/${chunk}', '*.ttl', 'http://sibils.org/rdf') ;"
isql-vt 1111 dba $DBA_PW "EXEC=select * from DB.DBA.load_list;"
isql-vt 1111 dba $DBA_PW "EXEC=rdf_loader_run();"

echo "$(date) - Deleting decompressed files"

rm ${chunk_dir}/*.ttl

echo "$(date) - Done"

