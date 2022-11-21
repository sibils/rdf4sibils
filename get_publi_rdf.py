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
def get_content_from_ftp():
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    content = dict()
    ftp = ftplib.FTP(ftp_server)
    ftp.login() 
    ftp.cwd(publi_base_url)
    pub_files = ftp.nlst()    
    pub_files.sort()
    content["pub_files"] = pub_files
    ftp.cwd(annot_base_url)
    annot_dirs = ftp.nlst()   
    annot_dirs.remove("covoc") # temp ignored cos contains its own subdirs
    content["annot_dirs"] = annot_dirs
    ftp.quit()
    # also create once for all the subdirectory needed for each annot type
    for item in annot_dirs:
        annot_dir = proxy_dir + item + "/"
        if not os.path.exists(annot_dir):
            os.makedirs(annot_dir)
    return content

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def download_chunk_from_ftp(file_name):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    ftp = ftplib.FTP(ftp_server)
    ftp.login()
    trg_file = proxy_dir + file_name
    # download main publication gz file if not done yet
    if not os.path.exists(trg_file):
        ftp.cwd(publi_base_url)
        print("### Getting chunk", proxy_dir + file_name)
        f = open(trg_file, "wb")
        ftp.retrbinary("RETR " + file_name, f.write)
        f.close()
        gunzip(trg_file)
    # download annot gz files if not done yet
    for subdir in ftp_content["annot_dirs"]:
        local_dir = proxy_dir + subdir + "/"
        local_file = local_dir + file_name
        if not os.path.exists(local_file):
            remote_dir = annot_base_url + subdir + "/"
            ftp.cwd(remote_dir)
            f = open(local_file, "wb")
            try:
                ftp.retrbinary("RETR " + file_name, f.write)
                f.close()
                gunzip(local_file)
            except ftplib.error_perm as e:
                print("### WARNING", remote_dir + file_name, repr(e))
                f.close()
                if os.path.exists(local_file): os.remove(local_file)

    ftp.quit()



# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# OK for sibils version 2.x
def get_term_URIRef_from_annot(annot):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    type = annot["type"]
    src = annot["concept_source"]
    db = src + "_" + type
    db = db.replace(" ","_")
    ac = annot["concept_id"]
    name = db + "|" +ac
    encoded_name = urllib.parse.quote(name)
    return URIRef(sibilc + encoded_name)    

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# OK for sibils version 2.x
def get_term_URIRef_from_term(concept_id, terminology):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    type = terminology["term_type"]
    src = terminology["term_source"]
    db = src + "_" + type
    db = db.replace(" ","_")
    ac = concept_id
    name = db + "|" +ac
    encoded_name = urllib.parse.quote(name)
    return URIRef(sibilc + encoded_name)    

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# OK for sibils version 2.x
def get_terminology_URIRef(terminology):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    type = terminology["term_type"]
    src = terminology["term_source"]
    name = src + "_" + type
    name = name.replace(" ","_")
    encoded_name = urllib.parse.quote(name)
    uri = URIRef(sibilo + encoded_name)
    return uri


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_triples_for_publi_annotations(publi):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    annotations = publi.get("annotation")
    publi_uri = get_publi_URIRef(publi)
    for annot in annotations:
        
        # - - - temp / for debug  - - -
        typ = annot["type"]
        src = annot["concept_source"]
        key = typ + " | " + src
        if key not in termino_dic: termino_dic[key]=0
        termino_dic[key] += 1        
        # - - - - - - - - - - - - - - -
        
        annot_bn = BNode()
        graph.add((publi_uri, URIRef(sibilo.hasAnnotation), annot_bn)) # simple way to link an annotation to its target publi
        graph.add((annot_bn, RDF.type, sibilo.Annotation))
        graph.add((annot_bn, sibilo.hasBody,  get_term_URIRef_from_annot(annot))) # the named entity found
        target_bn = BNode()
        graph.add((annot_bn, sibilo.hasTarget, target_bn))
        
        part_uri = get_part_URIRef(publi_uri, annot)
        subfield = (annot.get("subfield") or "").lower()
        if subfield == "caption":
            part_uri = get_part_caption_URIRef(part_uri)
        elif subfield == "footer":
            part_uri = get_part_footer_URIRef(part_uri)
            
        graph.add((target_bn, RDF.type, sibilo.AnnotationTarget))
        graph.add((target_bn, sibilo.hasSource, part_uri))
        selector_bn = BNode()
        graph.add((target_bn, sibilo.hasSelector, selector_bn))
        graph.add((selector_bn, RDF.type, sibilo.TextPositionSelector))
        start_pos = int(annot["concept_offset_in_section"]) # is actually offset in content, not in section !!!
        graph.add((selector_bn, sibilo.start, Literal(start_pos, datatype=XSD.integer)))
        end_pos = start_pos + int(annot["concept_length"])
        graph.add((selector_bn, sibilo.end, Literal(end_pos, datatype=XSD.integer)))
        concept_form = annot["concept_form"]
        graph.add((selector_bn, sibilo.exact, Literal(concept_form, datatype=XSD.string)))        
        

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_triples_for_publi(publi):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    
    pmcid = publi["pmcid"]
    print("### INFO", "pmcid", pmcid)

    publi_uri = get_publi_URIRef(publi)
    publi_class_uri = get_publi_class_URIRef(publi["article_type"])  
    graph.add((publi_uri , RDF.type, publi_class_uri))
    
    graph.add((publi_uri, sibilo.hasPubMedCentralId, Literal(pmcid, datatype=XSD.string)))

    medline_ta = publi.get("medline_ta")
    if medline_ta is not None:
        graph.add((publi_uri, sibilo.hasNLMJournalTitleAbbreviation, Literal(medline_ta, datatype=XSD.string)))

    pmid = publi.get("pmid")
    if pmid is not None:
        graph.add((publi_uri, sibilo.hasPubMedId, Literal(pmid, datatype=XSD.string)))
    
    doi = publi.get("doi")
    if doi is not None:
        graph.add((publi_uri, sibilo.doi, Literal(doi, datatype=XSD.string)))
        
    pubyear = publi.get("pubyear")
    if pubyear is not None:
        graph.add((publi_uri, sibilo.hasPublicationYear, Literal(pubyear, datatype=XSD.integer)))
    
    pubdate = publi.get("publication_date")
    if pubdate is not None:
        graph.add((publi_uri, sibilo.publicationDate, Literal(date_to_yyyy_mm_dd(pubdate), datatype=XSD.date)))
    
    keywords = publi.get("keywords")
    if keywords is not None and isinstance(keywords,list):
        for k in keywords:
            graph.add((publi_uri, sibilo.keyword, Literal(k, datatype=XSD.string)))
    
    issue = publi.get("issue")
    if issue is not None and len(issue)>0:
        graph.add((publi_uri, sibilo.issueIdentifier, Literal(issue, datatype=XSD.string)))

    volume = publi.get("volume")
    if issue is not None and len(volume)>0:
        graph.add((publi_uri, sibilo.volume, Literal(volume, datatype=XSD.string)))

    # starting, ending page and page range,
    # see https://sourceforge.net/p/sempublishing/code/HEAD/tree/JATS2RDF/jats2rdf.pdf?format=raw
    # :textual-entity frbr:embodiment [
    # a fabio:Manifestation ;
    # prism:startingPage “XXX” ;
    # prism:endingPage “WWW” ;
    # prism:pageRange “XXX-YYY, ZZZ-WWW” ] .
    blank_node = BNode()
    bn_empty = True
    o = publi.get("start_page")
    if o is not None and len(o)>0 : 
        bn_empty = False
        graph.add((blank_node, sibilo.startingPage, Literal(o, datatype=XSD.string)))

    o = publi.get("end_page")
    if o is not None and len(o)>0 : 
        bn_empty = False
        graph.add((blank_node, sibilo.endingPage, Literal(o, datatype=XSD.string)))

    o = publi.get("medline_pgn")
    if o is not None and len(o)>0 : 
        bn_empty = False
        graph.add((blank_node, sibilo.pageRange, Literal(o, datatype=XSD.string)))
    
    if not bn_empty:
        graph.add((blank_node, RDF.type, sibilo.Manifestation))
        graph.add((publi_uri, sibilo.embodiment, blank_node))
    # end page stuff
    
    o = publi.get("title")
    if o is not None and len(o)>0 : 
        graph.add((publi_uri, sibilo.title, Literal(o, datatype=XSD.string)))
    
    o = publi.get("abstract")
    if o is not None and len(o)>0 : 
        graph.add((publi_uri, sibilo.abstract, Literal(o, datatype=XSD.string)))
    
    add_triples_for_authors(publi)
            
    # create FrontMatter
    front_uri = get_front_matter_URIRef(publi_uri)
    graph.add((publi_uri, sibilo.contains, front_uri))
    graph.add((front_uri, RDF.type, sibilo.FrontMatter ))
    
    # add sections
    sct_list_names = ["body_sections", "back_sections", "float_sections"]
    for sct_list_name in sct_list_names:
        sct_list = publi.get(sct_list_name)
        if len(sct_list)>0: 
            for sct in sct_list:
                
                # ------- temp / for debug -------
                value = pmcid + "." + sct["id"]
                capt = sct.get("caption")
                if capt is not None and len(capt)>0:
                    if value not in sct_uuids: sct_uuids[value] = 0
                # --------------------------------
                
                parent_uri = get_part_parent_URIRef(publi_uri, sct)
                sct_uri = get_part_URIRef(publi_uri, sct)
                
                # create part type and part parent relationship 
                graph.add((parent_uri, sibilo.contains, sct_uri ))
                
                part_class_uri = get_sct_part_class_URIRef(sct)
                graph.add((sct_uri, RDF.type, part_class_uri ))

                # add section caption if apprropriate
                if part_class_uri == sibilo.CaptionedBox:
                    blank_node = BNode()
                    graph.add((blank_node, RDF.type, sibilo.Caption))
                    graph.add((blank_node, sibilo.chars, Literal(sct["caption"], datatype=XSD.string) ))
                    graph.add((sct_uri, sibilo.hasPart, blank_node))                  
                
                # add section title if apprropriate
                sct_title = sct.get("title")
                if sct_title is not None and len(sct_title)>0 and sct_title != "Title" and sct_title != "Abstract":
                    blank_node = BNode()
                    graph.add((blank_node, RDF.type, sibilo.SectionLabel))
                    graph.add((blank_node, sibilo.chars, Literal(sct_title, datatype=XSD.string)))
                    graph.add((sct_uri, sibilo.hasPart, blank_node))
                
                # add section contents
                for cnt in sct["contents"]:
                    
                    # ------- temp / for debug -------
                    tag = cnt["tag"]
                    if tag not in cnt_cls_spl: cnt_cls_spl[tag] = list()
                    lst = cnt_cls_spl[tag]
                    if len(lst) < 3: lst.append(pmcid)
                    
                    for fld in cnt:
                        if fld not in cnt_fields: cnt_fields[fld] = 0
                        cnt_fields[fld] += 1
                    # ----------------------------------
                        
                    # link to parent section and set content class
                    cnt_uri = get_part_URIRef(publi_uri, cnt)
                    graph.add((sct_uri, sibilo.contains, cnt_uri))
                    graph.add((cnt_uri, RDF.type, get_cnt_part_class_URIRef(cnt)))
                    
                    # set textual content
                    if cnt.get("text"):
                        graph.add((cnt_uri, sibilo.chars, Literal(cnt.get("text"), datatype=XSD.string)))

                    # set textual content of tables                    
                    cols = cnt.get("table_columns")
                    vals = cnt.get("table_values")
                    if cols or vals:
                        tokens = list()
                        chars = ""
                        if cols: flatten_nested_lists(cols, tokens)
                        if vals: flatten_nested_lists(vals, tokens)
                        chars = " ".join(tokens).replace("\n"," ")
                        graph.add((cnt_uri, sibilo.chars, Literal(chars, datatype=XSD.string)))

                    xrefUrl = cnt.get("xref_url")
                    if xrefUrl:
                        graph.add((cnt_uri, RDFS.seeAlso, URIRef(xrefUrl)))
                        
                    capt = cnt.get("caption")
                    if capt:
                        capt_uri = get_part_caption_URIRef(cnt_uri)
                        graph.add((cnt_uri, sibilo.hasPart, capt_uri))
                        graph.add((capt_uri, RDF.type, sibilo.Caption))
                        graph.add((capt_uri, sibilo.chars, Literal(capt, datatype=XSD.string)))

                    label = cnt.get("label")
                    if label:
                        label_uri = get_part_label_URIRef(cnt_uri)
                        graph.add((cnt_uri, sibilo.hasPart, label_uri))
                        graph.add((label_uri, RDF.type, sibilo.Label))
                        graph.add((label_uri, sibilo.chars, Literal(label, datatype=XSD.string)))

                    foot = cnt.get("footer")
                    if foot:
                        foot_uri = get_part_footer_URIRef(cnt_uri)
                        graph.add((cnt_uri, sibilo.hasPart, foot_uri))
                        graph.add((foot_uri, RDF.type, sibilo.TableFooter))
                        graph.add((foot_uri, sibilo.chars, Literal(foot, datatype=XSD.string)))

        else:
            print("### INFO", sct_list_name, "empty")

    # temp / for debug
    annotations = publi.get("annotation")
    for annot in annotations:
        uuid = pmcid + "." + annot["content_id"]
        if uuid in sct_uuids:
            sct_uuids[uuid] += 1
        
        k = annot.get("field")
        if annot.get("subfield"): k += "/" + annot.get("subfield")
        if not k in ann_fld_dic: ann_fld_dic[k] = 0
        ann_fld_dic[k] += 1
        

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
                            print("### ERROR", "found no name for affiliation id", aff_id, "in", pmcid)
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
def get_part_URIRef(publi_uri, part_or_annot):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # the second parameter can be a part or an annotation
    # we retrieve the part_id from a part using the "id" key or 
    # we retrieve the part_id from an annotation using the "content_id" key
    part_id = part_or_annot.get("id") or part_or_annot.get("content_id")
    return URIRef(publi_uri + "_part_" + part_id)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def get_part_parent_URIRef(publi_uri, part):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    if part.get("level") == 1:
        tag = part.get("tag")
        if tag is None and part.get("title")== "Title": 
            return  get_front_matter_URIRef(publi_uri)
        elif tag == "abstract":
            return  get_front_matter_URIRef(publi_uri)
        else:
            return publi_uri
    else:            
        part_id = part.get("id")
        # parent id: remove everything from right until LAST <dot> is reached
        parent_id = part_id[:part_id.rfind(".")]
        return URIRef(publi_uri + "_part_" + parent_id)


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
    print("### WARNING", "No section class defined for tag:", tag)   
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
   
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def print_debug_info():
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        print("### Sct with title and annotations")
        for k in sct_uuids:
            if sct_uuids[k]>0:
                print("### sct",k, "annot count:", sct_uuids[k])
            
        print("### Cnt fld list")
        for k in cnt_fields:
            print("### cnt fld",k, cnt_fields[k])
            
        print("### Annot fld/subfield values")
        for k in ann_fld_dic:
            print("### annot fld/subfield",k, ann_fld_dic[k])
        
        print("### Cnt class / examples")
        for cls in cnt_cls_spl:
            print("###", cls, cnt_cls_spl[cls])

        print("### terminology type / source, concept count")
        keys = [k for k in termino_dic]
        keys.sort()
        for k in keys:
            print("### terminology type|src", k, termino_dic[k])

# --------------------------------------------------------------------------------
if __name__ == '__main__':
# --------------------------------------------------------------------------------
    global ftp_server, annot_base_url, publi_base_url, proxy_dir, ftp_content
    global sct_uuids, cnt_fields, ann_fld_dic
    global graph

    sct_uuids = dict()
    cnt_fields = dict()
    ann_fld_dic = dict()
    cnt_cls_spl = dict()
    termino_dic = dict()

    ftp_server = "denver.hesge.ch"
    annot_base_url = "/SIBiLS/anapmc21/baseline/"
    publi_base_url = "/SIBiLS_v3/bibpmc/baseline/"
    proxy_dir = "./proxy_dir/"
    fetch_dir = proxy_dir + "fetch_pam/"
    prefixes = dict()
    
    # choose action
    action = sys.argv[1]
    print("### action:", sys.argv[1])

    # - - - - - - - - - - - - - - - - - - - - - - - -     
    if sys.argv[1] == "download":
    # - - - - - - - - - - - - - - - - - - - - - - - -       
        ftp_content = get_content_from_ftp()
        file_name = "pmc21n0757.json.gz"
        download_chunk_from_ftp(file_name)
        
    # - - - - - - - - - - - - - - - - - - - - - - - -     
    elif sys.argv[1] == "fetch_pam":
    # - - - - - - - - - - - - - - - - - - - - - - - -     
        ## get set of pmcid and save it as a file
        file_name = "pmc21n0757.json"
        json_file = proxy_dir + file_name
        f_in = open(json_file, "rb")
        obj = json.load(f_in)        
        f_in.close()
        pmcid_set = set()
        for publi in obj:
            pmcid = publi["pmcid"]
            pmcid_set.add(pmcid)
        filename = fetch_dir + "pmcid_set.pickle"
        f_out = open(filename, 'wb')
        pickle.dump(pmcid_set, f_out, protocol=3) 
        f_out.close()
        print("### saved pmcid set ", filename, "len(pmcid_set)", len(pmcid_set))    
        # use fetch_pam to retrieve batches of json publications with annotations
        while pmcid_set:
            ids = ""
            for i in range(30):
                if pmcid_set:
                    if len(ids)>0: ids += ","
                    ids += pmcid_set.pop()
            url = "https://candy.hesge.ch/SIBiLS/PMC/fetch_PAM.jsp?ids=" + ids
            print("### url", url)
            response = requests.get(url)
            print("### got response")
            data = response.json()
            print("### parsed response")
            for publi in data:
                pmcid = publi.get("pmcid")
                subdir = fetch_dir + pmcid[:5] + "/"
                os.makedirs(subdir, exist_ok=True)
                jsonfile = subdir + pmcid + ".pickle"
                f_out = open(jsonfile, 'wb')
                pickle.dump(publi, f_out, protocol=3) 
                f_out.close()
                print("### saved", jsonfile)

    # - - - - - - - - - - - - - - - - - - - - - - - -     
    elif sys.argv[1] == "parse":
    # - - - - - - - - - - - - - - - - - - - - - - - -     

        pub_per_file = 100
        max_pub = 100000000
        if len(sys.argv)>=3: max_pub = int(sys.argv[2])

        # read list of pmcid fro file generated by fetch_pam action above
        filename = fetch_dir + "pmcid_set.pickle"
        print("### Reading pmcid set", filename)        
        f_in = open(filename, 'rb')
        pmcid_set = pickle.load(f_in)
        f_in.close()
        pub_no = 0

        # create a ttl file for each pmcid subset
        pmcid_subsets = get_split_lists(list(pmcid_set), pub_per_file)
        for pmcid_subset in pmcid_subsets:
            offset = pub_no
            graph = get_new_graph()
            print("### Parsing pmcid set", filename, "offset", offset)
            for pmcid in pmcid_subset:
                pub_no += 1
                if pub_no > max_pub: break
                subdir = fetch_dir + pmcid[:5] + "/"
                jsonfile = subdir + pmcid + ".pickle"

                print("### Reading publi", jsonfile, "file no.", pub_no)
                f_in = open(jsonfile, 'rb')
                publi = pickle.load(f_in)
                f_in.close()

                print("### Building RDF for current publi")
                get_triples_for_publi(publi)
                get_triples_for_publi_annotations(publi)
                
            print_debug_info()

            ttl_file = "./output/publication_set_" + str(offset) + ".ttl"
            print("### Serializing to", ttl_file)            
            t0 = datetime.datetime.now()      
            graph.serialize(destination=ttl_file , format="turtle", encoding="utf-8")
            duration = datetime.datetime.now()-t0
            m,s = divmod(duration.seconds,60)
            print("duration:", m, "min", s, "seconds")

    print("### End")
    

