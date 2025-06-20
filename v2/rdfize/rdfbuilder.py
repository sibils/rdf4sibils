import sys
import os
import gzip
import json
from io import BytesIO
from ApiCommon import log_it
from api_platform import ApiPlatform
from namespace_registry import NamespaceRegistry
from pmc_rdfizer import PmcRdfizer
from medline_rdfizer import MedlineRdfizer


#-------------------------------------------------
class RdfBuilder:
#-------------------------------------------------

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def __init__(self, ns: NamespaceRegistry): 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        self.ns = ns
        self.ttldir = "../out/ttl"
        if not os.path.exists(self.ttldir): os.makedirs(self.ttldir)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_ttl_prefixes(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        lines = list()
        for item in self.ns.namespaces:
            lines.append(item.getTtlPrefixDeclaration())
        return "\n".join(lines) + "\n"


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_sparql_prefixes(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        lines = list()
        for item in self.ns.namespaces:
            lines.append(item.getSparqlPrefixDeclaration())
        return "\n".join(lines) + "\n"


    # - - - - - - - - - - - - - - - - - - - - 
    def get_ttl_from_publi_file(self, filename):
    # - - - - - - - - - - - - - - - - - - - - 
        # get json data from gz file
        stream = open(filename, 'rb')
        gzipped_data = stream.read()
        gz = gzip.GzipFile(fileobj=BytesIO(gzipped_data))
        decompressed_bytes = gz.read()
        json_str = decompressed_bytes.decode('utf-8')
        data = json.loads(json_str)
        stream.close()

        # build ttl from data and return it
        fileparts = filename.split("/")
        if "pmc" in fileparts:
            print("INFO, parsing pmc", filename)
            publi_rdfizer = PmcRdfizer(self.ns, data)
            return publi_rdfizer.get_ttl_for_publi()
        elif "medline" in fileparts:
            print("INFO, parsing medline", filename)
            publi_rdfizer = MedlineRdfizer(self.ns, data)
            return publi_rdfizer.get_ttl_for_publi()
        else:
            print("ERROR, skipping unknown file type", filename)
            return ""







#-------------------------------------------------
if __name__ == '__main__':
#-------------------------------------------------
    platform = ApiPlatform("prod")
    ns = NamespaceRegistry(platform)
    builder = RdfBuilder(ns)

    #print(builder.get_sparql_prefixes())
    #sys.exit()

    #collections = ["pmc", "medline"]

    filenames = list()
    for fn in "PMC1253521.json.gz,PMC125375.json.gz,PMC1253832.json.gz".split(","):
        filenames.append("../out/fetch/pmc/PMC12/" + fn)
    for fn in "3049071.json.gz,3049153.json.gz,3049254.json.gz".split(","):
        filenames.append("../out/fetch/medline/30/49/" + fn)

    ttl_file = builder.ttldir + "/data_test.ttl"
    f_out = open(ttl_file, "w")
    f_out.write(builder.get_ttl_prefixes())
    f_out.write("\n")

    for filename in filenames:
        f_out.write("\n".join(["#", f"# triples related to {filename}", "#", "\n"]))
        publi_ttl = builder.get_ttl_from_publi_file(filename)
        f_out.write(publi_ttl)

    f_out.close()

