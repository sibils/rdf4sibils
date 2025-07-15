import sys
import os
import gzip
import json
import requests
from pathlib import Path
from io import BytesIO
from ApiCommon import log_it
from api_platform import ApiPlatform
from namespace_registry import NamespaceRegistry
from pmc_rdfizer import PmcRdfizer
from medline_rdfizer import MedlineRdfizer
from term_rdfizer import TermRdfizer
from rdf_utils import TripleList


#-------------------------------------------------
class RdfBuilder:
#-------------------------------------------------

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def __init__(self, ns: NamespaceRegistry): 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        self.ns = ns
        self.ttldir = "../out/ttl"
        self.fetchdir = "../out/fetch"
        self.termidir = "../out/terminologies"
        if not os.path.exists(self.ttldir): os.makedirs(self.ttldir)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_ttl_prefixes(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        lines = list()
        for item in self.ns.namespaces:
            lines.append(item.getTtlPrefixDeclaration())
        return "\n".join(lines) + "\n\n"


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
            log_it("INFO, parsing pmc", filename)
            publi_rdfizer = PmcRdfizer(self.ns, data)
            return publi_rdfizer.get_ttl_for_publi()
        elif "medline" in fileparts:
            log_it("INFO, parsing medline", filename)
            publi_rdfizer = MedlineRdfizer(self.ns, data)
            return publi_rdfizer.get_ttl_for_publi()
        else:
            log_it("ERROR, skipping unknown file type", filename)
            return ""


    # - - - - - - - - - - - - - - - - - - - - 
    # reads pmc and medline publis (json.gz files) that were fetched earlier in the pipeline
    # and extracts terminology concepts cited in publi annotations
    # - - - - - - - - - - - - - - - - - - - - 
    def get_terminologies_with_cited_concepts(self):
    # - - - - - - - - - - - - - - - - - - - - 
        gz_files = list()
        for datadir in ["medline", "pmc"]:
            directory = Path("/".join([self.fetchdir, datadir]))
            gz_files.extend(list(directory.rglob('*.gz')))
        terminologies = dict()
        count = 0
        log_it("Reading cited concepts in publication json files")
        for file in gz_files:
            count += 1
            if count > 11000: break
            if count % 1000 == 0: log_it(f"Getting cited concepts in file {count} / {len(gz_files)}...")
            stream = open(file, 'rb')
            gzipped_data = stream.read()
            gz = gzip.GzipFile(fileobj=BytesIO(gzipped_data))
            decompressed_bytes = gz.read()
            json_str = decompressed_bytes.decode('utf-8')
            data = json.loads(json_str)
            stream.close()
            #doc_id = data["_id"]
            for ann in data["annotations"]:
                onto_id = ann["concept_source"]
                onto_ty = ann["type"]
                onto_ve = ann["version"]
                if onto_id not in terminologies: terminologies[onto_id] = { "version": onto_ve, "type": onto_ty, "usage": 0,  "cited_concepts" : dict() }
                onto = terminologies[onto_id]
                onto["usage"] += 1
                concepts = onto["cited_concepts"]
                cpt_id = ann["concept_id"]
                if cpt_id not in concepts: concepts[cpt_id] = ""
                if len(concepts[cpt_id]) < 36:
                    file_id = file.name.split("/")[-1]
                    concepts[cpt_id] += " " + file_id
        log_it(f"Got cited concepts in file {count} / {len(gz_files)}...")
        for term_id in sorted(terminologies):
            log_it("terminology: ", term_id)
            cited_count=0
            cited_concepts = terminologies[term_id]["cited_concepts"]
            for cpt_id in cited_concepts:
                cited_count +=1
                if cited_count > 5: break
                log_it(cpt_id, "cited in:", cited_concepts[cpt_id])
            log_it("\n")
        return terminologies


    # - - - - - - - - - - - - - - - - - - - - 
    # reads the content of the json file generated by the SIBiLS annotation process
    # the file contains some properties of the terminology and a list of concepts that
    # it contains as well as parent / child concept relationships
    # NOTE: the list of concepts is turned into a dictionary of concepts to ease
    # processes occuring later
    # NOTE: we add some hard-coded metadata used to build concept link to definition 
    # (native IRI and / or webpage)
    # - - - - - - - - - - - - - - - - - - - - 
    def get_full_terminology(self, filename):
    # - - - - - - - - - - - - - - - - - - - - 
        stream = open(filename, 'r', encoding='utf-8')
        data = json.load(stream)
        stream.close()
        # turn concept list into concept dict
        concept_dict = dict()
        for cpt in data["concepts"]: concept_dict[cpt["id"]] = cpt
        data["concepts"] = concept_dict

        return data


    # - - - - - - - - - - - - - - - - - - - - 
    # gathers some useful info about terminologies
    # via a SIBiLS HTTP service like label, decription, url
    # - - - - - - - - - - - - - - - - - - - - 
    def get_terminology_metadata_dictionary(self):
    # - - - - - - - - - - - - - - - - - - - - 
        url = "https://biodiversitypmc.sibils.org/api/otf/terminologies"
        response = requests.get(url)
        data = response.json()
        return data["terminologies"]


    # - - - - - - - - - - - - - - - - - - - - 
    # the file current-version.txt is provided by the annotation process
    # together with the list of terminologies in json format
    # the files links terminology identifiers with a file name 
    # terminology identifier values are to be found in annotation.concept_source
    # and in terminology.description.terminology
    # - - - - - - - - - - - - - - - - - - - - 
    def get_terminology_file_dictionary(self):
    # - - - - - - - - - - - - - - - - - - - - 
        termi2filename = dict()
        filename = "/".join([self.termidir, "current-version.txt"])
        stream = open(filename)
        for line in stream.readlines():
            id, file = line.strip().split("\t")
            termi2filename[id] = "/".join([self.termidir, file])
        stream.close()
        return termi2filename



    # - - - - - - - - - - - - - - - - - - - - 
    def get_ttl_for_terminologies(self):
    # - - - - - - - - - - - - - - - - - - - - 
        terminologies = self.get_terminologies_with_cited_concepts()
        termi2file = self.get_terminology_file_dictionary()
        term2meta = self.get_terminology_metadata_dictionary()

        termino_triples = TripleList()
        for term_id in terminologies:
            if term_id in [ "grant", "identifiers"]:
                log_it(f"WARNING, Skipped building of ttl for {term_id}...")
                continue                
            log_it(f"INFO, Building ttl for {term_id}...")
            termifile = termi2file[term_id]
            fulltermi = self.get_full_terminology(termifile)
            termimeta = term2meta.get(term_id) or dict()
            rdfizer = TermRdfizer(self.ns, fulltermi, termimeta)
            termino_triples.extend(rdfizer.get_triples_for_terminology())

            concepts_ttl_file = "/".join([self.ttldir, f"concept_{term_id}.ttl"])
            stream=open(concepts_ttl_file, "w")
            stream.write(self.get_ttl_prefixes())
            cited_concepts = terminologies[term_id]["cited_concepts"]
            for cpt_id in rdfizer.get_relevant_concepts(cited_concepts):
                concepts_triples = rdfizer.get_triples_for_concept(cpt_id)
                stream.write("".join(concepts_triples.lines))
            stream.close()

        termino_ttl_file = "/".join([self.ttldir, "terminologies.ttl"])
        stream=open(termino_ttl_file, "w")
        stream.write(self.get_ttl_prefixes())
        stream.write("".join(termino_triples.lines))
        stream.close()




#-------------------------------------------------
if __name__ == '__main__':
#-------------------------------------------------
    platform = ApiPlatform("prod")
    ns = NamespaceRegistry(platform)
    builder = RdfBuilder(ns)

    # terminologies = builder.get_terminologies_with_cited_concepts()
    # termi2file = builder.get_terminology_file_dictionary()
    # term2meta = builder.get_terminology_metadata_dictionary()
    # term_id = "covoccelllines"
    # termino_triples = TripleList()
    # termifile = termi2file[term_id]
    # fulltermi = builder.get_full_terminology(termifile)
    # termimeta = term2meta.get(term_id) or dict()
    # rdfizer = TermRdfizer(ns, fulltermi, termimeta)
    # rdfizer.print()

    builder.get_ttl_for_terminologies()
#    sys.exit()

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

#    log_it("end")

