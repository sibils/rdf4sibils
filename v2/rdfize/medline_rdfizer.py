from ApiCommon import log_it
from rdf_utils import TripleList, getBlankNode
from namespace_registry import NamespaceRegistry
from publi_rdfizer import PubliRdfizer

class MedlineRdfizer(PubliRdfizer):


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def __init__(self, ns: NamespaceRegistry, publi): 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        super().__init__(ns, publi)
        self.rank = 0


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_publi_id(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        return self.publi["document"]["pmid"]


   # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_publi_URIRef(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        publi_id = self.get_publi_id()
        if publi_id is None: return None
        return self.ns.sibils.IRI(publi_id)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_body_matter_URIRef(self, publi_uri):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        return publi_uri + "_part_bodyMatter"


   # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_next_rank(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        self.rank += 1
        return self.rank
    

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_sentence_part_URIRef(self, publi_uri, rank):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        return publi_uri + "_sen_" + str(rank)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_publi_expression_class_URIRef(self, publication_types):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -    
        ns = self.ns
        for article_type in publication_types:
            # Note: "Retracted Publication", "Published erratum" are handled in get_ttl_for_publi()
            if article_type == "Journal Article":               return ns.fabio.JournalArticle          # Expression
            if article_type == "Introductory Journal Article":  return ns.fabio.JournalArticle          # Expression
            if article_type == "Clinical Trial":                return ns.fabio.ReportDocument          # realizationOf ClinicalTrialReport
            if article_type == "Randomized Controlled Trial":   return ns.fabio.ReportDocument          # realizationOf ClinicalTrialReport
            if article_type == "Clinical Trial, Phase I":       return ns.fabio.ReportDocument          # realizationOf ClinicalTrialReport
            if article_type == "Clinical Trial, Phase II":      return ns.fabio.ReportDocument          # realizationOf ClinicalTrialReport
            if article_type == "Clinical Trial, Phase III":     return ns.fabio.ReportDocument          # realizationOf ClinicalTrialReport
            if article_type == "Case Reports":                  return ns.fabio.ReportDocument          # realizationOf ClinicalTrialReport
            if article_type == "Review":                        return ns.fabio.ReviewArticle           # Expression
            if article_type == "Letter":                        return ns.fabio.Letter                  # Expression
            if article_type == "English Abstract":              return ns.fabio.Abstract                # Expression
            if article_type == "Comment":                       return ns.fabio.Comment                 # Expression
            if article_type == "Historical Article":            return ns.fabio.Article                 # Expression
            if article_type == "Classical Article":             return ns.fabio.Article                 # Expression
            if article_type == "Corrected and Republished Article":  return ns.fabio.Article            # Expression      
            if article_type == "Comparative Study":             return ns.fabio.ReportDocument          # realizationOf Report 
            if article_type == "Clinical Study":                return ns.fabio.ReportDocument          # realizationOf Report
            if article_type == "Multicenter Study":             return ns.fabio.ReportDocument          # realizationOf Report
            if article_type == "Evaluation Study":              return ns.fabio.ReportDocument          # realizationOf Report
            if article_type == "Observational Study":           return ns.fabio.ReportDocument          # realizationOf Report
            if article_type == "Validation Study":              return ns.fabio.ReportDocument          # realizationOf Report
            if article_type == "Twin Study":                    return ns.fabio.ReportDocument          # realizationOf Report
            if article_type == "Meta-Analysis":                 return ns.fabio.ReportDocument          # realizationOf Report
            if article_type == "News":                          return ns.fabio.NewsItem                # Expression
            if article_type == "Editorial":                     return ns.fabio.Editorial               # Expression
            if article_type == "Biography":                     return ns.fabio.Expression              # realizationOf Biography
            if article_type == "Autobiography":                 return ns.fabio.Expression              # realizationOf Biography
            if article_type == "Technical Report":              return ns.fabio.ReportDocument          # realizationOf TechnicalReport
            if article_type == "Systematic Review":             return ns.fabio.ReviewArticle           # realizationOf SystematicReview
            if article_type == "Lecture":                       return ns.fabio.LectureNotes            # Expression
            if article_type.startswith("Research Support"):     return ns.fabio.Expression              # Expression

        publi_id = self.get_publi_id()
        print(f"ERROR, unexpected article_type in publication with id={publi_id}, using default Expression class:", article_type)
        return ns.fabio.Expression


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Sometimes there is no precise Expression subclass to specify the article type
    # but instead we have a specific Work subclass which is this the frbr:realizationOf the expression
    def get_publi_realization_of_work_class_URIRef(self, publication_types):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -    
        ns = self.ns
        for article_type in publication_types:
            if article_type == "case-report":                   return ns.fabio.CaseReport              # Work 
            if article_type == "meeting-report":                return ns.fabio.MeetingReport           # Work 
            if article_type == "correction":                    return ns.fabio.Correction              # Work 
            if article_type == "Clinical Trial":                return ns.fabio.ClinicalTrialReport     # Work
            if article_type == "Randomized Controlled Trial":   return ns.fabio.ClinicalTrialReport     # Work
            if article_type == "Clinical Trial, Phase I":       return ns.fabio.ClinicalTrialReport     # Work 
            if article_type == "Clinical Trial, Phase II":      return ns.fabio.ClinicalTrialReport     # Work
            if article_type == "Clinical Trial, Phase III":     return ns.fabio.ClinicalTrialReport     # Work 
            if article_type == "Case Reports":                  return ns.fabio.CaseReport              # Work
            if article_type == "Comparative Study":             return ns.fabio.Report                  # Work
            if article_type == "Clinical Study":                return ns.fabio.Report                  # Work
            if article_type == "Multicenter Study":             return ns.fabio.Report                  # Work
            if article_type == "Evaluation Study":              return ns.fabio.Report                  # Work
            if article_type == "Observational Study":           return ns.fabio.Report                  # Work
            if article_type == "Validation Study":              return ns.fabio.Report                  # Work
            if article_type == "Twin Study":                    return ns.fabio.Report                  # Work
            if article_type == "Meta-Analysis":                 return ns.fabio.Report                  # Work
            if article_type == "Biography":                     return ns.fabio.Biography               # Work
            if article_type == "Autobiography":                 return ns.fabio.Biography               # Work
            if article_type == "Technical Report":              return ns.fabio.TechnicalReport         # Work
            if article_type == "Systematic Review":             return ns.fabio.SystematicReview        # Work
        return None


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_triples_for_authors(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        ns = self.ns
        triples = TripleList()

        author_list = self.publi["document"].get("authors")
        if author_list is not None:
            for author in author_list:
                blank_node = getBlankNode()
                triples.append(blank_node, ns.rdf.type, ns.schema.Person)
                #triples.append(blank_node, ns.rdfs.label, ns.xsd.string(author))
                triples.append(blank_node, ns.schema.name, ns.xsd.string(author))
                triples.append(self.get_publi_URIRef(), ns.dcterms.creator, blank_node)

        return triples



    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Sentences which were added to the RDF are marked with a "rank" property
    # Only the annotations related to these sentences should be added to the RDF
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_triples_for_publi_annotations(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        ns = self.ns
        triples = TripleList()
        publi_uri = self.get_publi_URIRef()

        sentence_number2rank = dict()
        for sen in self.publi["sentences"]:
            rank = sen.get("rank")
            if rank is not None:
                num = sen["sentence_number"]
                sentence_number2rank[num] = rank

        annotations = self.publi["annotations"]
        for annot in annotations:
            annot_sen_num = annot["sentence_number"]
            if annot_sen_num not in sentence_number2rank: continue

            annot_bn = getBlankNode()
            triples.append(publi_uri, ns.sibilo.hasAnnotation, annot_bn)
            triples.append(annot_bn, ns.rdf.type, ns.sibilo.NexAnnotation)
            
            # the named entity found
            cpt_IRI = self.get_term_URIRef_from_annot(annot)
            if cpt_IRI is None: continue
            triples.append(annot_bn, ns.oa.hasBody, cpt_IRI)
            target_bn = getBlankNode()
            triples.append(annot_bn, ns.oa.hasTarget, target_bn)

            rank = sentence_number2rank[annot_sen_num]
            part_uri = self.get_sentence_part_URIRef(publi_uri, rank) # sentence_number is an annot property
            triples.append(target_bn, ns.rdf.type, ns.sibilo.AnnotationTarget)
            triples.append(target_bn, ns.oa.hasSource, part_uri)
            selector_bn = getBlankNode()
            triples.append(target_bn, ns.oa.hasSelector, selector_bn)
            triples.append(selector_bn, ns.rdf.type, ns.oa.TextPositionSelector)
            start_pos = int(annot["start_index"]) # index of concept form in the sentence
            triples.append(selector_bn, ns.oa.start, ns.xsd.integer(start_pos))
            end_pos = start_pos + int(annot["concept_length"])
            triples.append(selector_bn, ns.oa.end, ns.xsd.integer(end_pos))
            concept_form = annot["concept_form"]
            triples.append(selector_bn, ns.oa.exact, ns.xsd.string(concept_form))

        return triples


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_triples_for_sentences(self, field, parent_uri, sentence_class):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        ns = self.ns
        triples = TripleList()
        publi_uri = self.get_publi_URIRef()
        for sen in self.publi["sentences"]:
            if sen["field"] == field:
                sen_txt = sen["sentence"]
                if len(sen_txt) == 0: continue 
                rank = self.get_next_rank()
                sen["rank"] = rank                                      # <------ rank set here to be used later during annotation triple making process
                sen_uri = self.get_sentence_part_URIRef(publi_uri, rank)
                triples.append(parent_uri, ns.po.contains, sen_uri)
                triples.append(sen_uri, ns.rdf.type, sentence_class)
                triples.append(sen_uri, ns.cnt.chars, ns.xsd.string(sen_txt))
                triples.append(sen_uri, ns.sibilo.ordinal, ns.xsd.integer(rank))
        return triples



    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_triples_for_body_section(self, parent_uri, sct_class, sub_class, sen_class, sct_num, sct_label, sct_field):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        ns = self.ns
        triples = TripleList()
        if len(self.publi["document"].get(sct_field) or []) > 0:
            publi_uri = self.get_publi_URIRef()
            sct_uri = self.get_part_URIRef(publi_uri, str(sct_num))
            triples.append(parent_uri, ns.po.contains, sct_uri)
            triples.append(sct_uri, ns.rdf.type, sct_class)
            sub_uri = self.get_part_URIRef(publi_uri, str(sct_num) + ".1")
            label_BN = getBlankNode()
            triples.append(sct_uri, ns.dcterms.hasPart, label_BN)
            triples.append(label_BN, ns.rdf.type, ns.doco.SectionLabel)
            triples.append(label_BN, ns.cnt.chars, ns.xsd.string(sct_label))
            triples.append(label_BN, ns.sibilo.ordinal, ns.xsd.integer(self.get_next_rank()))
            triples.append(sct_uri, ns.po.contains, sub_uri)
            triples.append(sub_uri, ns.rdf.type, sub_class)
            triples.extend(self.get_triples_for_sentences(field=sct_field, parent_uri=sub_uri, sentence_class=sen_class))
        return triples


    # - - - - - - - - - - - - - - - - - - - - 
    def get_ttl_for_publi(self):
    # - - - - - - - - - - - - - - - - - - - - 
        ns = self.ns
        triples = TripleList()

        publi_doc = self.publi["document"]
        publi_uri = self.get_publi_URIRef()
        pmid = publi_doc.get("pmid")

        #
        # WARNING 
        # ignore retractions and erratums because our json file does NOT contain link to retracted / replaced pmid !!!
        #
        for publi_type in publi_doc["publication_types"]:
            if publi_type in ["Published Erratum", "Retraction Notice"]:
                log_it("WARNING", f"Ignoring rdfization of medline '{publi_type}' file for", pmid)
                return ""


        triples.append(publi_uri, ns.fabio.hasPubMedId, ns.xsd.string(pmid))
        triples.append(publi_uri, ns.rdfs.seeAlso, f"<https://pubmed.ncbi.nlm.nih.gov/{pmid}>")

        
        publi_class_uri = self.get_publi_expression_class_URIRef(publi_doc["publication_types"])
        triples.append(publi_uri , ns.rdf.type, publi_class_uri)    

        publi_work_class_uri = self.get_publi_realization_of_work_class_URIRef(publi_doc["publication_types"])
        if publi_work_class_uri is not None:
            work_BN = getBlankNode()
            triples.append(publi_uri, ns.frbr.realizationOf, work_BN)
            triples.append(work_BN, ns.rdf.type, publi_work_class_uri)


        pmcid = publi_doc.get("pmcid")  
        if pmcid is not None:
            triples.append(publi_uri, ns.fabio.hasPubMedCentralId, ns.xsd.string(pmcid))

        medline_ta = publi_doc.get("medline_ta")
        if medline_ta is not None:
            triples.append(publi_uri, ns.fabio.hasNLMJournalTitleAbbreviation, ns.xsd.string(medline_ta))

        doi = publi_doc.get("doi")
        if doi is not None:
            triples.append(publi_uri, ns.prism.hasDOI, ns.xsd.string(doi))

        pubyear = publi_doc.get("pubyear")
        if pubyear is not None:
            triples.append(publi_uri, ns.fabio.hasPublicationYear, ns.xsd.string(pubyear))

        pubdate = publi_doc.get("entrez_date")
        if pubdate is not None:
            triples.append(publi_uri, ns.prism.publicationDate, ns.xsd.date(pubdate)) # comes in expected format

        keywords = publi_doc.get("keywords")
        if keywords is not None and isinstance(keywords,list):
            for k in keywords:
                triples.append(publi_uri, ns.prism.keyword, ns.xsd.string(k))
                    
        o = publi_doc.get("title")
        if o is not None and len(o)>0 : 
            triples.append(publi_uri, ns.dcterms.title, ns.xsd.string3(o))

        o = publi_doc.get("abstract")
        if o is not None and len(o)>0 : 
            triples.append(publi_uri, ns.dcterms.abstract, ns.xsd.string3(o))

        triples.extend(self.get_triples_for_authors())

        # create FrontMatter
        front_uri = self.get_front_matter_URIRef(publi_uri)
        triples.append(publi_uri, ns.po.contains, front_uri)
        triples.append(front_uri, ns.rdf.type, ns.doco.FrontMatter)

        # front matter - title,
        title_uri = self.get_part_URIRef(publi_uri, "1")
        triples.append(front_uri, ns.po.contains, title_uri)
        triples.append(title_uri, ns.rdf.type, ns.doco.Title)       
        title_para_uri = self.get_part_URIRef(publi_uri, "1.1")
        triples.append(title_uri, ns.po.contains, title_para_uri)
        triples.append(title_para_uri, ns.rdf.type, ns.doco.Paragraph)
        triples.extend(self.get_triples_for_sentences(field="title", parent_uri=title_para_uri, sentence_class=ns.doco.Sentence))

        # front matter - authors (also exist as schema:Person in metadata)
        author_list = self.publi["document"].get("authors") or []
        if len(author_list) > 0:
            authors_str = ", ".join(author_list)
            authors_uri = self.get_part_URIRef(publi_uri, "2")
            triples.append(front_uri, ns.po.contains, authors_uri)                
            triples.append(authors_uri, ns.rdf.type, ns.doco.ListOfAuthors)
            triples.append(authors_uri, ns.cnt.chars, ns.xsd.string(authors_str))
            triples.append(authors_uri, ns.sibilo.ordinal, ns.xsd.integer(self.get_next_rank()))

        # front matter - affiliations
        aff_list = self.publi["document"].get("affiliations") or []
        if len(aff_list) > 0:
            affs_uri = self.get_part_URIRef(publi_uri, "3")
            triples.append(front_uri, ns.po.contains, affs_uri)                
            triples.append(affs_uri, ns.rdf.type, ns.doco.ListOfOrganizations)
            label_BN = getBlankNode()
            triples.append(affs_uri, ns.dcterms.hasPart, label_BN)
            triples.append(label_BN, ns.rdf.type, ns.doco.Label)
            triples.append(label_BN, ns.cnt.chars, ns.xsd.string("Affiliations"))
            triples.append(label_BN, ns.sibilo.ordinal, ns.xsd.integer(self.get_next_rank()))
            triples.extend(self.get_triples_for_sentences(field="affiliations", parent_uri=affs_uri, sentence_class=ns.sibilo.WordSequence))

        # create BodyMatter
        body_uri = self.get_body_matter_URIRef(publi_uri)
        triples.append(publi_uri, ns.po.contains, body_uri)
        triples.append(body_uri, ns.rdf.type, ns.doco.BodyMatter)

        # body matter sections
        triples.extend(self.get_triples_for_body_section(
            body_uri, ns.doco.Abstract, ns.doco.Paragraph, ns.doco.Sentence, "4", "Abstract", "abstract"))
        triples.extend(self.get_triples_for_body_section(
            body_uri, ns.doco.Section, ns.doco.List, ns.sibilo.WordSequence, "5", "Conflict of interest statement", "coi_statement"))
        # body matter - publication types - 6 - has no sentences in json
        pub_types = publi_doc.get("publication_types") or []
        if len(pub_types) > 0:
            pt_uri = self.get_part_URIRef(publi_uri, "6")
            triples.append(body_uri, ns.po.contains, pt_uri)
            triples.append(pt_uri, ns.rdf.type, ns.doco.Section)
            pt_sub_uri = self.get_part_URIRef(publi_uri, "6.1")
            label_BN = getBlankNode()
            triples.append(pt_uri, ns.dcterms.hasPart, label_BN)
            triples.append(label_BN, ns.rdf.type, ns.doco.SectionLabel)
            triples.append(label_BN, ns.cnt.chars, ns.xsd.string("Publication types"))
            triples.append(label_BN, ns.sibilo.ordinal, ns.xsd.integer(self.get_next_rank()))
            triples.append(pt_uri, ns.po.contains, pt_sub_uri)
            triples.append(pt_sub_uri, ns.rdf.type, ns.doco.List)
            for pt in publi_doc["publication_types"]:
                pt_BN = getBlankNode()
                triples.append(pt_sub_uri, ns.po.contains, pt_BN)
                triples.append(pt_BN, ns.rdf.type, ns.sibilo.WordSequence)
                triples.append(pt_BN, ns.cnt.chars, ns.xsd.string(pt))
                triples.append(pt_BN, ns.sibilo.ordinal, ns.xsd.integer(self.get_next_rank()))
        # more body matter sections
        triples.extend(self.get_triples_for_body_section(
            body_uri, ns.doco.Section, ns.doco.List, ns.sibilo.WordSequence, "7", "MeSH terms", "mesh_terms"))
        triples.extend(self.get_triples_for_body_section(
            body_uri, ns.doco.Section, ns.doco.List, ns.sibilo.WordSequence, "8", "Substances", "chemicals"))
        triples.extend(self.get_triples_for_body_section(
            body_uri, ns.doco.Section, ns.doco.List, ns.sibilo.WordSequence, "9", "Supplementary concepts", "sup_mesh_terms"))
        triples.extend(self.get_triples_for_body_section(
            body_uri, ns.doco.Section, ns.doco.List, ns.sibilo.WordSequence, "10", "Keywords", "keywords"))

        # add publi annotations
        triples.extend(self.get_triples_for_publi_annotations())

        return("".join(triples.lines))
