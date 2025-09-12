#!/bin/bash

set -e

this_dir=$(dirname $0)
cd $this_dir

echo "Get a local copy of terminologies..."


remote_server="superpam@rdfizer.lan.text-analytics.ch"
remote_files_location="/data/terminologies/v.t8/current-release"
target_dir="../out/terminologies/"

echo "target dir: $target_dir"

mkdir -p $target_dir
ssh $remote_server "tar czvf terminologies.tar.gz -C /data/terminologies/v.t8/current-release ."
scp $remote_server:terminologies.tar.gz $target_dir
cd $target_dir
tar xvzf terminologies.tar.gz

