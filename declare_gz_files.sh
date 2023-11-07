#!/bin/bash

if [ "$1" == "" ] ; then 
  echo "ERROR, usage is $0 chunk_dir [chunk_dir [...]], i.e.:"
  echo "- $0 pmc23n070*"
  exit 1
fi

export DBA_PW=Gx3DWCyHsj3bVY3MU2nR

for chunk_dir in $@ ; do

  echo "$(date) - declaring gz files of $chunk_dir"

  isql-vt 1111 dba $DBA_PW "EXEC=ld_dir ('${chunk_dir}', '*.gz', 'http://sibils.org/rdf') ;"
  if [ "$?" != "0" ]; then
    msg="$(date) - ERROR chunk $chunk : problem while adding files to load list with isql, exiting";
    exit 3
  fi

done

echo "$(date) - done"

