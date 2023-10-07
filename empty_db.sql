
-- parameters for SPONGE functionality

grant select on "DB.DBA.SPARQL_SINV_2" to "SPARQL";
grant execute on "DB.DBA.SPARQL_SINV_IMP" to "SPARQL";
GRANT SPARQL_SPONGE TO "SPARQL";
GRANT EXECUTE ON DB.DBA.L_O_LOOK TO "SPARQL";

-- empty sibils graph

log_enable(3,1);
SPARQL CLEAR GRAPH <http://sibils.org/rdf>; -- took ~4 minutes for 25 mega triples
checkpoint;

-- empty load list

delete from DB.DBA.load_list;
select * from DB.DBA.load_list;

-- done

-- find ./ttl/ -name "LOAD*" -exec rm {} \;

