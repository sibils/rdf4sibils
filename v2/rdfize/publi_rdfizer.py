from namespace_registry import NamespaceRegistry
from ApiCommon import log_it
from termi_extra import TermiExtraRegistry, TermiExtra
from rdf_utils import TripleList

class PubliRdfizer:

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def __init__(self, ns: NamespaceRegistry, publi): 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        self.ns = ns
        self.tex: TermiExtraRegistry = TermiExtraRegistry(ns)
        self.publi = publi


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def date_to_yyyy_mm_dd(self, dd_mm_yyyy):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        d,m,y = dd_mm_yyyy.split("-")
        return y + "-" + m + "-" + d


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_front_matter_URIRef(self, publi_uri):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        return publi_uri + "_part_frontMatter"


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_part_URIRef(self, publi_uri, part_id):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        return publi_uri + "_part_" + part_id


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_part_title_URIRef(self, part_uri):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        return part_uri + "_title"


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_part_label_URIRef(self, part_uri):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        return part_uri + "_label"


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_part_caption_URIRef(self, part_uri):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        return part_uri + "_caption"


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_part_footer_URIRef(self, part_uri):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        return part_uri + "_footer"



    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_sen_part_class_URIRef(self, sentence):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        ns = self.ns
        fld = sentence.get("field")
        if fld == "table_column": return ns.sibilo.TableColumnName
        if fld == "table_value": return ns.sibilo.TableCellValues
        return ns.doco.Sentence


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_term_URIRef_from_annot(self, annot):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        termi_id = annot["concept_source"]
        cpt_id = annot["concept_id"]
        tx : TermiExtra = self.tex.id2termi.get(termi_id)
        if tx is None:
            log_it(f"WARNING, ignoring annotation from unexpected terminology: {termi_id}")
            return None
        iri = tx.concept_IRI(cpt_id)            
        return iri


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_parent_part_URIRef(self, publi_uri, part):
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
                return  self.get_front_matter_URIRef(publi_uri)
            elif tag == "abstract":
                return  self.get_front_matter_URIRef(publi_uri)
            else:
                return publi_uri
        # case 3: part is a regular section (sct) or a content (cnt)
        else:            
            part_id = part.get("id")
            # parent id: remove everything from right until LAST <dot> is reached
            parent_id = part_id[:part_id.rfind(".")]
            return "".join([publi_uri , "_part_" , parent_id])


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_sct_part_class_URIRef(self, sct):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        ns = self.ns
        tag = sct.get("tag")
        
        if tag is None and sct.get("level") == 1 and sct.get("title") == "Title": 
            return ns.doco.Title

        if tag == "sec":
            caption = sct.get("caption")
            if caption is None or len(caption)==0: return ns.doco.Section
            return ns.doco.CaptionedBox

        if tag == "abstract": return ns.doco.Abstract
        if tag == "wrap": return ns.doco.Section

        if tag == "boxed-text":
            caption = sct.get("caption")
            if caption is None or len(caption)==0: return ns.doco.TextBox
            return ns.doco.CaptionedBox

        if tag == "body": return ns.doco.BodyMatter
        if tag == "back": return ns.doco.BackMatter
        if tag == "floats-group": return ns.sibilo.FloatMatter  # our extension
        if tag == "app": return ns.doco.Appendix

        # return default ancestor class in case of unexpected tag
        log_it("WARNING", "No section class defined for tag:", tag)
        return ns.deo.DiscourseElement


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_pmca_link(self, collection, id):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        # Examples of output
        # - https://biodiversitypmc.sibils.org/pmca/?id=PMC10020865&col=pmc
        # - https://biodiversitypmc.sibils.org/pmca/?id=33411943&col=medline

        return f"https://biodiversitypmc.sibils.org/pmca/?id={id}&col={collection}"


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_cnt_part_class_URIRef(self, cnt):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        ns = self.ns
        # sibilo classes below could be defined as sub classes of deo.DiscourseElement
        tag = cnt.get("tag")
        if tag == "p":           return ns.doco.Paragraph
        if tag == "fig":         return ns.doco.FigureBox
        if tag == "table":       return ns.doco.TableBox
        if tag == "list-item":   return ns.sibilo.ListItemBlock      # our extension
        if tag == "media":       return ns.sibilo.MediaBlock         # our extension
        if tag == "def-list":    return ns.doco.Glossary
        if tag == "disp-quote":  return ns.doco.BlockQuotation
        if tag == "statement":   return ns.sibilo.StatementBlock     # our extension
        if tag == "object-id":   return ns.sibilo.ObjectIdBlock      # our extension
        if tag == "speech":      return ns.sibilo.SpeechBlock         # our extension
        if tag == "verse-group": return ns.sibilo.VerseGroupBlock     # our extension
        if tag == "array":       return ns.doco.Table
        if tag == "ref-list":    return ns.doco.ListOfReferences
        return ns.deo.DiscourseElement # default, parent of doco:Paragraph, etc


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def find_affiliation_name(self, aff_id):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        affs = self.publi.get("affiliations")
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




