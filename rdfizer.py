import uuid

def getTtlPrefixDeclaration(prefix, baseurl):
    return "".join(["@prefix ", prefix, ": <", baseurl, "> .\n"])


# blank node label random generator
def getBlankNode():
    return "_:BN" + uuid.uuid4().hex

def getTriple(s, p, o, punctuation="."):
    return " ".join([s,p,o, punctuation, "\n"])


# namespace ancestor class 
# handles prefix and base URL
class BaseNamespace:
    def __init__(self, prefix, baseurl):
        self.pfx = prefix
        self.url = baseurl
    def prefix(self): return self.pfx
    def baseurl(self): return self.url
    def getTtlPrefixDeclaration(self): 
        return getTtlPrefixDeclaration(self.prefix(), self.baseurl())


class XsdNamespace(BaseNamespace):
    def __init__(self): 
        super(XsdNamespace, self).__init__("xsd", "http://www.w3.org/2001/XMLSchema#")

    def escape_string(self, str):
        # escape backslashes with double backslashes (\ => \\)
        str=str.replace("\\","\\\\")
        # escape double-quotes (" => \")
        str = str.replace("\"", "\\\"")
        return str

    # string datatype with triple quotes allow escape chars like \n \t etc.
    def string(self, str):
        return "".join(["\"", self.escape_string(str), "\"^^", self.prefix(), ":string"])

    def string3(self, str): 
        return "".join(["\"\"\"", self.escape_string(str), "\"\"\"^^", self.prefix(), ":string"])
    
    def date(self, str): 
        return "".join(["\"", str, "\"^^" + self.prefix() + ":date"])
    
    def integer(self, int): 
        return str(int)


class RdfNamespace(BaseNamespace):
    def __init__(self): super(RdfNamespace, self).__init__("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
    def type(self): return "rdf:type"
    def Property(self): return "rdf:Property"


class RdfsNamespace(BaseNamespace):
    def __init__(self): super(RdfsNamespace, self).__init__("rdfs", "http://www.w3.org/2000/01/rdf-schema#")
    def Class(self): return "rdfs:Class"
    def subClassOf(self): return "rdfs:subClassOf"
    def subPropertyOf(self): return "rdfs:subPropertyOf"
    def comment(self): return "rdfs:comment"
    def label(self): return "rdfs:label"
    def domain(self): return "rdfs:domain"
    def range(self): return "rdfs:range"
    def seeAlso(self): return "rdfs:seeAlso"
    def isDefinedBy(self): return "rdfs:isDefinedBy"


class OwlNamespace(BaseNamespace):
    def __init__(self): super(OwlNamespace, self).__init__("owl", "http://www.w3.org/2002/07/owl#")
    def Class(self): return "owl:Class"
    def DatatypeProperty(self): return "owl:DatatypeProperty"
    def FunctionalProperty(self): return "owl:FunctionalProperty"
    def NamedIndividual(self): return "owl:NamedIndividual"
    def ObjectProperty(self): return "owl:ObjectProperty"
    def TransitiveProperty(self): return "owl:TransitiveProperty"
    def allValuesFrom(self): return "owl:allValuesFrom"
    def sameAs(self): return "owl:sameAs"
    def unionOf(self): return "owl:unionOf"


class SkosNamespace(BaseNamespace):
    def __init__(self): super(SkosNamespace, self).__init__("skos", "http://www.w3.org/2004/02/skos/core#")
    def Concept(self): return "skos:Concept"
    def ConceptScheme(self): return "skos:ConceptScheme"
    def inScheme(self): return "skos:inScheme"
    def notation(self): return "skos:notation"
    def prefLabel(self): return "skos:prefLabel"
    def altLabel(self): return "skos:altLabel"


class FoafNamespace(BaseNamespace):
    def __init__(self): super(FoafNamespace, self).__init__("foaf", "http://xmlns.com/foaf/0.1/")
    def Person(self): return "foaf:Person"

# Sibils data namespace
class SibilsNamespace(BaseNamespace):
    def __init__(self): super(SibilsNamespace, self).__init__("sibils", "http://sibils.org/rdf/data/")
    def IRI(self, name): return "".join(["sibils:", name])


# Sibilc concept namespace
class SibilcNamespace(BaseNamespace):
    def __init__(self): super(SibilcNamespace, self).__init__("sibilc", "http://sibils.org/rdf/concept/")
    def IRI(self, name): return "".join(["sibilc:", name])




