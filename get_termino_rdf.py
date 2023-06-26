import sys
import os
import json
import glob
import datetime
from rdflib import BNode, Literal, URIRef, Graph, Namespace
from rdflib.namespace import XSD,RDF, RDFS, OWL, SKOS
from get_publi_rdf import get_term_URIRef_from_term, get_terminology_URIRef, sibilc, sibilo


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class TransitiveRelation:
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

    relation_dict = dict()

    def __init__(self):
        self.relation_dict = dict()
        print("### TransitiveRelation init()")

    def add_relation(self, a,b):
        if a not in self.relation_dict: self.relation_dict[a] = set()
        self.relation_dict[a].add(b)

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
    #    provides a mapping from terminology id (concept_source) to file name
    # 2) terminologies.psv: documentation file, copied manually 
    #    from the main table of https://github.com/sibils/techdoc/blob/master/docs/terminologies.md

    t_dict = dict()
    term_dir = "terminologies/"
    file_name = term_dir + "current-version.txt"
    f_in = open(file_name)
    line_no=0
    print("Reading", file_name)
    while True:
        line = f_in.readline()
        if line == "": break
        line_no += 1
        fields = line.strip().split("\t")
        if len(fields)!=2:
            print("ERROR, Unexpected number of fields at line", line_no)
            sys.exit()
        concept_source = fields[0]
        file_name = fields[1]
        file_exists = os.path.exists(term_dir + fields[1])
        if not file_exists:
            print("WARNING, terminology json file not found", file_name)
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
    line_no=0
    print("Reading", file_name)
    while True:
        line = f_in.readline()
        if line == "": break
        line_no += 1
        fields = line.strip().split("|")
        if len(fields)!=9:
            print("Unexpected number of fields at line", line_no)
            sys.exit()
        name = fields[1].strip()
        version = fields[4].strip()
        descr = fields[5].strip()
        concept_source = fields[7].strip()
        if concept_source not in t_dict or not t_dict[concept_source]["file_exists"]:
            print("WARNING, identifier in terminology.psv does not match any json file", concept_source)
            continue
        t_dict[concept_source]["name"] = name
        t_dict[concept_source]["version"] = version
        t_dict[concept_source]["description"] = descr
    f_in.close()
    # set default values (name, descr, version) for items not found in documentation file
    for el in t_dict.values():
        if not el.get("name"):
            el["name"] = el["concept_source"]
            print("WARNING, no documentation for terminology, setting default name to", el["concept_source"])
        if not el.get("version"):
            el["version"] = "unknown"
            print("WARNING, no documentation for terminology, setting default version to", el["concept_source"])
        if not el.get("description"):
            el["description"] = ""

    for k in t_dict:
        print(k, t_dict[k])

    return t_dict




# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def get_terminology_data(terminology_md):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    pattern = terminology_md["file_name"]
    f_list = glob.glob("./terminologies/" + pattern)
    if len(f_list)!=1:
        print("Error, json file not found", pattern)
        return None
    json_file = f_list[0]
    f_in = open(json_file, "rb")
    data = json.load(f_in)
    f_in.close()
    return data


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def save_rdf_for_terminology(data, terminology_md):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    graph = Graph()
    graph.bind("xsd", XSD)
    graph.bind("rdf", RDF)
    graph.bind("rdfs", RDFS)
    graph.bind("owl", OWL)
    graph.bind("skos", SKOS)
    graph.bind("sibilc", sibilc)  # sibilis concepts
    graph.bind(prefix="", namespace=sibilo, override=True, replace=True)  # sibils core ontology

    # first create a set of all concepts defined in the terminology
    defined_concepts = set()
    for concept in data["concepts"]:
        defined_concepts.add(concept["id"])

    # initialize tree-like structure for concept transitive relationships
    narrower_rel = TransitiveRelation()

    # now iterate on defined concepts and RDFize each of them
    termi_URI = get_terminology_URIRef(terminology_md) 
    for concept in data["concepts"]:
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
                print("Warning, ignored undefined parent concept", parent_id, "from", terminology_md["concept_source"])
                continue
            graph.add((concept_URI, SKOS.broader, get_term_URIRef_from_term(parent_id, terminology_md)))
            graph.add((get_term_URIRef_from_term(parent_id, terminology_md), SKOS.narrower, concept_URI))
            narrower_rel.add_relation(parent_id, id)
    
    # now add transitive narrower relationships
    trans_cnt=0
    for parent_id in narrower_rel.get_parent_set():
        for id in narrower_rel.get_child_set(parent_id):
            trans_cnt += 1
            graph.add((get_term_URIRef_from_term(parent_id, terminology_md), SKOS.narrowerTransitive, get_term_URIRef_from_term(id, terminology_md)))
    print("### added transitive narrower relationships", trans_cnt)

    file_name = "./output/" + terminology_md["concept_source"] + ".ttl"  
    file_name = file_name.replace(" ","_")     
    print("### Serializing", file_name)            
    t0 = datetime.datetime.now()
    graph.serialize(destination=file_name , format="turtle", encoding="utf-8")
    duration = datetime.datetime.now()-t0
    m,s = divmod(duration.seconds,60)
    print("duration:", m, "min", s, "seconds")


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def save_rdf_for_terminology_ontology(terminologies_md):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    graph = Graph()
    graph.bind("xsd", XSD)
    graph.bind("rdf", RDF)
    graph.bind("rdfs", RDFS)
    graph.bind("owl", OWL)
    graph.bind("skos", SKOS)
    graph.bind(prefix="", namespace=sibilo, override=True, replace=True)  # sibils core ontology

    # define class of sibils terminology: derived from skos ConceptScheme    
    termi_class_URI = URIRef(sibilo.SibilsTerminology)
    graph.add((termi_class_URI, RDF.type, OWL.Class))
    graph.add((termi_class_URI, RDFS.subClassOf, SKOS.ConceptScheme))
    graph.add((termi_class_URI, RDFS.label, Literal("SIBiLS Terminology", datatype=XSD.string)))
    graph.add((termi_class_URI, RDFS.comment, Literal("SIBiLS Terminology scheme containing the concepts used for annotating the publications.", datatype=XSD.string)))
    graph.add((termi_class_URI, RDFS.isDefinedBy, URIRef(sibilo) ))

    for term_id in terminologies_md:
        print("Reading file for terminology", term_id)
        meta_data = terminologies_md[term_id]
        if not meta_data["file_exists"]: continue
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
    print("### Serializing", file_name)            
    graph.serialize(destination=file_name , format="turtle", encoding="utf-8")




# --------------------------------------------------------------------------------
if __name__ == '__main__':
# --------------------------------------------------------------------------------

    terminologies_md = get_terminologies_metadata()

    # - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - - 
    if "onto" in sys.argv or len(sys.argv)==1 :
    # - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - - 
        print("Saving named individuals for terminologies to ./ontology directory...")
        save_rdf_for_terminology_ontology(terminologies_md)
        print("Saving terminologies named individuals for terminologies to ./ontology DONE")

    # - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - - 
    if "data" in sys.argv or len(sys.argv)==1 :
    # - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - -  - - 
        print("Saving terminologies to ./output directory...")
        for term_id in terminologies_md:
            meta_data = terminologies_md[term_id]
            print("Reading file for terminology", term_id)
            if meta_data["file_exists"]:
                data = get_terminology_data(meta_data)
                save_rdf_for_terminology(data, meta_data)
            else:
                print("WARNING, json file for",term_id, "not found, won't generate ttl file for it")
        print("Saving terminologies to ./output DONE")

    print("End")
