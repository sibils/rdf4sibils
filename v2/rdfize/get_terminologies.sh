#!/bin/bash

set -e

this_dir=$(dirname $0)
cd $this_dir

echo "Get a local copy of terminologies..."

remote_server="superpam@rdfizer.lan.text-analytics.ch"
files_location="/data/terminologies/v.t8/current-release"
target_dir="../out/terminologies/"
mode=$1

echo "source dir: $files_location"
echo "target dir: $target_dir"
echo "copy mode : $mode"

mkdir -p $target_dir

if [ "$mode" = "remote"  ]; then
  ssh $remote_server "tar czvf terminologies.tar.gz -C $files_location ."
  scp $remote_server:terminologies.tar.gz $target_dir
  cd $target_dir
  tar xvzf terminologies.tar.gz
elif [ "$mode" = "local" ]; then
  cp $files_location/* $target_dir
else
  echo "Error: usage is $0 local|remote"
  exit 1
fi





