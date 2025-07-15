from ApiCommon import log_it
from rdf_utils import TripleList, getBlankNode
from namespace_registry import NamespaceRegistry
from publi_rdfizer import PubliRdfizer


class PmcRdfizer(PubliRdfizer):


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def __init__(self, ns: NamespaceRegistry, publi): 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        super().__init__(ns, publi)
        self.skipped_sentences = set()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_publi_id(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        return self.publi["document"]["pmcid"]
        

   # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_publi_URIRef(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        publi_id = self.get_publi_id()
        if publi_id is None: return None
        return self.ns.sibils.IRI(publi_id)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_sentence_part_URIRef(self, publi_uri, sentence_or_annot):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        part_id = sentence_or_annot.get("id_sentence")                            # found in annotation object (not necessary anymore)
        if part_id is None: part_id = sentence_or_annot.get("sentence_number")    # found in sentence object
        return publi_uri + "_sen_" + str(part_id)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_publi_class_URIRef(self, article_type):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -    
        # see ontology at https://sparontologies.github.io/fabio/current/fabio.html
        # warning: do not mix Work and Expression, here we choose only Expression subclasses
        # https://sourceforge.net/p/sempublishing/code/HEAD/tree/JATS2RDF/jats2rdf.pdf?format=raw
        ns = self.ns
        if article_type == "research-article":  return ns.fabio.JournalArticle      
        if article_type == "review-article":    return ns.fabio.ReviewArticle       
        if article_type == "brief-report":      return ns.fabio.BriefReport        
        if article_type == "case-report":       return ns.fabio.CaseReport         
        if article_type == "discussion":        return ns.fabio.Expression         # default value
        if article_type == "editorial":         return ns.fabio.Editorial          
        if article_type == "letter":            return ns.fabio.Letter             
        if article_type == "article-commentary":return ns.fabio.Expression         # default value
        if article_type == "meeting-report":    return ns.fabio.MeetingReport      
        if article_type == "correction":        return ns.fabio.Expression         # default value
        print("ERROR, unexpected article_type", article_type)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_triples_for_authors(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        ns = self.ns
        triples = TripleList()

        author_list = self.publi.get("authors")
        if author_list is not None:

            for author in author_list:
                blank_node = getBlankNode()
                triples.append(blank_node, ns.rdf.type, ns.schema.Person)
                #triples.append(blank_node, ns.rdfs.label, ns.xsd.string(author.get("name")))
                triples.append(blank_node, ns.schema.name, ns.xsd.string(author.get("name")))
                aff_id_list = author.get("affiliations")
                if aff_id_list is not None:
                    for aff_id in aff_id_list:
                        aff_name = self.find_affiliation_name(aff_id)
                        if aff_name is None:
                            found = False
                            # if we found nothing let's try to split the author affiliations on <space>
                            # because some enter the list erroneously like: affiliations: ["id1 id2"] instead of affiliations: ["id1","id2"]
                            if len(aff_id_list)==1:                   
                                for split_aff_id in aff_id_list[0].split(" "):
                                    aff_name = self.find_affiliation_name(split_aff_id)
                                    if aff_name is not None:
                                        found = True
                                        triples.append(blank_node, ns.schema.affiliation, ns.xsd.string(aff_name))
                            if not found:
                                log_it("WARNING", "found no name for affiliation id", aff_id, "in", self.get_publi_id())
                        else:
                            triples.append(blank_node, ns.schema.affiliation, ns.xsd.string(aff_name))
                triples.append(self.get_publi_URIRef(), ns.dcterms.creator, blank_node)


        return triples


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_triples_for_publi_annotations(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        ns = self.ns
        triples = TripleList()

        publi_uri = self.get_publi_URIRef()
        annotations = self.publi["annotations"]
        for annot in annotations:
            
            if annot["sentence_number"] in self.skipped_sentences: continue

            annot_bn = getBlankNode()
            triples.append(publi_uri, ns.sibilo.hasAnnotation, annot_bn)
            triples.append(annot_bn, ns.rdf.type, ns.sibilo.NexAnnotation)
            
            # the named entity found
            cpt_IRI = self.get_term_URIRef_from_annot(annot)
            if cpt_IRI is None: continue
            triples.append(annot_bn, ns.oa.hasBody, cpt_IRI)
            target_bn = getBlankNode()
            triples.append(annot_bn, ns.oa.hasTarget, target_bn)

            # only sentences are annotated since version 3.2
            part_uri = self.get_sentence_part_URIRef(publi_uri, annot) # sentence_number is an annot property
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


    # - - - - - - - - - - - - - - - - - - - - 
    def get_ttl_for_publi(self):
    # - - - - - - - - - - - - - - - - - - - - 
        ns = self.ns
        triples = TripleList()

        publi_doc = self.publi["document"]
        pmcid = publi_doc["pmcid"]

        #log_it("DEBUG", "pmcid", pmcid)
        publi_uri = self.get_publi_URIRef()
        publi_class_uri = self.get_publi_class_URIRef(publi_doc["article_type"])
        triples.append(publi_uri , ns.rdf.type, publi_class_uri)    
        triples.append(publi_uri, ns.fabio.hasPubMedCentralId, ns.xsd.string(pmcid))

        medline_ta = publi_doc.get("medline_ta")
        if medline_ta is not None:
            triples.append(publi_uri, ns.fabio.hasNLMJournalTitleAbbreviation, ns.xsd.string(medline_ta))

        pmid = publi_doc.get("pmid")
        if pmid is not None:
            triples.append(publi_uri, ns.fabio.hasPubMedId, ns.xsd.string(pmid))

        doi = publi_doc.get("doi")
        if doi is not None:
            triples.append(publi_uri, ns.prism.hasDOI, ns.xsd.string(doi))

        pubyear = publi_doc.get("pubyear")
        if pubyear is not None:
            triples.append(publi_uri, ns.fabio.hasPublicationYear, ns.xsd.string(pubyear))

        pubdate = publi_doc.get("publication_date")
        if pubdate is not None:
            triples.append(publi_uri, ns.prism.publicationDate, ns.xsd.date(self.date_to_yyyy_mm_dd(pubdate)))

        keywords = publi_doc.get("keywords")
        if keywords is not None and isinstance(keywords,list):
            for k in keywords:
                triples.append(publi_uri, ns.prism.keyword, ns.xsd.string(k))

        issue = publi_doc.get("issue")
        if issue is not None and len(issue)>0:
            triples.append(publi_uri, ns.prism.issueIdentifier, ns.xsd.string(issue))

        volume = publi_doc.get("volume")
        if issue is not None and len(volume)>0:
            triples.append(publi_uri, ns.prism.volume, ns.xsd.string(volume))
            
        # starting, ending page and page range,
        # see https://sourceforge.net/p/sempublishing/code/HEAD/tree/JATS2RDF/jats2rdf.pdf?format=raw
        blank_node = getBlankNode()
        bn_empty = True
        o = publi_doc.get("start_page")
        if o is not None and len(o)>0 : 
            bn_empty = False
            triples.append(blank_node, ns.prism.startingPage, ns.xsd.string(o))

        o = publi_doc.get("end_page")
        if o is not None and len(o)>0 : 
            bn_empty = False
            triples.append(blank_node, ns.prism.endingPage,ns.xsd.string(o))

        o = publi_doc.get("medline_pgn")
        if o is not None and len(o)>0 : 
            bn_empty = False
            triples.append(blank_node, ns.prism.pageRange, ns.xsd.string(o))

        if not bn_empty:
            triples.append(blank_node, ns.rdf.type, ns.fabio.Manifestation)
            triples.append(publi_uri, ns.fabio.embodiement, blank_node)
        # end page stuff
        
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
        
        # add sections
        # parent_dic = dict() # DEBUG
        sct_list_names = ["body_sections", "back_sections", "float_sections"]
        for sct_list_name in sct_list_names:
            sct_list = publi_doc.get(sct_list_name)
            if len(sct_list)>0: 
                for sct in sct_list:
                    
                    parent_uri = self.get_parent_part_URIRef(publi_uri, sct)
                    sct_uri = self.get_part_URIRef(publi_uri, sct["id"])
                    
                    # create part type and part parent relationship 
                    triples.append(parent_uri, ns.po.contains, sct_uri)
                    part_class_uri = self.get_sct_part_class_URIRef(sct)
                    triples.append(sct_uri, ns.rdf.type, part_class_uri)

                    # # DEBUG: add sct_uri to parent_dic
                    # parent_dic[parent_uri]=list()
                    # parent_dic[sct_uri]=list()
                    # # end DEBUG

                    # add section caption if appropriate
                    # note: no sentences are generated by Julien for sct["caption"]
                    # kept as a blank node because never used in annotations
                    if part_class_uri == ns.doco.CaptionedBox:
                        blank_node = getBlankNode()
                        triples.append(blank_node, ns.rdf.type, ns.deo.Caption)
                        triples.append(blank_node, ns.cnt.chars, ns.xsd.string(sct["caption"]))
                        triples.append(sct_uri, ns.dcterms.hasPart, blank_node)

                    # add section title if appropriate
                    # note: sentences related to sct["title"] have sen["field"] = "section_title"
                    sct_title = sct.get("title")
                    if sct_title is not None and len(sct_title)>0 and sct_title != "Title" and sct_title != "Abstract":
                        tit_uri = self.get_part_title_URIRef(sct_uri)
                        triples.append(tit_uri, ns.rdf.type, ns.doco.SectionLabel)
                        triples.append(sct_uri, ns.dcterms.hasPart, tit_uri)

                        # # DEBUG: add tit_uri to parent_dic
                        # parent_dic[tit_uri]=list()
                        # # end DEBUG

                    # add section contents
                    for cnt in sct["contents"]:

                        # link to parent section and set content class
                        cnt_uri = self.get_part_URIRef(publi_uri, cnt["id"])
                        triples.append(sct_uri, ns.po.contains, cnt_uri)
                        triples.append(cnt_uri, ns.rdf.type, self.get_cnt_part_class_URIRef(cnt))

                        # # DEBUG: add tit_uri to parent_dic
                        # parent_dic[cnt_uri]=list()
                        # # end DEBUG

                        xrefUrl = cnt.get("xref_url")
                        if xrefUrl:
                            triples.append(cnt_uri, ns.rdfs.seeAlso, "<" + xrefUrl + ">")
                            
                        capt = cnt.get("caption")
                        if capt:
                            capt_uri = self.get_part_caption_URIRef(cnt_uri)
                            triples.append(cnt_uri, ns.dcterms.hasPart, capt_uri)
                            triples.append(capt_uri, ns.rdf.type, ns.deo.Caption)
                            # # DEBUG: add tit_uri to parent_dic
                            # parent_dic[capt_uri]=list()
                            # # end DEBUG

                        label = cnt.get("label")
                        if label:
                            label_uri = self.get_part_label_URIRef(cnt_uri)
                            triples.append(cnt_uri, ns.dcterms.hasPart, label_uri)
                            triples.append(label_uri, ns.rdf.type, ns.doco.Label)
                            # note: no sentences are generated by Julien for cnt["label"], so declare :chars here
                            # often used for figs and tables (i.e. Fig 1, Table 2)
                            triples.append(label_uri, ns.cnt.chars, ns.xsd.string(label))
                            # # DEBUG: add tit_uri to parent_dic
                            # parent_dic[label_uri]=list()
                            # # end DEBUG

                        foot = cnt.get("footer")
                        if foot:
                            foot_uri = self.get_part_footer_URIRef(cnt_uri)
                            triples.append(cnt_uri, ns.dcterms.hasPart, foot_uri)
                            triples.append(foot_uri, ns.rdf.type, ns.sibilo.TableFooter)
                            # # DEBUG: add tit_uri to parent_dic
                            # parent_dic[foot_uri]=list()
                            # # end DEBUG

            elif len(sct_list)==0 and sct_list_name == "body_sections" : 
                log_it("WARNING", sct_list_name, "empty")

        # add sentences
        for sen in self.publi["sentences"]:
            # we skip title ("0", "1"), abstract ("0", "2"), keywords ("0"), affiliations ("0")
            # in pmc json, the sentences skipped here are repeated in paragraphs of body sections related to title, abstract, keywords
            sen_num = int(sen["sentence_number"])
            if sen["content_id"] in ["0", "1", "2"]: 
                self.skipped_sentences.add(sen_num)
                continue 
            sen_txt = sen["sentence"]
            # we skip a few sentences which have an empty textual content
            if len(sen_txt)==0: continue
            sen_uri = self.get_sentence_part_URIRef(publi_uri, sen)
            sen_parent_uri = self.get_parent_part_URIRef(publi_uri, sen)
            triples.append(sen_parent_uri, ns.po.contains, sen_uri)
            sen_class = self.get_sen_part_class_URIRef(sen) 
            triples.append(sen_uri, ns.rdf.type, sen_class)
            triples.append(sen_uri, ns.cnt.chars, ns.xsd.string(sen_txt))
            triples.append(sen_uri, ns.sibilo.ordinal, ns.xsd.integer(sen_num))

        # add publi annotations
        triples.extend(self.get_triples_for_publi_annotations())

        return("".join(triples.lines))
