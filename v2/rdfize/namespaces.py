import hashlib
import urllib.parse
from api_platform import ApiPlatform
from namespace_term import Term


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# namespace ancestor class, handles prefix and base URL
class BaseNamespace:
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self, prefix, baseurl):
        self.pfx = prefix; self.url = baseurl; self.terms = dict()

    def getTtlPrefixDeclaration(self): return "".join(["@prefix ", self.pfx, ": <", self.url, "> ."])
    def getSparqlPrefixDeclaration(self): return "".join(["PREFIX ", self.pfx, ": <", self.url, "> "])
    def getSQLforVirtuoso(self): return f"insert into DB.DBA.SYS_XML_PERSISTENT_NS_DECL values ('{self.pfx}', '{self.url}');"

    def describe(self, subj_iri, prop_iri, value):
        #print(">>>", subj_iri, prop_iri,value)
        id = subj_iri.split(":")[1]
        t: Term = self.terms[id]
        if prop_iri not in t.props: t.props[prop_iri] = set()
        t.props[prop_iri].add(value)

    def term(self, iri) -> Term: 
        id = iri.split(":")[1]
        return self.terms.get(id)

    def registerTerm(self, id, p=None, v=None, hidden=False):
        if id not in self.terms: 
            t = Term(self.pfx, id, hidden)
            t.props["rdfs:isDefinedBy"] = { self.pfx + ":" }
            if p is not None and v is not None: t.props[p] = v
            self.terms[id] = t
        return self.terms[id].iri

    def registerNamedIndividual(self, id, label=None, comment=None, hidden=False):
        iri = self.registerTerm(id, p="rdf:type", v={ "owl:NamedIndividual" }, hidden=hidden)
        if label   is not None: self.describe(iri, "rdfs:label",   f"\"{label}\"")
        if comment is not None: self.describe(iri, "rdfs:comment", f"\"{comment}\"")
        return iri
    
    def registerClass(self, id, label=None, comment=None, hidden=False):
        iri = self.registerTerm(id, p="rdf:type", v={ "owl:Class" }, hidden=hidden)
        if label   is not None: self.describe(iri, "rdfs:label",   f"\"{label}\"")
        if comment is not None: self.describe(iri, "rdfs:comment", f"\"{comment}\"")
        return iri
    
    def registerProperty(self, id, hidden=False):
        return self.registerTerm(id, p="rdf:type", v={ "rdf:Property" }, hidden=hidden)

    def registerDatatypeProperty(self, id,   label=None, comment=None, hidden=False):
        iri = self.registerTerm(id, p="rdf:type", v={ "rdf:Property", "owl:DatatypeProperty" }, hidden=hidden)
        if label   is not None: self.describe(iri, "rdfs:label",   f"\"{label}\"")
        if comment is not None: self.describe(iri, "rdfs:comment", f"\"{comment}\"")
        return iri
    
    def registerObjectProperty(self, id,  label=None, comment=None, hidden=False):
        iri = self.registerTerm(id, p="rdf:type", v={ "rdf:Property", "owl:ObjectProperty" }, hidden=hidden)
        if label   is not None: self.describe(iri, "rdfs:label",   f"\"{label}\"")
        if comment is not None: self.describe(iri, "rdfs:comment", f"\"{comment}\"")
        return iri

    def registerAnnotationProperty(self, id,  label=None, comment=None, hidden=False):
        iri = self.registerTerm(id, p="rdf:type", v={ "rdf:Property", "owl:AnnotationProperty" }, hidden=hidden)
        if label   is not None: self.describe(iri, "rdfs:label",   f"\"{label}\"")
        if comment is not None: self.describe(iri, "rdfs:comment", f"\"{comment}\"")
        return iri


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class XsdNamespace(BaseNamespace):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self): 
        super(XsdNamespace, self).__init__("xsd", "http://www.w3.org/2001/XMLSchema#")
        self.dateDataType = self.registerTerm("date")

    def escape_string(self, str):
        str = str.replace("\\","\\\\")      # escape backslashes with double backslashes (\ => \\)
        str = str.replace("\"", "\\\"")     # escape double-quotes (" => \")
        return str
    def string(self, str):
        if '"' in str: return self.string3(str) # string datatype with triple quotes allow escape chars like \n \t etc.
        else: return self.string1(str)
    def string1(self, str): return "".join(["\"", self.escape_string(str), "\""])
    def string3(self, str): return "".join(["\"\"\"", self.escape_string(str), "\"\"\""])
    def date(self, str): return "".join(["\"", str, "\"^^xsd:date"])
    def integer(self, int_number): return str(int_number)
    def float(self, float_number): return "".join(["\"", str(float_number), "\"^^xsd:float"])
    def boolean(self, boolean_value): return str(boolean_value).lower() 


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class RdfNamespace(BaseNamespace):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self): 
        super(RdfNamespace, self).__init__("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
        self.type = self.registerTerm("type")
        self.Property = self.registerTerm("Property")


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class RdfsNamespace(BaseNamespace):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self): 
        super(RdfsNamespace, self).__init__("rdfs", "http://www.w3.org/2000/01/rdf-schema#")
        self.Class = self.registerTerm("Class", hidden=True)
        self.subClassOf = self.registerTerm("subClassOf", hidden=True)
        self.subPropertyOf = self.registerTerm("subPropertyOf", hidden=True)
        self.comment = self.registerTerm("comment", hidden=True)
        self.label = self.registerTerm("label", hidden=True)
        self.domain = self.registerTerm("domain", hidden=True)
        self.range = self.registerTerm("range", hidden=True)
        self.seeAlso = self.registerTerm("seeAlso", hidden=False)
        self.isDefinedBy = self.registerTerm("isDefinedBy", hidden=True)
        self.Literal = self.registerTerm("Literal", hidden=True)
        

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class OwlNamespace(BaseNamespace):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self): 
        super(OwlNamespace, self).__init__("owl", "http://www.w3.org/2002/07/owl#")
        self.Class  = self.registerTerm("Class")
        self.AnnotationProperty  = self.registerTerm("AnnotationProperty")
        self.DatatypeProperty  = self.registerTerm("DatatypeProperty")
        self.FunctionalProperty  = self.registerTerm("FunctionalProperty")
        self.NamedIndividual  = self.registerTerm("NamedIndividual")
        self.ObjectProperty  = self.registerTerm("ObjectProperty")
        self.TransitiveProperty  = self.registerTerm("TransitiveProperty")
        self.allValuesFrom  = self.registerTerm("allValuesFrom")
        self.sameAs  = self.registerTerm("sameAs")
        self.unionOf  = self.registerTerm("unionOf")
        self.equivalentClass  = self.registerTerm("equivalentClass")
        self.equivalentProperty  = self.registerTerm("equivalentProperty")
        self.versionInfo  = self.registerTerm("versionInfo")
        self.Ontology  = self.registerTerm("Ontology")
        self.inverseOf = self.registerTerm("inverseOf")



# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class SkosNamespace(BaseNamespace):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self): 
        super(SkosNamespace, self).__init__("skos", "http://www.w3.org/2004/02/skos/core#")
        #self.hiddenLabel = self.registerAnnotationProperty("hiddenLabel", comment="A hidden lexical label, represented by means of the skos:hiddenLabel property, is a lexical label for a resource, where a KOS designer would like that character string to be accessible to applications performing text-based indexing and search operations, but would not like that label to be visible otherwise. Hidden labels may for instance be used to include misspelled variants of other lexical labels.")
        self.Concept = self.registerTerm("Concept")
        self.ConceptScheme = self.registerTerm("ConceptScheme")
        self.inScheme = self.registerTerm("inScheme")
        self.notation = self.registerDatatypeProperty("notation", comment=" Notations are symbols which are not normally recognizable as words or sequences of words in any natural language and are thus usable independently of natural-language contexts. They are typically composed of digits, complemented with punctuation signs and other characters.")
        self.prefLabel = self.registerAnnotationProperty("prefLabel")
        self.altLabel = self.registerAnnotationProperty("altLabel")
        self.broader = self.registerObjectProperty("broader", label="has broader")
        self.broaderTransitive = self.registerObjectProperty("broaderTransitive", label="has broader transitive")
        self.exactMatch = self.registerTerm("exactMatch")
        self.closeMatch = self.registerTerm("closeMatch")
        self.broadMatch = self.registerTerm("broadMatch")


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class IAONamespace(BaseNamespace):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self): 
        super(IAONamespace, self).__init__("IAO", "http://purl.obolibrary.org/obo/IAO_")
        comment = "A (currently) primitive relation that relates an information artifact to an entity."
        self.is_about_0000136 = self.registerObjectProperty("0000136", label="is about", comment=comment)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class FrbrNamespace(BaseNamespace):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self): 
        super(FrbrNamespace, self).__init__("frbr", "http://purl.org/vocab/frbr/core#")

        # described as standalone
        self.embodiment = self.registerObjectProperty("embodiment", comment="Having a frbr:embodiment implies being something that, amongst other things, is a frbr:Expression")
        self.realizationOf = self.registerObjectProperty("realizationOf", comment=" Having a frbr:realizationOf implies being something that, amongst other things, is a frbr:Expression")


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class FabioNamespace(BaseNamespace):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self): 
        super(FabioNamespace, self).__init__("fabio", "http://purl.org/spar/fabio/")

        # described as standalone:
        self.hasPublicationYear = self.registerDatatypeProperty("hasPublicationYear", label="has publication year")
        self.Manifestation = self.registerClass("Manifestation", comment = """A subclass of FRBR manifestation, restricted to manifestations of fabio:Expressions. fabio:Manifestation specifically applies to electronic (digital) as well as to physical manifestations of expressions. """)
        self.Expression = self.registerClass("Expression")

        # described as subclasses of fabio:Expression
        self.Book = self.registerClass("Book")
        self.Chapter = self.registerClass("Chapter")
        self.BookChapter = self.registerClass("BookChapter")
        self.Thesis = self.registerClass("Thesis")
        self.BachelorsThesis = self.registerClass("BachelorsThesis", label = "Bachelor's thesis")
        self.MastersThesis = self.registerClass("MastersThesis", label = "Master's thesis")
        self.DoctoralThesis = self.registerClass("DoctoralThesis")
        self.Article = self.registerClass("Article")
        self.JournalArticle = self.registerClass("JournalArticle")
        self.SpecificationDocument = self.registerClass("SpecificationDocument")
        self.PatentDocument = self.registerClass("PatentDocument")
        self.ReportDocument = self.registerClass("ReportDocument")
        self.ProceedingsPaper = self.registerClass("ProceedingsPaper")
        self.ConferencePaper = self.registerClass("ConferencePaper")
        self.Letter = self.registerClass("Letter")
        comment = """Abstract as a publication in itself (more precisely a subclass of fabio:Expression). A brief summary of a work on a particular subject, designed to act as the point-of-entry that will help the reader quickly to obtain an overview of the work's contents. The abstract may be an integral part of the work itself, written by the same author(s) and appearing at the beginning of a work such as a research paper, report, review or thesis. Alternatively it may be separate from the published work itself, and written by someone other than the author(s) of the published work, for example by a member of a professional abstracting service such as CAB Abstracts."""
        self.Abstract = self.registerClass("Abstract", comment=comment)
        self.Comment = self.registerClass("Comment")
        self.NewsItem = self.registerClass("NewsItem")
        self.Editorial = self.registerClass("Editorial")
        self.ReviewArticle = self.registerClass("ReviewArticle")
        self.BriefReport = self.registerClass("BriefReport")
        self.Addendum = self.registerClass("Addendum")
        self.RapidCommunication = self.registerClass("RapidCommunication")
        self.LectureNotes = self.registerClass("LectureNotes")        

        # described as subclasses of fabio:Work
        self.Work = self.registerClass("Work")
        self.Report = self.registerClass("Report")
        self.CaseReport = self.registerClass("CaseReport")
        self.TrialReport = self.registerClass("TrialReport")
        self.ClinicalTrialReport = self.registerClass("ClinicalTrialReport")
        self.Review = self.registerClass("Review")
        self.SystematicReview = self.registerClass("SystematicReview")
        self.BookReview = self.registerClass("BookReview")
        self.ProductReview = self.registerClass("ProductReview")
        self.Correction = self.registerClass("Correction")
        self.Biography = self.registerClass("Biography")
        self.TechnicalReport = self.registerClass("TechnicalReport")        
        self.MeetingReport = self.registerClass("MeetingReport")    
        self.ScholarlyWork = self.registerClass("ScholarlyWork")
        self.MethodsPaper = self.registerClass("MethodsPaper")

        # described as subprop of dcterms:identifiers:
        self.hasNLMJournalTitleAbbreviation = self.registerDatatypeProperty("hasNLMJournalTitleAbbreviation", label = "has National Library of Medicine journal title abbreviation", comment="An internal identifier for the abbreviation of the title of journals available from the National Library of Medicine repository.")
        self.hasPubMedCentralId = self.registerDatatypeProperty("hasPubMedCentralId", label = "has PMC identifier", comment="PubMedCentral identifier for the resource.")
        self.hasPubMedId = self.registerDatatypeProperty("hasPubMedId", label = "has PubMed identifier", comment="PubMed identifier for the resource.")



# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class PrismNamespace(BaseNamespace):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # see also https://www.w3.org/submissions/prism/
    def __init__(self):                               
        super(PrismNamespace, self).__init__("prism", "http://prismstandard.org/namespaces/basic/2.0/")

        self.volume = self.registerDatatypeProperty("volume", comment="An identifier for a particular volume of a resource, such as a journal or a multi-volume book.")      # not hidden 
        self.hasDOI = self.registerDatatypeProperty("doi", label="has DOI")         # not hidden
        self.publicationDate = self.registerDatatypeProperty("publicationDate", label="has publication date", comment = "The date on which a resource is published or disclosed.")
        self.startingPage = self.registerDatatypeProperty("startingPage", comment="Identifies the first page of an entity such as a journal article." )              
        self.endingPage = self.registerDatatypeProperty("endingPage", comment="Identifies the last page of an entity such as a journal article." )    
        self.pageRange = self.registerDatatypeProperty("pageRange", hidden=False )    
        self.issueIdentifier = self.registerDatatypeProperty("issueIdentifier", hidden=False )    
        self.keyword = self.registerDatatypeProperty("keyword", hidden=False )    
        

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class UniProtCoreNamespace(BaseNamespace):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self): 
        super(UniProtCoreNamespace, self).__init__("up", "http://purl.uniprot.org/core/")

        self.Patent_Citation = self.registerClass("Patent_Citation")
        self.Thesis_Citation = self.registerClass("Thesis_Citation")
        self.Book_Citation = self.registerClass("Book_Citation", label="Book chapter citation")
        self.Journal_Citation = self.registerClass("Journal_Citation", label = "Journal article citation")    
        

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class ShaclNamespace(BaseNamespace):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self): 
        super(ShaclNamespace, self).__init__("sh", "http://www.w3.org/ns/shacl#")
        self.declare = self.registerTerm("declare")
        self._prefix = self.registerTerm("prefix")
        self.namespace = self.registerTerm("namespace")



# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class CntNamespace(BaseNamespace):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self): 
        super(CntNamespace, self).__init__("cnt", "http://www.w3.org/2011/content#")
        self.chars = self.registerDatatypeProperty("chars", label="Character sequence", comment="The character sequence of the text content.")


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class OaNamespace(BaseNamespace):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self): 
        super(OaNamespace, self).__init__("oa", "http://www.w3.org/ns/oa#")

        self.Annotation = self.registerClass("Annotation", comment="The class for Web Annotations.")
        self.SpecificResource = self.registerClass("SpecificResource", comment="Instances of the SpecificResource class identify part of another resource (referenced with oa:hasSource), a particular representation of a resource, a resource with styling hints for renders, or any combination of these, as used within an Annotation.")
        self.TextPositionSelector = self.registerClass("TextPositionSelector", comment="The TextPositionSelector describes a range of text by recording the start and end positions of the selection in the stream. Position 0 would be immediately before the first character, position 1 would be immediately before the second character, and so on.")
        self.start = self.registerDatatypeProperty("start", comment="Position of the first character of a range of text in a discourse element.")
        self.end = self.registerDatatypeProperty("end", comment="Position of the last character of a range of text in a discourse element.")
        self.exact = self.registerDatatypeProperty("exact", comment="Text representing the annotated concept as found in the discourse element.")
        self.hasBody = self.registerDatatypeProperty("hasBody", comment="The object of the relationship is a resource that is a body of the Annotation.")
        self.hasSelector = self.registerDatatypeProperty("hasSelector", comment="The object of the relationship is a Selector that describes the segment or region of interest within the source resource.  Please note that the domain ( oa:ResourceSelection ) is not used directly in the Web Annotation model.")
        self.hasSource = self.registerDatatypeProperty("hasSource", comment="The resource that the ResourceSelection, or its subclass SpecificResource, is refined from, or more specific than. Please note that the domain ( oa:ResourceSelection ) is not used directly in the Web Annotation model.")
        self.hasTarget = self.registerDatatypeProperty("hasTarget", comment="The relationship between an Annotation and its Target.")


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class SibilsNamespace(BaseNamespace): # Sibils data namespace (for publi, publi parts, ...)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self, platform: ApiPlatform): super(SibilsNamespace, self).__init__("sibils", platform.get_rdf_base_IRI() + "/data/")
    def IRI(self, name): 
        return ":".join([self.pfx, name])


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class SibilcNamespace(BaseNamespace): # Sibilc concept entities namespace
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self, platform: ApiPlatform): 
        super(SibilcNamespace, self).__init__("sibilc", platform.get_rdf_base_IRI() + "/concept/")
    

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class OurTerminologyNamespace(BaseNamespace): # sibilt terminology entities namespace
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self, platform: ApiPlatform): 
        super(OurTerminologyNamespace, self).__init__("sibilt", platform.get_rdf_base_IRI() + "/scheme/")


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class SibiloNamespace(BaseNamespace):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self, platform: ApiPlatform): 
        super(SibiloNamespace, self).__init__("sibilo", platform.get_rdf_base_IRI() + "/ontology/" )

        # derived from deo:DiscourseElement
        self.TableFooter = self.registerClass("TableFooter", comment = "Text appearing at the bottom of a table.")
        self.FloatMatter = self.registerClass("FloatMatter", comment = "Floating part of a document related to some aspect of the body section. Usually in a box with its own body with some title and / or caption.")
        self.ListItemBlock = self.registerClass("ListItemBlock", comment = "A list item part of a document. Usually appears multiple time in a sequence. May be prefixed with a bullet or a number.")
        self.MediaBlock = self.registerClass("MediaBlock", comment = "A reference or link to some media (audio, video) part of a document.")
        self.ObjectIdBlock = self.registerClass("ObjectIdBlock", comment = "An identifier appearing as a distinct part of a document.")
        self.SpeechBlock = self.registerClass("SpeechBlock", comment = "A dialog or part of dialog appearing as a distinct part of a document.")
        self.StatementBlock = self.registerClass("StatementBlock", comment = "A statement appearing as a distinct part of a document.")
        self.TableCellValues = self.registerClass("TableCellValues", comment = "A concatenation of the values found in the cells of a table separated with a space.") 
        self.TableColumnName = self.registerClass("TableColumnName", comment = "The name given to of a column in a table.")
        self.VerseGroupBlock = self.registerClass("VerseGroupBlock", comment = "A block containing one or several verses appearing as a distinct part of a document.")
        self.WordSequence = self.registerClass("WordSequence", comment = "A super class for sentences, table column names, table cell values or any textual item that is part of a list")

        # local only
        self.ordinal = self.registerDatatypeProperty("ordinal", comment = "Relative order of appearance of a sentence in the publication. A sentence right after another one usually have an ordinal incremented by 1 but the orginal value can sometimes be arbitrary, for instance between body contents and some floating content.")
        self.hasAnnotation = self.registerObjectProperty("hasAnnotation", comment="Links a publication to an annotation generated by named entity extraction.")

        # derived from oa
        self.NexAnnotation = self.registerClass("NexAnnotation", "Named Entity Extraction Annotation", "A concept identified at a specific position in a discourse element of a publication by a named entity extraction process.")
        self.AnnotationTarget = self.registerClass("AnnotationTarget", comment="Target of an annotation: a text selection within a subpart of a publication")    

        # derived from skos
        self.more_specific_than = self.registerObjectProperty("more_specific_than", comment = "Links two concepts. The subject concept is more specific than the object concept. The semantics is the similar to the skos:broader property but its label less ambiguous.")
        self.more_specific_than_transitive = self.registerObjectProperty("more_specific_than_transitive")
 
        # derived from schema
        self.inCollection = self.registerAnnotationProperty("inCollection", comment = "Within the SIBiLS RDF dataset, publications are grouped into two distinct collections, each reflecting the source from which they were obtained: 'pmc' or 'medline'.")

        # derived from rdfs
        self.seeAlsoAnnotated = self.registerAnnotationProperty("seeAlsoAnnotated", comment = "Provides a link to a URI where the annotated publication can be viewed.")


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class PoNamespace(BaseNamespace):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self): 
        super(PoNamespace, self).__init__("po", "http://www.essepuntato.it/2008/12/pattern#")

        # not necessary (deo:DiscourseElement is probably enough)
        # comment = "This class organise the document content as a sequence of nestable elements and text nodes.")
        # self.Block = self.registerClass("Block", comment = comment)  # unused

        # see https://sparontologies.github.io/doco/current/doco.html for subtle diff between po:contains / dcterms:hasPart
        self.contains = self.registerObjectProperty("contains", comment = "A structured element contains another generic element.") # used as is ?


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class DeoNamespace(BaseNamespace):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self): 
        super(DeoNamespace, self).__init__("deo", "http://purl.org/spar/deo/")

        self.DiscourseElement = self.registerClass("DiscourseElement", comment = "An element of a document that carries out a rhetorical function.") 
        self.Caption = self.registerClass("Caption", comment = "Caption of a text box.")


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class DocoNamespace(BaseNamespace):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self): 
        super(DocoNamespace, self).__init__("doco", "http://purl.org/spar/doco/")

        self.Abstract = self.registerClass("Abstract", comment = "Abstract as a part of a publication (or fabio:Expression). A brief summary of a book, a research article, thesis, review, conference proceeding or any in-depth analysis of a particular subject or discipline, the purpose of which is to help the reader quickly ascertain the publication's purpose.")
        self.Appendix = self.registerClass("Appendix", comment = "A supplemental addition to the main work. It may contain data, more detailed information about methods and materials, or provide additional detail concerning the information found in the main work.")
        self.BackMatter = self.registerClass("BackMatter", comment = "The final principle part of a document, in which is usually found the bibliography, index, appendixes, etc.")
        self.BlockQuotation = self.registerClass("BlockQuotation", comment = "A block quotation (also known as a long quotation or extract) is a quotation in a written document which is set off from the main text as a container for distinct paragraphs, which is typically distinguished visually using indentation, a different font, or smaller size. Block quotations are used for longer passages than run-in quotations (which are set off with quotation marks).")
        self.BodyMatter = self.registerClass("BodyMatter", comment = "The central principle part of a document, that contains the real content. It may be subdivided hierarchically by the use of chapters and sections.")
        self.CaptionedBox = self.registerClass("CaptionedBox", comment = "A rectangle space within a page that contains an object and its related caption.")
        self.FigureBox = self.registerClass("FigureBox", comment = "A space within a document that contains a figure and its caption.")
        self.FrontMatter = self.registerClass("FrontMatter", comment = "The initial principle part of a document, usually containing self-referential metadata. In a book, this typically includes its title, authors, publisher, publication date, ISBN and copyright declaration, together with the preface, foreword, table of content, etc. In a journal article, the front matter is normally restricted to the title, authors and the authors' affiliation details, although the latter may alternatively be included in a footnote or the back matter. In books, the front matter pages may be numbered in lowercase Roman numerals.")
        self.Glossary = self.registerClass("Glossary", comment = "A set of definitions of words or phrases of importance to the work, normally alphabetized. In longer works of fiction, the entries may contains places and characters.")
        self.Label = self.registerClass("Label", comment = """A block containing text, that may include a number (e.g., "Chapter Three", "3.2", "Figure 1", "Table"), used to identify an item within the document, for example a chapter, a figure, a section or a table.""")
        self.ListOfReferences = self.registerClass("ListOfReferences", comment = "A list of items each representing a reference to a specific part of the same document, or to another publication.")
        self.Paragraph = self.registerClass("Paragraph", comment = "A self-contained unit of discourse that deals with a particular point or idea. Paragraphs contains one or more sentences. The start of a paragraph is indicated by beginning on a new line, which may be indented or separated by a small vertical space by the preceding paragraph.")
        self.Section = self.registerClass("Section", comment = "A logical division of the text, usually numbered and/or titled, which may contain subsections.")
        self.SectionLabel = self.registerClass("SectionLabel", comment = "A block containing a label for the section, that may include the section number.")
        self.Sentence = self.registerClass("Sentence", comment = "An expression in natural language forming a single grammatical unit. A sentence minimally consists of a subject and an intransitive verb, or a subject, a transitive verb and an object, and may include additional dependent clauses. In written text, a sentence is always terminated by a full stop. A sentence can include words grouped meaningfully to express a statement, a question, an exclamation, a request or a command.")
        self.Table = self.registerClass("Table", comment = "A set of data arranged in cells within rows and columns.")
        self.TableBox = self.registerClass("TableBox", comment = "A space within a document that contains a table and its caption.")
        self.TextBox = self.registerClass("TextBox", comment = "A space within a document that contains textual content relating to, quoting from or expanding upon the main text. Usually a textbox is delimited by a border or use of a background colour distinct from that of the main text.")
        self.Title = self.registerClass("Title", comment = "A word, phrase or sentence that precedes and indicates the subject of a document or a document component - e.g., a book, a report, a news article, a chapter, a section or a table.")
        self.ListOfAgents = self.registerClass("ListOfAgents")
        self.ListOfOrganizations = self.registerClass("ListOfOrganizations", comment="A list of items each denoting an agent, such as an author, a contributor or an organization, related to a particular publication.")
        self.ListOfAuthors = self.registerClass("ListOfAuthors")
        self.List = self.registerClass("List", comment="List of items")


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class SchemaOrgNamespace(BaseNamespace):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self): 
        super(SchemaOrgNamespace, self).__init__("schema", "https://schema.org/")
        #self.location = self.registerDatatypeProperty("location")     # unused
        self.memberOf = self.registerObjectProperty("memberOf")        # parent for affiliation
        self.Organization = self.registerClass("Organization")
        self.Person = self.registerClass("Person")
        #self.provider = self.registerObjectProperty("provider")       # unused
        self.category = self.registerDatatypeProperty("category")
        self.name = self.registerDatatypeProperty("name")
        self.affiliation = self.registerObjectProperty("affiliation", comment="An organization that this person is affiliated with. For example, a school/university, a club, or a team.")


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class DctermsNamespace(BaseNamespace):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self): 
        super(DctermsNamespace, self).__init__("dcterms", "http://purl.org/dc/terms/")
        #self.source =       self.registerObjectProperty("source", hidden=False)        # unused
        #self.references =   self.registerAnnotationProperty("references", hidden=True) # unused
        self.created =      self.registerDatatypeProperty("created", hidden=True)       # hidden: only used in widoco descr of ontology
        self.modified =     self.registerDatatypeProperty("modified", hidden=True)      # hidden: only used in widoco descr of ontology
        self.description =  self.registerDatatypeProperty("description", hidden=True)   # hidden: only used in widoco descr of ontology
        self.license =      self.registerDatatypeProperty("license", hidden=True)       # hidden: only used in widoco descr of ontology
        self.publisher =    self.registerObjectProperty("publisher", hidden=True)       # hidden: only used in widoco descr of ontology
        self.bibliographicCitation = self.registerAnnotationProperty(
            "bibliographicCitation", hidden=True)                                       # hidden: only used in widoco descr of ontology
        self.hasVersion =   self.registerDatatypeProperty("hasVersion", hidden=False)   # visible, used to describe terminologies 
        self.abstract =     self.registerDatatypeProperty("abstract", hidden=False)     # used as is
        self.title =        self.registerDatatypeProperty("title", hidden=False)        # used as is
        self.creator =      self.registerObjectProperty("creator", hidden=False)        # used as is
        self.contributor =  self.registerObjectProperty("contributor", hidden=False)    # shown, as superprop of creator
        self.identifier =   self.registerDatatypeProperty("identifier", hidden=False)   # shown, as a superclass of other terms
        # see https://sparontologies.github.io/doco/current/doco.html for subtle diff between po:contains / dcterms:hasPart
        comment="Links a resource that is included either physically or logically in the described resource."
        self.hasPart = self.registerObjectProperty("hasPart", comment=comment) 


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class VannNamespace(BaseNamespace): # hidden in ontology_builder
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self): 
        super(VannNamespace, self).__init__("vann", "http://purl.org/vocab/vann/")                  # hidden, only describes onto
        self.preferredNamespacePrefix = self.registerTerm("preferredNamespacePrefix", hidden=True) 


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class BiboNamespace(BaseNamespace): # hidden in ontology_builder
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self): 
        super(BiboNamespace, self).__init__("bibo", "http://purl.org/ontology/bibo/")           # hidden, only describes onto
        self.status = self.registerTerm("status", hidden=True)                                     
        

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class WidocoNamespace(BaseNamespace): # hidden in ontology_builder
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self): 
        super(WidocoNamespace, self).__init__("widoco", "https://w3id.org/widoco/vocab#")         # hidden, only describes onto
        self.introduction = self.registerTerm("introduction")
        self.rdfxmlSerialization = self.registerTerm("rdfxmlSerialization")
        self.turtleSerialization = self.registerTerm("turtleSerialization")
        self.ntSerialization = self.registerTerm("ntSerialization")
        self.jsonldSerialization = self.registerTerm("jsonldSerialization")

                

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class HelpNamespace(BaseNamespace):                                                             # hidden, only describes onto
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self, platform: ApiPlatform): 
        super(HelpNamespace, self).__init__("help", platform.get_help_base_IRI() + "/")
    def IRI(self, page): return "help:" + page


