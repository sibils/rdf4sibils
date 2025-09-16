
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class PlatformError(Exception): 
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    pass

# - - - - - - - - - - - - - - - - - - - - - - - - 
class ApiPlatform:
# - - - - - - - - - - - - - - - - - - - - - - - - 


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def __init__(self, key):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

        # the value of platform_key must be set from elsewhere:
        # - in main.py by reading ENV variable
        # - in cellapi_builder.py by a script argument
        # expected values are: local, test, prod
        if key.lower() not in ["local", "test", "prod"]: raise PlatformError(f"Invalid platform key: {key}")

        self.platform_key = key.lower()

        self.platform_dict = {
            # ---------------------------------
            # WARNING: no final "/", please !
            # ---------------------------------
            "local": {
                #"base_IRI": "https://purl.expasy.org/sibils/rdf",                  # base URL for IRIs generated in sibils/c/t/o
                "base_IRI": "http://local.sibils.org/rdf",                          # fastapi server URL (minus final / )
                "help_IRI": "http://localhost:8891",                
                "public_sparql_IRI": "http://localhost/sibils-sparql/service",
                "private_sparql_IRI" : "http://localhost:8891/sparql",
                "builder_sparql_IRI" : "http://localhost:8891/sparql"     
            },
            "test": {                
                "base_IRI": "http://pamansible.lan.text-analytics.ch/describe/entity",                          # base URL for IRIs generated in sibils/c/t/o
                "help_IRI": "http://pamansible.lan.text-analytics.ch/",             # fastapi server URL (minus final / ) TODO: TO BE DEFINED
                "public_sparql_IRI": "http://pamansible.lan.text-analytics.ch/sparql",
                "private_sparql_IRI" : "http://localhost:8891/sparql",
                "builder_sparql_IRI" : "http://localhost:8891/sparql"
            },
            "prod": {
                "base_IRI": "https://purl.expasy.org/sibils/rdf",                   # base URL for IRIs generated in sibils/c/t/o
                "help_IRI": "https://xxx.sibils.org",                               # fastapi server URL (minus final / ) TODO: TO BE DEFINED
                "public_sparql_IRI": "https://sparql.sibils.org/sparql",
                "private_sparql_IRI" : "http://localhost:8891/sparql",
                "builder_sparql_IRI" : "http://localhost:8891/sparql"
            }
        }


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_rdf_graph_IRI(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        # no final "/", please !
        # CAREFUL if you change this:
        # to be sync'ed with ./scripts/load_ttl_files.sh
        return "https://www.sibils.org/rdf/graphs/main"


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_onto_preferred_prefix(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        # used as a descripor of the ontology in its ttl file
        return "sibils"


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_rdf_base_IRI(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        # used as a base for all IRIs for cello, xref, 
        # org and cvcl namespaces  
        return self.platform_dict[self.platform_key]["base_IRI"]


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_help_base_IRI(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        # used as a base for all IRIs for cello, xref 
        return self.platform_dict[self.platform_key]["help_IRI"]


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_builder_sparql_service_IRI(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        # it is the URL of the sparql service used during ontology building
        # for determining term domains and ranges !!!
        # used on building sparql-editor related pages
        return self.platform_dict[self.platform_key]["builder_sparql_IRI"]


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_public_sparql_service_IRI(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        # it is the public URL of the sparql service !!!
        # used on building sparql-editor related pages
        return self.platform_dict[self.platform_key]["public_sparql_IRI"]


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_private_sparql_service_IRI(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        # it is the private URL of the sparql service !!!
        # internal use for API only
        return self.platform_dict[self.platform_key]["private_sparql_IRI"]


