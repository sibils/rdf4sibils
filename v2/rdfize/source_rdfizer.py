from api_platform import ApiPlatform
from namespace_registry import NamespaceRegistry
from rdf_utils import TripleList

class SourceRdfizer:

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def __init__(self, ns: NamespaceRegistry): 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        self.ns = ns
        self.pmids_dir = "../out/pmids"
        self.citing_source_dict = dict()
        self.citing_source_dict["Cellosaurus"] =  { "seeAlso": "https://www.cellosaurus.org"  , "pmids" : self.get_set_from_file("cello-pmid.txt") }
        self.citing_source_dict["Rhea"] =         { "seeAlso": "https://www.rhea-db.org"      , "pmids" : self.get_set_from_file("rhea-pmid.txt") }
        self.citing_source_dict["SwissLipids"] =  { "seeAlso": "https://www.swisslipids.org"  , "pmids" : self.get_set_from_file("swisslipid-pmid.txt") }
        self.citing_source_dict["UniProtKB"] =    { "seeAlso": "https://www.uniprot.org"      , "pmids" : self.get_set_from_file("swissprot-pmid.txt") }


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_set_from_file(self, filename):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        fullname = "/".join([self.pmids_dir, filename])
        stream = open(fullname, 'r')
        lines = [line.rstrip('\n') for line in stream]
        return set(lines)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_citing_source_IRI(self, name):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        return ":".join([self.ns.sibils.pfx, name])


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_list_of_source_IRI_citing_pmid(self, pmid):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        result = list()
        for k in self.citing_source_dict:
            if pmid in self.citing_source_dict[k]["pmids"]:
                result.append(self.get_citing_source_IRI(k))
        return result
    

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_ttl_for_citing_sources(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        ns = self.ns
        triples = TripleList()
        for name in self.citing_source_dict:
            src_IRI = self.get_citing_source_IRI(name)
            src_lnk = self.citing_source_dict[name]["seeAlso"]
            triples.append(src_IRI, ns.rdf.type, ns.owl.NamedIndividual)
            triples.append(src_IRI, ns.rdf.type, ns.sibilo.CitingSource)
            triples.append(src_IRI, ns.rdfs.label, ns.xsd.string1(name))
            triples.append(src_IRI, ns.rdfs.seeAlso, f"<{src_lnk}>")
            triples.append("","","", punctuation="")

        return("".join(triples.lines))


#-------------------------------------------------
if __name__ == '__main__':
#-------------------------------------------------
    platform = ApiPlatform("prod")
    ns = NamespaceRegistry(platform)
    rdfizer = SourceRdfizer(ns)
    ttl = rdfizer.get_ttl_for_citing_sources()
    print(ttl)
    print("----")
    for k in rdfizer.citing_source_dict:
        size = len(rdfizer.citing_source_dict[k]["pmids"])
        print(k, size)

    print("---- cello list excerpt")
    pmid_list = list(rdfizer.citing_source_dict["Cellosaurus"]["pmids"])
    mini_list = list()
    for i in range(10):
        mini_list.append(pmid_list[i])
    print(mini_list)


    print("----")
    pmid = "21325339"
    for item in rdfizer.get_list_of_source_IRI_citing_pmid(pmid):
        print(pmid, "in", item)
