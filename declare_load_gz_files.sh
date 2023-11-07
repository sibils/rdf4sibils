#!/bin/bash

if [ "$1" == "" ] || [ "$2" == "" ] ; then 
  echo "ERROR, usage is $0 max_proc chunk_dir [chunk_dir [...]], i.e.:"
  echo "- $0 pmc23n070*"
  exit 1
fi

max_proc=$1
chunks=${@:2}


echo "$(date) - INFO max_proc: $max_proc"
echo "$(date) - INFO chunks  : $chunks"

./declare_gz_files.sh $chunks
./load_gz_files.sh $max_proc


echo "$(date) - INFO $0 done"

