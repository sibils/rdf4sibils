from pathlib import Path
import gzip
import json
from io import BytesIO


datadir = "../out/fetch/medline"
directory = Path(datadir)
gz_files = list(directory.rglob('*.gz'))
count = 0
fields = dict()
pubtypes = dict()
keywords = dict()
meshterms = dict()

coi_statement = dict()
sup_mesh_terms = dict()
chemicals = dict()
comments = dict()


ann_fields = dict()
sen_fields = dict()

for file in gz_files:
    count += 1
    if count > 1000000: break
    stream = open(file, 'rb')
    gzipped_data = stream.read()
    gz = gzip.GzipFile(fileobj=BytesIO(gzipped_data))
    decompressed_bytes = gz.read()
    json_str = decompressed_bytes.decode('utf-8')
    data = json.loads(json_str)
    stream.close()
    doc = data["document"]
    pmid = doc["pmid"]
    for k in doc:
        if k not in fields: fields[k] = 0
        fields[k] += 1
    for pt in doc["publication_types"]:
        if pt not in pubtypes: pubtypes[pt] = 0
        pubtypes[pt] += 1
    for k in doc["keywords"]:
        if len(keywords) > 50: break        
        if k not in keywords: keywords[k] = list()
        if len(keywords[k]) < 10: keywords[k].append(pmid)
    for k in doc["mesh_terms"]:
        if len(meshterms) > 50: break
        if k not in meshterms: meshterms[k] = list()
        if len(meshterms[k]) < 10: meshterms[k].append(pmid)
    coi = doc["coi_statement"]
    if coi != "" and len(coi_statement) < 50 : 
        if coi not in coi_statement: coi_statement[coi] = list()
        if len(coi_statement[coi]) < 10: coi_statement[coi].append(pmid)
    for k in doc["sup_mesh_terms"]:
        if len(sup_mesh_terms) > 50: break
        if k not in sup_mesh_terms: sup_mesh_terms[k] = list()
        if len(sup_mesh_terms[k]) < 10: sup_mesh_terms[k].append(pmid)

    for k in doc["chemicals"]:
        if len(chemicals) > 50: break
        if k not in chemicals: chemicals[k] = list()
        if len(chemicals[k]) < 10: chemicals[k].append(pmid)

    for k in doc["comments"]:
        if len(comments) > 50: break
        if k not in comments: comments[k] = list()
        if len(comments[k]) < 10: comments[k].append(pmid)

    sen2fld = dict()
    for s in data["sentences"]:
        num = s["sentence_number"]
        fld = s["field"]
        sen2fld[num] = fld
        if fld not in sen_fields: sen_fields[fld] = 0
        sen_fields[fld] += 1

    for ann in data["annotations"]:
        ann_fld = ann["field"]
        if ann_fld not in ann_fields: ann_fields[ann_fld] = 0
        ann_fields[ann_fld] += 1
        sen_num = ann["sentence_number"]        
        sen_fld = sen2fld[sen_num]
        if ann_fld != sen_fld:
            print(f"WARNING, inconsistent field in annot and sentence {sen_num} in pmid: {pmid}")
            continue
        

print("--- fields ---------------------")
for k in fields:
    print(k, fields[k])
print("--- publication_types  ---------------------")
for k in pubtypes: print(k, pubtypes[k])
print("--- keywords  ---------------------")
for k in keywords: print(k, keywords[k])
#print("--- mesh_terms  ---------------------")
#for k in meshterms: print(k, meshterms[k])
print("--- coi_statement  ---------------------")
for k in coi_statement: print(k, coi_statement[k])
print("--- sup_mesh_terms  ---------------------")
for k in sup_mesh_terms: print(k, sup_mesh_terms[k])
print("--- chemicals  ---------------------")
for k in chemicals: print(k, chemicals[k])
print("--- comments  ---------------------")
for k in comments: print(k, comments[k])

print("--- sen_fields ---------------------")
for k in sen_fields: print(k, sen_fields[k])
print("--- ann_fields ---------------------")
for k in ann_fields: print(k, ann_fields[k])

print("end")