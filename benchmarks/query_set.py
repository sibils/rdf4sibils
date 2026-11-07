"""The benchmark queries: v2 examples and queries, plus one or two for each kind of work."""
from api_platform import ApiPlatform
from namespace_registry import NamespaceRegistry
from queries_utils import QueryFileReader
import datamodel_builder

GRAPH = "https://www.sibils.org/rdf/graphs/main"
BASE = "https://purl.expasy.org/sibils/rdf"

# as it was in datamodel_builder.py before the rewrite
ORIGINAL_PROP_USE_QUERY = """
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    select ?property ?tag ?node_type (count(*) as ?triple_count) where {
    values ?property { <$prop_long_IRI> }
    {
        ?_ ?property ?o .
        optional {?o a ?o_class }
        bind(coalesce(?o_class, datatype(?o), xsd:anyURI) as ?node_type)
        bind('range' as ?tag)
    } union {
        ?s ?property ?_ .
        optional {?s a ?s_class }
        bind(coalesce(?s_class, datatype(?s), xsd:anyURI) as ?node_type)
        bind('domain' as ?tag)
    } union {
        ?_s ?property ?_o .
        bind(xsd:integer as ?node_type)
        bind('count' as ?tag)
    }
    }
    group by ?property ?tag ?node_type
    order by ?property ?tag ?node_type
"""


# as it was in datamodel_builder.py before the rewrite
ORIGINAL_CLASS_USE_QUERY = """
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    select ?subject_class ?property ?object_type (count(*) as ?triple_count) where {
    values ?subject_class { <$class_long_IRI> }
    ?s a ?subject_class .
    ?s ?property ?o .
    optional {?o a ?o_class }
    bind(coalesce(?o_class, datatype(?o), xsd:anyURI) as ?object_type)
    }
    group by ?subject_class ?property ?object_type
    order by ?subject_class ?property ?object_type
"""


# the costly properties of the classes tested, for the per-property form of class_use
OA = "http://www.w3.org/ns/oa#"
CLASS_PROPS = {
    "sibilo:NexAnnotation": (("oa:hasBody", OA + "hasBody"), ("oa:hasTarget", OA + "hasTarget")),
    "sibilo:AnnotationTarget": (("oa:hasSelector", OA + "hasSelector"), ("oa:hasSource", OA + "hasSource")),
}


def build_queries():
    ns = NamespaceRegistry(ApiPlatform("prod"))
    pre = "\n".join(n.getSparqlPrefixDeclaration() for n in ns.namespaces) + "\n"
    q = []

    def add(group, name, sparql, heavy=False):
        q.append({"group": group, "name": name, "sparql": pre + sparql, "heavy": heavy})

    for e in QueryFileReader().query_list:
        add("examples", f"example {e.id}", "\n".join(e.sparql))

    add("counts", "triples in main graph", f"select (count(*) as ?c) where {{ graph <{GRAPH}> {{ ?s ?p ?o }} }}")
    add("counts", "triples per predicate", "select ?p (count(*) as ?c) where { ?s ?p ?o } group by ?p")
    add("counts", "instances per class", "select ?t (count(*) as ?c) where { ?s a ?t } group by ?t")
    add("counts", "annotations", "select (count(*) as ?c) where { ?s oa:hasBody ?o }")

    for label, iri in (("PMC publication", "data/PMC10002150"), ("MEDLINE publication", "data/1000501"), ("GO concept", "concept/GO_0018982"),
                       ("largest publication", "data/PMC5599884")):
        q.append({"group": "describe", "name": f"describe {label}", "describe": f"{BASE}/{iri}"})

    add("lookup", "properties of one publication", "select ?p ?o where { sibils:PMC10002150 ?p ?o }")
    add("lookup", "subjects of one concept", "select ?a where { ?a oa:hasBody sibilc:GO_0018982 } limit 1000")
    add("lookup", "publication by year literal", 'select ?p where { ?p fabio:hasPublicationYear "1976" } limit 1000')
    add("lookup", "annotations of one publication", "select ?a ?c where { sibils:PMC10002150 sibilo:hasAnnotation ?a . ?a oa:hasBody ?c }")

    add("joins", "concepts of one publication with labels",
        "select ?c ?l where { sibils:PMC10002150 sibilo:hasAnnotation ?a . ?a oa:hasBody ?c . ?c skos:prefLabel ?l }")
    add("joins", "top concepts", "select ?c (count(*) as ?n) where { ?a oa:hasBody ?c } group by ?c order by desc(?n) limit 20")
    add("joins", "annotated publications per source",
        "select ?src (count(distinct ?p) as ?n) where { ?p dcterms:isReferencedBy ?src . ?p sibilo:hasAnnotation ?a . ?a oa:hasBody sibilc:GO_0018982 } group by ?src")
    add("joins", "domain of sibilo:ordinal", "select ?value (count(distinct ?s) as ?n) where { ?s sibilo:ordinal ?o . ?s a ?value } group by ?value")

    add("text", "contains over sentences", "select (count(*) as ?c) where { ?x cnt:chars ?t filter(contains(lcase(?t), 'doubling time')) }")
    add("text", "regex on concept labels", 'select ?c where { ?c a skos:Concept . ?c skos:prefLabel ?l . filter(regex(str(?l), "^apoptotic process$", "i")) } limit 100')
    add("text", "prefix on concept labels", 'select ?c ?l where { ?c skos:prefLabel ?l . filter(strstarts(lcase(str(?l)), "apopto")) } limit 100')

    add("filters", "date range", 'select (count(*) as ?c) where { ?x prism:publicationDate ?d filter(?d >= "2020-01-01"^^xsd:date) }')
    add("filters", "publications per year", "select ?y (count(*) as ?c) where { ?x fabio:hasPublicationYear ?y } group by ?y")
    add("filters", "latest publications", "select ?x ?d where { ?x prism:publicationDate ?d } order by desc(?d) ?x limit 10")
    add("filters", "deep paging", "select ?a ?c where { ?a oa:hasBody ?c } order by ?a ?c limit 100 offset 1000000")

    add("paths", "ancestors of a GO term", "select distinct ?p where { sibilc:GO_0018982 sibilo:more_specific_than+ ?p }")
    add("paths", "ancestors up to depth 3", "select distinct ?p where { sibilc:GO_0018982 sibilo:more_specific_than{,3} ?p }")
    add("paths", "descendants of a broad GO term", "select (count(distinct ?c) as ?n) where { ?c sibilo:more_specific_than+ sibilc:GO_0008150 }")

    b = datamodel_builder.DataModelBuilder("http://unused", engine="qlever")
    add("model", "class definitions", b.class_def_query)
    add("model", "property definitions", b.prop_def_query)
    add("model", "prefixes", b.prefix_query)
    for name, iri in (("fabio:JournalArticle", "http://purl.org/spar/fabio/JournalArticle"),
                      ("oa:TextPositionSelector", "http://www.w3.org/ns/oa#TextPositionSelector"),
                      ("sibilo:AnnotationTarget", BASE + "/ontology/AnnotationTarget"),
                      ("sibilo:NexAnnotation", BASE + "/ontology/NexAnnotation")):
        add("heavy", f"class_use {name} properties", b.class_prop_query.replace("$class_long_IRI", iri), heavy=True)
        for pname, piri in (("rdf:type", "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),) + CLASS_PROPS.get(name, ()):
            add("heavy", f"class_use {name} {pname}", b.class_use_query.replace("$class_long_IRI", iri).replace("$prop_long_IRI", piri), heavy=True)
        add("heavy", f"class_use {name} as first written", ORIGINAL_CLASS_USE_QUERY.replace("$class_long_IRI", iri), heavy=True)
    for name, iri in (("oa:hasBody", "http://www.w3.org/ns/oa#hasBody"), ("sibilo:ordinal", BASE + "/ontology/ordinal")):
        add("heavy", f"prop_use {name} as first written", ORIGINAL_PROP_USE_QUERY.replace("$prop_long_IRI", iri), heavy=True)
        for kind, tmpl in b.prop_use_queries.items():
            add("heavy", f"prop_use {name} {kind}", tmpl.replace("$prop_long_IRI", iri), heavy=True)
    add("heavy", "/describe/model", f"""select ?subject_class ?property ?object_type (count(*) as ?triple_count) where {{
        graph <{GRAPH}> {{ ?s ?property ?o . ?s a ?subject_class . optional {{?o a ?o_class }}
        bind(coalesce(?o_class, datatype(?o), 'IRI') as ?object_type) }}}}
        group by ?subject_class ?property ?object_type order by ?subject_class ?property ?object_type""", heavy=True)
    return q
