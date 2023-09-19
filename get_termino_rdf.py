import sys
import os
import json
#import orjson as json
import glob
import datetime
from get_publi_rdf import get_term_URIRef_from_term, get_terminology_URIRef, sibilc, sibilo, log_it
from SibiloNamespace import SibiloNamespace
from rdfizer import SibilcNamespace, SibilsNamespace
from rdfizer import RdfNamespace, RdfsNamespace, OwlNamespace, XsdNamespace, SkosNamespace, FoafNamespace
from rdfizer import getBlankNode, getTtlPrefixDeclaration,   getTriple

sibilo = SibiloNamespace()          # sibils core ontology
sibils = SibilsNamespace()          # sibils data
sibilc = SibilcNamespace()          # concepts used in sibils annotation
rdf = RdfNamespace()
rdfs = RdfsNamespace()
xsd = XsdNamespace()
owl = OwlNamespace()
skos = SkosNamespace()

TAB = "    "
COMMA = ","
SEMICOLON = ";"
DOTLINE = "    .\n"


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class TransitiveRelation:
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

    relation_dict = dict()

    def __init__(self):
        self.relation_dict = dict()
        #log_it("###", "TransitiveRelation init()")

    def add_relation(self, parent, child):
        if parent not in self.relation_dict: self.relation_dict[parent] = set()
        self.relation_dict[parent].add(child)

    def get_parent_set(self):
        parents = list(self.relation_dict.keys())
        return sorted(parents)

    def get_child_set(self, parent):
        if parent not in self.relation_dict: 
            return None
        children = set()
        for child in self.relation_dict[parent]:
            children.add(child)
            grand_children = self.get_child_set(child)
            if grand_children is not None:
                children.update(grand_children)
        return children

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def get_terminologies_metadata():
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    # 1) current-version.txt is tsv file provided by sibils in denver://D:/sibils/v3.2/terminologies
    # 1) current-version.txt is tsv file provided by sibils in denver://D:/users/emilie/terminologies/2023/current
    #    provides a mapping from terminology id (concept_source) to file name
    # 2) terminologies.psv: documentation file, copied manually 
    #    from the main table of https://github.com/sibils/techdoc/blob/master/docs/terminologies.md

    t_dict = dict()
    term_dir = "./terminologies/"
    file_name = term_dir + "current-version.txt"
    f_in = open(file_name)
    line_no=0
    log_it("INFO", "Reading", file_name)
    while True:
        line = f_in.readline()
        if line == "": break
        line_no += 1
        fields = line.strip().split("\t")
        if len(fields)!=2:
            log_it("ERROR, Unexpected number of fields at line", line_no)
            sys.exit()
        concept_source = fields[0]
        file_name = fields[1]

        # os.path.exists() is case INSENSITIVE on Mac, so we have to do something
        # a bit more complicated to know if the file exists or not
        file_exists = file_name in os.listdir(os.path.dirname(term_dir + file_name))
        if not file_exists:
            log_it("WARNING, terminology json file not found", file_name)
        t_dict[concept_source] = {
          "concept_source" : concept_source,
          "file_name" : file_name,
          "file_exists" : file_exists
        }
    f_in.close()

    #   | Name | Code | Type | Update / Version | Description | Link |  Concept_source |   
    # 0    1      2       3           4                5          6            7         8 
    file_name = "terminologies/terminologies.psv"
    f_in = open(file_name)
    f_in.readline() # skip first line with column names
    f_in.readline() # skip 2nd line with ------|----|--- ...
    line_no=2
    log_it("INFO", "Reading", file_name)
    while True:
        line = f_in.readline()
        if line == "": break
        line_no += 1
        fields = line.strip().split("|")
        if len(fields)!=9:
            log_it("FATAL", "Unexpected number of fields at line", line_no)
            sys.exit()
        name = fields[1].strip()
        version = fields[4].strip()
        descr = fields[5].strip()
        concept_source = fields[7].strip()
        if concept_source not in t_dict or not t_dict[concept_source]["file_exists"]:
            log_it("WARNING, identifier in terminology.psv does not match any json file", concept_source)
            continue
        t_dict[concept_source]["name"] = name
        t_dict[concept_source]["version"] = version
        t_dict[concept_source]["description"] = descr
    f_in.close()
    # set default values (name, descr, version) for items not found in documentation file
    for el in t_dict.values():
        if not el.get("name"):
            el["name"] = el["concept_source"]
            log_it("WARNING, no documentation for terminology, setting default name to", el["concept_source"])
        if not el.get("version"):
            el["version"] = "unknown"
            log_it("WARNING, no documentation for terminology, setting default version to", el["concept_source"])
        if not el.get("description"):
            el["description"] = ""

    #for k in t_dict: print(k, t_dict[k])

    return t_dict




# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def get_terminology_data(terminology_md):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    t0 = datetime.datetime.now()
    log_it("INFO", "Loading terminology from ", terminology_md["file_name"])
    pattern = terminology_md["file_name"]
    f_list = glob.glob("./terminologies/" + pattern)
    if len(f_list)!=1:
        log_it("ERROR", "json file not found", pattern)
        return None
    json_file = f_list[0]
    f_in = open(json_file, "rb")
    data = json.load(f_in)
    f_in.close()
    log_it("INFO", "Loaded terminology from ", terminology_md["file_name"], duration_since=t0)
    return data


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_prefixes():
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    lines = list()
    for ns in [sibilo, sibils, sibilc,rdf, rdfs, xsd, owl, skos]:
        lines.append(ns.getTtlPrefixDeclaration())
    return lines

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def save_rdf_for_terminology(data, terminology_md):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    log_it("INFO", "Collecting concepts from", terminology_md["concept_source"])

    # first create a set of all concepts defined in the terminology
    defined_concepts = set()
    for concept in data["concepts"]:
        defined_concepts.add(concept["id"])
    cpt_count = len(defined_concepts)
    log_it("INFO", "Collected", cpt_count, "concepts from", terminology_md["concept_source"])

    # initialize tree-like structure for concept transitive relationships
    parent_child_rel = TransitiveRelation()
    # comput IRI for terminology itself (used a lot below)
    termi_URI = get_terminology_URIRef(terminology_md) 

    # now iterate on defined concepts and RDFize each of them
    # we need to slice graph to avoid RAM problems (was true with first version using rdflib)
    max_per_file = 100000
    cpt_idx = -1
    unclosed = False
    file_name = None
    graph = None
    for concept in data["concepts"]:
        cpt_idx += 1
        # create new file and init graph each time cpt_idx % == 0
        if cpt_idx % max_per_file == 0:
            file_idx = int(cpt_idx / max_per_file)
            file_name = (output_dir + terminology_md["concept_source"] + "_" + str(file_idx) + ".ttl").replace(" ","_")
            f_out = open(file_name, "w")
            for pfx_line in get_prefixes(): f_out.write(pfx_line)
            f_out.write("\n")
            unclosed = True
        # generate triples foc current concept
        id = concept["id"]
        concept_URI = get_term_URIRef_from_term(id, terminology_md)
        
        f_out.write(getTriple(concept_URI, rdf.type(), skos.Concept(), SEMICOLON))
        f_out.write(getTriple(TAB, skos.inScheme(), termi_URI, SEMICOLON))
        f_out.write(getTriple(TAB, skos.notation(), xsd.string(id), SEMICOLON))
        f_out.write(getTriple(TAB, skos.prefLabel(), xsd.string(concept["preferred_term"]["term"]), SEMICOLON))
        for syn in concept["synonyms"]:
            f_out.write(getTriple(TAB, skos.altLabel(), xsd.string(syn["term"]), SEMICOLON))
        for parent_id in set(concept["parents"]):
            if parent_id not in defined_concepts:
                log_it("WARNING, ignored undefined parent concept", parent_id, "from", terminology_md["concept_source"])
                continue
            # INFO SKOS.broader means ?s "has broader concept" ?o
            # INFO skos property replaced with ours because less ambiguous
            #graph.add((concept_URI, SKOS.broader, get_term_URIRef_from_term(parent_id, terminology_md)))
            f_out.write(getTriple(TAB, sibilo.more_specific_than(), get_term_URIRef_from_term(parent_id, terminology_md), SEMICOLON))
            # INFO We forget about transitive relationships beween concepts for now, too costly
            #parent_child_rel.add_relation(parent_id, id)
        f_out.write(DOTLINE)

        # close file each time if contains N=max_per_file concepts
        if cpt_idx % max_per_file == max_per_file - 1:
            f_out.close()
            unclosed = False
    # save remaining concepts to be saved
    if unclosed:
        f_out.close()

    # NOTE for efficient queries about things related to a term T and terms more specific than T,
    # NOTE we don't use it for now
    if 1==2:
        max_per_file = 1000000
        trans_idx = -1
        unclosed = False
        file_name = None
        for parent_id in parent_child_rel.get_parent_set():
            parent_URI = get_term_URIRef_from_term(parent_id, terminology_md)
            for id in parent_child_rel.get_child_set(parent_id):
                trans_idx += 1
                if trans_idx % max_per_file == 0:
                    file_idx = int(trans_idx / max_per_file)
                    file_name = (output_dir + terminology_md["concept_source"] + "_trna_" + str(file_idx) + ".ttl").replace(" ","_")
                    f_out = open(file_name, "w")
                    for pfx_line in get_prefixes(): f_out.write(pfx_line)
                    f_out.write("\n")
                    unclosed = True
                child_URI = get_term_URIRef_from_term(id, terminology_md)
                f_out.write(getTriple(child_URI, sibilo.more_specific_than_transitive(), parent_URI))
                if trans_idx % max_per_file == max_per_file -1:
                    f_out.close()
                    unclosed = False
        if unclosed:
            f_out.close()
        log_it("###", "Added transitive narrower relationships from", terminology_md["concept_source"], trans_idx+1)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def save_rdf_for_terminology_ontology(terminologies_md):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    file_name = "./ontology/terminology-individuals.ttl"  
    log_it("###", "Serializing", file_name)
    f_out = open(file_name, "w")
    for pfx_line in get_prefixes(): f_out.write(pfx_line)
    f_out.write("\n")
    # remove final # of sibilo baseurl
    onto_IRI = sibilo.baseurl()
    if onto_IRI.endswith("#"): onto_IRI = onto_IRI[:-1]
    onto_IRI = "<" + onto_IRI + ">"
    # define class of sibils terminology: derived from skos ConceptScheme
    termi_class_URI = sibilo.SibilsTerminology()
    f_out.write(getTriple(termi_class_URI, rdf.type(), owl.Class(), SEMICOLON))
    f_out.write(getTriple(TAB, rdfs.subClassOf(), skos.ConceptScheme(), SEMICOLON))
    f_out.write(getTriple(TAB, rdfs.label(), xsd.string("SIBiLS Terminology"), SEMICOLON))
    f_out.write(getTriple(TAB, rdfs.comment(), xsd.string("SIBiLS Terminology scheme containing the concepts used for annotating the publications."), SEMICOLON))
    f_out.write(getTriple(TAB, rdfs.isDefinedBy(), onto_IRI, SEMICOLON))
    f_out.write(DOTLINE)
 
    for term_id in terminologies_md:
        meta_data = terminologies_md[term_id]
        if not meta_data["file_exists"]:
            log_it("WARNING", "No json file, skipping terminology", term_id)
            continue
        log_it("INFO", "Reading file for terminology", term_id)
        f_out.write("\n")
        termi_URI = get_terminology_URIRef(meta_data)
        f_out.write(getTriple(termi_URI, rdf.type(), owl.NamedIndividual(), COMMA))
        f_out.write(getTriple(TAB, TAB, termi_class_URI, SEMICOLON))
        label = meta_data["name"]
        f_out.write(getTriple(TAB, rdfs.label(), xsd.string(label), SEMICOLON))
        f_out.write(getTriple(TAB, sibilo.version(), xsd.string(meta_data["version"]), SEMICOLON))
        descr = meta_data.get("description")
        if descr is not None and len(descr)>0:
            f_out.write(getTriple(TAB, rdfs.comment(), xsd.string(descr), SEMICOLON))
        f_out.write(getTriple(TAB, rdfs.isDefinedBy(), onto_IRI, SEMICOLON))
        f_out.write(DOTLINE)

    f_out.close()
    log_it("###", "Serialized", file_name)




# --------------------------------------------------------------------------------
if __name__ == '__main__':
# --------------------------------------------------------------------------------

    output_dir = "./output/v3.3/"
    json_nl_dir = "./output/json.nl/"

    terminologies_md = get_terminologies_metadata()

    # - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - - 
    if "onto" in sys.argv or len(sys.argv)==1 :
    # - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - - 
        log_it("INFO", "Saving named individuals for terminologies to ./ontology directory...")
        save_rdf_for_terminology_ontology(terminologies_md)
        log_it("INFO", "Saved terminologies named individuals for terminologies to ./ontology directory")

    # - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - - 
    if "data" in sys.argv or len(sys.argv)==1 :
    # - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - - 
        log_it("INFO", "Saving terminologies to", output_dir, "directory...")
        for term_id in terminologies_md:
            meta_data = terminologies_md[term_id]
            if meta_data["file_exists"]:
                # if meta_data["concept_source"] != "go_bp": continue
                data = get_terminology_data(meta_data)
                save_rdf_for_terminology(data, meta_data)
            else:
                log_it("WARNING", "json file for",term_id, "not found, won't generate ttl file for it")
        log_it("INFO", "Saving terminologies to", output_dir, "DONE")

    # - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - - 
    if "json.nl" in sys.argv or len(sys.argv)==1 :
    # - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - - 
        log_it("INFO", "Saving terminologies to", output_dir, "directory...")
        for term_id in terminologies_md:
            meta_data = terminologies_md[term_id]
            if meta_data["file_exists"]:
                # if meta_data["concept_source"] != "go_bp": continue
                data = get_terminology_data(meta_data)
                #json.dump(date, fileToSave, ensure_ascii=True, indent=4, sort_keys=True)
                f_out=open(json_nl_dir + meta_data["name"] + ".json", "w")
                json.dump(data, fp=f_out, ensure_ascii=True, indent=4)
                f_out.close()
            else:
                log_it("WARNING", "json file for",term_id, "not found, won't generate ttl file for it")
        log_it("INFO", "Saving terminologies to", output_dir, "DONE")

    log_it("INFO", "End")
