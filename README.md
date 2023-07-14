# rdf4sibils

## Setup SPARQL endpoint

1. download image
```
docker pull openlink/virtuoso-opensource-7
```
2. check version
```
docker run openlink/virtuoso-opensource-7 version
```
3. create initial database
```
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
```
^C (stop container)

4. modifiy virtuoso.ini
```
DirsAllowed = ., ../database/input, ../vad, /usr/share/proj
```
5. restart container
```
docker start sibils_virtdb
```
6. open isql in interactive mode
```
docker exec -i sibils_virtdb isql 1111
```
7. send commands to isql
- tune some parameters
```
grant select on "DB.DBA.SPARQL_SINV_2" to "SPARQL";
grant execute on "DB.DBA.SPARQL_SINV_IMP" to "SPARQL";
GRANT SPARQL_SPONGE TO "SPARQL";
GRANT EXECUTE ON DB.DBA.L_O_LOOK TO "SPARQL";
```
- delete data
```
# display list of graphs (incl. system graphs)
SPARQL SELECT  DISTINCT ?g FROM  <http://localhost:8890/> { GRAPH  ?g     { ?s  a  ?t } } ;

log_enable(3,1);
SPARQL CLEAR GRAPH <http://sibils.org/rdf>; -- took ~4 minutes for 25 mega triples
or
log_enable(3,1);
SPARQL DROP SILENT GRAPH <http://sibils.org/rdf>;
or
log_enable(3,1);
DELETE FROM rdf_quad WHERE g = iri_to_id ('http://mygraph.org');
or
log_enable(3,1);

```
- reload data
```
delete from DB.DBA.load_list;
ld_dir ('../database/input', '*.ttl', 'http://sibils.org/rdf') ;
select * from DB.DBA.load_list;
rdf_loader_run();
```

## SPARQL query examples

useful prefixes
```
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX cnt: <http://www.w3.org/2011/content#> 
PREFIX dcterms: <http://purl.org/dc/terms/> 
PREFIX deo: <http://purl.org/spar/deo/> 
PREFIX doco: <http://purl.org/spar/doco/> 
PREFIX fabio: <http://purl.org/spar/fabio/> 
PREFIX foaf: <http://xmlns.com/foaf/0.1/> 
PREFIX frbr: <http://purl.org/vocab/frbr/core#> 
PREFIX oa: <http://www.w3.org/ns/oa#> 
PREFIX openbiodiv: <http://openbiodiv.net/> 
PREFIX po: <http://www.essepuntato.it/2008/12/pattern#> 
PREFIX prism: <http://prismstandard.org/namespaces/basic/2.0/> 
PREFIX skos: <http://www.w3.org/2004/02/skos/core#> 
PREFIX sibilo: <http://sibils.org/rdf#> 
PREFIX sibilc: <http://sibils.org/rdf/concept/> 
PREFIX sibilt: <http://sibils.org/rdf/terminology/> 
PREFIX sibils: <http://sibils.org/rdf/data/> 
```

publi count by class
```
select  ?publi_class (count(*) as ?count) where {
  ?s fabio:hasPubMedCentralId ?o.
  ?s a ?publi_class.
} group by ?publi_class
```


entities extracted with their position in a publication
```
select (str(?doi) as ?doi) (str(?cpt_id) as ?cpt_id) (str(?scheme) as ?scheme) (str(?start) as ?start) (str(?token) as ?token) (str(?part) as ?section) where {
    values ?publi { sibils:PMC2196267 }
    # ori values ?publi { sibils:PMC2718325 } 
    ?publi prism:doi ?doi.
    ?publi sibilo:has_annotation ?a .
    ?a oa:hasBody ?cpt .
    ?cpt skos:notation ?cpt_id .
    ?cpt skos:inScheme / rdfs:label ?scheme .
    ?a oa:hasTarget ?trg.
    ?trg oa:hasSource ?part.
    ?trg oa:hasSelector ?sel .
    ?sel oa:start ?start.
    ?sel oa:exact ?token.
} 
order by ?part ?start ?token
LIMIT 1000
```


sponge from nextprot
```
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
```