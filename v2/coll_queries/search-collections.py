import sys
import requests

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def get_coll_mapping(coll, pmid_list):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    pmid2pmcid = dict()
    warnings = list()
    idx = -1
    max = len(pmid_list)
    range_size = 1000
    while True:

        sub_list = list()
        for i in range(range_size):
            idx += 1
            if idx >= max: break
            #if idx >= 13: break
            sub_list.append(pmid_list[idx])
        if len(sub_list) == 0:
            idx -= 1 
            break

        print(f"Info, retrieving mapping for pmids in collection {coll} {idx + 1}/{len(pmid_list)} ...")
        url = "https://biodiversitypmc.sibils.org/api/pmid2pmcid"
        params = { "pmids": ",".join(sub_list) , "col": coll } 
        response = requests.post(url = url, data = params)
        status = response.status_code
        if status != 200:
            print(f"Error, response has status code {status}")
            sys.exit(1)
        data = response.json()
        #print(data)
        if data["success"] != True:
            msg = data["error"]
            print(f"Error, response data contains success : False, message: {msg}")
            sys.exit(1)
        warning = data["warning"]
        if len(warning) > 0:
            warnings.append(warning)
            print("Warning, ", warning)
        map_list = data["mapping"]
        for map in map_list:
            pmid2pmcid[ map["pmid"] ] = map["pmcid"]

    return pmid2pmcid




#-------------------------------------------------
if __name__ == '__main__':
#-------------------------------------------------

    if len(sys.argv) < 3 : 
        print("Error, usage is : python search-collections.py <input-file> <output_dir>")
        sys.exit(1)

    input_file = sys.argv[1]

    outdir = sys.argv[2]
    if not outdir.endswith("/") : outdir += "/"

    # read pmids saved in file generated in previous step
    stream = open(input_file, 'r')
    pmids = stream.read().splitlines()
    stream.close()

    # query SIBiLS about presence of pmid or corresponding pmcid in medline and pmc collections
    # SLOW process ( > 20 min )
    for coll in ["pmc", "medline"]:
        dic = get_coll_mapping(coll, pmids)
        outfile = outdir + coll + "-pmid-pmcid.txt"
        stream = open(outfile, "w")
        for k in dic: 
            value = "None" if dic[k] is None else dic[k]
            stream.write("".join([k, " : ", value, "\n"]))
        stream.close()

    # merge mappings found in pmc and medline collections
    merged_dic = dict()
    for k in pmids: merged_dic[k] = { "pmc": "None", "medline": "None" }
    for coll in ["pmc", "medline"]:
        stream = open(outdir + coll + "-pmid-pmcid.txt")
        for line in stream.read().splitlines():
            (pmid, pmcid) = line.split(" : ")
            merged_dic[pmid][coll] = pmcid
        stream.close()

    # save merged mapping dictionary in file
    outfile = outdir + "merged-mapping.txt"
    stream = open(outfile, "w")
    stream.write("pmid : medline : pmc\n")    
    for pmid in merged_dic:
        pmc = merged_dic[pmid]["pmc"]
        med = merged_dic[pmid]["medline"]
        if pmc != med and pmc != "None" and med != "None":
            print(f"Warning, inconsistent mapping for pmid {pmid}") 
        line = "".join([pmid, " : ", med, " : ", pmc, "\n"])
        stream.write(line)
    stream.close()

    print("end")