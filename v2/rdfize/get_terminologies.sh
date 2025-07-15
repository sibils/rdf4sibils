#!/bin/bash

set -e

echo "Get a l local copy of terminologies..."


remote_server="superpam@rdfizer.lan.text-analytics.ch"
remote_files_location="/data/terminologies/v.t8/current-release"
target_dir="../out/terminologies/"

mkdir -p $target_dir

ssh $remote_server "tar czvf terminologies.tar.gz -C /data/terminologies/v.t8/current-release ."
scp $remote_server:terminologies.tar.gz $target_dir
cd $target_dir
tar xvzf terminologies.tar.gz


# Transfer with compression
# rsync -avz $remote_files $target_dir

# Compress non-GZ files post-transfer
# find $target_dir -type f ! -name '*.gz' -exec gzip {} \;
