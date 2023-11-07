#!/bin/bash

if [ "$1" == "" ] ; then 
  echo "ERROR, usage is $0 max_proc [no_checkpoint], i.e.:"
  echo "- $0 4 no_checkpoint"
  exit 1
fi

export DBA_PW=Gx3DWCyHsj3bVY3MU2nR

max_proc=$1

echo "$(date) - INFO loading declared gz files with $max_proc process(es)"

for ((i=1; i<=max_proc; i++)); do
  isql-vt 1111 dba $DBA_PW "EXEC=rdf_loader_run();" &
done

wait

if [ "$2" == "no_checkout" ]; then
  echo "$(date) - INFO Skipping checkpoint after load of chunk $chunk"
else
  echo "$(date) - INFO Starting checkpoint after load of chunk $chunk"
  isql-vt 1111 dba $DBA_PW "EXEC=checkpoint;"
  if [ "$?" != "0" ]; then 
    msg="$(date) - ERROR chunk $chunk : problem while running checkpoint load"; 
    touch ${chunk_dir}/LOAD_ERROR
    exit 8
  fi
fi

echo "$(date) - INFO done"

