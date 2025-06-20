import json

# ./chunks/medline/baseline/pubmed23n0024/bib_pubmed23n0024.json
# ./chunks/pmc/baseline/pmc23n0023/bib_pmc23n0023.json

'''
some pmc chunk publication ids

      "_id": "PMC2212067",
      "_id": "PMC2212068",
      "_id": "PMC2212069",
      "_id": "PMC2212070",
      "_id": "PMC2212071",
      "_id": "PMC2212072",
      "_id": "PMC2212073",
      
some medline chunk publication ids

      "_id": "729629",
      "_id": "729630",
      "_id": "729634",
      "_id": "729635",
      "_id": "729636",
      "_id": "729639",
      "_id": "729640",

some authors_ chunk publication ids

      "_id": "PMC2699768",
      "_id": "PMC2699770",
      "_id": "PMC2699771",
      "_id": "PMC2699773",
      "_id": "PMC2699840",
      "_id": "PMC2699841",
      "_id": "PMC2699860",
      "_id": "PMC2699888",

some pensoft chunk publication ids

      "_id": "10.3897/zse.96.48342",
      "_id": "10.3897/zse.96.56272",
      "_id": "10.3897/zse.96.53880",
      "_id": "10.3897/zse.96.55733",
      "_id": "10.3897/zse.96.56097",
      "_id": "10.3897/zse.96.55837",
      "_id": "10.3897/zse.96.56885",
      "_id": "10.3897/zse.96.55210",

'''



def get_publi_props(file):
    f_in = open(file)
    obj = json.load(f_in)
    publi_list = obj["article_list"]
    f_in.close()
    cnt = 0
    prop_dict = dict()
    for publi in publi_list:
        cnt += 1
        for prop in publi:
            if prop not in prop_dict: prop_dict[prop]=set()
            data_type = type(publi[prop]).__name__
            if data_type == "list" and len(publi[prop])>0:
                data_type += "[" + type(publi[prop][0]).__name__ + "]"

            prop_dict[prop].add(data_type)
    return prop_dict

file1 = "./chunks/medline/baseline/pubmed23n0024/bib_pubmed23n0024.json"
mdl_dic = get_publi_props(file1)
file2 = "./chunks/pmc/baseline/pmc23n0023/bib_pmc23n0023.json"
pmc_dic = get_publi_props(file2)
file3 = "./chunks/plazi/baseline/treatments23n0007/bib_treatments23n0007.json"
plz_dic = get_publi_props(file3)
file4 = "./chunks/pensoft/baseline/pensoft23n0001/bib_pensoft23n0001.json"
pen_dic = get_publi_props(file4)
file5 = "./chunks/authors_manuscripts/baseline/aut23n0015/bib_aut23n0015.json"
aut_dic = get_publi_props(file5)

final_dic = dict()
keys = set(mdl_dic.keys())
keys.update(set(pmc_dic.keys()))
keys.update(set(pen_dic.keys()))
keys.update(set(plz_dic.keys()))
keys.update(set(aut_dic.keys()))

for k in keys:
    v1 = ",".join(mdl_dic[k]) if k in mdl_dic else "n/a"  
    v2 = ",".join(pmc_dic[k]) if k in pmc_dic else "n/a"  
    v3 = ",".join(plz_dic[k]) if k in plz_dic else "n/a"  
    v4 = ",".join(pen_dic[k]) if k in pen_dic else "n/a"  
    v5 = ",".join(aut_dic[k]) if k in aut_dic else "n/a"  
    values =  [k, v1, v2, v3, v4, v5]
    final_dic[k] = values
keys = list(final_dic.keys())
keys.sort()
for k in keys: print("\t".join(final_dic[k]))

