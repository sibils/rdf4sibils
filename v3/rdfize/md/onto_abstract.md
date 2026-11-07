SIBiLS (Swiss Institute of Bioinformatics Literature Services) is a resource that enables personalized retrieval of biomedical literature through REST APIs, utilizing semantically enriched content to support curation workflows. 
A subset of the SIBiLS content is represented as RDF and made available via a SPARQL endpoint. 
The OWL SIBiLS ontology serves as the semantic model for the diverse information contained within the SIBiLS RDF.

The SIBiLS RDF includes a collection of full-text publications from PubMed Central as well as a collection of MedLine records, all semantically enriched with annotations.

Publications in the RDF are annotated to identify and localize biological concepts both within the full text and metadata. These concepts are extracted from a curated set of terminologies and ontologies relevant to the biological domain. The terminologies, ontologies, their concepts, and some of their semantic relationships are also represented in the RDF, enabling powerful and precise SPARQL queries.

The subset of scientific publications included in SIBiLS RDF is the union of those cited in other curated [SIB](https://www.sib.swiss/) resources such as [UniProtKB](https://www.uniprot.org/), [Rhea](https://www.rhea-db.org/), [SwissLipids](https://www.swisslipids.org/), and [Cellosaurus](https://www.cellosaurus.org/). When the full text of a publication is freely available from [PubMed Central](https://pmc.ncbi.nlm.nih.gov/), it is included; otherwise, only the [MedLine](https://www.nlm.nih.gov/medline/medline_home.html) record is used.

Each publication’s RDF representation contains metadata (including publication year, title, abstract, journal, and identifiers), as well as a hierarchical structure of the publication’s content. This structure is broken down into sections and subsections, which include paragraphs, tables, and figures, and further into leaf components such as titles, sentences, and list items where the actual textual content is found.

Delivering a RDF version of SIBiLS is an important step towards FAIRification. Making it available from our [SPARQL endpoint]($public_sparql_URL) is key to Linked Open Data (LOD) perspective and for improving interoperability in particular thanks to federated queries.

Two key principles guided the construction of the SIBiLS ontology:

  * Anchorage and reuse. A common vocabulary is essential for RDF to allow good interoperability so reusing terms from standard ontologies was a priority. Most of the classes and properties used in our ontology are terms defined in standard preexisting ontologies. 
  * Practicalities. Readability and documentation are important for us humans. Local equivalent classes and / or properties with human readable IRIs as well as sub-properties with documented domains and ranges were defined in order to take advantage of the [SPARQL-editor](/sparql-editor) (autocompletion functionality) and of the [widoco](https://github.com/dgarijo/Widoco) documentation tool which generated this page.

