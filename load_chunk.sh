#!/bin/bash


if [ "$1" == "" ] || [ "$2" == "" ] ; then 
  echo "ERROR, usage is $0 <chunk_name> <max_load_process>, ie. $0 pmc23n0978 4"
  exit 1
fi

export DBA_PW=Gx3DWCyHsj3bVY3MU2nR

chunk=$1
max_proc=$2

chunk_dir=/share/rdf/ttl/${chunk}


#
# make sure we have not already handled this chunk
#

if [ -e ${chunk_dir}/LOADED ] || [ -e ${chunk_dir}/LOADING ] || [ -e ${chunk_dir}/LOAD_ERROR ] ; then
  echo "$(date) - INFO chunk $chunk : load already handled elsewhere"
  exit 0
fi

touch ${chunk_dir}/LOADING

#
# get a list of ttl.lz4 files related to this chunk and make sure we have at least one
#

lz4_files=$(ls -1 ${chunk_dir}/ | grep "ttl.lz4")
if [ "$lz4_files" == "" ]; then
  echo "$(date) - ERROR chunk $chunk : no lz4 files found in $chunk_dir, exiting"
  touch ${chunk_dir}/LOAD_ERROR
  exit 1
fi
let "lz4_cnt=0"
for f in $lz4_files; do let "lz4_cnt+=1"; done
echo "$(date) - INFO Found $lz4_cnt lz4 files for chunk $chunk"


#
# decompress ttl.lz4 files
#

echo "$(date) - INFO Decompressing lz4 files in $chunk_dir"

rm -f ${chunk_dir}/*.ttl
lz4 -m -d ${chunk_dir}/*.ttl.lz4
if [ "$?" != "0" ]; then 
  msg="$(date) - ERROR chunk $chunk : problem while decompressing files in $chunk_dir, exiting"; 
  touch ${chunk_dir}/LOAD_ERROR
  exit 2
fi


#
# declare the decompresses ttl files to virtuoso
#

echo "$(date) - INFO Adding ttl files of $chunk to virtuoso load list"

isql-vt 1111 dba $DBA_PW "EXEC=ld_dir ('/share/rdf/ttl/${chunk}', '*.ttl', 'http://sibils.org/rdf') ;"
if [ "$?" != "0" ]; then
  msg="$(date) - ERROR chunk $chunk : problem while adding files to load list with isql, exiting";
  touch ${chunk_dir}/LOAD_ERROR
  exit 3
fi

#
# check that all ttl files of this chunk are in the virtuoso load list as to be loaded (ll_state=0)
#

ttl_files=$(isql-vt 1111 dba $DBA_PW "EXEC=select ll_file from DB.DBA.load_list where ll_file like '*$chunk*' and ll_state=0;" | grep ".ttl")
if [ "$?" != "0" ]; then
  msg="$(date) - ERROR chunk $chunk : problem while reading list of files to load with isql, exiting";
  touch ${chunk_dir}/LOAD_ERROR
  exit 4
fi
let "ttl_cnt=0"
for ttl in $ttl_files; do let "ttl_cnt+=1"; done
if ! [ "$lz4_cnt" == "$ttl_cnt" ]; then
  echo "$(date) - ERROR chunk $chunk : discrepency between lz4 files and ttl files declared to virtuoso, exiting"
  touch ${chunk_dir}/LOAD_ERROR
  exit 5
fi


echo "$(date) - INFO Loading $ttl_cnt ttl files of chunk $chunk using $max_proc process(es)"

for ((i=1; i<=max_proc; i++)); do
  isql-vt 1111 dba $DBA_PW "EXEC=rdf_loader_run();" &
done
wait


echo "$(date) - INFO Checking load status for chunk $chunk"

files=$(isql-vt 1111 dba $DBA_PW "EXEC=select ll_file, ll_error from DB.DBA.load_list where ll_file like '*$chunk*' and ll_state=2;" | grep ".ttl")
let "fil_cnt=0"
for fil in $files; do let "fil_cnt+=1"; done
if ! [ "$fil_cnt" == "$ttl_cnt" ]; then
  echo "$(date) - ERROR chunk $chunk : discrepency between ttl files declared to virtuoso and actually loaded file, exiting"
  touch ${chunk_dir}/LOAD_ERROR
  exit 6
fi

load_errors=no
for row in $files; do
  if [[ $row != *NULL* ]]; then
    load_errors=yes
    echo "$(date) - ERROR chunk $chunk : $row"
  fi
done
if [ "$load_errors" == "yes" ]; then
  echo "$(date) - ERROR chunk $chunk : virtoso reported load error(s)"
  exit 7
fi

echo "$(date) - INFO Starting checkpoint after load of chunk $chunk"

isql-vt 1111 dba $DBA_PW "EXEC=checkpoint;"
if [ "$?" != "0" ]; then 
  msg="$(date) - ERROR chunk $chunk : problem while running checkpoint load"; 
  exit 8
fi


echo "$(date) - INFO Deleting decompressed files of chunk $chunk"

rm ${chunk_dir}/*.ttl


echo "$(date) - Load of chunk $chunk completed"


