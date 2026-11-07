import os
import sys
import datetime
from optparse import OptionParser
import json
from SPARQLWrapper import SPARQLWrapper, JSON


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def log_it(*things, duration_since=None):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    t1 = datetime.datetime.now()
    now = t1.isoformat().replace('T',' ')[:23]
    pid = "[" + str(os.getpid()) + "]"
    if duration_since is not None:
        duration = round((t1 - duration_since).total_seconds(),3)
        print(now, pid, *things, "duration", duration, flush=True)
    else:
        print(now, pid, *things, flush=True)



#-------------------------------------------------
class EndpointClient:
#-------------------------------------------------

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def __init__(self, server_url):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        self.server_url = server_url
        self.endpoint = SPARQLWrapper(server_url)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def run_query(self, query):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        t0 = datetime.datetime.now()
        try:
            self.endpoint.setQuery(query)
            self.endpoint.setMethod("POST")
            self.endpoint.setReturnFormat(JSON)
            response = self.endpoint.query().convert()
            duration = round((datetime.datetime.now()-t0).total_seconds(),3)
            response["duration"] = duration
            response["rows"] = len(response.get("results").get("bindings"))
            response["success"] = True
            return response
        except Exception as e:
            typ, msg, _ = sys.exc_info()
            duration = round((datetime.datetime.now()-t0).total_seconds(),3)
            return {"success" : False, "duration" : duration, "rows": 0, "error_type": typ.__name__, "error_msg": str(msg).replace('\\n','\n')}



#-------------------------------------------------
class DataModelBuilder:
#-------------------------------------------------

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def __init__(self, sparql_service, engine=None):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        # No default: querying the wrong store would silently give a wrong data model
        engine = engine or os.getenv("SIBILS_SPARQL_ENGINE")
        if engine not in ("virtuoso", "qlever"):
            raise ValueError(f"SIBILS_SPARQL_ENGINE must be virtuoso or qlever, got: {engine!r}")
        self.url2pfx = dict()
        self.pfx2url = dict()
        self.client = EndpointClient(sparql_service)

        self.class_def_query = """
            # CAUTION: we remove subjects that are blank nodes !

            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            select * where {
            {   select distinct ?subj where {
                values ?kind { owl:Class }
                ?subj a ?kind .
                filter (! strstarts(str(?subj), str(owl:)) && ! isBlank(?subj))
                }
            }
            ?subj ?prop ?obj .
            }
            order by ?subj ?prop ?obj
        """
        
        self.prop_def_query = """
            # CAUTION: blank nodes in range & domain objects

            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            select ?subj ?prop ?obj where {
                {   select distinct ?subj where {
                    values ?kind { rdf:Property owl:DatatypeProperty owl:ObjectProperty owl:AnnotationProperty owl:OntologyProperty }
                    ?subj a ?kind .
                    filter (! strstarts(str(?subj), str(owl:)) && ! strstarts(str(?subj), str(rdfs:)))
                    }
                }
                ?subj ?prop ?obj .
            }
            order by ?subj ?prop ?obj        
        """

        self.class_prop_query = """
            select ?property where { ?s a <$class_long_IRI> . ?s ?property ?o }
            group by ?property
            order by ?property
        """

        # One query per property of a class: a single query over all the properties
        # of the biggest classes needs more memory than QLever is given.
        #
        # The query forms depend on the engine:
        # - QLever needs the aggregate first: the outer query then sees one row per
        #   distinct value instead of one row per triple, otherwise it runs out of memory
        # - Virtuoso needs the plain form: it silently returns too low counts for the
        #   aggregate first form, i.e. 52,001,528 instead of 115,333,426 for oa:hasTarget
        def type_count_query(pattern, node):
            if engine == "qlever":
                where = f"""{{ select ?{node} (count(*) as ?n) where {{ {pattern} }} group by ?{node} }}"""
                total = "sum(?n)"
            else:
                where = pattern
                total = "count(*)"
            return f"""
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            select ?node_type ({total} as ?triple_count) where {{
            {where}
            optional {{?{node} a ?{node}_class }}
            bind(coalesce(?{node}_class, datatype(?{node}), xsd:anyURI) as ?node_type)
            }}
            group by ?node_type
            order by ?node_type
            """

        self.class_use_query = type_count_query("?s a <$class_long_IRI> . ?s <$prop_long_IRI> ?o", "o")

        self.prop_use_queries = {
            "count": """
            select (count(*) as ?triple_count) where { ?s <$prop_long_IRI> ?o }
            """,
            "domain": type_count_query("?s <$prop_long_IRI> ?o", "s"),
            "range": type_count_query("?s <$prop_long_IRI> ?o", "o")
        }

        self.prefix_query ="""
            PREFIX sh: <http://www.w3.org/ns/shacl#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            select ?pfx ?url where {
            ?onto a owl:Ontology .
            ?onto sh:declare ?declaration .
            ?declaration sh:prefix ?pfx; sh:namespace ?url.
            }
        """

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_short_IRI(self, long_iri):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        for url in self.url2pfx:
            if long_iri.startswith(url):
                pfx = self.url2pfx[url]
                id = long_iri[len(url):]
                return ":".join([pfx, id ])
        return long_iri


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_type_short_IRI(self, long_iri):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        # QLever reports the integers of the data as xsd:int
        short_iri = self.get_short_IRI(long_iri)
        return "xsd:integer" if short_iri == "xsd:int" else short_iri


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_long_IRI(self, prefixed_iri):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        pfx, id = prefixed_iri.split(":")
        url = self.pfx2url[pfx]
        return "".join([url, id])

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def load_prefixes(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        response = self.client.run_query(self.prefix_query)
        if not response.get("success"):
            log_it(f"ERROR while running query for getting prefixes", response.get("error_type"))
            log_it(response.get("error_msg"))
            sys.exit(2)
        rows = response.get("results").get("bindings")
        for row in rows:            
            pfx = self.get_short_IRI(row["pfx"]["value"])
            url = self.get_short_IRI(row["url"]["value"])
            self.pfx2url[pfx] = url
            self.url2pfx[url] = pfx

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def load_use_for_prop_entities(self, entities):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        for entity_key in entities:
            entity = entities[entity_key]
            if entity["tag"] != "prop" : continue
            #print("entity_key:",entity_key)
            long_IRI = self.get_long_IRI(entity_key)
            log_it("INFO", f"querying for usage of {entity_key}")
            for tag, template in self.prop_use_queries.items():
                query = template.replace("$prop_long_IRI", long_IRI)
                response = self.client.run_query(query)
                if not response.get("success"):
                    log_it(f"ERROR while running query for usage of entitites prop", response.get("error_type"))
                    log_it(response.get("error_msg"))
                    sys.exit(2)
                rows = response.get("results").get("bindings")
                for row in rows:
                    node_type = self.get_type_short_IRI(row["node_type"]["value"]) if tag != "count" else "xsd:integer"
                    count = row["triple_count"]["value"]
                    if int(count) == 0: continue
                    if tag == "count": entities[entity_key]["count"] = int(count)
                    statement = " | ".join([entity_key, tag, node_type, count])
                    entities[entity_key]["usage"].append(statement)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def load_use_for_class_entities(self, entities):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        for entity_key in entities:
            entity = entities[entity_key]
            if entity["tag"] != "class" : continue
            long_IRI = self.get_long_IRI(entity_key)
            log_it("INFO", f"querying for usage of {entity_key}")
            prop_rows = self.run_class_use_query(self.class_prop_query.replace("$class_long_IRI", long_IRI))
            for prop_row in prop_rows:
                prop_IRI = prop_row["property"]["value"]
                query = self.class_use_query.replace("$class_long_IRI", long_IRI).replace("$prop_long_IRI", prop_IRI)
                for row in self.run_class_use_query(query):
                    count = row["triple_count"]["value"]
                    subj = entity_key
                    prop = self.get_short_IRI(prop_IRI)
                    obj = self.get_type_short_IRI(row["node_type"]["value"])
                    if prop == "rdf:type" and subj == entity_key: entities[subj]["count"] = int(count)
                    statement = " | ".join([subj, prop, obj, count])
                    entities[subj]["usage"].append(statement)
                    if obj in entities:
                        statement = " | ".join([subj, prop, obj, count])
                        entities[obj]["usage"].append(statement)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def run_class_use_query(self, query):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        response = self.client.run_query(query)
        if not response.get("success"):
            log_it(f"ERROR while running query for usage of entitites class", response.get("error_type"))
            log_it(response.get("error_msg"))
            sys.exit(2)
        return response.get("results").get("bindings")


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def load_def_for_entities(self, query, tag, entities):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        response = self.client.run_query(query)
        if not response.get("success"):
            log_it(f"ERROR while running query for definition of entities {tag}", response.get("error_type"))
            log_it(response.get("error_msg"))
            sys.exit(2)
        rows = response.get("results").get("bindings")
        relations = list()
        for row in rows:            
            subj = self.get_short_IRI(row["subj"]["value"])
            prop = self.get_short_IRI(row["prop"]["value"])
            obj = self.get_short_IRI(row["obj"]["value"])
            relations.append( { "subj": subj, "prop": prop, "obj": obj } )
            if subj not in entities: entities[subj] = { "tag": tag , "count": 0, "definition": list(), "usage" : list() }
        for rel in relations:
            subj = rel["subj"]
            prop = rel["prop"]
            obj = rel["obj"]
            statement = " | ".join([subj, prop, obj])
            entities[subj]["definition"].append(statement)
            if obj in entities:
                statement = " | ".join([subj, prop, obj])
                entities[obj]["definition"].append(statement)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def retrieve_and_save_model(self, jsonfile):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        entities = dict()

        self.load_prefixes()
        self.load_def_for_entities(self.class_def_query, "class", entities)
        self.load_def_for_entities(self.prop_def_query, "prop", entities)
        self.load_use_for_class_entities(entities)
        self.load_use_for_prop_entities(entities)

        data = dict()
        data["entities"] = entities
        data["pfx2url"] = self.pfx2url
        f_out = open(jsonfile, "w", encoding="utf-8")
        json.dump(data, f_out, indent=2, ensure_ascii=False)
        f_out.close()



#-------------------------------------------------
if __name__ == '__main__':
#-------------------------------------------------
    optparser = OptionParser(usage="python datamodel_builder.py [--crlf] sparql_service_url output_file")
    optparser.add_option("-c", "--crlf",
        action="store_true", dest="with_crlf", default=False,
        help="When set, output file line sep is CR/LF instead of LF")
    (options, args) = optparser.parse_args()
    with_crlf = options.with_crlf
    if len(args) != 2:
        print("ERROR, usage is: python datamodel_builder.py [--crlf] sparql_service_url output_file")    
        sys.exit(1)

    builder = DataModelBuilder(sparql_service=args[0])
    builder.retrieve_and_save_model(jsonfile=args[1])

