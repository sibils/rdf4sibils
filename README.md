# rdf4sibils

## how to setup SPARQL endpoint

### download image
docker pull openlink/virtuoso-opensource-7

### check version
docker run openlink/virtuoso-opensource-7 version

### create initial database
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

^C (stop container)

### modifiy virtuoso.ini
DirsAllowed = ., ../database/input, ../vad, /usr/share/proj

### restart container
docker start sibils_virtdb

### open isql in interactive mode
docker exec -i sibils_virtdb isql 1111

### send commands to isql

#### tune some parameters
grant select on "DB.DBA.SPARQL_SINV_2" to "SPARQL";
grant execute on "DB.DBA.SPARQL_SINV_IMP" to "SPARQL";
GRANT SPARQL_SPONGE TO "SPARQL";
GRANT EXECUTE ON DB.DBA.L_O_LOOK TO "SPARQL";

#### delete / reload data
delete from DB.DBA.load_list;
ld_dir ('../database/input', '*.ttl', 'http://sibils.org/rdf') ;
select * from DB.DBA.load_list;
rdf_loader_run();


