import ftplib
import os
import gzip
import sys
import json
import enum
import pickle
import requests
import datetime
import urllib.parse

from rdflib import BNode, Literal, URIRef, Graph, Namespace
from rdflib.namespace import XSD,RDF, RDFS, OWL, FOAF

sibilo = Namespace("http://sibils.org/rdf#")          # sibils core ontology
sibils = Namespace("http://sibils.org/rdf/data/")     # sibils data
sibilc = Namespace("http://sibils.org/rdf/concept/")  # name space for concepts used in sibils annotation 

# sibilo defines subclasses  subproperties for all the resources defined in the namespaces below
doco = Namespace("http://purl.org/spar/doco/")
fabio = Namespace("http://purl.org/spar/fabio/")   
frbr = Namespace("http://purl.org/vocab/frbr/core#")
dcterms = Namespace("http://purl.org/dc/terms/")
prism = Namespace("http://prismstandard.org/namespaces/basic/2.0/")
openbiodiv = Namespace("http://openbiodiv.net/")
CNT = Namespace("http://www.w3.org/2011/content#") # in uppercase to avoid collision with cnt variable
deo = Namespace("http://purl.org/spar/deo/")  
po = Namespace("http://www.essepuntato.it/2008/12/pattern#")
oa = Namespace("http://www.w3.org/ns/oa#")

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def log_it(*things, duration_since=None):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    t1 = datetime.datetime.now()
    now = t1.isoformat().replace('T',' ')[:23]
    pid = "[" + str(os.getpid()) + "]"
    if duration_since is not None:
        duration = round((t1 - duration_since).total_seconds(),3)
        print(now, pid, *things, "duration", duration, flush=True)
    else:
        print(now, pid, *things, flush=True)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_new_graph():
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    graph = Graph()
    graph.bind("xsd", XSD)
    graph.bind("rdf", RDF)
    graph.bind("rdfs", RDFS)
    graph.bind("owl", OWL)
    graph.bind("foaf", FOAF)
    # - - - - - - - - - - - - - - - - - - - - - - - - 
    graph.bind(prefix="", namespace=sibilo, override=True, replace=True)  # sibils core ontology
    graph.bind("sibilc",sibilc)  # sibils concepts
    graph.bind("sibils",sibils)  # sibils data
    # - - - - - - - - - - - - - - - - - - - - - - - - 
    graph.bind("doco", doco)
    graph.bind("fabio", fabio)
    graph.bind("frbr", frbr)
    graph.bind("dcterms", dcterms)
    graph.bind("prism", prism)
    graph.bind("openbiodiv", openbiodiv)
    graph.bind(prefix="cnt", namespace=CNT, override=True, replace=True)
    graph.bind("deo", deo)
    graph.bind("po", po)
    graph.bind("oa", oa)
    return graph

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def gunzip(gz_file):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    f_in = gzip.open(gz_file, 'rb')
    decompressed_file = gz_file[0:-3]
    f_out = open(decompressed_file, 'wb')
    f_out.write(f_in.read())
    f_out. close()
    f_in. close()


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def download_chunk_from_ftp_v32(file_name):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    ftp = ftplib.FTP(ftp_server)
    ftp.login()

    # download main publication gz file if not done yet
    trg_file = proxy_dir + "bib_" + file_name
    if not os.path.exists(trg_file):
        log_it("INFO", "Downloading ", trg_file)
        ftp.cwd(publi_base_url)
        f = open(trg_file, "wb")
        ftp.retrbinary("RETR " + "bib_" + file_name, f.write)
        f.close()
        log_it("INFO", "Decompressing ", trg_file)
        gunzip(trg_file)
    else:
        log_it("INFO", "Skipped download, target file already exists", trg_file)

    # in current implementation we use only bib file to extract pmcid list and 
    # then get the json of annotated publications from sibils http service (see fetch_pam)

    # # download annot gz files if not done yet
    # trg_file = proxy_dir + "ana_" + file_name
    # if not os.path.exists(trg_file):
    #     log_it("INFO", "Downloading ", trg_file)
    #     ftp.cwd(annot_base_url)
    #     f = open(trg_file, "wb")
    #     ftp.retrbinary("RETR " + "ana_" + file_name, f.write)
    #     f.close()
    #     log_it("INFO", "Decompressing ", trg_file)
    #     gunzip(trg_file)
    # else:
    #     log_it("INFO", "Skipped download, target file already exists", trg_file)

    # # download annot gz files if not done yet
    # trg_file = proxy_dir + "sen_" + file_name
    # if not os.path.exists(trg_file):
    #     log_it("INFO", "Downloading ", trg_file)
    #     ftp.cwd(sen_base_url)
    #     f = open(trg_file, "wb")
    #     ftp.retrbinary("RETR " + "sen_" + file_name, f.write)
    #     f.close()
    #     log_it("INFO", "Decompressing ", trg_file)
    #     gunzip(trg_file)
    # else:
    #     log_it("INFO", "Skipped download, target file already exists", trg_file)

    ftp.quit()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# OK for sibils version 3.2 (not retro-compatible with v2.x)
# derive a NamedIndividual name for a terminology from its correxponding concept_source
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
    return URIRef(sibilc + encoded_name)    

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# OK for sibils version 3.2 (not retro-compatible with v2.x)
def get_term_URIRef_from_term(concept_id, terminology):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    db = get_terminology_NI_name(terminology["concept_source"])
    ac = concept_id
    name = db + "|" +ac
    encoded_name = urllib.parse.quote(name)
    return URIRef(sibilc + encoded_name)    

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# OK for sibils version 3.2 (not retro-compatible with v2.x)
def get_terminology_URIRef(terminology):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    name = get_terminology_NI_name(terminology["concept_source"])
    encoded_name = urllib.parse.quote(name)
    uri = URIRef(sibilo + encoded_name)
    return uri

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_triples_for_publi_annotations(publi):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    publi_doc = publi["document"]
    publi_uri = get_publi_URIRef(publi_doc)
    annotations = publi["annotations"]
    for annot in annotations:
        
        annot_bn = BNode()
        graph.add((publi_uri, URIRef(sibilo.hasAnnotation), annot_bn)) # simple way to link an annotation to its target publi
        graph.add((annot_bn, RDF.type, sibilo.Annotation))
        graph.add((annot_bn, sibilo.hasBody,  get_term_URIRef_from_annot(annot))) # the named entity found
        target_bn = BNode()
        graph.add((annot_bn, sibilo.hasTarget, target_bn))
        # only sentences are annotated since version 3.2
        part_uri = get_sentence_part_URIRef(publi_uri, annot) # sentence_number is an annot property
        graph.add((target_bn, RDF.type, sibilo.AnnotationTarget))
        graph.add((target_bn, sibilo.hasSource, part_uri))
        selector_bn = BNode()
        graph.add((target_bn, sibilo.hasSelector, selector_bn))
        graph.add((selector_bn, RDF.type, sibilo.TextPositionSelector))
        start_pos = int(annot["start_index"]) # index of concept form in the sentence
        graph.add((selector_bn, sibilo.start, Literal(start_pos, datatype=XSD.integer)))
        end_pos = start_pos + int(annot["concept_length"])
        graph.add((selector_bn, sibilo.end, Literal(end_pos, datatype=XSD.integer)))
        concept_form = annot["concept_form"]
        graph.add((selector_bn, sibilo.exact, Literal(concept_form, datatype=XSD.string)))        
        

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_triples_for_publi(publi):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    
    publi_doc = publi["document"]

    pmcid = publi_doc["pmcid"]
    log_it("INFO", "pmcid", pmcid)

    publi_uri = get_publi_URIRef(publi_doc)
    publi_class_uri = get_publi_class_URIRef(publi_doc["article_type"])  
    graph.add((publi_uri , RDF.type, publi_class_uri))
    
    graph.add((publi_uri, sibilo.hasPubMedCentralId, Literal(pmcid, datatype=XSD.string)))

    medline_ta = publi_doc.get("medline_ta")
    if medline_ta is not None:
        graph.add((publi_uri, sibilo.hasNLMJournalTitleAbbreviation, Literal(medline_ta, datatype=XSD.string)))

    pmid = publi_doc.get("pmid")
    if pmid is not None:
        graph.add((publi_uri, sibilo.hasPubMedId, Literal(pmid, datatype=XSD.string)))
    
    doi = publi_doc.get("doi")
    if doi is not None:
        graph.add((publi_uri, sibilo.doi, Literal(doi, datatype=XSD.string)))
        
    pubyear = publi_doc.get("pubyear")
    if pubyear is not None:
        graph.add((publi_uri, sibilo.hasPublicationYear, Literal(pubyear, datatype=XSD.integer)))
    
    pubdate = publi_doc.get("publication_date")
    if pubdate is not None:
        graph.add((publi_uri, sibilo.publicationDate, Literal(date_to_yyyy_mm_dd(pubdate), datatype=XSD.date)))
    
    keywords = publi_doc.get("keywords")
    if keywords is not None and isinstance(keywords,list):
        for k in keywords:
            graph.add((publi_uri, sibilo.keyword, Literal(k, datatype=XSD.string)))
    
    issue = publi_doc.get("issue")
    if issue is not None and len(issue)>0:
        graph.add((publi_uri, sibilo.issueIdentifier, Literal(issue, datatype=XSD.string)))

    volume = publi_doc.get("volume")
    if issue is not None and len(volume)>0:
        graph.add((publi_uri, sibilo.volume, Literal(volume, datatype=XSD.string)))

    # starting, ending page and page range,
    # see https://sourceforge.net/p/sempublishing/code/HEAD/tree/JATS2RDF/jats2rdf.pdf?format=raw
    blank_node = BNode()
    bn_empty = True
    o = publi_doc.get("start_page")
    if o is not None and len(o)>0 : 
        bn_empty = False
        graph.add((blank_node, sibilo.startingPage, Literal(o, datatype=XSD.string)))

    o = publi_doc.get("end_page")
    if o is not None and len(o)>0 : 
        bn_empty = False
        graph.add((blank_node, sibilo.endingPage, Literal(o, datatype=XSD.string)))

    o = publi_doc.get("medline_pgn")
    if o is not None and len(o)>0 : 
        bn_empty = False
        graph.add((blank_node, sibilo.pageRange, Literal(o, datatype=XSD.string)))
    
    if not bn_empty:
        graph.add((blank_node, RDF.type, sibilo.Manifestation))
        graph.add((publi_uri, sibilo.embodiment, blank_node))
    # end page stuff
    
    o = publi_doc.get("title")
    if o is not None and len(o)>0 : 
        graph.add((publi_uri, sibilo.title, Literal(o, datatype=XSD.string)))
    
    o = publi_doc.get("abstract")
    if o is not None and len(o)>0 : 
        graph.add((publi_uri, sibilo.abstract, Literal(o, datatype=XSD.string)))
    
    add_triples_for_authors(publi_doc)
            
    # create FrontMatter
    front_uri = get_front_matter_URIRef(publi_uri)
    graph.add((publi_uri, sibilo.contains, front_uri))
    graph.add((front_uri, RDF.type, sibilo.FrontMatter ))
    
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
                graph.add((parent_uri, sibilo.contains, sct_uri ))
                part_class_uri = get_sct_part_class_URIRef(sct)
                graph.add((sct_uri, RDF.type, part_class_uri ))

                # # DEBUG: add sct_uri to parent_dic
                # parent_dic[parent_uri]=list()
                # parent_dic[sct_uri]=list()
                # # end DEBUG

                # add section caption if appropriate
                # note: no sentences are generated by Julien for sct["caption"]
                # kept as a blank node because never used in annotations
                if part_class_uri == sibilo.CaptionedBox:
                    blank_node = BNode()
                    graph.add((blank_node, RDF.type, sibilo.Caption))
                    graph.add((blank_node, sibilo.chars, Literal(sct["caption"], datatype=XSD.string) ))
                    graph.add((sct_uri, sibilo.hasPart, blank_node))
                
                # add section title if appropriate
                # note: sentences related to sct["title"] have sen["field"] = "section_title"
                sct_title = sct.get("title")
                if sct_title is not None and len(sct_title)>0 and sct_title != "Title" and sct_title != "Abstract":
                    tit_uri = get_part_title_URIRef(sct_uri)
                    graph.add((tit_uri, RDF.type, sibilo.SectionLabel))
                    graph.add((sct_uri, sibilo.hasPart, tit_uri))

                    # # DEBUG: add tit_uri to parent_dic
                    # parent_dic[tit_uri]=list()
                    # # end DEBUG

                # add section contents
                for cnt in sct["contents"]:

                    # link to parent section and set content class
                    cnt_uri = get_part_URIRef(publi_uri, cnt)
                    graph.add((sct_uri, sibilo.contains, cnt_uri))
                    graph.add((cnt_uri, RDF.type, get_cnt_part_class_URIRef(cnt)))

                    # # DEBUG: add tit_uri to parent_dic
                    # parent_dic[cnt_uri]=list()
                    # # end DEBUG

                    xrefUrl = cnt.get("xref_url")
                    if xrefUrl:
                        graph.add((cnt_uri, RDFS.seeAlso, URIRef(xrefUrl)))
                        
                    capt = cnt.get("caption")
                    if capt:
                        capt_uri = get_part_caption_URIRef(cnt_uri)
                        graph.add((cnt_uri, sibilo.hasPart, capt_uri))
                        graph.add((capt_uri, RDF.type, sibilo.Caption))
                        # # DEBUG: add tit_uri to parent_dic
                        # parent_dic[capt_uri]=list()
                        # # end DEBUG


                    label = cnt.get("label")
                    if label:
                        label_uri = get_part_label_URIRef(cnt_uri)
                        graph.add((cnt_uri, sibilo.hasPart, label_uri))
                        graph.add((label_uri, RDF.type, sibilo.Label))
                        # note: no sentences are generated by Julien for cnt["label"], so declare :chars here
                        # often used for figs and tables (i.e. Fig 1, Table 2)
                        graph.add((label_uri, sibilo.chars, Literal(label, datatype=XSD.string)))
                        # # DEBUG: add tit_uri to parent_dic
                        # parent_dic[label_uri]=list()
                        # # end DEBUG

                    foot = cnt.get("footer")
                    if foot:
                        foot_uri = get_part_footer_URIRef(cnt_uri)
                        graph.add((cnt_uri, sibilo.hasPart, foot_uri))
                        graph.add((foot_uri, RDF.type, sibilo.TableFooter))
                        # # DEBUG: add tit_uri to parent_dic
                        # parent_dic[foot_uri]=list()
                        # # end DEBUG

        else:
            log_it("INFO", sct_list_name, "empty")

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
        graph.add((sen_parent_uri, sibilo.contains, sen_uri))
        sen_class = get_sen_part_class_URIRef(sen) 
        graph.add((sen_uri, RDF.type, sen_class))
        graph.add((sen_uri, sibilo.chars, Literal(sen_txt, datatype=XSD.string)))
        sen_ord = int(sen["sentence_number"])
        graph.add((sen_uri, sibilo.ordinal, Literal(sen_ord, datatype=XSD.integer)))

        # # DEBUG add sen_uri / parent pair to dico
        # sen_parent_dic[sen_uri]=sen_parent_uri

    # # DEBUG check parent parts of sentences are all defined above in sct / content
    # print("Checking sentences all have a parent part")
    # for sen_uri in sen_parent_dic:
    #     parent_uri = sen_parent_dic[sen_uri]
    #     if parent_uri not in parent_dic:
    #         print("ERROR, sentence with no parent", sen_uri, "parent", parent_uri)
    #     else:
    #         parent_dic[parent_uri].append(sen_uri)
    #         print("INFO", sen_uri, parent_uri)
    # print("Checked", len(sen_parent_dic),"sentences")


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def date_to_yyyy_mm_dd(dd_mm_yyyy):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    d,m,y = dd_mm_yyyy.split("-")
    return y + "-" + m + "-" + d
    
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def flatten_nested_lists(elem, flat_list):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    if isinstance(elem, list):
        for item in elem:
            flatten_nested_lists(item, flat_list)
    else:
        flat_list.append(elem)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def add_triples_for_authors(publi):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    author_list = publi.get("authors")
    if author_list is not None:
        for author in author_list:
            blank_node = BNode()
            graph.add((blank_node, RDF.type, FOAF.Person))
            graph.add((blank_node, RDFS.label, Literal(author.get("name"), datatype=XSD.string)))
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
                                    graph.add((blank_node, sibilo.affiliation, Literal(aff_name, datatype=XSD.string)))
                        if not found:
                            log_it("ERROR", "found no name for affiliation id", aff_id, "in", pmcid)
                    else:
                        graph.add((blank_node, sibilo.affiliation, Literal(aff_name, datatype=XSD.string)))

            graph.add((get_publi_URIRef(publi), sibilo.creator, blank_node))


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_publi_URIRef(publi):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    pmcid = publi.get("pmcid")
    return URIRef(sibils + pmcid)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_front_matter_URIRef(publi_uri):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    return URIRef(publi_uri + "_part_frontMatter")

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_part_label_URIRef(part_uri):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    return URIRef(part_uri + "_label")

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_part_caption_URIRef(part_uri):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    return URIRef(part_uri + "_caption")

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_part_footer_URIRef(part_uri):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    return URIRef(part_uri + "_footer")

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_part_title_URIRef(part_uri):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    return URIRef(part_uri + "_title")

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_sentence_part_URIRef(publi_uri, sentence_or_annot):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    part_id = str(sentence_or_annot.get("sentence_number"))
    return URIRef(publi_uri + "_sen_" + part_id)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_sentence_parent_part_URIRef(publi_uri, sen):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    parent_id = sen["content_id"]
    publi_uri + "_part_" + parent_id


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_part_URIRef(publi_uri, sct):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    part_id = sct.get("id")
    return URIRef(publi_uri + "_part_" + part_id)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_parent_part_URIRef(publi_uri, part):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    fld = part.get("field")
    # case 1: part is a sentence
    if fld is not None:
        part_id = part["content_id"]
        # by order of frequency in data to improve preformance
        if fld == "text": return URIRef(publi_uri + "_part_" + part_id)
        if fld == "fig_caption": return URIRef(publi_uri + "_part_" + part_id + "_caption")
        if fld == "section_title": return URIRef(publi_uri + "_part_" + part_id + "_title")
        if fld == "table_column": return URIRef(publi_uri + "_part_" + part_id)
        if fld == "table_footer": return URIRef(publi_uri + "_part_" + part_id + "_footer")
        if fld == "table_value": return URIRef(publi_uri + "_part_" + part_id)
        if fld == "table_caption": return URIRef(publi_uri + "_part_" + part_id + "_caption")
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
        return URIRef(publi_uri + "_part_" + parent_id)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_sen_part_class_URIRef(sentence):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    fld = sentence.get("field")
    if fld == "table_column": return sibilo.TableColumnName
    if fld == "table_value": return sibilo.TableCellValues
    return sibilo.Sentence

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_cnt_part_class_URIRef(cnt):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # sibilo classes below could be defined as sub classes of po:Block
    tag = cnt.get("tag")
    if tag == "p":           return sibilo.Paragraph
    if tag == "fig":         return sibilo.FigureBox
    if tag == "table":       return sibilo.TableBox
    if tag == "list-item":   return sibilo.ListItemBlock      # our extension
    if tag == "media":       return sibilo.MediaBlock         # our extension
    if tag == "def-list":    return sibilo.Glossary
    if tag == "disp-quote":  return sibilo.BlockQuotation
    if tag == "statement":   return sibilo.StatementBlock     # our extension
    if tag == "object-id":   return sibilo.ObjectIdBlock      # our extension
    if tag == "speech":      return sibilo.SpeechBlock         # our extension
    if tag == "verse-group": return sibilo.VerseGroupBlock     # our extension
    if tag == "array":       return sibilo.Table
    if tag == "ref-list":    return sibilo.ListOfReferences
    return sibilo.Block # default, parent of doco:Paragraph in essepuntato (po)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_sct_part_class_URIRef(sct):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    tag = sct.get("tag")
    
    if tag is None and sct.get("level") == 1 and sct.get("title") == "Title": 
        return sibilo.Title

    if tag == "sec":
        caption = sct.get("caption")
        if caption is None or len(caption)==0: return sibilo.Section
        return sibilo.CaptionedBox

    if tag == "abstract": return sibilo.Abstract
    if tag == "wrap": return sibilo.Section

    if tag == "boxed-text":
        caption = sct.get("caption")
        if caption is None or len(caption)==0: return sibilo.TextBox
        return sibilo.CaptionedBox

    if tag == "body": return sibilo.BodyMatter
    if tag == "back": return sibilo.BackMatter
    if tag == "floats-group": return sibilo.FloatMatter  # our extension
    if tag == "app": return sibilo.Appendix

    # return default ancestor class in case of unexpected tag
    log_it("WARNING", "No section class defined for tag:", tag)   
    return sibilo.DiscourseElement


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

    if article_type == "research-article":  return sibilo.JournalArticle     # a Expression 
    if article_type == "review-article":    return sibilo.ReviewArticle      # a Expression 
    if article_type == "brief-report":      return sibilo.BriefReport        # a Expression
    if article_type == "case-report":       return sibilo.CaseReport         # a Expression
    if article_type == "discussion":        return sibilo.Publication        # default value
    if article_type == "editorial":         return sibilo.Editorial          # a Expression
    if article_type == "letter":            return sibilo.Letter             # Expression
    if article_type == "article-commentary":return sibilo.Publication        # default value
    if article_type == "meeting-report":    return sibilo.MeetingReport      # a Expression
    if article_type == "correction":        return sibilo.Publication        # default value
    return sibilo.Publication

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
    global ftp_server, annot_base_url, publi_base_url, proxy_dir, ftp_content
    global graph

    ftp_server = "denver.hesge.ch"
    #annot_base_url = "/SIBiLS/anapmc21/baseline/"
    #publi_base_url = "/SIBiLS_v3/bibpmc/baseline/"

    annot_base_url = "/SIBiLS_v3.2/pmc/baseline/ana/v1/"
    publi_base_url = "/SIBiLS_v3.2/pmc/baseline/bib/"
    sen_base_url = "/SIBiLS_v3.2/pmc/baseline/sen/"

    proxy_dir = "./proxy_dir/v32/"
    fetch_dir = proxy_dir + "fetch_pam/"
    prefixes = dict()
    
    # choose action
    action = sys.argv[1]
    log_it("INFO", "action:", sys.argv[1])

    # - - - - - - - - - - - - - - - - - - - - - - - -     
    if sys.argv[1] == "download":
    # - - - - - - - - - - - - - - - - - - - - - - - -       
        file_name = "pmc23n0023.json.gz"
        download_chunk_from_ftp_v32(file_name)

    # - - - - - - - - - - - - - - - - - - - - - - - -     
    elif sys.argv[1] == "fetch_pam":
    # - - - - - - - - - - - - - - - - - - - - - - - -     
        ## get set of pmcid and save it as a file
        file_name = "bib_pmc23n0023.json"
        json_file = proxy_dir + file_name
        f_in = open(json_file, "rb")
        obj = json.load(f_in)        
        f_in.close()
        pmcid_set = set()
        publi_list = obj["article_list"]
        for publi in publi_list:
            pmcid = publi["pmcid"]
            pmcid_set.add(pmcid)
        filename = fetch_dir + "pmcid_set.pickle"
        f_out = open(filename, 'wb')
        pickle.dump(pmcid_set, f_out, protocol=3) 
        f_out.close()
        log_it("Saved pmcid set ", filename, "len(pmcid_set)", len(pmcid_set))
        # use fetch_pam to retrieve batches of json publications with annotations
        while pmcid_set:
            ids = ""
            for i in range(30):
                if pmcid_set:
                    if len(ids)>0: ids += ","
                    ids += pmcid_set.pop()
            # v2.x url = "https://candy.hesge.ch/SIBiLS/PMC/fetch_PAM.jsp?ids=" + ids
            # v3.2 - use default format
            url = "https://sibils.text-analytics.ch/api/v3.2/fetch?col=pmc&ids=" + ids
            log_it("INFO", "### url", url)
            response = requests.get(url)
            log_it("INFO", "Got response")
            data = response.json()
            log_it("INFO", "Parsed response")
            publi_sublist = data["sibils_article_set"]
            for publi in publi_sublist:
                pmcid = publi.get("_id") # _id contains pmcid or doi or pmid depending on collection
                subdir = fetch_dir + pmcid[:5] + "/"
                os.makedirs(subdir, exist_ok=True)
                jsonfile = subdir + pmcid + ".pickle"
                f_out = open(jsonfile, 'wb')
                pickle.dump(publi, f_out, protocol=3) 
                f_out.close()
                log_it("INFO", "Saved", jsonfile)


    # - - - - - - - - - - - - - - - - - - - - - - - -     
    elif sys.argv[1] == "test1":
    # - - - - - - - - - - - - - - - - - - - - - - - -     
        max_pub = 100000000
        if len(sys.argv)>=3: max_pub = int(sys.argv[2])
        # read list of pmcid fro file generated by fetch_pam action above
        filename = fetch_dir + "pmcid_set.pickle"
        log_it("INFO", "Reading pmcid set", filename)
        f_in = open(filename, 'rb')
        pmcid_set = pickle.load(f_in)
        f_in.close()
        pub_no = 0
        for pmcid in pmcid_set:
            sct_dic = dict()
            offset = pub_no
            pub_no += 1
            if pub_no > max_pub: break
            subdir = fetch_dir + pmcid[:5] + "/"
            jsonfile = subdir + pmcid + ".pickle"
            log_it("INFO", "Reading publi", jsonfile, "file no.", pub_no)
            f_in = open(jsonfile, 'rb')
            publi = pickle.load(f_in)
            publi_doc = publi["document"]
            for sct_group in ["body_sections","float_sections", "back_sections"]:
                for sct in publi_doc[sct_group]:
                    hasTitle = False
                    sct_title = sct.get("title")
                    if sct_title is not None and len(sct_title)>0 and sct_title != "Title" and sct_title != "Abstract": hasTitle = True
                    sct_caption = sct.get("caption")
                    hasCaption = False
                    if sct_caption is not None and len(sct_caption)>0: hasCaption = True
                    if hasTitle or hasCaption:
                        sct_id = sct["id"]
                        sct_dic[sct_id] = {"hasTitle": hasTitle, "hasCaption": hasCaption, "title": sct_title, "caption": sct_caption, "sentences": list()}
            for sen in publi["sentences"]:
                cnt_id = sen["content_id"]
                if cnt_id == "0": continue
                if cnt_id in sct_dic:
                    fld = sen["field"]
                    txt = sen["sentence"]
                    sct_dic[cnt_id]["sentences"].append({"field":fld, "txt":txt})
            f_in.close()
            log_it("pmcid", pmcid)
            for id in sct_dic:
                rec = sct_dic[id]
                #print("section", id, "hasTitle", rec["hasTitle"], "hasCaption", rec["hasCaption"])
                if rec["hasTitle"]== True:   print("section   title :", id, rec["title"])
                if rec["hasCaption"]== True: print("section caption :", id, rec["caption"])
                for sen in rec["sentences"]:
                    print("sentence        :", id, sen["field"], sen["txt"])
            log_it("----")

    # - - - - - - - - - - - - - - - - - - - - - - - -     
    elif sys.argv[1] == "parse":
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
            graph = get_new_graph()
            log_it("INFO", "Parsing pmcid set", filename, "offset", offset)
            for pmcid in pmcid_subset:
                pub_no += 1
                if pub_no > max_pub: break
                subdir = fetch_dir + pmcid[:5] + "/"
                jsonfile = subdir + pmcid + ".pickle"
                log_it("INFO", "Reading publi", jsonfile, "file no.", pub_no)
                f_in = open(jsonfile, 'rb')
                publi = pickle.load(f_in)
                f_in.close()
                log_it("INFO","Building RDF for current publi")
                get_triples_for_publi(publi)
                get_triples_for_publi_annotations(publi)
                
            ttl_file = "./output/publication_set_" + str(offset) + ".ttl"
            log_it("INFO", "Serializing to", ttl_file)
            t0 = datetime.datetime.now()
            graph.serialize(destination=ttl_file , format="turtle", encoding="utf-8")
            log_it("INFO", "Serialized", ttl_file, duration_since=t0)

    log_it("INFO", "End")
    

