import sys
import os
import json
import glob
import datetime
from rdflib import BNode, Literal, URIRef, Graph, Namespace
from rdflib.namespace import XSD,RDF, RDFS, OWL, SKOS
from get_publi_rdf_old import get_term_URIRef_from_term, get_terminology_URIRef, sibilc, sibilo, log_it


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

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def init_graph():
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    graph = Graph()
    graph.bind("xsd", XSD)
    graph.bind("rdf", RDF)
    graph.bind("rdfs", RDFS)
    graph.bind("owl", OWL)
    graph.bind("skos", SKOS)
    graph.bind("sibilc", sibilc)  # sibilis concepts
    graph.bind(prefix="", namespace=sibilo, override=True, replace=True)  # sibils core ontology
    return graph

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
    # we need to slice graph to avoid RAM problems
    max_per_file = 100000
    cpt_idx = -1
    unsaved = False
    file_name = None
    graph = None
    for concept in data["concepts"]:
        cpt_idx += 1
        # create new file and init graph each time cpt_idx % == 0
        if cpt_idx % max_per_file == 0:
            file_idx = int(cpt_idx / max_per_file)
            file_name = (output_dir + terminology_md["concept_source"] + "_" + str(file_idx) + ".ttl").replace(" ","_")
            unsaved = True
            graph = init_graph()
        # generate triples foc current concept
        id = concept["id"]
        concept_URI = get_term_URIRef_from_term(id, terminology_md)
        graph.add((concept_URI, SKOS.inScheme, termi_URI))
        graph.add((concept_URI, RDF.type, SKOS.Concept))
        graph.add((concept_URI, SKOS.notation, Literal(id, datatype=XSD.string)))
        graph.add((concept_URI, SKOS.prefLabel, Literal(concept["preferred_term"]["term"], datatype=XSD.string)))
        for syn in concept["synonyms"]:
            graph.add((concept_URI, SKOS.altLabel, Literal(syn["term"], datatype=XSD.string)))
        for parent_id in concept["parents"]:
            if parent_id not in defined_concepts:
                log_it("WARNING, ignored undefined parent concept", parent_id, "from", terminology_md["concept_source"])
                continue
            # INFO SKOS.broader means ?s "has broader concept" ?o
            # INFO skos property replaced with ours because less ambiguous
            #graph.add((concept_URI, SKOS.broader, get_term_URIRef_from_term(parent_id, terminology_md)))
            graph.add((concept_URI, sibilo.more_specific_than, get_term_URIRef_from_term(parent_id, terminology_md)))

            # INFO We forget about transitive relationships beween concepts for now, too costly
            #parent_child_rel.add_relation(parent_id, id)

        # save file each time if contains N=max_per_file concepts
        if cpt_idx % max_per_file == max_per_file - 1:
            serialize_graph(graph, file_name)
            unsaved = False
    # save remaining concepts to be saved
    if unsaved:
        serialize_graph(graph, file_name)

    # NOTE for efficient queries about things related to a term T and terms more specific than T,
    # NOTE we don't use it for now
    if 1==2:
        max_per_file = 1000000
        trans_idx = -1
        unsaved = False
        file_name = None
        graph = None
        for parent_id in parent_child_rel.get_parent_set():
            parent_URI = get_term_URIRef_from_term(parent_id, terminology_md)
            for id in parent_child_rel.get_child_set(parent_id):
                trans_idx += 1
                if trans_idx % max_per_file == 0:
                    file_idx = int(trans_idx / max_per_file)
                    file_name = (output_dir + terminology_md["concept_source"] + "_trna_" + str(file_idx) + ".ttl").replace(" ","_")
                    unsaved = True
                    graph = init_graph()
                child_URI = get_term_URIRef_from_term(id, terminology_md)
                graph.add((child_URI, sibilo.more_specific_than_transitive, parent_URI))
                #graph.add((child_URI, SKOS.broaderTransitive, parent_URI))
                if trans_idx % max_per_file == max_per_file -1:
                    serialize_graph(graph, file_name)
                    unsaved = False
        if unsaved:
            serialize_graph(graph, file_name)
        log_it("###", "Added transitive narrower relationships from", terminology_md["concept_source"], trans_idx+1)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def serialize_graph(graph, file_name):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    log_it("###", "Serializing", file_name)
    t0 = datetime.datetime.now()
    graph.serialize(destination=file_name , format="turtle", encoding="utf-8")
    log_it("###", "Serialized", file_name, duration_since=t0)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def save_rdf_for_terminology_ontology(terminologies_md):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    graph = init_graph()

    # define class of sibils terminology: derived from skos ConceptScheme    
    termi_class_URI = URIRef(sibilo.SibilsTerminology)
    graph.add((termi_class_URI, RDF.type, OWL.Class))
    graph.add((termi_class_URI, RDFS.subClassOf, SKOS.ConceptScheme))
    graph.add((termi_class_URI, RDFS.label, Literal("SIBiLS Terminology", datatype=XSD.string)))
    graph.add((termi_class_URI, RDFS.comment, Literal("SIBiLS Terminology scheme containing the concepts used for annotating the publications.", datatype=XSD.string)))
    graph.add((termi_class_URI, RDFS.isDefinedBy, URIRef(sibilo) ))

    for term_id in terminologies_md:
        meta_data = terminologies_md[term_id]
        if not meta_data["file_exists"]:
            log_it("WARNING", "No json file, skipping terminology", term_id)
            continue
        log_it("INFO", "Reading file for terminology", term_id)
        termi_URI = get_terminology_URIRef(meta_data)
        graph.add((termi_URI, RDF.type, OWL.NamedIndividual))
        graph.add((termi_URI, RDF.type, termi_class_URI))
        label = meta_data["name"]
        graph.add((termi_URI, RDFS.label, Literal(label, datatype=XSD.string)))
        graph.add((termi_URI, sibilo.version, Literal(meta_data["version"], datatype=XSD.string)))
        descr = meta_data.get("description")
        if descr is not None and len(descr)>0:
            graph.add((termi_URI, RDFS.comment, Literal(descr, datatype=XSD.string)))
        graph.add((termi_URI, RDFS.isDefinedBy, URIRef(sibilo) ))

    file_name = "./ontology/terminology-individuals.ttl"  
    log_it("###", "Serializing", file_name)
    graph.serialize(destination=file_name , format="turtle", encoding="utf-8")




# --------------------------------------------------------------------------------
if __name__ == '__main__':
# --------------------------------------------------------------------------------

    output_dir = "./output/v3.3/"

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

    log_it("INFO", "End")
