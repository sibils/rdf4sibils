import uuid
import urllib.parse


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def getBlankNode():
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    return "_:BN" + uuid.uuid4().hex


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# OK for sibils version 3.2 (not retro-compatible with v2.x)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_term_URIRef_from_annot(ns, annot):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    db = get_terminology_NI_name(annot["concept_source"])
    concept_id = annot["concept_id"]
    return get_term_URIRef_from_dbac(ns, db, concept_id)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# OK for sibils version 3.2 (not retro-compatible with v2.x)
# derive a NamedIndividual name for a terminology from its corresponding concept_source
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_terminology_NI_name(concept_source):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    return concept_source.replace(" ","_").upper()


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_term_URIRef_from_dbac(ns, db, concept_id):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    ac = concept_id.replace(":","_")
    name = db + "_" +ac
    if db in ["CHEBI", "ECO", "ENVO", "GO_BP", "GO_CC", "GO_MF"]: name = ac
    encoded_name = urllib.parse.quote(name)
    return ns.sibilc.IRI(encoded_name)


#-------------------------------------------------
class TripleList:
#-------------------------------------------------
    def __init__(self):
        self.lines = list()
    def append(self, s, p, o, punctuation="."):
        line = " ".join([s,p,o, punctuation, "\n"])
        self.lines.append(line)
    def extend(self, triple_list):
        self.lines.extend(triple_list.lines)


