import sys
import os
import gzip
import json
import requests
import subprocess
from optparse import OptionParser
from pathlib import Path
from io import BytesIO
from ApiCommon import log_it
from api_platform import ApiPlatform
from namespace_registry import NamespaceRegistry
from source_rdfizer import SourceRdfizer
from pmc_rdfizer import PmcRdfizer
from medline_rdfizer import MedlineRdfizer
from term_rdfizer import TermRdfizer
from rdf_utils import TripleList
from ontology_builder import OntologyBuilder
from queries_utils import QueryFileReader, Query
from datamodel_builder import DataModelBuilder



#-------------------------------------------------
class RdfBuilder:
#-------------------------------------------------

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def __init__(self, ns: NamespaceRegistry): 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        self.ns = ns
        self.voidgendir = "../../../sibils-void-generator"
        self.ttldir = "../out/ttl"
        self.fetchdir = "../out/fetch"
        self.termidir = "../out/terminologies"
        self.src_rdfizer = SourceRdfizer(self.ns)
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
            publi_rdfizer = PmcRdfizer(self.ns, self.src_rdfizer, data)
            return publi_rdfizer.get_ttl_for_publi()
        elif "medline" in fileparts:
            log_it("INFO, parsing medline", filename)
            publi_rdfizer = MedlineRdfizer(self.ns, self.src_rdfizer, data)
            return publi_rdfizer.get_ttl_for_publi()
        else:
            log_it("ERROR, skipping unknown file type", filename)
            return ""


    # - - - - - - - - - - - - - - - - - - - - 
    # reads pmc and medline publis (json.gz files) that were fetched earlier in the pipeline
    # and extracts terminology concepts cited in publi annotations
    # - - - - - - - - - - - - - - - - - - - - 
    def get_terminologies_with_cited_concepts(self, sample_only=False):
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
            if sample_only and count > 11000: break
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
    def write_ttl_for_terminologies(self):
    # - - - - - - - - - - - - - - - - - - - - 
        terminologies = self.get_terminologies_with_cited_concepts(sample_only=False)
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


    # - - - - - - - - - - - - - - - - - - - - 
    def write_ttl_file_for_citing_sources(self):
    # - - - - - - - - - - - - - - - - - - - - 
        ttl_file = "/".join([self.ttldir, "citing-sources.ttl"])
        log_it(f"INFO, writing ttl file for citing sources: {ttl_file}")
        f_out = open(ttl_file, "w")
        f_out.write(self.get_ttl_prefixes())
        f_out.write("\n")
        f_out.write("\n".join(["#", f"# List of owl:NamedIndividual for citing sources", "#", "\n"]))
        ttl_str = self.src_rdfizer.get_ttl_for_citing_sources()        
        f_out.write(ttl_str)
        f_out.close()
        log_it(f"INFO, wrote ttl file for citing sources: {ttl_file}")


    # - - - - - - - - - - - - - - - - - - - - 
    def write_ttl_gz_file_for_publi_list(self, input_filenames, ttl_gz_file):
    # - - - - - - - - - - - - - - - - - - - - 
        log_it(f"INFO, writing ttl file for {len(input_filenames)} json.gz files: {ttl_gz_file}")
        #f_out = open(ttl_gz_file, "w")
        f_out = gzip.open(ttl_gz_file, 'wt')
        f_out.write(self.get_ttl_prefixes())
        f_out.write("\n")
        for filename in input_filenames:
            f_out.write("\n".join(["#", f"# triples related to {filename}", "#", "\n"]))
            publi_ttl = self.get_ttl_from_publi_file(filename)
            f_out.write(publi_ttl)
        f_out.close()
        log_it(f"INFO, wrote ttl file for {len(input_filenames)} json.gz files: {ttl_gz_file}")


    # - - - - - - - - - - - - - - - - - - - - 
    def get_medline_json_filenames(self):
    # - - - - - - - - - - - - - - - - - - - - 
        log_it(f"INFO, retrieving list of json.gz medline files to be rdfized")
        filenames = list()
        basedir = self.fetchdir + "/medline"
        for root, dirs, files in os.walk(basedir):
            for file in files: 
                if file.endswith("json.gz"):
                    filenames.append(root + "/" + file)
        filenames.sort()
        log_it(f"INFO, retrieved {len(filenames)} json.gz medline file names to be rdfized")
        return filenames
    

    # - - - - - - - - - - - - - - - - - - - - 
    def get_pmc_json_filenames(self):
    # - - - - - - - - - - - - - - - - - - - - 
        log_it(f"INFO, retrieving list of json.gz pmc files to be rdfized")
        filenames = list()
        basedir = self.fetchdir + "/pmc"
        for root, dirs, files in os.walk(basedir):
            for file in files: 
                if file.endswith("json.gz"):
                    filenames.append(root + "/" + file)
        filenames.sort()
        log_it(f"INFO, retrieved {len(filenames)} json.gz pmc file names to be rdfized")
        return filenames
    

    # - - - - - - - - - - - - - - - - - - - - 
    def write_ttl_gz_files_for_medline(self):
    # - - - - - - - - - - - - - - - - - - - - 
        pack_size = 500
        filenames = self.get_medline_json_filenames()
        pack_num = 0
        while pack_num * pack_size < len(filenames):
            pack_ttlname = self.ttldir + f"/data_medline_{pack_num:04d}.ttl.gz"
            idx = pack_num * pack_size
            input_files = filenames[idx : idx + pack_size]
            #print("DEBUG", pack_ttlname, idx)
            self.write_ttl_gz_file_for_publi_list(input_files, pack_ttlname)
            pack_num += 1


    # - - - - - - - - - - - - - - - - - - - - 
    def write_ttl_gz_files_for_pmc(self):
    # - - - - - - - - - - - - - - - - - - - - 
        pack_size = 40
        filenames = self.get_pmc_json_filenames()
        pack_num = 0
        while pack_num * pack_size < len(filenames):
            pack_ttlname = self.ttldir + f"/data_pmc_{pack_num:04d}.ttl.gz"
            idx = pack_num * pack_size
            input_files = filenames[idx : idx + pack_size]
            #print("DEBUG", pack_ttlname, idx)
            self.write_ttl_gz_file_for_publi_list(input_files, pack_ttlname)
            pack_num += 1


    # - - - - - - - - - - - - - - - - - - - - 
    def write_ttl_for_ontology(self, describe_ranges_and_domains=True):
    # - - - - - - - - - - - - - - - - - - - - 
        platform = self.ns.platform
        ob = OntologyBuilder(platform, self.ns, describe_ranges_and_domains=describe_ranges_and_domains)
        onto_lines = ob.get_onto_pretty_ttl_lines("dev version")
        onto_ttl_file = "/".join([self.ttldir, "ontology.ttl"])
        stream=open(onto_ttl_file, "w")
        stream.write(self.get_ttl_prefixes())
        stream.write("\n".join(onto_lines))
        stream.close()


    # - - - - - - - - - - - - - - - - - - - - 
    def write_ttl_gz_files_for_model(self):
    # - - - - - - - - - - - - - - - - - - - - 
        pass

    # - - - - - - - - - - - - - - - - - - - - 
    def write_ttl_file_for_void(self):
    # - - - - - - - - - - - - - - - - - - - - 
        log_it("INFO", "BUILD_RDF", "void", "starting...")
        void_script = "/".join([self.voidgendir, "doit-sibils.sh"])
        result = subprocess.run(['bash', void_script], capture_output=True, text=True) 
        if result.returncode == 0:
            generated_void_ttl = "/".join([self.voidgendir, "void-sibils.ttl"])
            result = subprocess.run(['cp', generated_void_ttl, self.ttldir], capture_output=True, text=True) 
        if result.returncode == 0:
            log_it("INFO", "BUILD_RDF", "void", "succeeded")
        else:
            print(result.stdout)
            print(result.stderr)
            log_it("ERROR", "BUILD_RDF", "void", "failed")


    # - - - - - - - - - - - - - - - - - - - - 
    def save_virtuoso_isql_setup_file(self, output_file):
    # - - - - - - - - - - - - - - - - - - - - 
        lines = []
        lines.append("""grant select on "DB.DBA.SPARQL_SINV_2" to "SPARQL";""")
        lines.append("""grant execute on "DB.DBA.SPARQL_SINV_IMP" to "SPARQL";""")
        lines.append("""GRANT SPARQL_SPONGE TO "SPARQL";""")
        lines.append("""GRANT EXECUTE ON DB.DBA.L_O_LOOK TO "SPARQL";""")
        for a_ns in self.ns.namespaces:
            lines.append(a_ns.getSQLforVirtuoso())
        f_out = open(output_file, "w")
        for line in lines: f_out.write(line + "\n")
        f_out.close()


    # - - - - - - - - - - - - - - - - - - - - 
    def write_ttl_file_for_queries(self):
    # - - - - - - - - - - - - - - - - - - - - 
        # create ttl file containing a list of example SPARQL queries 
 
        rdf_dir = self.ttldir + "/"
        rdf_file = open(rdf_dir + "queries.ttl", "wb")
        log_it("INFO:", f"serializing example SPARQL queries")   
        reader = QueryFileReader()
        rdf_file.write(bytes("#\n", "utf-8"))
        rdf_file.write(bytes("# example SPARQL queries\n", "utf-8"))
        rdf_file.write(bytes("#\n\n", "utf-8"))
        rdf_file.write(bytes("@prefix schema: <https://schema.org/> . \n", "utf-8"))
        rdf_file.write(bytes("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> . \n", "utf-8"))
        rdf_file.write(bytes("@prefix sh: <http://www.w3.org/ns/shacl#> . \n", "utf-8"))
        rdf_file.write(bytes("@prefix spex: <https://purl.expasy.org/sparql-examples/ontology#> . \n", "utf-8"))
        rdf_file.write(bytes(f"@prefix sibilo: <{self.ns.sibilo.url}> .\n", "utf-8"))
        rdf_file.write(bytes("\n\n", "utf-8"))
        count = 0
        for q in reader.query_list:    
            query : Query = q
            count += 1
            ttl = query.get_ttl_for_sparql_endpoint(self.ns)
            rdf_file.write(bytes(ttl + "\n\n", "utf-8"))
        log_it("INFO", f"wrote {count} queries")
        log_it("INFO:", f"serialized example SPARQL queries")
        rdf_file.close()


#-------------------------------------------------
if __name__ == '__main__':
#-------------------------------------------------

    parser = OptionParser()
    parser.add_option(
        "-p", "--platform", action="store", type="string", dest="platform_key", default="(none)",
        help="API platform key: test,prod, or local")

    (options, args) = parser.parse_args()

    platform_key = options.platform_key.lower()
    if platform_key not in ["local", "test", "prod"]: 
        sys.exit("Invalid --platform option, expected local, test, or prod")

    usage = "Invalid arg1, expected BUILD_RDF, LOAD_RDF, MODEL, STATIC_PAGES" 
    if len(args) < 1: sys.exit(usage)

    if args[0] not in [ "BUILD_RDF", "LOAD_RDF", "MODEL", "STATIC_PAGES" ]: 
        sys.exit(usage)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    if args[0]=="BUILD_RDF":
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        if len(args) < 2 or args[1] not in ["pmc", "medline", "terminology", "sources", "ontology", "queries", "void"]:
            sys.exit("Invalid arg2, expected pmc, medline, terminology, sources, ontology, queries or void")

        platform = ApiPlatform(platform_key)
        ns = NamespaceRegistry(platform)
        builder = RdfBuilder(ns)

        if args[1] == "pmc": 
            builder.write_ttl_gz_files_for_pmc()
        elif args[1] == "medline": 
            builder.write_ttl_gz_files_for_medline()
        elif args[1] == "terminology": 
            builder.write_ttl_for_terminologies()
        elif args[1] == "sources": 
            builder.write_ttl_file_for_citing_sources()
        elif args[1] == "ontology": 
            if len(args) > 2 and args[2] == "no-dr":
                builder.write_ttl_for_ontology(describe_ranges_and_domains=False)
            else:
                builder.write_ttl_for_ontology()
        elif args[1] == "queries": 
            builder.write_ttl_file_for_queries()
        elif args[1] == "void": 
            builder.write_ttl_file_for_void()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    elif args[0]=="LOAD_RDF":
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        if len(args) < 2 or args[1] not in ["clear", "pmc", "medline", "terminology", "sources", "ontology", "void", "queries"]:
            sys.exit("Invalid arg2, expected clear, pmc, medline, terminology, sources, ontology, void, queries")

        platform = ApiPlatform(platform_key)
        ns = NamespaceRegistry(platform)
        builder = RdfBuilder(ns)
        result = None

        if args[1] == "clear": 
            # clear the virtuoso database
            result = subprocess.run(['bash', '../virt/sparql_service.sh', 'clear'], capture_output=True, text=True) 
            if result.returncode == 0:
                # generate and load virtuoso setup file
                builder.save_virtuoso_isql_setup_file('../virt/virtuoso_setup.sql')
                result = subprocess.run(['bash', '../virt/load_ttl_files.sh', 'setup'], capture_output=True, text=True) 

        elif args[1] == "pmc": 
            result = subprocess.run(['bash', '../virt/load_ttl_files.sh', 'data_pmc', 'no_checkpoint'], capture_output=True, text=True) 
        elif args[1] == "medline": 
            result = subprocess.run(['bash', '../virt/load_ttl_files.sh', 'data_medline', 'no_checkpoint'], capture_output=True, text=True) 
        elif args[1] == "terminology": 
            result = subprocess.run(['bash', '../virt/load_ttl_files.sh', 'termino', 'no_checkpoint'], capture_output=True, text=True) 
            if result: result = subprocess.run(['bash', '../virt/load_ttl_files.sh', 'concept', 'no_checkpoint'], capture_output=True, text=True) 
        elif args[1] == "sources": 
            result = subprocess.run(['bash', '../virt/load_ttl_files.sh', 'citing-sources', 'no_checkpoint'], capture_output=True, text=True) 
        elif args[1] == "ontology": 
            result = subprocess.run(['bash', '../virt/load_ttl_files.sh', 'onto', 'no_checkpoint'], capture_output=True, text=True) 
        elif args[1] == "void": 
            result = subprocess.run(['bash', '../virt/load_ttl_files.sh', 'void', 'no_checkpoint'], capture_output=True, text=True) 
        elif args[1] == "queries": 
            result = subprocess.run(['bash', '../virt/load_ttl_files.sh', 'queries', 'no_checkpoint'], capture_output=True, text=True) 

        if result.returncode == 0:
            log_it("INFO", "LOAD_RDF", args[1], "succeeded")
        else:
            print(result.stdout)
            print(result.stderr)
            log_it("ERROR", "LOAD_RDF", args[1], "failed")
            sys.exit(1)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    elif args[0]=="MODEL":
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        #
        # create json file containing sibils RDF data model
        #
        fileout = "../serve/static/datamodel.json"
        log_it("INFO:", f"serializing SIBiLS RDF data model to: {fileout}")        
        platform = ApiPlatform(platform_key)
        builder = DataModelBuilder(platform.get_builder_sparql_service_IRI())
        builder.retrieve_and_save_model(fileout)
        log_it("INFO:", f"serialized SIBiLS RDF data model to: {fileout}")


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    elif args[0]=="STATIC_PAGES":
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        result = subprocess.run(['bash', '../serve/prepare_static_pages.sh'], capture_output=True, text=True) 

        if result.returncode == 0:
            log_it("INFO", "STATIC_PAGES", "succeeded")
        else:
            print(result.stdout)
            print(result.stderr)
            log_it("ERROR", "STATIC_PAGES", "failed")
            sys.exit(1)


    log_it("INFO, end")

    sys.exit()

