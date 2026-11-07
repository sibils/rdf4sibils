import os
import json

this_dir = os.path.dirname(os.path.abspath(__file__))
term_dir = this_dir + "/../out/terminologies" 

stream = open(term_dir + "/fundername_prefLabel_doi_category.txt")
concept_dic = dict()
while True:
    line = stream.readline()
    if line == "": break
    fields = line.strip().split("\t")
    alt = fields[0]
    pref = fields[1]
    doi = fields[2]
    if not doi.startswith("https://doi.org/10.13039/") : print("ERROR, unexpected DOI organization, expected 10.13039", line)

    cat = fields[3]
    if doi not in concept_dic: concept_dic[doi] = { "id": doi, "synonyms": dict() }
    record = concept_dic[doi]
    record["id"] = doi
    record["preferred_term"] = { "term": pref, "relevance": True }
    if alt != pref:
        record["synonyms"][alt] = {"term": alt, "source": "synonym", "relevance": True}
stream.close()

concept_list = list(concept_dic.values())
for cpt in concept_list:
    synonym_list = list(cpt["synonyms"].values())
    cpt["synonyms"] = synonym_list

for cpt in concept_list:
    if cpt.get("preferred_term") is None: print("ERROR, no preferred term", cpt)
    if cpt.get("id") is None: print("ERROR, no id", cpt)

termi_obj = {
    "description": {
        "terminology": "grant",
        "version": "v2",
        "date": "2025-10-13",
        "file_creation": "2025-10-13",
        "code": "grant",
        "type": "grant",
        "cleaners": { "df_general": True, "exclusion_general": True, "exclusion_specific": True, "length": False, "alphanum": False }
    },
    "concepts": concept_list
}

with open(term_dir + "/grant_v2.json", 'w') as f:
    json.dump(termi_obj, f, indent=4)
