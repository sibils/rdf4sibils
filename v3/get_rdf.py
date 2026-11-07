import requests 

go_id = "GO_0007249"  # Use underscore, not colon
#       http://purl.obolibrary.org/obo/GO_0007249
url = f"http://purl.obolibrary.org/obo/{go_id}"

#response = requests.get(url, headers={"Accept": "application/rdf+xml"})
response = requests.get(url, headers={"Accept": "text/turtle"})

if response.status_code == 200:
    print(response.text)  # RDF/XML content
else:
    print(f"Term not found, status: {response.status_code}")
