import sys
import pickle
import datetime
import urllib.parse
from utils import log_it

from SibiloNamespace import SibiloNamespace
from rdfizer import SibilcNamespace, SibilsNamespace
from rdfizer import RdfNamespace, RdfsNamespace, OwlNamespace, XsdNamespace, SkosNamespace, FoafNamespace
from rdfizer import getBlankNode, getTtlPrefixDeclaration, getTriple

sibilo = SibiloNamespace()          # sibils core ontology
sibils = SibilsNamespace()          # sibils data
sibilc = SibilcNamespace()          # concepts used in sibils annotation
rdf = RdfNamespace()
rdfs = RdfsNamespace()
xsd = XsdNamespace()
foaf = FoafNamespace()


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_prefixes():
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    lines = list()
    for ns in [sibilo, sibils, sibilc,rdf, rdfs, xsd, foaf]:
        lines.append(ns.getTtlPrefixDeclaration())
    return lines


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# OK for sibils version 3.2 (not retro-compatible with v2.x)
# derive a NamedIndividual name for a terminology from its corresponding concept_source
def get_terminology_NI_name(concept_source):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    return concept_source.replace(" ","_").capitalize() + "_St" # St stands for Sibils terminology

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# OK for sibils version 3.2 (not retro-compatible with v2.x)
def get_term_URIRef_from_annot(annot):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    db = get_terminology_NI_name(annot["concept_source"])
    ac = annot["concept_id"]
    name = db + "|" +ac
    encoded_name = urllib.parse.quote(name)
    return sibilc.IRI(encoded_name)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# OK for sibils version 3.2 (not retro-compatible with v2.x)
def get_term_URIRef_from_term(concept_id, terminology):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    db = get_terminology_NI_name(terminology["concept_source"])
    ac = concept_id
    name = db + "|" +ac
    encoded_name = urllib.parse.quote(name)
    return sibilc.IRI(encoded_name)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# OK for sibils version 3.2 (not retro-compatible with v2.x)
def get_terminology_URIRef(terminology):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    name = get_terminology_NI_name(terminology["concept_source"])
    encoded_name = urllib.parse.quote(name)
    return sibilo.IRI(encoded_name)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_triples_for_publi_annotations(publi):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    lines = list()
    publi_doc = publi["document"]
    publi_uri = get_publi_URIRef(publi_doc)
    annotations = publi["annotations"]
    for annot in annotations:
        
        annot_bn = getBlankNode()
        lines.append(getTriple(publi_uri, sibilo.hasAnnotation(), annot_bn))
        lines.append(getTriple(annot_bn, rdf.type(), sibilo.Annotation()))
        
        # the named entity found
        lines.append(getTriple(annot_bn, sibilo.hasBody(), get_term_URIRef_from_annot(annot))) 
        target_bn = getBlankNode()
        lines.append(getTriple(annot_bn, sibilo.hasTarget(), target_bn))

        # only sentences are annotated since version 3.2
        part_uri = get_sentence_part_URIRef(publi_uri, annot) # sentence_number is an annot property
        lines.append(getTriple(target_bn, rdf.type(), sibilo.AnnotationTarget()))
        lines.append(getTriple(target_bn, sibilo.hasSource(), part_uri))
        selector_bn = getBlankNode()
        lines.append(getTriple(target_bn, sibilo.hasSelector(), selector_bn))
        lines.append(getTriple(selector_bn, rdf.type(), sibilo.TextPositionSelector()))
        start_pos = int(annot["start_index"]) # index of concept form in the sentence
        lines.append(getTriple(selector_bn, sibilo.start(), xsd.integer(start_pos)))
        end_pos = start_pos + int(annot["concept_length"])
        lines.append(getTriple(selector_bn, sibilo.end(), xsd.integer(end_pos)))
        concept_form = annot["concept_form"]
        lines.append(getTriple(selector_bn, sibilo.exact(), xsd.string3(concept_form)))

    return lines


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_triples_for_publi(publi):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    lines = list()
    publi_doc = publi["document"]
    pmcid = publi_doc["pmcid"]
    #log_it("DEBUG", "pmcid", pmcid)
    publi_uri = get_publi_URIRef(publi_doc)
    publi_class_uri = get_publi_class_URIRef(publi_doc["article_type"])
    lines.append(getTriple(publi_uri , rdf.type(), publi_class_uri))    
    lines.append(getTriple(publi_uri, sibilo.hasPubMedCentralId(), xsd.string3(pmcid)))

    medline_ta = publi_doc.get("medline_ta")
    if medline_ta is not None:
        lines.append(getTriple(publi_uri, sibilo.hasNLMJournalTitleAbbreviation(), xsd.string3(medline_ta)))

    pmid = publi_doc.get("pmid")
    if pmid is not None:
        lines.append(getTriple(publi_uri, sibilo.hasPubMedId(), xsd.string3(pmid)))

    doi = publi_doc.get("doi")
    if doi is not None:
        lines.append(getTriple(publi_uri, sibilo.doi(), xsd.string3(doi)))

    pubyear = publi_doc.get("pubyear")
    if pubyear is not None:
        lines.append(getTriple(publi_uri, sibilo.hasPublicationYear(), xsd.integer(pubyear)))

    pubdate = publi_doc.get("publication_date")
    if pubdate is not None:
        lines.append(getTriple(publi_uri, sibilo.publicationDate(), xsd.date(date_to_yyyy_mm_dd(pubdate))))

    keywords = publi_doc.get("keywords")
    if keywords is not None and isinstance(keywords,list):
        for k in keywords:
            lines.append(getTriple(publi_uri, sibilo.keyword(), xsd.string3(k)))

    issue = publi_doc.get("issue")
    if issue is not None and len(issue)>0:
        lines.append(getTriple(publi_uri, sibilo.issueIdentifier(), xsd.string3(issue)))

    volume = publi_doc.get("volume")
    if issue is not None and len(volume)>0:
        lines.append(getTriple(publi_uri, sibilo.volume(), xsd.string3(volume)))
        
    # starting, ending page and page range,
    # see https://sourceforge.net/p/sempublishing/code/HEAD/tree/JATS2RDF/jats2rdf.pdf?format=raw
    blank_node = getBlankNode()
    bn_empty = True
    o = publi_doc.get("start_page")
    if o is not None and len(o)>0 : 
        bn_empty = False
        lines.append(getTriple(blank_node, sibilo.startingPage(), xsd.string3(o)))

    o = publi_doc.get("end_page")
    if o is not None and len(o)>0 : 
        bn_empty = False
        lines.append(getTriple(blank_node, sibilo.endingPage(), xsd.string3(o)))

    o = publi_doc.get("medline_pgn")
    if o is not None and len(o)>0 : 
        bn_empty = False
        lines.append(getTriple(blank_node, sibilo.pageRange(), xsd.string3(o)))

    if not bn_empty:
        lines.append(getTriple(blank_node, rdf.type(), sibilo.Manifestation()))
        lines.append(getTriple(publi_uri, sibilo.embodiment(), blank_node))
    # end page stuff
    
    o = publi_doc.get("title")
    if o is not None and len(o)>0 : 
        lines.append(getTriple(publi_uri, sibilo.title(), xsd.string3(o)))

    o = publi_doc.get("abstract")
    if o is not None and len(o)>0 : 
        lines.append(getTriple(publi_uri, sibilo.abstract(), xsd.string3(o)))

    lines.extend(add_triples_for_authors(publi_doc, pmcid))
            
    # create FrontMatter
    front_uri = get_front_matter_URIRef(publi_uri)
    lines.append(getTriple(publi_uri, sibilo.contains(), front_uri))
    lines.append(getTriple(front_uri, rdf.type(), sibilo.FrontMatter()))
    
    # add sections
    # parent_dic = dict() # DEBUG
    sct_list_names = ["body_sections", "back_sections", "float_sections"]
    for sct_list_name in sct_list_names:
        sct_list = publi_doc.get(sct_list_name)
        if len(sct_list)>0: 
            for sct in sct_list:
                
                parent_uri = get_parent_part_URIRef(publi_uri, sct)
                sct_uri = get_part_URIRef(publi_uri, sct)
                
                # create part type and part parent relationship 
                lines.append(getTriple(parent_uri, sibilo.contains(), sct_uri))
                part_class_uri = get_sct_part_class_URIRef(sct)
                lines.append(getTriple(sct_uri, rdf.type(), part_class_uri))

                # # DEBUG: add sct_uri to parent_dic
                # parent_dic[parent_uri]=list()
                # parent_dic[sct_uri]=list()
                # # end DEBUG

                # add section caption if appropriate
                # note: no sentences are generated by Julien for sct["caption"]
                # kept as a blank node because never used in annotations
                if part_class_uri == sibilo.CaptionedBox():
                    blank_node = getBlankNode()
                    lines.append(getTriple(blank_node, rdf.type(), sibilo.Caption()))
                    lines.append(getTriple(blank_node, sibilo.chars(), xsd.string3(sct["caption"])))
                    lines.append(getTriple(sct_uri, sibilo.hasPart(), blank_node))

                # add section title if appropriate
                # note: sentences related to sct["title"] have sen["field"] = "section_title"
                sct_title = sct.get("title")
                if sct_title is not None and len(sct_title)>0 and sct_title != "Title" and sct_title != "Abstract":
                    tit_uri = get_part_title_URIRef(sct_uri)
                    lines.append(getTriple(tit_uri, rdf.type(), sibilo.SectionLabel()))
                    lines.append(getTriple(sct_uri, sibilo.hasPart(), tit_uri))

                    # # DEBUG: add tit_uri to parent_dic
                    # parent_dic[tit_uri]=list()
                    # # end DEBUG

                # add section contents
                for cnt in sct["contents"]:

                    # link to parent section and set content class
                    cnt_uri = get_part_URIRef(publi_uri, cnt)
                    lines.append(getTriple(sct_uri, sibilo.contains(), cnt_uri))
                    lines.append(getTriple(cnt_uri, rdf.type(), get_cnt_part_class_URIRef(cnt)))

                    # # DEBUG: add tit_uri to parent_dic
                    # parent_dic[cnt_uri]=list()
                    # # end DEBUG

                    xrefUrl = cnt.get("xref_url")
                    if xrefUrl:
                        lines.append(getTriple(cnt_uri, rdfs.seeAlso(), "<" + xrefUrl + ">"))
                        
                    capt = cnt.get("caption")
                    if capt:
                        capt_uri = get_part_caption_URIRef(cnt_uri)
                        lines.append(getTriple(cnt_uri, sibilo.hasPart(), capt_uri))
                        lines.append(getTriple(capt_uri, rdf.type(), sibilo.Caption()))
                        # # DEBUG: add tit_uri to parent_dic
                        # parent_dic[capt_uri]=list()
                        # # end DEBUG

                    label = cnt.get("label")
                    if label:
                        label_uri = get_part_label_URIRef(cnt_uri)
                        lines.append(getTriple(cnt_uri, sibilo.hasPart(), label_uri))
                        lines.append(getTriple(label_uri, rdf.type(), sibilo.Label()))
                        # note: no sentences are generated by Julien for cnt["label"], so declare :chars here
                        # often used for figs and tables (i.e. Fig 1, Table 2)
                        lines.append(getTriple(label_uri, sibilo.chars(), xsd.string3(label)))
                        # # DEBUG: add tit_uri to parent_dic
                        # parent_dic[label_uri]=list()
                        # # end DEBUG

                    foot = cnt.get("footer")
                    if foot:
                        foot_uri = get_part_footer_URIRef(cnt_uri)
                        lines.append(getTriple(cnt_uri, sibilo.hasPart(), foot_uri))
                        lines.append(getTriple(foot_uri, rdf.type(), sibilo.TableFooter()))
                        # # DEBUG: add tit_uri to parent_dic
                        # parent_dic[foot_uri]=list()
                        # # end DEBUG

        elif len(sct_list)==0 and sct_list_name == "body_sections" : 
            log_it("WARNING", sct_list_name, "empty")

    # add sentences
    # sen_parent_dic = dict() # DEBUG
    for sen in publi["sentences"]:
        # we skip title ("0", "1"), abstract ("0", "2"), keywords ("0"), affiliations ("0")
        if sen["content_id"] in ["0", "1", "2"]: continue 
        sen_txt = sen["sentence"]
        # we skip a few sentences which have an empty textual content
        if len(sen_txt)==0: continue
        sen_uri = get_sentence_part_URIRef(publi_uri, sen)
        sen_parent_uri = get_parent_part_URIRef(publi_uri, sen)
        lines.append(getTriple(sen_parent_uri, sibilo.contains(), sen_uri))
        sen_class = get_sen_part_class_URIRef(sen) 
        lines.append(getTriple(sen_uri, rdf.type(), sen_class))
        lines.append(getTriple(sen_uri, sibilo.chars(), xsd.string3(sen_txt)))
        sen_ord = int(sen["sentence_number"])
        lines.append(getTriple(sen_uri, sibilo.ordinal(), xsd.integer(sen_ord)))
        
    return lines


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def date_to_yyyy_mm_dd(dd_mm_yyyy):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    d,m,y = dd_mm_yyyy.split("-")
    return y + "-" + m + "-" + d
    

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def add_triples_for_authors(publi, pmcid):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    lines = list()
    author_list = publi.get("authors")
    if author_list is not None:
        for author in author_list:
            blank_node = getBlankNode()
            lines.append(getTriple(blank_node, rdf.type(), foaf.Person()))
            lines.append(getTriple(blank_node, rdfs.label(), xsd.string3(author.get("name"))))
            aff_id_list = author.get("affiliations")
            if aff_id_list is not None:
                for aff_id in aff_id_list:
                    aff_name = find_affiliation_name(publi, aff_id)
                    if aff_name is None:
                        found = False
                        # if we found nothing let's try to split the author affiliations on <space>
                        # because some enter the list erroneously like: affiliations: ["id1 id2"] instead of affiliations: ["id1","id2"]
                        if len(aff_id_list)==1:                   
                            for split_aff_id in aff_id_list[0].split(" "):
                                aff_name = find_affiliation_name(publi, split_aff_id)
                                if aff_name is not None:
                                    found = True
                                    lines.append(getTriple(blank_node, sibilo.affiliation(), xsd.string3(aff_name)))
                        if not found:
                            log_it("ERROR", "found no name for affiliation id", aff_id, "in", pmcid)
                    else:
                        lines.append(getTriple(blank_node, sibilo.affiliation(), xsd.string3(aff_name)))

            lines.append(getTriple(get_publi_URIRef(publi), sibilo.creator(), blank_node))
    return lines

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_publi_URIRef(publi):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    pmcid = publi.get("pmcid")
    return sibils.IRI(pmcid)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_front_matter_URIRef(publi_uri):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    return publi_uri + "_part_frontMatter"

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_part_label_URIRef(part_uri):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    return part_uri + "_label"

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_part_caption_URIRef(part_uri):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    return part_uri + "_caption"

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_part_footer_URIRef(part_uri):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    return part_uri + "_footer"

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_part_title_URIRef(part_uri):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    return part_uri + "_title"

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_sentence_part_URIRef(publi_uri, sentence_or_annot):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    part_id = str(sentence_or_annot.get("sentence_number"))
    return publi_uri + "_sen_" + part_id


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_part_URIRef(publi_uri, sct):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    part_id = sct.get("id")
    return publi_uri + "_part_" + part_id


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_parent_part_URIRef(publi_uri, part):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    fld = part.get("field")
    # case 1: part is a sentence
    if fld is not None:
        part_id = part["content_id"]
        # by order of frequency in data to improve preformance
        if fld == "text": return "".join([publi_uri , "_part_" , part_id])
        if fld == "fig_caption": return "".join([publi_uri , "_part_" , part_id , "_caption"])
        if fld == "section_title": return "".join([publi_uri , "_part_" , part_id , "_title"])
        if fld == "table_column": return "".join([publi_uri , "_part_" , part_id])
        if fld == "table_footer": return "".join([publi_uri , "_part_" , part_id , "_footer"])
        if fld == "table_value": return "".join([publi_uri , "_part_" , part_id])
        if fld == "table_caption": return "".join([publi_uri , "_part_" , part_id , "_caption"])
        raise Exception("Unexpected sentence field value in " + publi_uri + ", part_id " + part_id + ", field=" + fld)
    # case 2: part is a top level container
    elif part.get("level") == 1:
        tag = part.get("tag")
        if tag is None and part.get("title")== "Title": 
            return  get_front_matter_URIRef(publi_uri)
        elif tag == "abstract":
            return  get_front_matter_URIRef(publi_uri)
        else:
            return publi_uri
    # case 3: part is a regular section (sct) or a content (cnt)
    else:            
        part_id = part.get("id")
        # parent id: remove everything from right until LAST <dot> is reached
        parent_id = part_id[:part_id.rfind(".")]
        return "".join([publi_uri , "_part_" , parent_id])

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_sen_part_class_URIRef(sentence):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    fld = sentence.get("field")
    if fld == "table_column": return sibilo.TableColumnName()
    if fld == "table_value": return sibilo.TableCellValues()
    return sibilo.Sentence()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_cnt_part_class_URIRef(cnt):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # sibilo classes below could be defined as sub classes of po:Block
    tag = cnt.get("tag")
    if tag == "p":           return sibilo.Paragraph()
    if tag == "fig":         return sibilo.FigureBox()
    if tag == "table":       return sibilo.TableBox()
    if tag == "list-item":   return sibilo.ListItemBlock()      # our extension
    if tag == "media":       return sibilo.MediaBlock()         # our extension
    if tag == "def-list":    return sibilo.Glossary()
    if tag == "disp-quote":  return sibilo.BlockQuotation()
    if tag == "statement":   return sibilo.StatementBlock()     # our extension
    if tag == "object-id":   return sibilo.ObjectIdBlock()      # our extension
    if tag == "speech":      return sibilo.SpeechBlock()         # our extension
    if tag == "verse-group": return sibilo.VerseGroupBlock()     # our extension
    if tag == "array":       return sibilo.Table()
    if tag == "ref-list":    return sibilo.ListOfReferences()
    return sibilo.Block() # default, parent of doco:Paragraph in essepuntato (po)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_sct_part_class_URIRef(sct):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    tag = sct.get("tag")
    
    if tag is None and sct.get("level") == 1 and sct.get("title") == "Title": 
        return sibilo.Title()

    if tag == "sec":
        caption = sct.get("caption")
        if caption is None or len(caption)==0: return sibilo.Section()
        return sibilo.CaptionedBox()

    if tag == "abstract": return sibilo.Abstract()
    if tag == "wrap": return sibilo.Section()

    if tag == "boxed-text":
        caption = sct.get("caption")
        if caption is None or len(caption)==0: return sibilo.TextBox()
        return sibilo.CaptionedBox()

    if tag == "body": return sibilo.BodyMatter()
    if tag == "back": return sibilo.BackMatter()
    if tag == "floats-group": return sibilo.FloatMatter()  # our extension
    if tag == "app": return sibilo.Appendix()

    # return default ancestor class in case of unexpected tag
    log_it("WARNING", "No section class defined for tag:", tag)
    return sibilo.DiscourseElement()


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_split_lists(big_list, max_size):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    lists = list()
    first_el = 0
    while True:
        last_el = first_el + max_size
        if last_el > len(big_list): last_el = len(big_list)
        if last_el <= first_el: break
        lists.append(list(big_list[first_el:last_el]))
        first_el = last_el
    return lists

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def find_affiliation_name(publi, aff_id):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    affs = publi.get("affiliations")
    if affs is not None:
        for aff in affs:
            name = aff.get("name")
            if name is not None:
                if aff.get("id") == aff_id:
                    return name
                if name == aff_id:
                    return name
                if aff.get("label") == aff_id:
                    return name
    return None


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_publi_class_URIRef(article_type):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -    
    # see ontology at https://sparontologies.github.io/fabio/current/fabio.html
    # warning: do not mix Work and Expression, here we choose only Expression subclasses
    # TODO: check my mapping like the one described below:     
    # https://sourceforge.net/p/sempublishing/code/HEAD/tree/JATS2RDF/jats2rdf.pdf?format=raw

    if article_type == "research-article":  return sibilo.JournalArticle()     # a Expression 
    if article_type == "review-article":    return sibilo.ReviewArticle()      # a Expression 
    if article_type == "brief-report":      return sibilo.BriefReport()        # a Expression
    if article_type == "case-report":       return sibilo.CaseReport()         # a Expression
    if article_type == "discussion":        return sibilo.Publication()        # default value
    if article_type == "editorial":         return sibilo.Editorial()          # a Expression
    if article_type == "letter":            return sibilo.Letter()             # Expression
    if article_type == "article-commentary":return sibilo.Publication()        # default value
    if article_type == "meeting-report":    return sibilo.MeetingReport()      # a Expression
    if article_type == "correction":        return sibilo.Publication()        # default value
    return sibilo.Publication()

    # sample values found in 3000 publications
    # 2186     "article_type": "research-article",
    #  311     "article_type": "review-article",
    #   94     "article_type": "brief-report",
    #   89     "article_type": "case-report",
    #   75     "article_type": "discussion",
    #   58     "article_type": "editorial",
    #   48     "article_type": "other",
    #   45     "article_type": "letter",
    #   32     "article_type": "article-commentary",
    #   20     "article_type": "meeting-report",
    #   12     "article_type": "correction",
    #    7     "article_type": "abstract",
    #    6     "article_type": "report",
    #    6     "article_type": "news",
    #    4     "article_type": "book-review",
    #    3     "article_type": "oration",
    #    2     "article_type": "introduction",
    #    1     "article_type": "obituary",
    #    1     "article_type": "in-brief",
   

# --------------------------------------------------------------------------------
if __name__ == '__main__':
# --------------------------------------------------------------------------------
    
    # choose action
    action = sys.argv[1]
    log_it("INFO", "action:", sys.argv[1])

    fetch_dir = "./please/define/this/dir/"

    # - - - - - - - - - - - - - - - - - - - - - - - -     
    if sys.argv[1] == "build_rdf": 
    # - - - - - - - - - - - - - - - - - - - - - - - -     

        pub_per_file = 100
        max_pub = 100000000
        if len(sys.argv)>=3: max_pub = int(sys.argv[2])

        # read list of pmcid fro file generated by fetch_pam action above
        filename = fetch_dir + "pmcid_set.pickle"
        log_it("INFO", "Reading pmcid set", filename)        
        f_in = open(filename, 'rb')
        pmcid_set = pickle.load(f_in)
        f_in.close()
        pub_no = 0

        # create a ttl file for each pmcid subset
        pmcid_subsets = get_split_lists(list(pmcid_set), pub_per_file)
        for pmcid_subset in pmcid_subsets:
            offset = pub_no
            t0 = datetime.datetime.now()
            log_it("INFO", "Parsing pmcid set", filename, "offset", offset)
            ttl_file = "./output/publication_set_" + str(offset) + ".ttl"
            log_it("INFO", "Serializing to", ttl_file)
            f_out = open(ttl_file, "w")
            for pfx_line in get_prefixes():
                f_out.write(pfx_line)
            for pmcid in pmcid_subset:
                pub_no += 1
                if pub_no > max_pub: break
                subdir = fetch_dir + pmcid[:5] + "/"
                jsonfile = subdir + pmcid + ".pickle"
                log_it("INFO", "Reading publi", jsonfile, "file no.", pub_no)
                f_in = open(jsonfile, 'rb')
                publi = pickle.load(f_in)
                f_in.close()
                for l in get_triples_for_publi(publi):
                    f_out.write(l)
                for l in get_triples_for_publi_annotations(publi):
                    f_out.write(l)
            
            f_out.close()
            log_it("INFO", "Serialized", ttl_file, duration_since=t0)


    log_it("INFO", "End")
    

