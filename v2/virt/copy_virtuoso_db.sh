#!/bin/bash

set -e

trg_host=sibils-sparql.lan.text-analytics.ch
cur_dir=/home/pam/work/tools/virtuoso-opensource/sibils_database

new_dir=${cur_dir}.new
old_dir=${cur_dir}.old.$(date +%Y%m%d.%H%M)

echo "$(date) Stopping virtuoso on local source host $(hostname)"
/home/pam/work/rdf4sibils/v2/virt/sparql_service.sh stop

echo "$(date) Copying local virtuoso db to new target directory ${trg_host}:${new_dir}"
ssh ${trg_host} "rm -rf ${new_dir} ; mkdir -p ${new_dir}"
scp -r ${cur_dir}/* ${trg_host}:${new_dir}

echo "$(date) Stopping virtuoso on target host ${trg_host}"
ssh ${trg_host} "/home/pam/work/rdf4sibils/v2/virt/sparql_service.sh stop"

echo "$(date) Switching to new virtuoso db directory on target host ${tfg_host}"
ssh ${trg_host} "mv ${cur_dir} ${old_dir}"
ssh ${trg_host} "mv ${new_dir} ${cur_dir}"

echo "$(date) Removing old virtuoso db directory on target host ${trg_host}:${old_dir}"
ssh ${trg_host} "rm -rf ${old_dir}

echo "$(date) Restarting virtuoso on target host ${trg_host}"
ssh ${trg_host} "/home/pam/work/rdf4sibils/v2/virt/sparql_service.sh start"

echo "$(date) Retarting virtuoso on local source host $(hostname)"
/home/pam/work/rdf4sibils/v2/virt/sparql_service.sh start

echo "$(date) End"
