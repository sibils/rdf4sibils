import os
import sys
import datetime
from optparse import OptionParser
from SPARQLWrapper import SPARQLWrapper, JSON
from lxml import etree


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
if __name__ == '__main__':
#-------------------------------------------------

    if len(sys.argv) < 2 : 
        print("Error, usage is : python cello-pmid-getter.py <output_dir>")
        sys.exit(1)

    outdir = sys.argv[1]
    if not outdir.endswith("/") : outdir += "/"

    query = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX cello: <https://purl.expasy.org/cellosaurus/rdf/ontology/>

        select distinct ?pmid  where {
        ?p a / rdfs:subClassOf+ cello:Publication .
        ?p cello:pmid ?pmid .
        # optional { ?p cello:pmcId ?pmcid . }
        }
        # limit 100
    """

    sparql_service = "https://sparql.cellosaurus.org/sparql"

    log_it("Querying cellosaurus SPARQL service...", sparql_service)
    client = EndpointClient(sparql_service)
    response = client.run_query(query)
    log_it("Retrieving response...")
    if not response.get("success"):
        log_it(f"ERROR while running query to get cellosaurus pmids", response.get("error_type"))
        log_it(response.get("error_msg"))
        sys.exit(2)
    rows = response.get("results").get("bindings")
    fileout = outdir + "cello-pmid.txt"
    log_it("Saving pmids...")
    f_out = open(fileout, "w")
    for row in rows:
        pmid = row["pmid"]["value"]
        f_out.write("".join([pmid, "\n"]))
    f_out.close()
    log_it("Saved pmids in file", fileout)
    print("end")