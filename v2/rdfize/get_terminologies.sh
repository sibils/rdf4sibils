#!/bin/bash

set -e

this_dir=$(dirname $0)
cd $this_dir

echo "Get a local copy of terminologies..."

remote_server="pam@rdfizer"
#remote_server="pam@rdfizer.lan.text-analyzer.ch"
termi_location="/data/terminologies/v.t8/current-release"
grant_location="/data/grants/v2"
target_dir="../out/terminologies/"
mode=$1

echo "termi  dir: $termi_location"
echo "grant  dir: $termi_location"
echo "target dir: $target_dir"
echo "copy mode : $mode"

mkdir -p $target_dir

if [ "$mode" = "remote"  ]; then
  ssh $remote_server "tar czvf terminologies.tar.gz -C $termi_location ."
  scp $remote_server:terminologies.tar.gz $target_dir
  scp $remote_server:$grant_location/fundername_prefLabel_doi_category.txt $target_dir
  cd $target_dir
  tar xvzf terminologies.tar.gz
 elif [ "$mode" = "local" ]; then
  cp $termi_location/* $target_dir
  cp $grant_location/fundername_prefLabel_doi_category.txt $target_dir
else
  echo "Error: usage is $0 local|remote"
  exit 1
fi





