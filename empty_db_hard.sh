#!/bin/bash

# as ROOT:

service virtuoso-opensource-7 stop
cd /var/lib/virtuoso-opensource-7
rm -rf db.old
mv db db.old
tar xvzf db-empty.tar.gz 
service virtuoso-opensource-7 start

