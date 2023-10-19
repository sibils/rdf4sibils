#!/bin/bash

find ./ttl/ -name chunk*.ttl -exec rm {} \;
find ./ttl/ -name LOAD* -exec rm {} \;
