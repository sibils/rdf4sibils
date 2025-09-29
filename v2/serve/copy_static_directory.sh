#!/bin/bash

set -e

trg_host=sibils-sparql.lan.text-analytics.ch
cur_dir=/home/pam/work/rdf4sibils/v2/serve/static

new_dir=${cur_dir}.new
old_dir=${cur_dir}.old.$(date +%Y%m%d.%H%M)

echo "$(date) Copying static directory to new target directory ${trg_host}:${new_dir}"
ssh ${trg_host} "rm -rf ${new_dir} ; mkdir -p ${new_dir}"
scp -r ${cur_dir}/* ${trg_host}:${new_dir}

echo "$(date) Switching to new static directory on target host ${trg_host}"
ssh ${trg_host} "mv ${cur_dir} ${old_dir}"
ssh ${trg_host} "mv ${new_dir} ${cur_dir}"

echo "$(date) Removing old static directory on target host ${trg_host}:${old_dir}"
ssh ${trg_host} "rm -rf ${old_dir}

echo "$(date) Restarting fastapi on target host ${trg_host}"
ssh ${trg_host} 'bash -l -c "/home/pam/work/rdf4sibils/v2/serve/fastapi_service.sh stop"'
ssh ${trg_host} 'bash -l -c "/home/pam/work/rdf4sibils/v2/serve/fastapi_service.sh start"'

echo "$(date) End"
