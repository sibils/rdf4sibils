#!/bin/bash

set -e

ttldir=../out/ttl
grep -v "more_specific_than" $ttldir/concept_mdd.ttl > $ttldir/concept_mdd.ttl.ok
mv $ttldir/concept_mdd.ttl.ok $ttldir/concept_mdd.ttl

