#!/bin/bash

if [ "$1" == "" ] ; then 
  echo "ERROR, usage is $0 <max_process>"
  exit 1
fi

export DBA_PW=Gx3DWCyHsj3bVY3MU2nR

if [ "${DBA_PW}" == "" ]; then
  echo "ERROR, please define and export environment variable DBA_PW"
  exit 2
fi

max_proc=$1

echo "$(date) - Load remaining files - Starting"

echo "$(date) - Files to be loaded:"

isql-vt 1111 dba $DBA_PW "EXEC=select ll_file, ll_state, ll_error from DB.DBA.load_list where ll_state=0;"

todos=$(isql-vt 1111 dba $DBA_PW "EXEC=select ll_file, ll_state, ll_error from DB.DBA.load_list where ll_state=0;" | grep ttl | wc -l)

echo "$(date) - Found $todos files to be loaded"

for ((i=1; i<=max_proc; i++)); do
  echo "$(date) - Starting load process $i"
  isql-vt 1111 dba $DBA_PW "EXEC=rdf_loader_run();" &
  sleep 1
done

echo "$(date) - Waiting for load processes to return..."
wait

todos=$(isql-vt 1111 dba $DBA_PW "EXEC=select ll_file, ll_state, ll_error from DB.DBA.load_list where ll_state=0;" | grep ttl | wc -l)
echo "$(date) - Found $todos remaining files to be loaded"

errors=$(isql-vt 1111 dba $DBA_PW "EXEC=select ll_file, ll_state, ll_error from DB.DBA.load_list where ll_error is not null;" | grep ttl | wc -l)
if [ "${errors}" == "0" ]; then
    echo "$(date) - Load remaining files - Done"
else
    echo "$(date) - ERROR(s):"
    isql-vt 1111 dba $DBA_PW "EXEC=select ll_file, ll_state, ll_error from DB.DBA.load_list where ll_error is not null;"
    echo "$(date) - Load remaining files - Done with ERROR(s)"
    exit 1
fi


