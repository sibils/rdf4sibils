from api_platform import ApiPlatform
from namespace_registry import NamespaceRegistry
import types

# -------------------------------------------------
class TermiExtra:
# -------------------------------------------------

    def __init__(self, ns: NamespaceRegistry, concept_source, rdf_id, fullname, exact_match_pattern, see_also_pattern):
        self.ns = ns
        self.concept_source = concept_source                # concept_source value used in annotations as a terminology id
        self.rdf_id = rdf_id                                # terminology to be used in RDF
        self.exact_match_pattern = exact_match_pattern      # pattern to build a link to the IRI defining the concept (skos:exactMatch) 
        self.see_also_pattern = see_also_pattern            # pattern to build a link to the URL of a webpage defining the concept
        self.fullname = fullname

    def IRI(self):
        return ":".join([self.ns.sibilt.pfx, self.rdf_id])

    def concept_IRI(self, concept_id):
        db_ac = "_".join([self.rdf_id, self.concept_rdf_id(concept_id)])
        return ":".join([self.ns.sibilc.pfx, db_ac])

    # default function, can be overriden
    def concept_notation(self, concept_id):
        return ":".join([self.rdf_id, self.concept_rdf_id(concept_id)])        

    # default function, can be overriden
    def concept_rdf_id(self, concept_id):
        return concept_id

    # default function, can be overriden
    def concept_exact_match(self, concept_id):
        if self.exact_match_pattern is None: return None
        return self.exact_match_pattern.format(cpt_id=concept_id)

    # default function, can be overriden
    def concept_see_also(self, concept_id):
        if self.see_also_pattern is None: return None
        return self.see_also_pattern.format(cpt_id=concept_id)


# -------------------------------------------------
class TermiExtraRegistry:
# -------------------------------------------------

    def atc_exact_match_fun(self, cpt_id):
        if cpt_id.startswith("http://purl.bioontology.org/ontology/STY/"):
            return cpt_id
        else:
            rdf_id = self.atc.concept_rdf_id(cpt_id)
            return f"http://purl.bioontology.org/ontology/ATC/{rdf_id}"

    def atc_concept_rdf_id(self, cpt_id):
        if cpt_id.startswith("http://purl.bioontology.org/ontology/STY/"):
            return "STY_" + cpt_id.split("/")[-1]
        else:
            return cpt_id.split("/")[-1]

    def atc_concept_notation(self, cpt_id):
        if cpt_id.startswith("http://purl.bioontology.org/ontology/STY/"):
            return "STY:" + cpt_id.split("/")[-1]
        else:
            return "ATC:" + cpt_id

    def covoc_concept_notation(self, cpt_id): return "COVoc:" + cpt_id
    def covoc_concept_IRI(self, cpt_id): return self.ns.sibilc.pfx + ":COVoc_" + cpt_id

    def go_concept_notation(self, cpt_id): return cpt_id
    def go_concept_IRI(self, cpt_id): return self.ns.sibilc.pfx + ":" + cpt_id.replace(":", "_")

    def grant_concept_IRI(self, cpt_id): return self.ns.sibilc.pfx + ":GRANT_" + cpt_id[25:]
    def grant_concept_notation(self, cpt_id): return "grant:" + cpt_id[25:]


    # - - - - - - - - - - - - - - - - - -
    def __init__(self, ns: NamespaceRegistry):
    # - - - - - - - - - - - - - - - - - -
        self.ns = ns
        self.agrovoc = TermiExtra(ns, "agrovoc", "AGROVOC", None, "http://aims.fao.org/aos/agrovoc/{cpt_id}", None)

        self.atc = TermiExtra(ns, "atc", "ATC", "Anatomical Therapeutic Chemical Classification", None, None)
        self.atc.concept_exact_match = self.atc_exact_match_fun
        self.atc.concept_rdf_id = self.atc_concept_rdf_id
        self.atc.concept_notation = self.atc_concept_notation

        self.cellontology = TermiExtra(ns, "cellontology", "CL", "Cell Ontology","http://purl.obolibrary.org/obo/{cpt_id}", None) 
        self.cellontology.concept_notation = types.MethodType(lambda self, cpt_id: cpt_id.replace("_", ":"), self.cellontology)
        self.cellontology.concept_rdf_id = types.MethodType(lambda self, cpt_id: cpt_id[3:] if cpt_id.startswith("CL") else cpt_id, self.cellontology)

        self.cellosaurus = TermiExtra(ns, "cellosaurus", "CVCL", "Cellosaurus","https://purl.expasy.org/cellosaurus/rdf/cvcl/{cpt_id}", "https://www.cellosaurus.org/{cpt_id}") 
        self.cellosaurus.concept_rdf_id = types.MethodType(lambda self, cpt_id: cpt_id[5:], self.cellosaurus)

        self.chebi = TermiExtra(ns, "chebi", "CHEBI", "ChEBI", None, None) 
        self.chebi.concept_rdf_id = types.MethodType(lambda self, cpt_id: cpt_id[6:], self.chebi)
        self.chebi.concept_exact_match = types.MethodType(lambda self, cpt_id: "http://purl.obolibrary.org/obo/" + cpt_id.replace(":", "_"), self.chebi)

        self.covocbiomed = TermiExtra(ns, "covocbiomed", "COVocBMV", "COVoc Biomedical vocabulary", None, None) 
        self.covocbiomed.concept_notation = self.covoc_concept_notation
        self.covocbiomed.concept_IRI = self.covoc_concept_IRI
        
        self.covoccelllines = TermiExtra(ns, "covoccelllines", "COVocCL", "COVoc Cell lines", None, None) 
        self.covoccelllines.concept_notation = self.covoc_concept_notation
        self.covoccelllines.concept_IRI = self.covoc_concept_IRI

        self.covocchemicals = TermiExtra(ns, "covocchemicals", "COVocDG", "COVoc Chemicals", None, None) 
        self.covocchemicals.concept_notation = self.covoc_concept_notation
        self.covocchemicals.concept_IRI = self.covoc_concept_IRI

        self.covocclinicaltrials = TermiExtra(ns, "covocclinicaltrials", "COVocCT", "COVoc Clinical trials", None, None) 
        self.covocclinicaltrials.concept_notation = self.covoc_concept_notation
        self.covocclinicaltrials.concept_IRI = self.covoc_concept_IRI

        self.covocconceptualentities = TermiExtra(ns, "covocconceptualentities", "COVocCE", "COVoc Conceptual entities", None, None) 
        self.covocconceptualentities.concept_notation = self.covoc_concept_notation
        self.covocconceptualentities.concept_IRI = self.covoc_concept_IRI

        self.covocdiseaseandsyndrom = TermiExtra(ns, "covocdiseaseandsyndrom", "COVocDIS", "COVoc Diseases and syndromes", None, None) 
        self.covocdiseaseandsyndrom.concept_notation = self.covoc_concept_notation
        self.covocdiseaseandsyndrom.concept_IRI = self.covoc_concept_IRI

        self.covocgeographicloc = TermiExtra(ns, "covocgeographicloc", "COVocLOC", "COVoc Geographic locations", None, None) 
        self.covocgeographicloc.concept_notation = self.covoc_concept_notation
        self.covocgeographicloc.concept_IRI = self.covoc_concept_IRI

        self.covocorganism = TermiExtra(ns, "covocorganism", "COVocSP", "COVoc Organisms", None, None) 
        self.covocorganism.concept_notation = self.covoc_concept_notation
        self.covocorganism.concept_IRI = self.covoc_concept_IRI

        self.covocproteinsgenomes = TermiExtra(ns, "covocproteinsgenomes", "COVocPG", "COVoc Proteins and genomes", None, None) 
        self.covocproteinsgenomes.concept_notation = self.covoc_concept_notation
        self.covocproteinsgenomes.concept_IRI = self.covoc_concept_IRI

        self.detectionmethods = TermiExtra(ns, "detectionmethods", "DM", "Detection methods", None, None) 

        self.disprot_type1 = TermiExtra(ns, "disprot_type1", "DisProtType1", None, None, None) 
        self.disprot_type2 = TermiExtra(ns, "disprot_type2", "DisProtType2", None, None, None) 
        self.disprot_type3 = TermiExtra(ns, "disprot_type3", "DisProtType3", None, None, None) 
        self.disprot_type4 = TermiExtra(ns, "disprot_type4", "DisProtType4", None, None, None) 

        self.drugbank = TermiExtra(ns, "drugbank", "DrugBank", None, None, "https://go.drugbank.com/drugs/{cpt_id}") 

        self.eco = TermiExtra(ns, "eco", "ECO", "Evidence & Conclusion Ontology", None, None) 
        self.eco.concept_rdf_id = types.MethodType(lambda self, cpt_id: cpt_id[4:], self.eco)
        self.eco.concept_exact_match = types.MethodType(lambda self, cpt_id: "http://purl.obolibrary.org/obo/" + cpt_id.replace(":", "_"), self.eco)

        self.envo = TermiExtra(ns, "envo", "ENVO", "The Environment Ontology", "http://purl.obolibrary.org/obo/{cpt_id}", None) 
        self.envo.concept_notation = types.MethodType(lambda self, cpt_id: cpt_id.replace("_", ":"), self.envo)
        self.envo.concept_rdf_id = types.MethodType(lambda self, cpt_id: cpt_id[5:] if cpt_id.startswith("ENVO") else cpt_id, self.envo)

        self.flopo = TermiExtra(ns, "flopo", "FLOPO", "Flora phenotype ontology", "http://purl.obolibrary.org/obo/{cpt_id}", "http://aber-owl.net/ontology/FLOPO/#/Browse/%3Chttp%3A%2F%2Fpurl.obolibrary.org%2Fobo%2F{cpt_id}%3E") 
        self.flopo.concept_notation = types.MethodType(lambda self, cpt_id: cpt_id.replace("_", ":"), self.flopo)
        self.flopo.concept_rdf_id = types.MethodType(lambda self, cpt_id: cpt_id[6:] if cpt_id.startswith("FLOPO") else cpt_id, self.flopo)

        self.go_bp = TermiExtra(ns, "go_bp", "GO_BP", "Gene ontology biological processes", None, None)
        self.go_bp.concept_notation = self.go_concept_notation
        self.go_bp.concept_IRI = self.go_concept_IRI

        self.go_mf = TermiExtra(ns, "go_mf", "GO_MF", "Gene ontology molecular functions", None, None)
        self.go_mf.concept_notation = self.go_concept_notation
        self.go_mf.concept_IRI = self.go_concept_IRI

        self.go_cc = TermiExtra(ns, "go_cc", "GO_CC", "Gene ontology cellular components", None, None)
        self.go_cc.concept_notation = self.go_concept_notation
        self.go_cc.concept_IRI = self.go_concept_IRI

        self.icdo3 = TermiExtra(ns, "icdo3", "ICDO3", "International Classification of Diseases for Oncology", None, None)
        self.icdo3.concept_IRI = types.MethodType(lambda self, cpt_id: self.ns.sibilc.pfx + ":" + cpt_id.replace("/","-"), self.icdo3)

        self.ictv = TermiExtra(ns, "ictv", "ICTV", "International Committee on Taxonomy of Viruses", None, "http://ictv.global/id/MSL40/ICTV{cpt_id}")
        self.ictv.concept_notation = types.MethodType(lambda self, cpt_id: "ICTV"+ cpt_id, self.ictv)

        self.ictv_subset = TermiExtra(ns, "ictv_subset", "ICTV_subset", "International Committee on Taxonomy of Viruses (subset)", None, "http://ictv.global/id/MSL40/ICTV{cpt_id}")
        self.ictv_subset.concept_notation = types.MethodType(lambda self, cpt_id: "ICTV"+ cpt_id, self.ictv_subset)

        self.license = TermiExtra(ns, "license", "License", "SPDX License List", "http://spdx.org/licenses/{cpt_id}", None)
        self.license.concept_rdf_id = types.MethodType(lambda self, cpt_id: cpt_id.replace("+","plus"), self.license)

        self.lotus = TermiExtra(ns, "lotus", "LOTUS", "Lotus", "http://www.wikidata.org/entity/{cpt_id}", None)

        self.mdd = TermiExtra(ns, "mdd", "MDD", "Mammal Diversity Database", None, "https://www.mammaldiversity.org/taxon/{cpt_id}/")

        self.mesh = TermiExtra(ns, "mesh", "MeSH", "Medical Subject Headings", "https://id.nlm.nih.gov/mesh/{cpt_id}", "https://id.nlm.nih.gov/mesh/{cpt_id}.html")

        self.ncbitaxon_full = TermiExtra(ns, "ncbitaxon_full", "NCBI_TaxID", "NCBI Taxononmy database", "http://purl.obolibrary.org/obo/NCBITaxon_{cpt_id}", "https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?mode=Info&id={cpt_id}&lvl=3")

        self.ncbitaxon_models = TermiExtra(ns, "ncbitaxon_models", "NCBI_Model", "NCBI Taxononmy database (models)", None, None)
        self.ncbitaxon_models.concept_rdf_id = types.MethodType(lambda self, cpt_id: cpt_id.split("taxID: ")[-1], self.ncbitaxon_models)
        self.ncbitaxon_models.concept_exact_match = types.MethodType(lambda self, cpt_id: "http://purl.obolibrary.org/obo/NCBITaxon_" + cpt_id.split("taxID: ")[-1], self.ncbitaxon_models)
        self.ncbitaxon_models.concept_see_also = types.MethodType(lambda self, cpt_id: "https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?mode=Info&id=" + cpt_id.split("taxID: ")[-1] + "&lvl=3", self.ncbitaxon_models)

        self.ncbitaxon_viruses = TermiExtra(ns, "ncbitaxon_viruses", "NCBI_Virus", "NCBI Taxononmy (viruses)", "http://purl.obolibrary.org/obo/NCBITaxon_{cpt_id}", "https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?mode=Info&id={cpt_id}&lvl=3")

        self.ncit = TermiExtra(ns, "ncit", "NCIt", "NCI Thesaurus", "http://purl.obolibrary.org/obo/NCIT_{cpt_id}", "https://evsexplore.semantics.cancer.gov/evsexplore/concept/ncit/{cpt_id}")

        self.nextprot = TermiExtra(ns, "nextprot", "nextprot", "neXtProt", None, None)

        self.ott = TermiExtra(ns, "ott", "OTT", "Open Tree of Life", None, "https://tree.opentreeoflife.org/taxonomy/browse?id={cpt_id}")

        self.po = TermiExtra(ns, "po", "PO", "Plant Ontology", None, None)
        self.po.concept_rdf_id = types.MethodType(lambda self, cpt_id: cpt_id[3:], self.po)
        self.po.concept_exact_match = types.MethodType(lambda self, cpt_id: "http://purl.obolibrary.org/obo/" + cpt_id.replace(":", "_"), self.po)

        self.ppiptm = TermiExtra(ns, "ppiptm", "ppiptm", None, None, None)
        self.ppiptm.concept_rdf_id = types.MethodType(lambda self, cpt_id: cpt_id.replace(":", "_"), self.ppiptm)
        
        self.psimi = TermiExtra(ns, "psimi", "MI", "Molecular Interactions Controlled Vocabulary", None, None)
        self.psimi.concept_rdf_id = types.MethodType(lambda self, cpt_id: cpt_id[3:], self.psimi)
        self.psimi.concept_exact_match = types.MethodType(lambda self, cpt_id: "http://purl.obolibrary.org/obo/" + cpt_id.replace(":", "_"), self.psimi)

        self.pubchemmesh = TermiExtra(ns, "pubchemmesh", "PubChem", None, None, "https://pubchem.ncbi.nlm.nih.gov/compound/{cpt_id}")

        self.robiext = TermiExtra(ns, "robiext", "ROBIext", "Relation ontology extended with Biotic Interactions", None, None)
        self.robiext.concept_exact_match = types.MethodType(lambda self, cpt_id: None if cpt_id.startswith("RO_e") else "http://purl.obolibrary.org/obo/" + cpt_id, self.robiext)

        self.ror = TermiExtra(ns, "ror", "ROR", "Research Organization Registry", None, "https://ror.org/{cpt_id}")

        self.uniprot_swissprot = TermiExtra(ns, "uniprot_swissprot", "uniprot", "UniProtKB/SwissProt", "http://purl.uniprot.org/uniprot/{cpt_id}", "https://www.uniprot.org/uniprotkb/{cpt_id}/entry")
        
        self.grant = TermiExtra(ns, "grant", "GRANT", "Open Funder Registry", "{cpt_id}", None)
        self.grant.concept_IRI = self.grant_concept_IRI
        self.grant.concept_notation = self.grant_concept_notation

        
        self.terminologies = [ 
            self.agrovoc, self.atc, self.cellontology, self.cellosaurus, self.chebi, self.covocbiomed, self.covoccelllines, self.covocchemicals, 
            self.covocclinicaltrials, self.covocconceptualentities, self.covocdiseaseandsyndrom, self.covocgeographicloc, self.covocorganism, 
            self.covocproteinsgenomes, self.detectionmethods, self.disprot_type1, self.disprot_type2, self.disprot_type3, self.disprot_type4, 
            self.drugbank, self.eco, self.envo, self.flopo, self.go_bp, self.go_cc, self.go_mf, self.icdo3, self.ictv, self.ictv_subset, self.license, 
            self.lotus, self.mdd, self.mesh, self.ncbitaxon_full, self.ncbitaxon_models, self.ncbitaxon_viruses, self.ncit, self.nextprot, self.ott, 
            self.po, self.ppiptm, self.psimi, self.pubchemmesh, self.robiext, self.ror, self.uniprot_swissprot, self.grant ]

        self.id2termi = dict()
        for el in self.terminologies: self.id2termi[el.concept_source] = el


# ------------------------------------------------------------------------------------------

def print_result(termix, concept_id):
    print("concept_id          :", concept_id)    
    print("concept_source      :", termix.concept_source) 
    print("=>")
    print("rdf_id              :", termix.rdf_id)
    print("local_IRI           :", termix.IRI())
    print("local_concept_IRI   :", termix.concept_IRI(concept_id))
    print("concept_notation    :", termix.concept_notation(concept_id))
    print("concept_exact_match :", termix.concept_exact_match(concept_id))
    print("concept_see_also    :", termix.concept_see_also(concept_id))
    print("--- ")

def test_result(termix, concept_id, expected_result):
    print("concept_id          :", concept_id)    
    print("concept_source      :", termix.concept_source) 
    print("=>")
    error_count = 0
    result = "OK   " if termix.rdf_id == expected_result.get("rdf_id") else "ERROR"
    if result != "OK   ": error_count += 1
    print(f"{result} rdf_id              :", termix.rdf_id)
    result = "OK   " if termix.IRI() == expected_result.get("local_IRI") else "ERROR"
    if result != "OK   ": error_count += 1
    print(f"{result} local_IRI           :", termix.IRI())
    result = "OK   " if termix.concept_IRI(concept_id) == expected_result.get("local_concept_IRI") else "ERROR"
    if result != "OK   ": error_count += 1
    print(f"{result} local_concept_IRI   :", termix.concept_IRI(concept_id))
    result = "OK   " if termix.concept_notation(concept_id) == expected_result.get("concept_notation") else "ERROR"
    if result != "OK   ": error_count += 1
    print(f"{result} concept_notation    :", termix.concept_notation(concept_id))
    result = "OK   " if termix.concept_exact_match(concept_id) == expected_result.get("concept_exact_match") else "ERROR"
    if result != "OK   ": error_count += 1
    print(f"{result} concept_exact_match :", termix.concept_exact_match(concept_id))
    result = "OK   " if termix.concept_see_also(concept_id) == expected_result.get("concept_see_also") else "ERROR"
    if result != "OK   ": error_count += 1
    print(f"{result} concept_see_also    :", termix.concept_see_also(concept_id))
    print("--- ")
    return error_count


# ====================================
if __name__ == '__main__':
# ====================================

    platform = ApiPlatform("prod")
    ns = NamespaceRegistry(platform)
    tex = TermiExtraRegistry(ns)

    errors = 0

    errors += test_result(tex.grant, "https://doi.org/10.13039/100022722", {
        "rdf_id" : "GRANT",
        "local_IRI" : "sibilt:GRANT",
        "local_concept_IRI"   : "sibilc:GRANT_100022722",
        "concept_notation"    : "grant:100022722",
        "concept_exact_match" : "https://doi.org/10.13039/100022722",
        "concept_see_also"    : None
    })

    errors += test_result(tex.agrovoc, "c_27580", {
        "rdf_id" : "AGROVOC",
        "local_IRI" : "sibilt:AGROVOC",
        "local_concept_IRI"   : "sibilc:AGROVOC_c_27580",
        "concept_notation"    : "AGROVOC:c_27580",
        "concept_exact_match" : "http://aims.fao.org/aos/agrovoc/c_27580",
        "concept_see_also"    : None
    })
    errors += test_result(tex.atc, "http://purl.bioontology.org/ontology/STY/L3445", {
        "rdf_id"              : "ATC",
        "local_IRI"           : "sibilt:ATC",
        "local_concept_IRI"   : "sibilc:ATC_STY_L3445",
        "concept_notation"    : "STY:L3445",
        "concept_exact_match" : "http://purl.bioontology.org/ontology/STY/L3445",
        "concept_see_also"    : None
    }) # some non ATC concepts included as IRI


    errors += test_result(tex.atc, "L04AX03", {
        "rdf_id"              : "ATC",
        "local_IRI"           : "sibilt:ATC",
        "local_concept_IRI"   : "sibilc:ATC_L04AX03",
        "concept_notation"    : "ATC:L04AX03",
        "concept_exact_match" : "http://purl.bioontology.org/ontology/ATC/L04AX03",
        "concept_see_also"    : None

    })

    errors += test_result(tex.cellontology, "CL_0000415", {
        "rdf_id"              : "CL",
        "local_IRI"           : "sibilt:CL",
        "local_concept_IRI"   : "sibilc:CL_0000415",
        "concept_notation"    : "CL:0000415",
        "concept_exact_match" : "http://purl.obolibrary.org/obo/CL_0000415",
        "concept_see_also"    : None
    })

    errors += test_result(tex.cellontology, "GO_0000415", {
        "rdf_id"              : "CL",
        "local_IRI"           : "sibilt:CL",
        "local_concept_IRI"   : "sibilc:CL_GO_0000415",
        "concept_notation"    : "GO:0000415",
        "concept_exact_match" : "http://purl.obolibrary.org/obo/GO_0000415",
        "concept_see_also"    : None
    })                            # some GO terms are embedded in CL ontology
    
    errors += test_result(tex.cellosaurus, "CVCL_0030", {
        "rdf_id"              : "CVCL",
        "local_IRI"           : "sibilt:CVCL",
        "local_concept_IRI"   : "sibilc:CVCL_0030",
        "concept_notation"    : "CVCL:0030",
        "concept_exact_match" : "https://purl.expasy.org/cellosaurus/rdf/cvcl/CVCL_0030",
        "concept_see_also"    : "https://www.cellosaurus.org/CVCL_0030"        
    })
    
    errors += test_result(tex.chebi, "CHEBI:124094", {
        "rdf_id"              : "CHEBI",
        "local_IRI"           : "sibilt:CHEBI",
        "local_concept_IRI"   : "sibilc:CHEBI_124094",
        "concept_notation"    : "CHEBI:124094",
        "concept_exact_match" : "http://purl.obolibrary.org/obo/CHEBI_124094",
        "concept_see_also"    : None        
    })
    
    errors += test_result(tex.covocbiomed, "BMV_103", {
        "rdf_id"              : "COVocBMV",
        "local_IRI"           : "sibilt:COVocBMV",
        "local_concept_IRI"   : "sibilc:COVoc_BMV_103",
        "concept_notation"    : "COVoc:BMV_103",
        "concept_exact_match" : None,
        "concept_see_also"    : None        
    })                                # other COVoc terminologies are defined a similar way
    
    errors += test_result(tex.detectionmethods, "ViDM35", {
        "rdf_id"              : "DM",
        "local_IRI"           : "sibilt:DM",
        "local_concept_IRI"   : "sibilc:DM_ViDM35",
        "concept_notation"    : "DM:ViDM35",
        "concept_exact_match" : None,
        "concept_see_also"    : None
    })
    
    errors += test_result(tex.disprot_type1, "FRET", {
        "rdf_id"              : "DisProtType1",
        "local_IRI"           : "sibilt:DisProtType1",
        "local_concept_IRI"   : "sibilc:DisProtType1_FRET",
        "concept_notation"    : "DisProtType1:FRET",
        "concept_exact_match" : None,
        "concept_see_also"    : None        
    })                                 # other disprot terminologies are defined a similar way
    
    errors += test_result(tex.drugbank, "DB12847", {
        "rdf_id"              : "DrugBank",
        "local_IRI"           : "sibilt:DrugBank",
        "local_concept_IRI"   : "sibilc:DrugBank_DB12847",
        "concept_notation"    : "DrugBank:DB12847",
        "concept_exact_match" : None,
        "concept_see_also"    : "https://go.drugbank.com/drugs/DB12847"        
    })
    
    errors += test_result(tex.eco, "ECO:0008036", {
        "rdf_id"              : "ECO",
        "local_IRI"           : "sibilt:ECO",
        "local_concept_IRI"   : "sibilc:ECO_0008036",
        "concept_notation"    : "ECO:0008036",
        "concept_exact_match" : "http://purl.obolibrary.org/obo/ECO_0008036",
        "concept_see_also"    : None        
    })
    
    errors += test_result(tex.envo, "ENVO_00000416", {
        "rdf_id"              : "ENVO",
        "local_IRI"           : "sibilt:ENVO",
        "local_concept_IRI"   : "sibilc:ENVO_00000416",
        "concept_notation"    : "ENVO:00000416",
        "concept_exact_match" : "http://purl.obolibrary.org/obo/ENVO_00000416",
        "concept_see_also"    : None        
    })                                 
    
    errors += test_result(tex.envo, "GO_1234567", {
        "rdf_id"              : "ENVO",
        "local_IRI"           : "sibilt:ENVO",
        "local_concept_IRI"   : "sibilc:ENVO_GO_1234567",
        "concept_notation"    : "GO:1234567",
        "concept_exact_match" : "http://purl.obolibrary.org/obo/GO_1234567",
        "concept_see_also"    : None        
    })                                    # GO terms supported: just in case cos ENVO contains GO and other external terms
    
    errors += test_result(tex.flopo, "FLOPO_0000697", {
        "rdf_id"              : "FLOPO",
        "local_IRI"           : "sibilt:FLOPO",
        "local_concept_IRI"   : "sibilc:FLOPO_0000697",
        "concept_notation"    : "FLOPO:0000697",
        "concept_exact_match" : "http://purl.obolibrary.org/obo/FLOPO_0000697",
        "concept_see_also"    : "http://aber-owl.net/ontology/FLOPO/#/Browse/%3Chttp%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FFLOPO_0000697%3E"
        
    })                                 
    
    errors += test_result(tex.go_bp, "GO:0000697", {
        "rdf_id"              : "GO_BP",
        "local_IRI"           : "sibilt:GO_BP",
        "local_concept_IRI"   : "sibilc:GO_0000697",
        "concept_notation"    : "GO:0000697",
        "concept_exact_match" : None,
        "concept_see_also"    : None
        
    })                                   # other GO subsets (go_mf, go_cc) are defined similarly, only GO terms inside                             
    
    errors += test_result(tex.icdo3, "9931/3", {
        "rdf_id"              : "ICDO3",
        "local_IRI"           : "sibilt:ICDO3",
        "local_concept_IRI"   : "sibilc:9931-3",
        "concept_notation"    : "ICDO3:9931/3",
        "concept_exact_match" : None,
        "concept_see_also"    : None        
    })                                       # slash are replaced with "-" for local concept_IRI
    
    errors += test_result(tex.ictv, "202215077", {
    "rdf_id"              : "ICTV",
    "local_IRI"           : "sibilt:ICTV",
    "local_concept_IRI"   : "sibilc:ICTV_202215077",
    "concept_notation"    : "ICTV202215077",
    "concept_exact_match" : None,
    "concept_see_also"    : "http://ictv.global/id/MSL40/ICTV202215077"        
    })                                     # WARNING: external IRI may depend on version !!!                                  
    
    errors += test_result(tex.ictv_subset, "202215077", {
        "rdf_id"              : "ICTV_subset",
        "local_IRI"           : "sibilt:ICTV_subset",
        "local_concept_IRI"   : "sibilc:ICTV_subset_202215077",
        "concept_notation"    : "ICTV202215077",
        "concept_exact_match"    : None,        
        "concept_see_also" : "http://ictv.global/id/MSL40/ICTV202215077"
    })                              # WARNING: external IRI may depend on version !!!                                  
    
    errors += test_result(tex.license, "GPL-1.0+", {
        "rdf_id"              : "License",
        "local_IRI"           : "sibilt:License",
        "local_concept_IRI"   : "sibilc:License_GPL-1.0plus",
        "concept_notation"    : "License:GPL-1.0plus",
        "concept_exact_match" : "http://spdx.org/licenses/GPL-1.0+", # see also rdf definition in https://github.com/spdx/license-list-data/tree/main/rdfturtle
        "concept_see_also"    : None
    })                                   # WARNING "+" not allowed in prefix:QName form => "+" turned into "plus" for local IRIs, but authorized in full form for exact match IRI as <...>
    
    errors += test_result(tex.lotus, "Q110175262", {
        "rdf_id"              : "LOTUS",
        "local_IRI"           : "sibilt:LOTUS",
        "local_concept_IRI"   : "sibilc:LOTUS_Q110175262",
        "concept_notation"    : "LOTUS:Q110175262",
        "concept_exact_match" : "http://www.wikidata.org/entity/Q110175262",
        "concept_see_also"    : None
    }) 
    
    errors += test_result(tex.mdd, "1000718", {
        "rdf_id"              : "MDD",
        "local_IRI"           : "sibilt:MDD",
        "local_concept_IRI"   : "sibilc:MDD_1000718",
        "concept_notation"    : "MDD:1000718",
        "concept_exact_match" : None,
        "concept_see_also"    : "https://www.mammaldiversity.org/taxon/1000718/",
    }) 
    
    errors += test_result(tex.mesh, "D019830", {
        "rdf_id"              : "MeSH",
        "local_IRI"           : "sibilt:MeSH",
        "local_concept_IRI"   : "sibilc:MeSH_D019830",
        "concept_notation"    : "MeSH:D019830",
        "concept_exact_match" : "https://id.nlm.nih.gov/mesh/D019830",              # RDF page, try: curl -L -H "Accept: application/rdf+xml" "https://id.nlm.nih.gov/mesh/D019830"
        "concept_see_also"    : "https://id.nlm.nih.gov/mesh/D019830.html"        
    }) 
    
    errors += test_result(tex.ncbitaxon_full, "2920168", {
        "rdf_id"              : "NCBI_TaxID",
        "local_IRI"           : "sibilt:NCBI_TaxID",
        "local_concept_IRI"   : "sibilc:NCBI_TaxID_2920168",
        "concept_notation"    : "NCBI_TaxID:2920168",
        "concept_exact_match" : "http://purl.obolibrary.org/obo/NCBITaxon_2920168",
        "concept_see_also"    : "https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?mode=Info&id=2920168&lvl=3"        
    })                             # taxID identifier as expected
    
    errors += test_result(tex.ncbitaxon_models, "Japanese medaka taxID: 8090", {
        "rdf_id"              : "NCBI_Model",
        "local_IRI"           : "sibilt:NCBI_Model",
        "local_concept_IRI"   : "sibilc:NCBI_Model_8090",
        "concept_notation"    : "NCBI_Model:8090",
        "concept_exact_match" : "http://purl.obolibrary.org/obo/NCBITaxon_8090",
        "concept_see_also"    : "https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?mode=Info&id=8090&lvl=3"        
    })       # junk before taxID identifier found in terminology is removed
    
    errors += test_result(tex.ncbitaxon_models, "taxID: 59463", {
        "rdf_id"              : "NCBI_Model",
        "local_IRI"           : "sibilt:NCBI_Model",
        "local_concept_IRI"   : "sibilc:NCBI_Model_59463",
        "concept_notation"    : "NCBI_Model:59463",
        "concept_exact_match" : "http://purl.obolibrary.org/obo/NCBITaxon_59463",
        "concept_see_also"    : "https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?mode=Info&id=59463&lvl=3",       
    })                      # junk chars found before taxID identifier is removed
    
    errors += test_result(tex.ncbitaxon_models, "9267", {
        "rdf_id"              : "NCBI_Model",
        "local_IRI"           : "sibilt:NCBI_Model",
        "local_concept_IRI"   : "sibilc:NCBI_Model_9267",
        "concept_notation"    : "NCBI_Model:9267",
        "concept_exact_match" : "http://purl.obolibrary.org/obo/NCBITaxon_9267",
        "concept_see_also"    : "https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?mode=Info&id=9267&lvl=3"        
    })                              # taxID identifier as expected
    
    errors += test_result(tex.ncbitaxon_viruses, "1757215", {
        "rdf_id"              : "NCBI_Virus",
        "local_IRI"           : "sibilt:NCBI_Virus",
        "local_concept_IRI"   : "sibilc:NCBI_Virus_1757215",
        "concept_notation"    : "NCBI_Virus:1757215",
        "concept_exact_match" : "http://purl.obolibrary.org/obo/NCBITaxon_1757215",
        "concept_see_also"    : "https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?mode=Info&id=1757215&lvl=3",        
    })                          # taxID identifier as expected
    

    errors += test_result(tex.ncit, "C195921", {
        "rdf_id"              : "NCIt",
        "local_IRI"           : "sibilt:NCIt",
        "local_concept_IRI"   : "sibilc:NCIt_C195921",
        "concept_notation"    : "NCIt:C195921",
        "concept_exact_match" : "http://purl.obolibrary.org/obo/NCIT_C195921",
        "concept_see_also"    : "https://evsexplore.semantics.cancer.gov/evsexplore/concept/ncit/C195921",        
    })
    
    errors += test_result(tex.nextprot, "NX_O60663", {
        "rdf_id"              : "nextprot",
        "local_IRI"           : "sibilt:nextprot",
        "local_concept_IRI"   : "sibilc:nextprot_NX_O60663",
        "concept_notation"    : "nextprot:NX_O60663",
        "concept_exact_match" : None,
        "concept_see_also"    : None        
    })    
    
    errors += test_result(tex.ott, "3274723", {
        "rdf_id"              : "OTT",
        "local_IRI"           : "sibilt:OTT",
        "local_concept_IRI"   : "sibilc:OTT_3274723",
        "concept_notation"    : "OTT:3274723",
        "concept_exact_match" : None,
        "concept_see_also"    : "https://tree.opentreeoflife.org/taxonomy/browse?id=3274723"        
    })
    
    errors += test_result(tex.po, "PO:0025018", {
        "rdf_id"              : "PO",
        "local_IRI"           : "sibilt:PO",
        "local_concept_IRI"   : "sibilc:PO_0025018",
        "concept_notation"    : "PO:0025018",
        "concept_exact_match" : "http://purl.obolibrary.org/obo/PO_0025018",
        "concept_see_also"    : None        
    })                                              # imports terms from many other ontologies but not used by our annotations, no parents relationship in our json ontology
    
    errors += test_result(tex.ppiptm, "PTM:10", {
        "rdf_id"              : "ppiptm",
        "local_IRI"           : "sibilt:ppiptm",
        "local_concept_IRI"   : "sibilc:ppiptm_PTM_10",
        "concept_notation"    : "ppiptm:PTM_10",
        "concept_exact_match" : None,
        "concept_see_also"    : None        
    })
    
    errors += test_result(tex.psimi, "MI:0841", {
        "rdf_id"              : "MI",
        "local_IRI"           : "sibilt:MI",
        "local_concept_IRI"   : "sibilc:MI_0841",
        "concept_notation"    : "MI:0841",
        "concept_exact_match" : "http://purl.obolibrary.org/obo/MI_0841",
        "concept_see_also"    : None        
    })
    
    errors += test_result(tex.pubchemmesh, "61586", {
        "rdf_id"              : "PubChem",
        "local_IRI"           : "sibilt:PubChem",
        "local_concept_IRI"   : "sibilc:PubChem_61586",
        "concept_notation"    : "PubChem:61586",
        "concept_exact_match" : None,
        "concept_see_also"    : "https://pubchem.ncbi.nlm.nih.gov/compound/61586"        
    })
    
    errors += test_result(tex.robiext, "RO_0002638", {
        "rdf_id"              : "ROBIext",
        "local_IRI"           : "sibilt:ROBIext",
        "local_concept_IRI"   : "sibilc:ROBIext_RO_0002638",
        "concept_notation"    : "ROBIext:RO_0002638",
        "concept_exact_match" : "http://purl.obolibrary.org/obo/RO_0002638",
        "concept_see_also"    : None        
    })                                 # regular RO identifier => exact_match = <http://purl.obolibrary.org/obo/RO_0002638>
    
    errors += test_result(tex.robiext, "RO_e000033", {
        "rdf_id"              : "ROBIext",
        "local_IRI"           : "sibilt:ROBIext",
        "local_concept_IRI"   : "sibilc:ROBIext_RO_e000033",
        "concept_notation"    : "ROBIext:RO_e000033",
        "concept_exact_match" : None,
        "concept_see_also"    : None        
    })                                 # identifier of extension (where does it come from?) => exact_match = None
    
    errors += test_result(tex.ror, "04ttjf776", {
        "rdf_id"              : "ROR",
        "local_IRI"           : "sibilt:ROR",
        "local_concept_IRI"   : "sibilc:ROR_04ttjf776",
        "concept_notation"    : "ROR:04ttjf776",
        "concept_exact_match" : None,
        "concept_see_also"    : "https://ror.org/04ttjf776"        
    })                                      
    
    errors += test_result(tex.uniprot_swissprot, "Q54NB6", {
        "rdf_id"              : "uniprot",
        "local_IRI"           : "sibilt:uniprot",
        "local_concept_IRI"   : "sibilc:uniprot_Q54NB6",
        "concept_notation"    : "uniprot:Q54NB6",
        "concept_exact_match" : "http://purl.uniprot.org/uniprot/Q54NB6",
        "concept_see_also"    : "https://www.uniprot.org/uniprotkb/Q54NB6/entry"        
    })                                      

    print("ERRORs:", errors)
