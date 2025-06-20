from rdfizer import BaseNamespace

class SibiloNamespace(BaseNamespace):
    def __init__(self):
        super(SibiloNamespace, self).__init__("","http://sibils.org/rdf#")

    def IRI(self, name): return "".join([":", name])

    # discouse elements either from deo, doco or local
    def DiscourseElement(self): return ":DiscourseElement"      # deo
    def Caption(self): return ":Caption"                        # deo
    def TableFooter(self): return ":TableFooter"                # local
    def Abstract(self): return ":Abstract"                      # doco
    def Appendix(self): return ":Appendix"
    def BackMatter(self): return ":BackMatter"
    def BlockQuotation(self): return ":BlockQuotation"
    def BodyMatter(self): return ":BodyMatter"
    def CaptionedBox(self): return ":CaptionedBox"
    def FloatMatter(self): return ":FloatMatter"               # local
    def FrontMatter(self): return ":FrontMatter"
    def Glossary(self): return ":Glossary"
    def Label(self): return ":Label"
    def ListItemBlock(self): return ":ListItemBlock"
    def ListOfReferences(self): return ":ListOfReferences"
    def MediaBlock(self): return ":MediaBlock"
    def ObjectIdBlock(self): return ":ObjectIdBlock"
    def Paragraph(self): return ":Paragraph"
    def Section(self): return ":Section"
    def SectionLabel(self): return ":SectionLabel"
    def Sentence(self): return ":Sentence"
    def SpeechBlock(self): return ":SpeechBlock"
    def StatementBlock(self): return ":StatementBlock"
    def Table(self): return ":Table"
    def TableBox(self): return ":TableBox"
    def TableCellValues(self): return ":TableCellValues"
    def TableColumnName(self): return ":TableColumnName"
    def TextBox(self): return ":TextBox"
    def Title(self): return ":Title"
    def VerseGroupBlock(self): return ":VerseGroupBlock"
    def WordSequence(self): return ":WordSequence"

    # publication types from fabio:
    def JournalArticle(self): return ":JournalArticle"
    def ReviewArticle(self): return ":ReviewArticle"
    def BriefReport(self): return ":BriefReport"
    def CaseReport(self): return ":CaseReport"
    def Publication(self): return ":Publication"
    def Editorial(self): return ":Editorial"
    def Letter(self): return ":Letter"
    def MeetingReport(self): return ":MeetingReport"

    def Manifestation(self): return ":Manifestation"    
    def Block(self): return ":Block"                            # not used ?


    def ordinal(self): return ":ordinal"                                                # local
    def more_specific_than(self): return ":more_specific_than"                          # local, subclass of skos
    def more_specific_than_transitive(self): return ":more_specific_than_transitive"    # local, subclass of skos

    def affiliation(self): return ":affiliation"                # schema
    
    def doi(self): return ":doi"                                # prism
    def endingPage(self): return ":endingPage"                  # prism
    def issueIdentifier(self): return ":issueIdentifier"        # prism
    def keyword(self): return ":keyword"                        # prism
    def pageRange(self): return ":pageRange"                    # prism
    def publicationDate(self): return ":publicationDate"        # prism
    def startingPage(self): return ":startingPage"              # prism
    def volume(self): return ":volume"                          # prism

    def abstract(self): return ":abstract"                      # dcterms
    def title(self): return ":title"                            # dcterms
    def creator(self): return ":creator"                        # dcterms
    def hasPart(self): return ":hasPart"                        # dcterms create subprop ?

    def contains(self): return ":contains"                      # po      create subprop ?
    
    def embodiment(self): return ":embodiment"                                          # frbr

    def hasNLMJournalTitleAbbreviation(self): return ":hasNLMJournalTitleAbbreviation"  # fabio
    def hasPubMedCentralId(self): return ":hasPubMedCentralId"                          # fabio
    def hasPubMedId(self): return ":hasPubMedId"                                        # fabio
    def hasPublicationYear(self): return ":hasPublicationYear"                          # fabio
    
    def NexAnnotation(self): return ":NexAnnotation"                                    # local, subclass of oa:Annotation
    def AnnotationTarget(self): return ":AnnotationTarget"                              # local, subclass of oa:SpecificResource
    def TextPositionSelector(self): return ":TextPositionSelector"                      # oa
    def hasAnnotation(self): return ":hasAnnotation"                                    # local
    def start(self): return ":start"                                                    # oa
    def end(self): return ":end"                                                        # oa
    def exact(self): return ":exact"                                                    # oa
    def hasBody(self): return ":hasBody"                                                # oa
    def hasSelector(self): return ":hasSelector"                                        # oa
    def hasSource(self): return ":hasSource"                                            # oa
    def hasTarget(self): return ":hasTarget"                                            # oa

    def chars(self): return ":chars"                                                    # cnt

    def version(self): return ":version"                                                # dcterms


    def Atc_St(self): return ":Atc_St"                      # <--- go on here: see which classes & props are involved in describing these sibils terminologies
    def Cellosaurus_St(self): return ":Cellosaurus_St"
    def Chebi_St(self): return ":Chebi_St"
    def Covocbiomed_St(self): return ":Covocbiomed_St"
    def Covoccelllines_St(self): return ":Covoccelllines_St"
    def Covocchemicals_St(self): return ":Covocchemicals_St"
    def Covocclinicaltrials_St(self): return ":Covocclinicaltrials_St"
    def Covocconceptualentities_St(self): return ":Covocconceptualentities_St"
    def Covocdiseaseandsyndrom_St(self): return ":Covocdiseaseandsyndrom_St"
    def Covocgeographicloc_St(self): return ":Covocgeographicloc_St"
    def Covocorganism_St(self): return ":Covocorganism_St"
    def Covocproteinsgenomes_St(self): return ":Covocproteinsgenomes_St"
    def Detectionmethods_St(self): return ":Detectionmethods_St"
    def Disprot_type1_St(self): return ":Disprot_type1_St"
    def Disprot_type2_St(self): return ":Disprot_type2_St"
    def Disprot_type3_St(self): return ":Disprot_type3_St"
    def Disprot_type4_St(self): return ":Disprot_type4_St"
    def Drugbank_St(self): return ":Drugbank_St"
    def Eco_St(self): return ":Eco_St"
    def Envo_St(self): return ":Envo_St"
    def Go_bp_St(self): return ":Go_bp_St"
    def Go_cc_St(self): return ":Go_cc_St"
    def Go_mf_St(self): return ":Go_mf_St"
    def Icdo3_St(self): return ":Icdo3_St"
    def Ictv_St(self): return ":Ictv_St"
    def License_St(self): return ":License_St"
    def Lotus_St(self): return ":Lotus_St"
    def Mdd_St(self): return ":Mdd_St"
    def Mesh_St(self): return ":Mesh_St"
    def Ncbitaxon_clinic_St(self): return ":Ncbitaxon_clinic_St"
    def Ncbitaxon_full_St(self): return ":Ncbitaxon_full_St"
    def Ncit_St(self): return ":Ncit_St"
    def Nextprot_St(self): return ":Nextprot_St"
    def Ott_St(self): return ":Ott_St"
    def Ppiptm_St(self): return ":Ppiptm_St"
    def Pubchemmesh_St(self): return ":Pubchemmesh_St"
    def Robi_St(self): return ":Robi_St"
    def Uniprot_small_St(self): return ":Uniprot_small_St"
    def SibilsTerminology(self): return ":SibilsTerminology"
