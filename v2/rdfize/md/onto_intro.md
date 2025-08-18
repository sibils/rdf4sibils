**Links with other ontologies**

Most of the classes and properties defined within the SIBiLS ontology (prefix sibilo:) are derived from existing terms defined in general purpose or domain specific OWL ontologies:

* [fabio:](https://sparontologies.github.io/fabio/current/fabio.html) which extends dcterms and provides with a classification of bibliographic entities and more attributes (e.g. fabio:JournalArticle, ConferencePaper, ...)
* [prism:](https://www.w3.org/submissions/prism/) and [dcterms:](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/) which allow to describe most of publication metadata (e.g. dcterms:title, prism:year prism:doi, etc.)
* [deo:](https://sparontologies.github.io/deo/current/deo.html) and [doco:](https://sparontologies.github.io/doco/current/doco.html) terms are used to describe the structure of the publication which breaks into connected discourse elements (e.g. doco:Section, doco:Sentence, etc.) 
* [oa:](https://www.w3.org/ns/oa#) terms are used to describe annotations linked to a publication, specifying which concept is identified and its exact location (e.g., the position within a sentence). 
* [schema:](https://schema.org/) provides concepts for persons, organizations, membership and affiliation
* [skos](https://www.w3.org/2004/02/skos/) terms are used to define concept schems (terminologies, ontologies) and to link related concepts within concept schemes. It is also used to add informal semantic links between terms across ontologies, for example between fabio:Thesis and up:ThesisCitation. Note that skos properties linking our terms to other ontology terms are displayed in the _has relation_ section of the term.


**Concept schemes and concepts**

In SIBiLS RDF, publications are annotated with concepts derived from standard terminologies or ontologies:

* each terminology is represented as an owl:NamedIndividual and also as an instance of slos:ConceptScheme. 
* each concept is represented as an instance of skos:Concept and linked to its terminology using the skos:inScheme property. 

When a terminology defines a subsumption relationship between two concepts within the same terminology, it is represented by the sibilo:more_specific_than property, which is a sub-property of skos:broader.

For any concept used in SIBiLS to annotate a publication, the RDF provide with:

* all the parent concepts up to the root concept in the original terminology (when subsuming relationships exist)
* the hierarchical structure with property _sibilo:more_specific_than_ properties linking concepts

Making the hierarchy of concepts available within SIBiLS makes it possible to build SPARQL queries using a criterion like 

> ?any_concept sibilo:more_specific_than* ?some_concept . 

See also SPARQL query examples at [sparql-editor](/sparql-editor) 


**Named individuals**

The SIBiLS ontology defines a number of so-called named individuals (owl:NamedIndividual) for terminologies. They belong to the class cello:CelloConceptScheme and there IRIs are  in the _sibilt:_ namespace (e.g. sibilt:uniprot, sibilt:ECO, sibilt:NCBI_TaxID, sibilt:CHEBI, etc.). See [Named Individuals](#namedindividuals) for the full list.


**Main namespaces**

Here is a list of the most important namespaces used in the SIBiLS RDF.  

| Prefix     | IRI        | Name |
|------------|------------|------|
| sibils:    | $sibils_url | SIBiLS data |
| sibilo:    | $sibilo_url | SIBiLS ontology classes and properties |
| sibilt:    | $sibilt_url | SIBiLS terminologies |
| sibilc:    | $sibilc_url | SIBiLS concepts |
| fabio:     | http://purl.org/spar/fabio/ | FaBiO, the FRBR-aligned Bibliographic Ontology |
| prism:     | (http://prismstandard.org/namespaces/basic/2.0/) | PRISM Specification Package - W3C Member Submission 10 September 2020 |
| dcterms:   | http://purl.org/dc/terms/ | DCMI Metadata Terms |
| deo:       | http://purl.org/spar/deo/ | The Discourse Elements Ontology |
| doco:      | http://purl.org/spar/doco/ | DoCO, the Document Components Ontology |
| oa:        | http://www.w3.org/ns/oa# | Web Annotation Ontology (W3C) |
| schema:    | https://schema.org/ | Schemas for structured data on the Internet |
| skos:      | http://www.w3.org/2004/02/skos/core# | Simple Knowledge Organization System |
| owl:       | http://www.w3.org/2002/07/owl# | The OWL 2 Schema vocabulary  |
| rdf:       | http://www.w3.org/1999/02/22-rdf-syntax-ns# | The RDF Concepts Vocabulary |
| rdfs:      | http://www.w3.org/2000/01/rdf-schema# | The RDF Schema vocabulary |









