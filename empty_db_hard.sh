#!/bin/bash

this_script="$(basename $0)"
if ! [ -e "$this_script" ]; then
    echo "ERROR, $0 must be run from its own directory"
    exit 2
fi

./start-stop-virtuoso stop

this_dir=$(pwd)
cd /var/lib/virtuoso-opensource-7
rm -rf db.old
mv db db.old
tar xvzf db-empty.tar.gz 
cd $this_dir

./start-stop-virtuoso start
