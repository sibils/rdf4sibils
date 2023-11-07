#!/bin/bash

if [ "$1" == "" ] ; then 
  echo "ERROR, usage is $0 chunk_dir [chunk_dir [...]], i.e.:"
  echo "- $0 pmc23n070*"
  exit 1
fi

for chunk_dir in $@ ; do
  echo "$(date) - decompressing lz4 files in $chunk_dir"
  lz4 -m -d ${chunk_dir}/*.ttl.lz4
  echo "$(date) - gzipping ttl files in $chunk_dir"
  gzip --fast ${chunk_dir}/*.ttl
  echo "$(date) - removing lz4 files in $chunk_dir"
  rm ${chunk_dir}/*.lz4
done

echo "$(date) - done"

