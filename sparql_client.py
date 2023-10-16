from SPARQLWrapper import SPARQLWrapper, JSON
import json
import sys
import datetime

# see https://github.com/RDFLib/sparqlwrapper/tree/master


class EndpointClient:

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def __init__(self, server_url):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        self.server_url = server_url
        self.endpoint = SPARQLWrapper(server_url)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_graph_stats(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        query = """
            SELECT ?graph (COUNT(*) as ?tripleCount)
            WHERE { GRAPH ?graph { ?s ?p ?o } }
            GROUP BY ?graph
        """
        return self.run_query(query)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def query_from_file(self, file_name):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

        with open(file_name,"r") as f: query = f.read() 
        return self.run_query(query)
    

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
 


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = 
if __name__ == '__main__' :
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = 

    if len(sys.argv) < 2:
        print("\nERROR, usage is:\n\n\tpython " + sys.argv[0] + " <sparql_query_file_name>\n\n")
        sys.exit(1)

    query_file_name = sys.argv[1]

    client = EndpointClient("http://sibils-sparql.lan.text-analytics.ch:8890/sparql")
    response = client.query_from_file(query_file_name)

    if response.get("success"):

        col_names = response.get("head").get("vars")
        print("HEAD\t" + "\t".join(col_names))
        rows = response.get("results").get("bindings")
        for row in rows:
            cols = list()
            for cn in col_names:
                col = row.get(cn)
                colval = col.get("value")
                cols.append(row.get(cn).get("value"))
            print("ROWS\t" +"\t".join(cols))
        
    else:
        print("ERROR", response.get("error_type"))
        print(response.get("error_msg"))
    
    print("META\tsuccess\t", response.get("success"))
    print("META\tduration[s]\t", response.get("duration"))
    print("META\tcount\t", response.get("rows"))
    print("END")