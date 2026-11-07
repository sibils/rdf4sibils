#!/bin/bash
# Load the benchmark data into a private Virtuoso instance, in the same order as do-rdfize.sh.
# usage: load_virtuoso.sh LABEL LOADERS   (v2 uses 1 loader)
set -e
label=$1; loaders=${2:-1}
B=${BENCH:-/home/pmichel/work/tools/qlever/bench}; V=/home/pmichel/work/tools/virtuoso-opensource
here=$(cd $(dirname $0); pwd); isql="$V/bin/isql 1122 dba dba"; graph=https://www.sibils.org/rdf/graphs/main
$isql "exec=shutdown;" >/dev/null 2>&1 || true; sleep 3
rm -rf $B/virtuoso/sibils_database; mkdir -p $B/virtuoso/sibils_database
cd $B/virtuoso/bin; $V/bin/virtuoso-t +wait +configfile $B/virtuoso/virtuoso.ini
$isql $here/../v2/virt/virtuoso_setup.sql > /dev/null
susp0=$(python3 -c "import time;print(time.clock_gettime(time.CLOCK_BOOTTIME)-time.clock_gettime(time.CLOCK_MONOTONIC))")
t0=$(date +%s)
for prefix in citing-sources termino concept data_medline data_pmc onto queries void; do
  [ "$prefix" == onto ] && $isql "exec=checkpoint;" > /dev/null
  echo "$(date) $prefix"
  $isql "exec=delete from DB.DBA.load_list;" > /dev/null
  $isql "exec=ld_dir ('../sibils_input', '${prefix}*.ttl*', '$graph');" > /dev/null
  for ((i=1;i<=loaders;i++)); do $isql "exec=rdf_loader_run();" > /dev/null & done; wait
  n=$($isql exec="select 'errcnt:', count(*) from db.dba.load_list where ll_error is not null" | grep errcnt | grep -v select | awk '{print $2}')
  [ "$n" == "0" ] || { echo "load errors in $prefix: $n"; exit 7; }
done
$isql "exec=checkpoint;" > /dev/null
t1=$(date +%s)
peak=$(awk '/VmHWM/{printf "%.1f", $2/1048576}' /proc/$(pgrep -f $B/virtuoso/virtuoso.ini | head -1)/status)
c=$($isql "exec=sparql select count(*) where { graph <$graph> { ?s ?p ?o } };" | grep -E '^[0-9]+$' | head -1)
size=$(du -sb $B/virtuoso/sibils_database/virtuoso.db | cut -f1)
susp1=$(python3 -c "import time;print(time.clock_gettime(time.CLOCK_BOOTTIME)-time.clock_gettime(time.CLOCK_MONOTONIC))")
echo "{\"name\":\"$label\",\"loaders\":$loaders,\"seconds\":$((t1-t0)),\"triples\":\"$c\",\"size_gb\":$(python3 -c "print(round($size/1e9,2))"),\"peak_rss_gb\":\"$peak\",\"suspended_s\":$(python3 -c "print(round($susp1-$susp0))")}" | tee -a $here/results/virtuoso_runs.jsonl
$isql "exec=shutdown;" > /dev/null || true
