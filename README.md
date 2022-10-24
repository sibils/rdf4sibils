# rdf4sibils

## Setup SPARQL endpoint

1. download image
'''
docker pull openlink/virtuoso-opensource-7
'''
2. check version
'''
docker run openlink/virtuoso-opensource-7 version
'''
3. create initial database
'''
mkdir sibils_virtdb
cd sibils_virtdb
docker run \
    --name sibils_virtdb \
    --interactive \
    --tty \
    --env DBA_PASSWORD=somepassword \
    --publish 1111:1111 \
    --publish  8899:8890 \
    --user $(id -u):$(id -g) \
    --volume `pwd`:/database \
    openlink/virtuoso-opensource-7:latest
'''
^C (stop container)

4. modifiy virtuoso.ini
'''
DirsAllowed = ., ../database/input, ../vad, /usr/share/proj
'''
5. restart container
'''
docker start sibils_virtdb
'''
6. open isql in interactive mode
'''
docker exec -i sibils_virtdb isql 1111
'''
7. send commands to isql
   - tune some parameters
'''
grant select on "DB.DBA.SPARQL_SINV_2" to "SPARQL";
grant execute on "DB.DBA.SPARQL_SINV_IMP" to "SPARQL";
GRANT SPARQL_SPONGE TO "SPARQL";
GRANT EXECUTE ON DB.DBA.L_O_LOOK TO "SPARQL";
'''
   - delete / reload data
'''
delete from DB.DBA.load_list;
ld_dir ('../database/input', '*.ttl', 'http://sibils.org/rdf') ;
select * from DB.DBA.load_list;
rdf_loader_run();
'''

## SPARQL query examples

sponge from nextprot
'''
PREFIX fabio: <http://purl.org/spar/fabio/>
PREFIX np: <http://nextprot.org/rdf#>
select * where {
  SERVICE <https://api.nextprot.org/sparql> {
select  
  ?e where {
  ?e a np:Entry .
}
limit 10		   
}}
'''