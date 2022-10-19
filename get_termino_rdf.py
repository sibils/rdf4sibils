import sys
import json
import glob
import datetime
from rdflib import BNode, Literal, URIRef, Graph, Namespace
from rdflib.namespace import XSD,RDF, RDFS, OWL, SKOS
from get_publi_rdf import get_term_URIRef_from_term, get_terminology_URIRef, sibilc, sibilt, sibilo

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def get_terminologies():
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    t_list = list()
    file_name = "terminologies.tsv"
    f_in = open(file_name)
    line_no=0
    print("Reading", file_name)
    while True:
        line = f_in.readline()
        if line == "": break
        line_no += 1
        fields = line.strip().split("\t")
        if len(fields)!=4:
            print("Unexpected number of fields at line", line_no)
            sys.exit()
        t_list.append({
          "file_pattern" : fields[0],
          "term_type" : fields[1],
          "term_source" : fields[2]
        })
    f_in.close()
    return t_list


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def get_terminology_data(terminology):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    pattern = terminology["file_pattern"]
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
def save_rdf_for_terminology(data, terminology):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    graph = Graph()
    graph.bind("xsd", XSD)
    graph.bind("rdf", RDF)
    graph.bind("rdfs", RDFS)
    graph.bind("OWL", OWL)
    graph.bind("SKOS", SKOS)
    graph.bind("sibilt", sibilt)  # terminologies
    graph.bind("sibilc", sibilc)  # concepts

    # add triples related to the terminology features
    termi_URI = get_terminology_URIRef(terminology)
    graph.add((termi_URI, RDF.type, SKOS.ConceptScheme))
    label = terminology["term_source"] + " " + terminology["term_type"]
    graph.add((termi_URI, RDFS.label, Literal(label, datatype=XSD.string)))
    graph.add((termi_URI, sibilo.version, Literal(data["description"]["version"], datatype=XSD.string)))

    # first create a set of all concepts defined in the terminology
    defined_concepts = set()
    for concept in data["concepts"]:
        defined_concepts.add(concept["id"])

    # now iterate on defined concepts and RDFize each of them
    for concept in data["concepts"]:
        id = concept["id"]
        concept_URI = get_term_URIRef_from_term(id, terminology)
        graph.add((concept_URI, SKOS.inScheme, termi_URI))
        graph.add((concept_URI, RDF.type, SKOS.Concept))
        graph.add((concept_URI, SKOS.notation, Literal(id, datatype=XSD.string)))
        graph.add((concept_URI, SKOS.prefLabel, Literal(concept["preferred_term"]["term"], datatype=XSD.string)))
        for syn in concept["synonyms"]:
            graph.add((concept_URI, SKOS.altLabel, Literal(syn["term"], datatype=XSD.string)))
        for parent_id in concept["parents"]:
            if parent_id not in defined_concepts:
                print("Warning, ignored undefined parent concept", parent_id, "from", terminology["term_source"], terminology["term_type"])
                continue
            graph.add((concept_URI, SKOS.broader, get_term_URIRef_from_term(parent_id, terminology)))
            graph.add((get_term_URIRef_from_term(parent_id, terminology), SKOS.narrower, concept_URI))
    
    file_name = terminology["term_source"] + "_" + terminology["term_type"] + ".ttl"  
    file_name = file_name.replace(" ","_")     
    print("### Serializing", file_name)            
    t0 = datetime.datetime.now()
    graph.serialize(destination=file_name , format="turtle", encoding="utf-8")
    duration = datetime.datetime.now()-t0
    m,s = divmod(duration.seconds,60)
    print("duration:", m, "min", s, "seconds")





# --------------------------------------------------------------------------------
if __name__ == '__main__':
# --------------------------------------------------------------------------------
    terminologies = get_terminologies()
    for t in terminologies:
        print("Reading file for terminology", t["term_source"], t["term_type"])
        data = get_terminology_data(t)
        save_rdf_for_terminology(data, t)

        print("----")
    print("End")




