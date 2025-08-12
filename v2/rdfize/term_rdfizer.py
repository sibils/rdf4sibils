from ApiCommon import log_it
from rdf_utils import TripleList, getBlankNode, remove_accents
from namespace_registry import NamespaceRegistry
from termi_extra import TermiExtra, TermiExtraRegistry
import json


class TermRdfizer():


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def __init__(self, ns: NamespaceRegistry, terminology, meta): 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        self.ns = ns
        self.terminology = terminology
        self.meta = meta
        self.extra: TermiExtra = self.get_terminology_extra(self.get_id())


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def print(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        print(json.dumps(self.terminology, indent=4))


    # - - - - - - - - - - - - - - - - - - - - 
    # add functions to get terminology and concept properties from 
    # concept_source (termi_id) and concept_id (cpt_id)
    # e.g. exact_match_fun(cpt_id), ...
    # - - - - - - - - - - - - - - - - - - - - 
    def get_terminology_extra(self, termi_id):
    # - - - - - - - - - - - - - - - - - - - - 
        tex = TermiExtraRegistry(self.ns)
        return tex.id2termi[self.get_id()]


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_concept_exact_match(self, cpt_id):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        return self.extra.concept_exact_match(cpt_id)
    

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_concept_see_also(self, cpt_id):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        return self.extra.concept_see_also(cpt_id)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_concept_notation(self, cpt_id):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        return self.extra.concept_notation(cpt_id)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_concept_IRI(self, cpt_id):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        return self.extra.concept_IRI(cpt_id)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_label(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        term_id = self.get_id()
        label = self.meta.get("label")
        if term_id.startswith("covoc"): label = "COVOC " + label
        if label is None: label = term_id.capitalize()
        return label
    

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_url(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        return self.meta.get("url")
    

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_description(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        return self.meta.get("description")
    

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_id(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        return self.terminology["description"]["terminology"]


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_IRI(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        return self.extra.IRI()


    # - - - - - - - - - - - - - - - - - - - - 
    # relevant concepts are concepts cited in publi annotations
    # plus parent concepts of cited concepts
    # - - - - - - - - - - - - - - - - - - - - 
    def get_relevant_concepts(self, cited_concepts):
    # - - - - - - - - - - - - - - - - - - - - 
        relevant_concepts = set()
        for cpt_id in cited_concepts: # cited_concepts is a dictionary where key = cpt_id and value = short list of files where the concept id was cited
            parent_concepts = set()
            citing_files = cited_concepts[cpt_id]
            self.get_parent_concepts(cpt_id, citing_files, parent_concepts)
            relevant_concepts.update(parent_concepts)
        return relevant_concepts
    

    # - - - - - - - - - - - - - - - - - - - - 
    # recursive method to get all the parents 
    # of a concept including itself
    # - - - - - - - - - - - - - - - - - - - - 
    def get_parent_concepts(self, cpt_id, citing_files, parent_set):
    # - - - - - - - - - - - - - - - - - - - - 
        concept = self.terminology["concepts"].get(cpt_id)
        if concept is None: 
            # weird things we need to handle
            if cpt_id == "" and self.get_id() == "ott": return # "" is the parent of the root concept !
            if cpt_id == "http://www.w3.org/2002/07/owl#Thing" and self.get_id() == "atc": return
            if cpt_id == "" and self.get_id() == "atc": return
            if cpt_id == "IAO_0000030" and self.get_id() == "eco": return
            if cpt_id == "" and self.get_id() == "ncbitaxon_viruses": return
            # weird things triggering a WARNING because denotes an inconsistency
            log_it(f"WARNING, concept not found in terminology {self.get_id()}: '{cpt_id}' in file(s) {citing_files}")
            return
        if cpt_id in parent_set:
            return
        parent_set.add(cpt_id)
        for parent_id in concept.get("parents") or []:
            self.get_parent_concepts(parent_id, "terminology file " + self.get_id(), parent_set)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_triples_for_terminology(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        ns = self.ns
        triples = TripleList()
        termi_IRI = self.get_IRI()
        triples.append(termi_IRI, ns.rdf.type, ns.skos.ConceptScheme)
        triples.append(termi_IRI, ns.rdf.type, ns.owl.NamedIndividual)
        version = self.terminology["description"]["version"]
        triples.append(termi_IRI, ns.dcterms.hasVersion, ns.xsd.string(version))
        triples.append(termi_IRI, ns.rdfs.label, ns.xsd.string(self.get_label()))
        if self.get_description() is not None:
            triples.append(termi_IRI, ns.rdfs.comment, ns.xsd.string(self.get_description()))
        if self.get_url() is not None:
            triples.append(termi_IRI, ns.rdfs.seeAlso, "<" + self.get_url() + ">")

        triples.append("","","", punctuation="") # space line only

        return triples


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_triples_for_concept(self, cpt_id):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        ns = self.ns
        triples = TripleList()
        concept = self.terminology["concepts"].get(cpt_id)
        if concept is None:
            log_it(f"WARNING, concept not found in terminology {self.get_id()}: {cpt_id}")
            return triples
        
        cpt_IRI = self.get_concept_IRI(cpt_id)
        triples.append(cpt_IRI, ns.rdf.type, ns.skos.Concept)
        triples.append(cpt_IRI, ns.skos.inScheme, self.get_IRI())
        cpt_label = concept["preferred_term"]["term"]
        no_accent_label = remove_accents(cpt_label)
        triples.append(cpt_IRI, ns.skos.prefLabel, ns.xsd.string(no_accent_label))     
        triples.append(cpt_IRI, ns.skos.notation, ns.xsd.string(self.get_concept_notation(cpt_id)))
        for alt in concept.get("synonyms") or []:
            if alt["relevance"] == False: continue
            no_accent_label = remove_accents(alt["term"])
            triples.append(cpt_IRI, ns.skos.altLabel, ns.xsd.string(no_accent_label))
        for parent_id in concept.get("parents") or []:
            if self.terminology["concepts"].get(parent_id) is None:
                log_it(f"WARNING, concept not found in terminology {self.get_id()}: {cpt_id} has unknown parent {parent_id}")
            else:
                parent_IRI = self.get_concept_IRI(parent_id)            
                triples.append(cpt_IRI, ns.sibilo.more_specific_than, parent_IRI)
        exact_match_iri = self.get_concept_exact_match(cpt_id)
        if exact_match_iri is not None:
            triples.append(cpt_IRI, ns.skos.exactMatch, f"<{exact_match_iri}>")
        see_also_iri = self.get_concept_see_also(cpt_id)
        if see_also_iri is not None:
            triples.append(cpt_IRI, ns.rdfs.seeAlso, f"<{see_also_iri}>")

        triples.append("","","", punctuation="") # space line only

        return triples


