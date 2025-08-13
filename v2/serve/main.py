import os
import sys
import json
import argparse
import datetime
from lxml import etree, html

from fastapi import FastAPI, Query, responses, Path, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.openapi.docs import get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html
from fastapi.staticfiles import StaticFiles
#from fastapi.openapi.docs import get_redoc_html,
#from fastapi import status, HTTPException
from gunicorn import glogging
from typing import Optional
#from typing import List
from pydantic import BaseModel
#from pydantic import Field as PydanticField
from urllib.parse import urlencode
import uvicorn
from enum import Enum
from starlette.middleware.base import BaseHTTPMiddleware

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'rdfize')))

import ApiCommon
from ApiCommon import log_it, get_format_from_headers
from api_platform import ApiPlatform
from namespace_registry import NamespaceRegistry
from html_builder import HtmlBuilder

import requests


# ----------------------------------------
# to be run first (in spyder only)
# ----------------------------------------
# import nest_asyncio
# nest_asyncio.apply()
# ----------------------------------------


# used for API documentation about errors
class ErrorMessage(BaseModel):
    message: str
    code: int

# used to give verified values for output format
class Format(str, Enum):
    jsn = "json"
    xml = "xml"
    txt = "txt"
    tsv = "tsv"



json_type_responses = { "description": "Successful response", "content" : { "application/json": {} } }


# simple multi media types response
four_media_types_responses = { "description": "Successful response", "content" : {
  "application/json": {},
  "text/plain": {},
  "application/xml": {},
  "text/tab-separated-values": {}
  }
}

class ThreeFormat(str, Enum):
    jsn = "json"
    txt = "txt"
    tsv = "tsv"

three_media_types_responses = { "description": "Successful response", "content" : {
  "application/json": {},
  "text/plain": {},
  "text/tab-separated-values": {}
  }
}

# NOTE:
# for some reason, rdf_is_visible, platform, ns_reg (global variables) used as 
# a parameter value in some @app.get(...)  must be declared and set before the @app.get(...) methods
rdf_is_visible = (os.getenv("RDF_IS_VISIBLE","False").upper() == "TRUE")
log_it("INFO:", "reading / getting default for env variable", f"RDF_IS_VISIBLE={rdf_is_visible}")
platform_key = os.getenv("PLATFORM_KEY","prod").lower()
log_it("INFO:", "building platform from env variable", f"PLATFORM_KEY={platform_key}")
platform = ApiPlatform(platform_key)
log_it("INFO:", "building namespace registry (ns_reg) from platform", f"PLATFORM_KEY={platform_key}")
ns_reg = NamespaceRegistry(platform)


subns_dict = dict()
for ns in [ns_reg.sibils, ns_reg.sibilo, ns_reg.sibilt, ns_reg.sibilc ]:
  subdir = ns.url.split("/")[-2]
  subns_dict[subdir] = subdir
SubNs = Enum('SubNs', subns_dict)

class RdfFormat(str, Enum):
    ttl = "ttl"
    rdf = "rdf"
    n3 = "n3"
    jsonld = "jsonld"
    html = "html"

format2mimetype = {
    "ttl": "text/turtle",
    "rdf": "application/rdf+xml",
    "n3": "application/n-triples",
    "jsonld": "application/ld+json",
    "html": "text/html"
}

rdf_media_types_responses = { "description": "Successful response", "content" : {
    "text/turtle": {},
    "application/rdf+xml": {},
    "application/n-triples": {},
    "application/ld+json": {},
    "text/html": {},
  }
}


# documentation for categories containng the API methods in the display, see also tags=["..."] below
tags_metadata = [
    {   "name": "General",
        "description": "Get general information about the current SIBiLS release",
    }]
if rdf_is_visible:
    tags_metadata.append({ "name": "RDF", "description": "RDF description of entities" })




class CacheControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-cache"
        #log_it(">>> no cache", request.url)
        return response


# general documentation in the header of the page
app = FastAPI(
    title="Cellosaurus API methods",
    description="This API is dedicated to users who want to query and access programmatically Cellosaurus data.",
    version=ApiCommon.CELLAPI_VERSION,
    terms_of_service="https://www.expasy.org/terms-of-use",
#    contact={
#        "name": "Cellosaurus",
#        "email": "cellosaurus@sib.swiss", # requires a valid email address otherwise openapi.json fails to build
#    },
    license_info={
        "name": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "url": "https://creativecommons.org/licenses/by/4.0/",
    },
    docs_url = None, redoc_url = None,
    #docs_url="/docs", redoc_url="/alt/help",
    openapi_tags=tags_metadata,
    # root_path = "/bla/bla" # see https://fastapi.tiangolo.com/advanced/behind-a-proxy/
    # root_path can be passed to fastapi from uvicorn as an argument (see __main__ below) 
    # but cannot be passed from gunicorn unless a custom worker class is created
    # see https://github.com/Midnighter/fastapi-mount/tree/root-path
    # but a simple ENV variable or config file can also be used to set root_path directly 
    # here in the FastAPI c'tor
    )


#
# Adds a Cache-control: no-cache header in response
# see CacheControlMiddleware class above
#
# With this setting, perplexity.ai says:
# FastAPI will always resend a fresh response with status 200 for your own routes if you only set Cache-Control: no-cache 
# and do not implement validation headers like ETag or Last-Modified or handle conditional requests. The no-cache directive forces the 
# browser to revalidate with the server, but unless your server checks the client's cache validation headers and returns a 
# 304 Not Modified when appropriate, FastAPI will simply generate and send a new response with status 200 every time
#
# It seems that the header Cache-Control: no-cache is also sent by CacheControlMiddleware for static resources whatever the response status (200, 304).
# Browsers seem to send If-Not_Modified-Since and If-None-Match headers which are properly handled by FastAPI
# The best "trick" to make sure cache is handled properly on browsers is to update the timestamp of resource files befaore each release
#
# Conclusion: we don't use CacheControlMiddleware class
#  
# app.add_middleware(CacheControlMiddleware)
#


# local hosting of js / css for swagger and redocs
# see https://fastapi.tiangolo.com/advanced/extending-openapi/

# Note: 
# Local copy of old swagger ui because is not compatible with new openai syntax is not used anymore
# Does not work with current json generated by fastapi.
# Local copy of swagger css modified by me is not used anymore by swagger generated page... but still used by api-quick-start and api-fields pages

# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# historical routes with permanent redirect
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# @app.get("/help-methods")
# async def redirect_to_new_route():
#     return RedirectResponse(url="/api-methods", status_code=301)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# active routes
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
@app.get("/api-methods", include_in_schema=False)
async def custom_swagger_ui_html(request: Request):
    print("calling custom_swagger_ui_html()")
    scope = request.scope.get("root_path")
    if scope is None or scope == "/": scope = ""
    #print("scope", scope)
    html_response = get_swagger_ui_html(
        openapi_url=scope + app.openapi_url,
        title=app.title,
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        #swagger_js_url= scope + "/static/swagger-ui-bundle.js", # see note above
        #swagger_css_url= scope + "/static/swagger-ui.css",      # see note above
        swagger_favicon_url = scope + "/static/favicon32.png"
    )
 
    # now add navigation to the swagger page generated by FastAPI
    content_tree = html.fromstring(html_response.body.decode())
    # build a new HTTP response with amended content
    htmlBuilder.add_nav_css_link_to_head(content_tree)
    htmlBuilder.add_nav_node_to_body(content_tree)
    final_content = html.tostring(content_tree, pretty_print=True, method="html", doctype="<!DOCTYPE html>",  encoding="utf-8")    
    return HTMLResponse(content=final_content, status_code=200)


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
@app.on_event("startup")
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
async def startup_event():

    global htmlBuilder, rdf_is_visible, platform, ns_reg # these vars are init'ed before creating app

    t0 = datetime.datetime.now()
    htmlBuilder = HtmlBuilder(platform) # TODO: see if other vars can be init'ed here or move this towards other vars
    
    # Note: log_it() is self-made, unrelated to fastAPI / uvicorn /gunicorn logging system
    log_it("INFO:", "app.stattup() callback was called :-)", duration_since=t0)



# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# see also https://github.com/tiangolo/fastapi/issues/50
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
@app.get("/release-info", 
         name="Get SIBiLS release information in various formats",
         tags=["General"],
         responses={ "200":four_media_types_responses})
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
async def get_release_info(
        request: Request,
        format: Format = Query(
            default= None,
            description="""Use this parameter to choose the response output format.
            Alternatively you can also use the HTTP Accept header of your
            request and set it to either text/plain, text/tab-separated-values, application/xml, application/json.
            If the format parameter is used, the accept header value is ignored.
            If both the format parameter and the Accept header are undefined, then the response will use the json format."""
            )
        ):

    t0 = datetime.datetime.now()
    # precedence of format over request headers
    #print("format", format)
    if format is None: format = get_format_from_headers(request.headers) # this might return "html" which is not suitable here
    #print("format", format)
    if format is None or format == "html": format = "json"
    #print("format", format)

    release_info = { "version": "1.0", "updated": "2025-08-13", "nb-publications": "(undefined)"}
    # build and return response in appropriate format
    if format == "tsv":
        data = "version\tupdated\tnb-publications\n"
        data += release_info.get("version") + "\t"
        data += release_info.get("updated") + "\t"
        data += release_info.get("nb-publications") + "\n"
        log_it("INFO:", "Processed" , request.url, "format", format, duration_since=t0)
        return responses.Response(content=data, media_type="text/tab-separated-values")
    elif format == 'txt':
        data  = "version: " +release_info.get("version") + "; "
        data += "updated: " +release_info.get("updated") + "; "
        data += "nb-cell-lines: " +release_info.get("nb-cell-lines") + "; "
        data += "nb-publications: " +release_info.get("nb-publications") + "\n"
        log_it("INFO:", "Processed" , request.url, "format", format, duration_since=t0)
        return responses.Response(content=data,media_type="text/plain")
    elif format == 'json':
        obj = {"Cellosaurus": {"header": {"release": release_info}}}
        data = json.dumps(obj, sort_keys=True, indent=2)
        log_it("INFO:", "Processed" , request.url, "format", format, duration_since=t0)
        return responses.Response(content=data,media_type="application/json")
    elif format == "xml":
        root_el = etree.Element("Cellosaurus")
        head_el = etree.SubElement(root_el, "header")
        rel_el = etree.SubElement(head_el, "release")
        rel_el.attrib["version"] = release_info.get("version")
        rel_el.attrib["updated"] = release_info.get("updated")
        rel_el.attrib["nb-cell-lines"] = release_info.get("nb-cell-lines")
        rel_el.attrib["nb-publications"] = release_info.get("nb-publications")
        data = etree.tostring(root_el, encoding="utf-8", pretty_print=True)
        log_it("INFO:", "Processed" , request.url, "format", format, duration_since=t0)
        return responses.Response(content=data, media_type="application/xml")


# some useful links:
# see also https://github.com/tiangolo/fastapi/issues/50
# see also https://fastapi.tiangolo.com/advanced/additional-responses/


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
@app.get("/describe/entity/ontology/.{format}" , name="RDF description of the SIBiLS ontology", tags=["RDF"], response_class=responses.Response, responses={"200":rdf_media_types_responses, "400": {"model": ErrorMessage}}, include_in_schema=rdf_is_visible)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
async def describe_onto(
        request: Request,
        format: RdfFormat = Path(
            title="Response format",
            description="Response output format"
            ),
        ):
    return describe_any(SubNs["ontology"], "", format, request)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
@app.get("/describe/entity/ontology/" , name="RDF description of the SIBiLS ontology", tags=["RDF"], response_class=responses.Response, responses={"200":rdf_media_types_responses, "400": {"model": ErrorMessage}}, include_in_schema=rdf_is_visible)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
async def describe_onto(
        request: Request,
        format: RdfFormat = Query(
            default= None,
            title="Response format",
            description="""Use this parameter to choose the response output format.
            Alternatively you can also use the HTTP Accept header of your
            request and set it to either text/turtle, application/rdf+xml, application/n-triples, application/ld+json.
            If the format parameter is used, the accept header value is ignored.
            If both the format parameter and the Accept header are undefined, then the response will use the ld+json format."""
            )
        ):
    return describe_any(SubNs["ontology"], "", format, request)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# TODO: decide whether we keep it or not
@app.get("/describe/entity/{prefix}/{id}.{format}" , name="RDF description of a SIBiLS entity", tags=["RDF"], response_class=responses.Response, responses={"200":rdf_media_types_responses, "400": {"model": ErrorMessage}}, include_in_schema=rdf_is_visible)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
async def describe_entity(
        request: Request,
        prefix: SubNs = Path(        
            title="Prefix of the entity ",
            description="The prefix (or namespace) of the resource IRI, i.e. 'fabio' in fabio:Abstract"            
            ),
        id: str = Path(
            title="Identifier of the entity",
            description="The identifier of the entity in its namespace (prefix), i.e. 'Abstract' in fabio:Abstract"
            ),
        format: RdfFormat = Path(
            title="Response format",
            description="Response output format"
            ),
        ):
    return describe_any(prefix, id, format, request)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
@app.get("/describe/entity/{prefix}/{id}" , name="RDF description of a SIBiLS entity", tags=["RDF"], response_class=responses.Response, responses={"200":rdf_media_types_responses, "400": {"model": ErrorMessage}}, include_in_schema=rdf_is_visible)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
async def describe_entity(
        request: Request,
        prefix: SubNs = Path(        
            title="Prefix of the entity ",
            description="The prefix (or namespace) of the resource IRI, i.e. 'fabio' in fabio:Abstract"            
            ),
        id: str = Path(
            title="Identifier of the entity",
            description="The identifier of the entity in its namespace (prefix), i.e. 'Abstract' in fabio:Abstract"
            ),
        format: RdfFormat = Query(
            default= None,
            title="Response format",
            description="""Use this parameter to choose the response output format.
            Alternatively you can also use the HTTP Accept header of your
            request and set it to either text/turtle, application/rdf+xml, application/n-triples, application/ld+json.
            If the format parameter is used, the accept header value is ignored.
            If both the format parameter and the Accept header are undefined, then the response will use the ld+json format."""
            )
        ):
    return describe_any(prefix, id, format, request)


def describe_any(dir, ac, format, request):
    t0 = datetime.datetime.now()
    log_it("INFO", f"called describe_any(dir=\"{dir.value}\", ac=\"{ac}\")")

    # precedence of format over request headers (does NOT work from swagger page !!! but of from curl)
    #print(">>>> format 1", format, format== RdfFormat.jsonld)
    #print(request.headers)
    if format is None: format = get_format_from_headers(request.headers)
    #print(">>>> format 2", format, format== RdfFormat.jsonld)
    if format is None: format = RdfFormat.jsonld
    #print(">>>> format 3", format, format== RdfFormat.jsonld)

    # method to redirect to website in case of text/html Accept header
    # using the virtuoso x-nice-microdata instead was chosen, see below.
    # if format == RdfFormat.html:
    #     url = "https://www.cellosaurus.org/" + ac
    #     log_it("INFO:", "Processed" , request.url, "format", format, duration_since=t0)
    #     return responses.RedirectResponse(url=url, status_code=301) # 301: Permanent redirect

    sparql_service = platform.get_private_sparql_service_IRI()
    iri = f"<{platform.get_rdf_base_IRI()}/{dir.value}/{ac}>"
    query = f"""DEFINE sql:describe-mode "CBD" describe {iri}"""
    print("query:", query)
    payload = {"query": query}
    if format == RdfFormat.html: payload["format"] = "application/x-nice-microdata"
    mimetype = format2mimetype.get(format)
    headers = { "Content-Type": "application/x-www-form-urlencoded" , "Accept" : mimetype }    
    response = requests.post(sparql_service, data=urlencode(payload), headers=headers)
    log_it("INFO:", "Processed" , request.url, "format", format, duration_since=t0)
    return responses.Response(content=response.text, media_type=mimetype )



# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
@app.get("/describe/model" , name="Typical triples found in Cellosaurus RDF", tags=["RDF"], response_class=responses.Response, responses={"200":json_type_responses, "400": {"model": ErrorMessage}}, include_in_schema=rdf_is_visible)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
async def get_model_description(request:Request):
    t0 = datetime.datetime.now()
    log_it("INFO", f"called describe/model")
    sparql_service = platform.get_private_sparql_service_IRI()
    query = """
        select ?subject_class ?property ?object_type (count(*) as ?triple_count) where {
        GRAPH <https://www.sibils.org/rdf/graphs/main> {
            ?s ?property ?o .
            ?s a ?subject_class .
            optional {?o a ?o_class }
            bind(coalesce(?o_class, datatype(?o), 'IRI') as ?object_type)
        }}
        group by ?subject_class ?property ?object_type
        order by ?subject_class ?property ?object_type
    """
    print("query:", query)
    payload = {"query": query}
    mimetype = "application/sparql-results+json"
    headers = { "Content-Type": "application/x-www-form-urlencoded" , "Accept" : mimetype }    
    response = requests.post(sparql_service, data=urlencode(payload), headers=headers)
    log_it("INFO:", "Processed" , request.url, "format", format, duration_since=t0)
    return responses.Response(content=response.text, media_type=mimetype )





# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
@app.get("/", tags=["General"], response_class=responses.HTMLResponse, include_in_schema=False)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
async def get_basic_help(request: Request):
    scope = request.scope.get("root_path")
    if scope is None or scope == "/": scope = ""
    # print(">>> scope", scope, "version", request.app.version)
    # read HTML template
    content = htmlBuilder.get_file_content("html.templates/api-quick-start.template.html")
    # build response and send it
    content = content.replace("$scope", scope).replace("$version",request.app.version)
    content_tree = html.fromstring(content)
    htmlBuilder.add_nav_css_link_to_head(content_tree)
    htmlBuilder.add_nav_node_to_body(content_tree)
    final_content = html.tostring(content_tree, pretty_print=True, method="html", doctype="<!DOCTYPE html>",  encoding="utf-8")    
    return responses.Response(content=final_content,media_type="text/html")



# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
@app.get("/rdf-concept-hopper", tags=["General"], response_class=responses.HTMLResponse, include_in_schema=False)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
async def get_rdf_concept_hopper(request: Request):
    scope = request.scope.get("root_path")
    if scope is None or scope == "/": scope = ""
    # print(">>> scope", scope, "version", request.app.version)
    # read HTML template
    content = htmlBuilder.get_file_content("html.templates/rdf-concept-hopper.template.html")
    # build response and send it
    #content = content.replace("$base_IRI", platform.get_rdf_base_IRI()) # no variable to set so far
    content_tree = html.fromstring(content)
    htmlBuilder.add_nav_css_link_to_head(content_tree)
    htmlBuilder.add_nav_node_to_body(content_tree)
    final_content = html.tostring(content_tree, pretty_print=True, method="html", doctype="<!DOCTYPE html>",  encoding="utf-8")    
    return responses.Response(content=final_content, media_type="text/html")


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
@app.get("/rdf-downloads", tags=["General"], response_class=responses.HTMLResponse, include_in_schema=False)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
async def get_rdf_downloads(request: Request):
    scope = request.scope.get("root_path")
    if scope is None or scope == "/": scope = ""
    # print(">>> scope", scope, "version", request.app.version)
    # read HTML template
    content = htmlBuilder.get_file_content("html.templates/rdf-downloads.template.html")
    # build response and send it
    #content = content.replace("$base_IRI", platform.get_rdf_base_IRI()) # no variable to set so far
    content_tree = html.fromstring(content)
    htmlBuilder.add_nav_css_link_to_head(content_tree)
    htmlBuilder.add_nav_node_to_body(content_tree)
    final_content = html.tostring(content_tree, pretty_print=True, method="html", doctype="<!DOCTYPE html>",  encoding="utf-8")    
    return responses.Response(content=final_content,media_type="text/html")


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
@app.get("/rdf-dereferencing", tags=["General"], response_class=responses.HTMLResponse, include_in_schema=False)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
async def get_help_resolver(request: Request):
    scope = request.scope.get("root_path")
    if scope is None or scope == "/": scope = ""
    # print(">>> scope", scope, "version", request.app.version)
    # read HTML template
    content = htmlBuilder.get_file_content("html.templates/rdf-dereferencing.template.html")
    # build response and send it
    content = content.replace("$base_IRI", platform.get_rdf_base_IRI())
    content_tree = html.fromstring(content)
    htmlBuilder.add_nav_css_link_to_head(content_tree)
    htmlBuilder.add_nav_node_to_body(content_tree)
    final_content = html.tostring(content_tree, pretty_print=True, method="html", doctype="<!DOCTYPE html>",  encoding="utf-8")    
    return responses.Response(content=final_content,media_type="text/html")


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
@app.get("/sparql-service", tags=["General"], response_class=responses.HTMLResponse, include_in_schema=False)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
async def get_help_resolver(request: Request):
    scope = request.scope.get("root_path")
    if scope is None or scope == "/": scope = ""
    content = htmlBuilder.get_file_content("html.templates/sparql-service.template.html")
    # build response and send it
    content = content.replace("$base_IRI", platform.get_rdf_base_IRI())
    content = content.replace("$public_sparql_URI", platform.get_public_sparql_service_IRI())
    content_tree = html.fromstring(content)
    htmlBuilder.add_nav_css_link_to_head(content_tree)
    htmlBuilder.add_nav_node_to_body(content_tree)
    final_content = html.tostring(content_tree, pretty_print=True, method="html", doctype="<!DOCTYPE html>",  encoding="utf-8")    
    return responses.Response(content=final_content,media_type="text/html")


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
@app.get("/sparql-editor", tags=["General"], response_class=responses.HTMLResponse, include_in_schema=False)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
async def get_sparql_editor(request: Request):
    scope = request.scope.get("root_path")
    if scope is None or scope == "/": scope = ""
    #print(">>> scope", scope, "version", request.app.version)
    # read HTML template
    f=open("html.templates/sparql-editor.template.html","r")
    content = f.read()
    f.close()
    # build response and send it
    content = content.replace("$sparql_IRI", platform.get_public_sparql_service_IRI())
    content_tree = html.fromstring(content)
    htmlBuilder.add_nav_css_link_to_head(content_tree)
    htmlBuilder.add_nav_node_to_body(content_tree)
    final_content = html.tostring(content_tree, pretty_print=True, method="html", doctype="<!DOCTYPE html>",  encoding="utf-8")    
    return responses.Response(content=final_content,media_type="text/html")


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
@app.get("/rdf-ontology", tags=["General"], response_class=responses.HTMLResponse, include_in_schema=False)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
async def get_sparql_editor(request: Request):
    scope = request.scope.get("root_path")
    if scope is None or scope == "/": scope = ""
    # print(">>> scope", scope, "version", request.app.version)
    # read original file, insert navgation header, and send it
    
    content = htmlBuilder.get_file_content("static/sparql/doc/index-en.html")     # the file generated by widoco
    content_tree = html.fromstring(content)
    htmlBuilder.fix_ontology_css_collisions(content_tree)
    htmlBuilder.add_nav_css_link_to_head(content_tree)
    htmlBuilder.add_nav_favicon_link_to_head(content_tree)
    htmlBuilder.add_script_node_to_head(content_tree)
    htmlBuilder.add_nav_node_to_body(content_tree)
    final_content = html.tostring(content_tree, pretty_print=True, method="html", doctype="<!DOCTYPE html>",  encoding="utf-8")    
    return responses.Response(content=final_content,media_type="text/html")




# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# NOTE: mounting /static at the end of this file rather than just after app creation allows
# for app.get() methods defined above to override the default behaviour for static files directory
# see example app.get("/static/toto")

# serve files in ./static as if they were in ./static
# this is necessary for fastapi / swagger to know where the static files are served i.e. cellosaurus.ng above)
# note: the name value is arbitrary
app.mount("/static", StaticFiles(directory="static"), name="static")

# serve files in ./static/sparql/doc as if they were in ./
# this is used for serving page "/rdf-ontology"
# note: the name value is arbitrary
app.mount("/", StaticFiles(directory="static/sparql/doc"), name="widoco")

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 




# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# the __main__ code is used when you run this program as below:
#
# $ python main.py -s $server -p $port -r $scope -l True
#
# In production main.py run from an external script invoking gunicorn,
# a multiprocess HTTP request handler, see api_service.sh
# requirements: pip3.x install "uvicorn[standard]" gunicorn
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
if __name__ == '__main__':
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

    #print("I was in __main__")

    parser = argparse.ArgumentParser(description="Run a simple HTTP proxy for cellapi services")
    parser.add_argument("-s", "--server", default="localhost", help="IP address on which the server listens")
    parser.add_argument("-p", "--port", type=int, default=8088, help="port on which the server listens")
    parser.add_argument("-w", "--workers", default="1", help="Number of processes to run in parallel")
    parser.add_argument("-r", "--root_path", default="/", help="root path")
    parser.add_argument("-l", "--reload", default=False, help="reload on source code change")
    args = parser.parse_args()

    print("args.root_path",args.root_path)

    # add timestamp in logging system of uvicorn (does NOT work for gunicorn)
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"]["fmt"] =  '%(asctime)s %(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s'
    log_config["formatters"]["default"]["fmt"] = '%(asctime)s %(levelprefix)s %(message)s'
    log_config["loggers"]["uvicorn.access"]["propagate"] = True
    # uvicorn is mono-process, see gunicorn usage in api_service.sh
    uvicorn.run("main:app", port=args.port, host=args.server, reload=args.reload, log_level="info", log_config=log_config, root_path=args.root_path) #, workers=args.workers )