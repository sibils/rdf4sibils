import json
import os

# Load the JSON file

filename = 'sibils.html/doc/webvowl/data/ontology.json'
os.rename(filename, filename + ".ori")
with open(filename + ".ori", 'r') as file:
    data = json.load(file)

# Fixes
languages = data["header"]["languages"]
if "en" not in languages: 
    print("adding 'en' to  header.languages list")
    languages.insert(0, "en")

title = data["header"].get("title")
if title is None:
    print("adding 'SIBiLS ontology' as header.title.undefined value")
    data["header"]["title"] = { "undefined": "SIBiLS ontology"}


# Save the modified JSON to a new file
with open(filename, 'w') as file:
    json.dump(data, file, indent=2)


