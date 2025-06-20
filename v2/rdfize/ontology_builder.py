import sys
from datetime import datetime
from namespace_term import Term
from namespace_registry import NamespaceRegistry
from ApiCommon import log_it, split_string
from api_platform import ApiPlatform
from sparql_client import EndpointClient
from tree_functions import Tree


#-------------------------------------------------
class OntologyBuilder:
#-------------------------------------------------

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def __init__(self, platform: ApiPlatform, ns: NamespaceRegistry, describe_ranges_and_domains=True):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

        # - - - - - - - - - - - - - - - - - - - - - - - - - - -         
        # load info from data_in used later by describe...() functions
        # - - - - - - - - - - - - - - - - - - - - - - - - - - -         
        self.platform = platform
        self.ns = ns
        self.prefixes = list()
        for space in self.ns.namespaces: self.prefixes.append(space.getTtlPrefixDeclaration())
        lines = list()
        for space in self.ns.namespaces: lines.append(space.getSparqlPrefixDeclaration())
        rqPrefixes = "\n".join(lines)

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        # store queries used to retrieve ranges and domains of properties from sparql endpoint
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        self.client = EndpointClient(platform.get_builder_sparql_service_IRI(), self.ns)
        self.domain_query_template = rqPrefixes + """
            select ?prop ?value (count(distinct ?s) as ?count) where {
                values ?prop { $prop }
                ?s ?prop ?o .
                ?s rdf:type ?value .
            } group by ?prop ?value"""        
        self.range_query_template = rqPrefixes + """
            select  ?prop ?value (count(*) as ?count) where {
                values ?prop { $prop }
                ?s ?prop ?o .
                optional { ?o rdf:type ?cl . }
                BIND(
                IF (bound(?cl) , ?cl,  IF ( isIRI(?o), 'rdfs:Resource', datatype(?o))
                ) as ?value)
            } group by ?prop ?value"""


        self.setup_domains_ranges_to_remove()
        self.describe_terms()
        if describe_ranges_and_domains: self.describe_ranges_and_domains()


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def setup_domains_ranges_to_remove(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        ns = self.ns

        self.rdfs_domain_to_remove = dict()
        #self.rdfs_domain_to_remove[ns.cello.accession] = { ns.skos.Concept }
        #self.rdfs_domain_to_remove[ns.cello.database] = { ns.skos.Concept  }
        #self.rdfs_domain_to_remove[ns.cello.more_specific_than] = { ns.cello.Xref  }

        self.rdfs_range_to_remove = dict()
        #self.rdfs_range_to_remove[ns.cello.seeAlsoXref] = { ns.skos.Concept }
        #self.rdfs_range_to_remove[ns.cello.isIdentifiedByXref] = { ns.skos.Concept }
        #self.rdfs_range_to_remove[ns.cello.more_specific_than] = { ns.cello.Xref } 
        #self.rdfs_range_to_remove[ns.cello.database] = { ns.owl.NamedIndividual, ns.cello.CelloConceptScheme } 
        

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def build_class_tree(self, local_only=False):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        ns = self.ns
        # NOW build tree with (local) child - parent relationships based on rdfs:subClassOf()
        edges = dict()
        relevant_namespaces = ns.namespaces
        if local_only: relevant_namespaces = [ ns.cello ]
        for space in relevant_namespaces:
            for term_id in space.terms:
                term: Term = space.terms[term_id]
                if not term.isA(ns.owl.Class): continue
                for parent_iri in term.props.get(ns.rdfs.subClassOf) or set():
                    if parent_iri.startswith(ns.cello.pfx) or not local_only:
                        #print("DEBUG tree", term.iri, "has parent", parent_iri)
                        if term.iri in edges:
                            log_it(f"WARNING, multiple parents for {term.iri}:  parent {edges[term.iri]} replaced with {parent_iri}")
                        edges[term.iri] = parent_iri
        self.tree = Tree(edges)



    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def describe_ranges_and_domains(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        self.build_class_tree()
        ns = self.ns
        for term_id in ns.cello.terms:
            term: Term = ns.cello.terms[term_id]
            if not term.isA(ns.rdf.Property): continue
            # gather domain classes
            log_it("DEBUG", "querying prop_name", term.iri, "domains")
            domain_dic = dict()
            domain_query = self.domain_query_template.replace("$prop", term.iri)
            response = self.client.run_query(domain_query)
            if not response.get("success"):
                log_it("ERROR", response.get("error_type"))
                log_it(response.get("error_msg"))
                sys.exit(2)
            rows = response.get("results").get("bindings")
            for row in rows:
                value = self.client.apply_prefixes(row.get("value").get("value"))
                count = int(row.get("count").get("value"))
                domain_dic[value]=count

            # simplify domain
            domain_set1 = set(domain_dic.keys())
            if len(domain_set1)>3: 
                domain_set = self.tree.get_close_parent_set(domain_set1)
            else:
                domain_set = set(domain_set1)
            for domain_to_remove in self.rdfs_domain_to_remove.get(term.iri) or {}:
                domain_set = domain_set - { domain_to_remove }
            # DEBUG CODE
            # if domain_set1 != domain_set:
            #     print("domain simplified for", term_id)
            #     print("simplified :", domain_set)
            #     print("original   :", domain_set1)

            # gather range datatypes / classes
            log_it("DEBUG", "querying prop_name", term.iri, "ranges")
            range_dic = dict()
            range_query = self.range_query_template.replace("$prop", term.iri)
            response = self.client.run_query(range_query)
            if not response.get("success"):
                log_it("ERROR", response.get("error_type"))
                log_it(response.get("error_msg"))
                sys.exit(2)
            rows = response.get("results").get("bindings")
            for row in rows:
                value = self.client.apply_prefixes(row.get("value").get("value"))
                count = int(row.get("count").get("value"))
                range_dic[value]=count
            # ttl comment about domain classes found in data
            domain_comments = list()
            tmp = list()
            for k in domain_dic: tmp.append(f"{k}({domain_dic[k]})")
            for line in split_string(" ".join(tmp), 90):
                domain_comments.append("#   domain classes found in data: " + line)

            # simplify ranges
            range_set = set(range_dic.keys())
            if len(range_set)>3:
                range_set = self.tree.get_close_parent_set(range_set)
            # hack to replace xsd:date with rdfs:Literal to be OWL2 frienly                    
            if ns.xsd.dateDataType in range_set:
                range_set = range_set - { ns.xsd.dateDataType }
                range_set.add(ns.rdfs.Literal)
            for range_to_remove in self.rdfs_range_to_remove.get(term.iri) or {}:
                range_set = range_set - { range_to_remove } 
            # ttl comment about prop range
            range_comments = list()
            tmp = list()
            for k in range_dic: tmp.append(f"{k}({range_dic[k]})")
            for line in split_string(" ".join(tmp), 90):
                range_comments.append("#   range entities found in data: " + line)
            # check prop type
            prop_types = set() # we should have a single item in this set (otherwise OWL reasoners dislike it)
            for r in range_dic:
                if r.startswith("xsd:") or r == ns.rdfs.Literal: prop_types.add("owl:DatatypeProperty") 
                else: prop_types.add("owl:ObjectProperty") 
            if len(prop_types) != 1: 
                log_it("ERROR", term.iri, "has not one and only one type", prop_types)
            else:
                declared_types = term.props.get(ns.rdf.type) # also includes rdf:Property
                found_type = prop_types.pop()
                if found_type not in declared_types and ns.owl.AnnotationProperty not in declared_types: 
                    log_it("ERROR", term.iri, f"range declaration {declared_types} does not match data {found_type}")
                        
            for domain in domain_set: ns.describe(term.iri, ns.rdfs.domain, domain)
            for comment in domain_comments: ns.describe(term.iri, "domain_comments", comment)
            for range in range_set: ns.describe(term.iri, ns.rdfs.range, range)
            for comment in range_comments: ns.describe(term.iri, "range_comments", comment)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def describe_terms(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        ns = self.ns

        #
        # Classes
        #

        # Hierarchy based on fabio Expression
        ns.describe( ns.fabio.Book,                     ns.rdfs.subClassOf, ns.fabio.Expression)
        ns.describe( ns.fabio.BookChapter,              ns.rdfs.subClassOf, ns.fabio.Expression)
        ns.describe( ns.fabio.JournalArticle,           ns.rdfs.subClassOf, ns.fabio.Expression)
        ns.describe( ns.fabio.PatentDocument,           ns.rdfs.subClassOf, ns.fabio.Expression)
        ns.describe( ns.fabio.ReportDocument,           ns.rdfs.subClassOf, ns.fabio.Expression)
        ns.describe( ns.fabio.ConferencePaper,          ns.rdfs.subClassOf, ns.fabio.Expression)
        ns.describe( ns.fabio.Thesis,                   ns.rdfs.subClassOf, ns.fabio.Expression)
        ns.describe( ns.fabio.BachelorsThesis,          ns.rdfs.subClassOf, ns.fabio.Thesis)
        ns.describe( ns.fabio.MastersThesis,            ns.rdfs.subClassOf, ns.fabio.Thesis)
        ns.describe( ns.fabio.DoctoralThesis,           ns.rdfs.subClassOf, ns.fabio.Thesis)

        ns.describe( ns.fabio.ClinicalTrialReport,      ns.rdfs.subClassOf, ns.fabio.Expression)
        ns.describe( ns.fabio.CaseReport,               ns.rdfs.subClassOf, ns.fabio.Expression)
        ns.describe( ns.fabio.Review,                   ns.rdfs.subClassOf, ns.fabio.Expression)
        ns.describe( ns.fabio.Letter,                   ns.rdfs.subClassOf, ns.fabio.Expression)
        ns.describe( ns.fabio.Abstract,                 ns.rdfs.subClassOf, ns.fabio.Expression)
        ns.describe( ns.fabio.Comment,                  ns.rdfs.subClassOf, ns.fabio.Expression)
        ns.describe( ns.fabio.Article,                  ns.rdfs.subClassOf, ns.fabio.Expression)
        ns.describe( ns.fabio.Report,                   ns.rdfs.subClassOf, ns.fabio.Expression)
        ns.describe( ns.fabio.NewsItem,                 ns.rdfs.subClassOf, ns.fabio.Expression)
        ns.describe( ns.fabio.Editorial,                ns.rdfs.subClassOf, ns.fabio.Expression)
        ns.describe( ns.fabio.Biography,                ns.rdfs.subClassOf, ns.fabio.Expression)
        ns.describe( ns.fabio.TechnicalReport,          ns.rdfs.subClassOf, ns.fabio.Expression)
        ns.describe( ns.fabio.SystematicReview,         ns.rdfs.subClassOf, ns.fabio.Expression)


        # Relationships with UniProt
        ns.describe( ns.fabio.BookChapter,              ns.skos.closeMatch, ns.up.Book_Citation)  # book citation is for book chapter !
        ns.describe( ns.fabio.JournalArticle,           ns.skos.closeMatch, ns.up.Journal_Citation )
        ns.describe( ns.fabio.PatentDocument,           ns.skos.closeMatch, ns.up.Patent_Citation)
        ns.describe( ns.fabio.Thesis,                   ns.skos.closeMatch, ns.up.Thesis_Citation)
        ns.describe( ns.fabio.BachelorsThesis,          ns.skos.broadMatch, ns.up.Thesis_Citation)
        ns.describe( ns.fabio.MastersThesis,            ns.skos.broadMatch, ns.up.Thesis_Citation)
        ns.describe( ns.fabio.DoctoralThesis,           ns.skos.broadMatch, ns.up.Thesis_Citation)

        ns.describe( ns.sibils2.TableFooter, ns.rdfs.subClassOf, ns.deo.DiscourseElement)
        ns.describe( ns.deo.Caption, ns.rdfs.subClassOf, ns.deo.DiscourseElement)

        ns.describe( ns.doco.Abstract, ns.rdfs.subClassOf, ns.deo.DiscourseElement)
        ns.describe( ns.doco.Appendix, ns.rdfs.subClassOf, ns.deo.DiscourseElement)
        ns.describe( ns.doco.BackMatter, ns.rdfs.subClassOf, ns.deo.DiscourseElement)
        ns.describe( ns.doco.BodyMatter, ns.rdfs.subClassOf, ns.deo.DiscourseElement)
        ns.describe( ns.sibils2.FloatMatter, ns.rdfs.subClassOf, ns.deo.DiscourseElement)
        ns.describe( ns.doco.CaptionedBox, ns.rdfs.subClassOf, ns.deo.DiscourseElement)
        ns.describe( ns.doco.FrontMatter, ns.rdfs.subClassOf, ns.deo.DiscourseElement)
        ns.describe( ns.doco.Label, ns.rdfs.subClassOf, ns.deo.DiscourseElement)
        ns.describe( ns.doco.Glossary, ns.rdfs.subClassOf, ns.deo.DiscourseElement)               
        ns.describe( ns.doco.FigureBox, ns.rdfs.subClassOf, ns.deo.DiscourseElement)              
        ns.describe( ns.doco.BlockQuotation, ns.rdfs.subClassOf, ns.deo.DiscourseElement)         
        ns.describe( ns.doco.ListOfReferences, ns.rdfs.subClassOf, ns.deo.DiscourseElement)       
        ns.describe( ns.doco.Paragraph, ns.rdfs.subClassOf, ns.deo.DiscourseElement)              
        ns.describe( ns.doco.ListItemBlock, ns.rdfs.subClassOf, ns.deo.DiscourseElement)          

        ns.describe( ns.doco.Section, ns.rdfs.subClassOf, ns.deo.DiscourseElement)
        ns.describe( ns.doco.SectionLabel, ns.rdfs.subClassOf, ns.deo.DiscourseElement)
        ns.describe( ns.doco.TextBox, ns.rdfs.subClassOf, ns.deo.DiscourseElement)
        ns.describe( ns.doco.Title, ns.rdfs.subClassOf, ns.deo.DiscourseElement)

        ns.describe( ns.doco.Table, ns.rdfs.subClassOf, ns.deo.DiscourseElement)                  
        ns.describe( ns.doco.TableBox, ns.rdfs.subClassOf, ns.deo.DiscourseElement)               

        ns.describe( ns.sibils2.WordSequence, ns.rdfs.subClassOf, ns.deo.DiscourseElement)
        ns.describe( ns.doco.Sentence, ns.rdfs.subClassOf, ns.sibils2.WordSequence)              
        ns.describe( ns.sibils2.TableCellValues, ns.rdfs.subClassOf, ns.sibils2.WordSequence)    
        ns.describe( ns.sibils2.TableColumnName, ns.rdfs.subClassOf, ns.sibils2.WordSequence)    

        ns.describe( ns.sibils2.MediaBlock, ns.rdfs.subClassOf, ns.deo.DiscourseElement)          
        ns.describe( ns.sibils2.ObjectIdBlock, ns.rdfs.subClassOf, ns.deo.DiscourseElement)       
        ns.describe( ns.sibils2.SpeechBlock, ns.rdfs.subClassOf, ns.deo.DiscourseElement)         
        ns.describe( ns.sibils2.StatementBlock, ns.rdfs.subClassOf, ns.deo.DiscourseElement)      
        ns.describe( ns.sibils2.VerseGroupBlock, ns.rdfs.subClassOf, ns.deo.DiscourseElement)     

        ns.describe( ns.sibils2.NexAnnotation, ns.rdfs.subClassOf, ns.oa.Annotation)
        ns.describe( ns.sibils2.AnnotationTarget, ns.rdfs.subClassOf, ns.oa.SpecificResource)
        

        #
        # Properties
        #
        ns.describe(ns.sibils2.more_specific_than, ns.rdfs.subPropertyOf, ns.skos.broader)
        ns.describe(ns.sibils2.more_specific_than_transitive, ns.rdfs.subPropertyOf, ns.skos.broaderTransitive)

        ns.describe(ns.schema.affiliation, ns.rdfs.subPropertyOf, ns.schema.memberOf)
        ns.describe(ns.schema.name, ns.owl.equivalentProperty, ns.dcterms.title)

        ns.describe(ns.fabio.hasNLMJournalTitleAbbreviation, ns.rdfs.subPropertyOf, ns.dcterms.identifier)
        ns.describe(ns.fabio.hasPubMedCentralId, ns.rdfs.subPropertyOf, ns.dcterms.identifier)
        ns.describe(ns.fabio.hasPubMedId, ns.rdfs.subPropertyOf, ns.dcterms.identifier)





    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_onto_header(self, version="alpha"):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        ns = self.ns

        lines = list()

        # set last modification date for ontology
        now = datetime.now()
        date_string = now.strftime("%Y-%m-%d")
        
        # set ontology URL
        onto_url = "<" + self.get_onto_url() + ">"
        
        # set ontology abstract
        # appears in abstract onto page
        onto_abstract = open('html.templates/onto_abstract.md', 'r').read()
        onto_abstract = onto_abstract.replace("$public_sparql_URL", self.platform.get_public_sparql_service_IRI())

        # set ontology introduction
        # appears in onto page, section 1
        # TODO: pam approach
        onto_intro = open('html.templates/onto_intro.md', 'r').read()
        onto_intro = onto_intro.replace("$cello_url", ns.cello.url)
        onto_intro = onto_intro.replace("$cvcl_url", ns.cvcl.url)
        onto_intro = onto_intro.replace("$orga_url", ns.orga.url)
        onto_intro = onto_intro.replace("$db_url", ns.db.url)
        onto_intro = onto_intro.replace("$xref_url", ns.xref.url)

        # set ontology description
        # appears in onto page, section 3 under webowl
        # TODO: pam approach
        onto_descr = open('html.templates/onto_descr.md', 'r').read()
        
        # Note: all the prefixes are declared in namespace.py but not necessarily all the properties because used only once...
        lines.append(onto_url)
        lines.append("    a " + ns.owl.Ontology + " ;")
        lines.append("    " + ns.rdfs.label + " " + ns.xsd.string("Cellosaurus ontology") + " ;")
        lines.append("    " + ns.dcterms.created + " " + ns.xsd.date("2025-03-30") + " ;")
        lines.append("    " + ns.dcterms.modified + " " + ns.xsd.date(date_string) + " ;")
        lines.append("    " + ns.dcterms.description + " " + ns.xsd.string3(onto_descr) + " ;")
        lines.append("    " + ns.dcterms.license + " <http://creativecommons.org/licenses/by/4.0> ;")
        lines.append("    " + ns.dcterms.title + " " + ns.xsd.string("Cellosaurus ontology") + " ;")

        version = " - ".join([version, str(datetime.now()), self.platform.platform_key])

        lines.append("    " + ns.dcterms.hasVersion + " " + ns.xsd.string(version) + " ;")
        lines.append("    " + ns.owl.versionInfo + " " + ns.xsd.string(version) + " ;")
        lines.append("    " + ns.dcterms.abstract + " " + ns.xsd.string3(onto_abstract) + " ;")
        lines.append("    " + ns.vann.preferredNamespacePrefix + " " + ns.xsd.string(self.platform.get_onto_preferred_prefix()) + " ;")
        #lines.append("    " + ns.bibo.status + " <http://purl.org/ontology/bibo/status/published> ;")
        lines.append("    " + ns.bibo.status + " <http://purl.org/ontology/bibo/status/draft> ;")
        lines.append("    " + ns.widoco.introduction + " " + ns.xsd.string3(onto_intro) + " ;")
        lines.append("    " + ns.rdfs.seeAlso + " " + ns.help.IRI("rdf-ontology") + " ;")   
        lines.append("    " + ns.widoco.rdfxmlSerialization + " " + ns.help.IRI("ontology.owl") + " ;")      
        lines.append("    " + ns.widoco.ntSerialization + " " + ns.help.IRI("ontology.nt") + " ;")      
        lines.append("    " + ns.widoco.turtleSerialization + " " + ns.help.IRI("ontology.ttl") + " ;")      
        lines.append("    " + ns.widoco.jsonldSerialization + " " + ns.help.IRI("ontology.jsonld") + " ;")
        lines.append("    " + ns.dcterms.contributor + " " + "<https://orcid.org/0000-0003-2826-6444>" + " ;")
        lines.append("    " + ns.dcterms.contributor + " " + "<https://orcid.org/0000-0002-0819-0473>" + " ;")
        lines.append("    " + ns.dcterms.contributor + " " + "<https://orcid.org/0000-0002-7023-1045>" + " ;")
        lines.append("    " + ns.dcterms.creator + " " + "<https://orcid.org/0000-0002-7023-1045>" + " ;")
        lines.append("    " + ns.dcterms.publisher + " " + "<https://www.sib.swiss>" + " ;")
        lines.append("    " + ns.dcterms.bibliographicCitation + " " + ns.xsd.string("(to be defined)") + " ;")
        

        # shacl declaration of prefixes for void tools        
        for elem in ns.namespaces:
            lines.append("    " + ns.sh.declare + " [ ")
            pfx = elem.pfx
            if pfx == "": pfx = "cello"
            lines.append("        " + ns.sh._prefix  + " " + ns.xsd.string(pfx) + " ;")
            lines.append("        " + ns.sh.namespace  + " " + ns.xsd.string(elem.url) + " ;")
            lines.append("    ] ;")
        lines.append("    .")
        lines.append("")

        # lines.append("<https://orcid.org/0000-0003-2826-6444>")
        # lines.append("    " + "<http://www.w3.org/ns/org#memberOf>" + " " + "<https://www.sib.swiss>" + " ;")
        # lines.append("    " + "<http://xmlns.com/foaf/0.1/name>" + " " + ns.xsd.string("Amos Bairoch") + " ;")
        # lines.append("    .")

        # lines.append("")
        # lines.append("<https://orcid.org/0000-0002-0819-0473>")
        # lines.append("    " + "<http://www.w3.org/ns/org#memberOf>" + " " + "<https://www.sib.swiss>" + " ;")
        # lines.append("    " + "<http://xmlns.com/foaf/0.1/name>" + " " + ns.xsd.string("Paula Duek") + " ;")
        # lines.append("    .")

        # lines.append("")
        # lines.append("<https://orcid.org/0000-0002-7023-1045>")
        # lines.append("    " + "<http://www.w3.org/ns/org#memberOf>" + " " + "<https://www.sib.swiss>" + " ;")
        # lines.append("    " + "<http://xmlns.com/foaf/0.1/name>" + " " + ns.xsd.string("Pierre-André Michel") + " ;")
        # lines.append("    .")

        lines.append("")
        return lines





    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_onto_url(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        onto_url = self.ns.cello.url
        if onto_url.endswith("#"): onto_url = onto_url[:-1]
        return onto_url

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_onto_prefixes(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        return self.prefixes


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_imported_terms(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        ns = self.ns
        lines = list()
        
        allButCello = list(ns.namespaces)
        
        # remove basic ones
        allButCello.remove(ns.xsd)
        allButCello.remove(ns.rdf)
        allButCello.remove(ns.rdfs)
        allButCello.remove(ns.owl)
        allButCello.remove(ns.sh)
        allButCello.remove(ns.widoco)
        #allButCello.remove(ns.dcterms) # only some terms are hidden for the moment
        
        # remove namespaces for our data
        allButCello.remove(ns.cello)
        allButCello.remove(ns.cvcl)
        allButCello.remove(ns.db)
        allButCello.remove(ns.orga)
        allButCello.remove(ns.xref)
        
        # remove irrelevant ones
        allButCello.remove(ns.pubmed)

        for nspace in allButCello: lines.extend(self.get_terms(nspace))
        return lines
    

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_terms(self, nspace, owlType=None):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        lines = list()
        for id in nspace.terms:
            term: Term = nspace.terms[id]
            if owlType is None or term.isA(owlType):
                term_lines = self.ns.ttl_lines_for_ns_term(term)
                lines.extend(term_lines)
        return lines
    
    
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_onto_terms(self, owlType=None):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        return self.get_terms(self.ns.cello, owlType)
    

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_onto_pretty_ttl_lines(self, version):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        ns = self.ns
        lines = list()    
        lines.extend(self.get_onto_prefixes())
        lines.append("\n#\n# Ontology properties\n#\n")
        lines.extend(self.get_onto_header(version))
        lines.append("#\n# External terms used in ontology\n#\n")
        lines.extend(self.get_imported_terms())
        lines.append("#\n# Classes defined in ontology\n#\n")
        lines.extend(self.get_onto_terms(ns.owl.Class))
        lines.append("#\n# Annotation Properties used in ontology\n#\n")
        lines.extend(self.get_onto_terms(ns.owl.AnnotationProperty))
        lines.append("#\n# Object Properties used in ontology\n#\n")
        lines.extend(self.get_onto_terms(ns.owl.ObjectProperty))
        lines.append("#\n# Datatype Properties used in ontology\n#\n")
        lines.extend(self.get_onto_terms(ns.owl.DatatypeProperty))
        lines.extend(self.get_topic_and_topic_annotations())
        return lines


# =============================================
if __name__ == '__main__':
# =============================================
    platform = ApiPlatform("local")
    ns = NamespaceRegistry(platform)
    ob = OntologyBuilder(platform, ns)
    lines = ob.get_onto_pretty_ttl_lines("dev version")
    for l in lines: print(l)
