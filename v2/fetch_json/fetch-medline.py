import sys
import os
import requests
import json
import subprocess


#-------------------------------------------------
class MedlineJsonFetcher:
#-------------------------------------------------
    

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self, input_file, output_dir): 
    # - - - - - - - - - - - - - - - - - - - - - - - - - -
        self.input_file = input_file
        self.output_dir = output_dir
        self.state_file = output_dir + "medline-json-fetcher-state.txt"
        self.fetch_size = 500

        # read file containing list of pmids to fetch
        # line format = pmid : pmcid : pmcid
        stream = open(input_file)
        self.input_lines = stream.read().splitlines()
        stream.close()
        self.current_state = self.get_state() # contains pointer on input_lines


    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    def pmc_file_exists(self, pmcid):
    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # WARNING: this duplicates more or less code in PmcJsonFetcher class
    # - - - - - - - - - - - - - - - - - - - - - - - - - -
        publi_dir = self.output_dir + "../pmc/" + pmcid[0:5] + "/"
        file = publi_dir + pmcid + ".json.gz"
        return os.path.isfile(file)


    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_publi_dir(self, pmid):
    # - - - - - - - - - - - - - - - - - - - - - - - - - -
        publi_dir = self.output_dir + pmid[0:2] + "/"+ pmid[2:4] + "/"
        os.makedirs(publi_dir, exist_ok=True)
        return publi_dir


    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    def save_state(self, index):
    # - - - - - - - - - - - - - - - - - - - - - - - - - -
        stream = open(self.state_file, "w")
        stream.write(f"# this file persists state of MedlineJsonFetcher\ninput-lines-index={index}\n")
        stream.close()


    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_state(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - -
        # create file if does not exist
        if not os.path.exists(self.state_file): self.save_state(0)
        stream = open(self.state_file)
        # read state from file
        index = -1
        for line in stream.read().splitlines():
            if line.startswith("input-lines-index="):
                index = int(line[18:])
                break
        stream.close()
        return index


    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_next_medline_list(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - -
        self.current_state = self.get_state()
        medline_list = list()
        while True:
            if self.current_state + 1 >= len(self.input_lines): break
            if len(medline_list) > self.fetch_size: break
            self.current_state += 1
            (pmid, pmcid1, pmcid2) = self.input_lines[self.current_state].split(" : ")
            if pmcid1 != "None" and self.pmc_file_exists(pmcid1): continue # we skip pmid for which we already have loaded a pmc version
            if pmcid2 != "None" and self.pmc_file_exists(pmcid2): continue # we skip pmid for which we already have loaded a pmc version
            medline_list.append(pmid) 
        return medline_list
            

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    def fetch_medline_list(self, pmid_list):
    # - - - - - - - - - - - - - - - - - - - - - - - - - -
        pmids = ",".join(pmid_list)
        params = { "ids": pmids, "col": "medline" }
        url = "https://biodiversitypmc.sibils.org/api/fetch"
        warnings = list()
        response = requests.post(url = url, data = params)
        status = response.status_code
        if status != 200:
            print(f"Error, response has status code {status}")
            sys.exit(1)
        data = response.json()
        if data["success"] != True:
            msg = data["error"]
            print(f"Error, response data contains success : False, message: {msg}")
            sys.exit(1)
        warning = data["warning"]
        if len(warning) > 0:
            warnings.append(warning)
            print("Warning, ", warning)
        pub_list = data["sibils_article_set"]
        return pub_list


    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    def save_json_publi(self, publi):
    # - - - - - - - - - - - - - - - - - - - - - - - - - -
        pmid = publi["_id"]
        filename = self.get_publi_dir(pmid) + pmid + ".json"
        print("saving publi ", pmid, "as", filename + ".gz")
        stream = open(filename, 'w')
        json.dump(publi, stream, indent=2, ensure_ascii=True)  # indent=2 makes the file nicely formatted
        stream.close()
        subprocess.run(['gzip', '-f', filename], check=True)


    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    def fetch_and_save_next_medline_list(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - -
        print("medline fetch loop")
        print("initial state     :", fetcher.get_state())
        medline_list = fetcher.get_next_medline_list()
        print("medline list to fetch :",  medline_list)
        print("current state     :", fetcher.current_state)
        publi_list = fetcher.fetch_medline_list(medline_list)
        print("doc list size     :", len(publi_list))
        for publi in publi_list: fetcher.save_json_publi(publi)
        fetcher.save_state(fetcher.current_state)


#-------------------------------------------------
if __name__ == '__main__':
#-------------------------------------------------

    if len(sys.argv) < 3 : 
        print("Error, usage is : python fetch-medline.py <input-file> <output_dir>")
        sys.exit(1)

    input_file = sys.argv[1]

    outdir = sys.argv[2]
    if not outdir.endswith("/") : outdir += "/"

    fetcher = MedlineJsonFetcher(input_file, outdir)
    while fetcher.current_state + 1 < len(fetcher.input_lines):
        fetcher.fetch_and_save_next_medline_list()

