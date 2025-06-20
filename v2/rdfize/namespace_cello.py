from namespaces import BaseNamespace
from api_platform import ApiPlatform

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class CelloOntologyNamespace(BaseNamespace):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self, platform: ApiPlatform): 
        super(CelloOntologyNamespace, self).__init__("cello", platform.get_rdf_base_IRI() + "/ontology/")

        #
        # Classes
        #

        self.Database = self.registerClass("Database")                          # described

        comment="Class of cellosaurus terminologies containing some concepts used for annotating cell lines."
        self.CelloConceptScheme = self.registerClass("CelloConceptScheme", label="Cellosaurus Concept Scheme", comment=comment)      # described
        
        # self.Organization = self.registerClass("Organization")                  # described, defined in schema namespace

        self.Xref = self.registerClass("Xref", "Cross-Reference")                                  # described as NCIT:C43621 subclass

        #
        # Properties
        #

        # publication properties
        # see also https://sparontologies.github.io/fabio/current/fabio.html
        # see also https://sibils.text-analytics.ch/doc/api/sparql/sibils-ontology.html

        self.internalId = self.registerDatatypeProperty("internalId", label="internal identifier")              # described as sub dcterms:identifier

        self.pmcId = self.registerDatatypeProperty("pmcId", label="PMCID")                                      # described as sub prop of fabio:haspmcid which is a subprop of dcterms:identifier
        self.pmid = self.registerDatatypeProperty("pmid", label="PMID")                                         # described as sub prop of fabio:haspmid which is a subprop of dcterms:identifier
        self.publicationYear = self.registerDatatypeProperty("publicationYear", label="publication year")       # described as sub prop of fabio:hasPublicationYear

        self.issn13 = self.registerDatatypeProperty("issn13", label="ISSN13")                                   # described as sub dcterms:identifier

        comment="An identifier for a particular volume of a resource, such as a journal or a multi-volume book."
        self.volume = self.registerDatatypeProperty("volume", comment=comment)             # described as sub of prism:volume which is sub of dcterms:identifier  
        self.doi = self.registerDatatypeProperty("doi", label="DOI")                # described as sub of prism:volume which is sub of dcterms:identifier
        self.publicationDate = self.registerDatatypeProperty("publicationDate", label="publication date")   # described as sub of prism term
        self.startingPage = self.registerDatatypeProperty("startingPage" )                                      # described as sub of prism term
        self.endingPage = self.registerDatatypeProperty("endingPage")                                           # described as sub of prism term

        # journal abbreviation, see also:
        # https://ftp.ncbi.nih.gov/pubmed/J_Medline.txt
        # https://en.wikipedia.org/wiki/ISO_4

        # described as sub dcterms:identifier: # Amos uses abbreviation also used by UniProt based on ISO4
        self.iso4JournalTitleAbbreviation = self.registerDatatypeProperty(                                       # described, see line above
            "iso4JournalTitleAbbreviation", label="ISO4 Journal Title Abbreviation") 
        
        self.title = self.registerDatatypeProperty("title")                             # defined as sub prop of dcterms
        self.creator = self.registerObjectProperty("creator")                            # defined as sub prop of dcterms equivalent
        self.publisher = self.registerObjectProperty("publisher")                        # sdefined as sub prop of dcterms equivalent
        
        self.editor = self.registerObjectProperty("editor")                                                         # described as sub of dcterms:contributor


        comment = "Unique identifier for an entity in a database."
        self.accession = self.registerDatatypeProperty("accession", comment=comment)                                # described as subProp of dcterms:identifier
        
        comment = "A human-readable version of a resource's name."
        self.name = self.registerAnnotationProperty("name", comment=comment)                                          # described, as sub prop of rdfs:label


        comment="A database cross-reference that is referenced, cited, or otherwise pointed to with the purpose to provide further information about the described resource"
        self.seeAlsoXref = self.registerAnnotationProperty("seeAlsoXref", label="see also xref", comment=comment)         # defined as sub prop of rdfs:seeAlso

        comment="A database cross-reference that is referenced, cited, or otherwise pointed to with the purpose to unequivocally identify the described resource."
        self.isIdentifiedByXref = self.registerAnnotationProperty("isIdentifiedByXref", label="is identified by xref", comment=comment)         # defined as sub prop of rdfs:seeAlso

        comment="An IRI that is referenced, cited, or otherwise pointed to with the purpose to unequivocally identify the described resource."
        self.isIdentifiedByIRI = self.registerAnnotationProperty("isIdentifiedByIRI", label="is identified by IRI", comment=comment)         # defined as sub prop of rdfs:seeAlso


        self.bookTitle = self.registerDatatypeProperty("bookTitle")                                                 # described as sub dcterms:title
        self.conferenceTitle = self.registerDatatypeProperty("conferenceTitle")                                     # described as sub dcterms:title
        self.documentTitle = self.registerDatatypeProperty("documentTitle")                                         # described as sub dcterms:title
        self.documentSerieTitle = self.registerDatatypeProperty("documentSerieTitle")                               # described as sub dcterms:title
        

        self.version = self.registerDatatypeProperty("version")                                                    # described as sub of dcterms term
        self.created = self.registerDatatypeProperty("created")                                                     # described as sub of dcterms term
        self.modified = self.registerDatatypeProperty("modified")                                                   # described as sub of dcterms term

        self.database = self.registerObjectProperty("database")                                                     # TODO: later
        
        comment="Links two concepts where he subject concept is more specific than the object concept. The semantics is similar to skos:broader."
        self.more_specific_than = self.registerObjectProperty("more_specific_than", comment=comment)                # described as equivalent of skos:broader
        