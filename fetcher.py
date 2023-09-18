import ftplib
import os
import gzip
import sys
import json
import enum
import pickle
import datetime
from utils import log_it, gunzip

from get_publi_rdf import get_split_lists, get_triples_for_publi, get_triples_for_publi_annotations, get_prefixes

ftp_server="denver.text-analytics.ch"
ftp_dir_dict = dict()
# ftp_dir_dict["ana"] = "/SIBiLS_v3.2/pmc/baseline/ana/v1/"
# ftp_dir_dict["bib"] = "/SIBiLS_v3.2/pmc/baseline/bib/"
# ftp_dir_dict["sen"] = "/SIBiLS_v3.2/pmc/baseline/sen/"
ftp_dir_dict["ana"] = "/SIBiLS_v3.3/pmc/baseline/ana/v2/"
ftp_dir_dict["bib"] = "/SIBiLS_v3.3/pmc/baseline/bib/"
ftp_dir_dict["sen"] = "/SIBiLS_v3.3/pmc/baseline/sen/"

chunks_dir = "./chunks/"

# ------------------------------------------------------------------
def fetch_by_ftp(ftp_dir, ftp_file, target_dir):
# ------------------------------------------------------------------
    ftp = ftplib.FTP(ftp_server)
    ftp.login()
    # create dir(s) if necessary
    if not os.path.exists(target_dir): os.makedirs(target_dir)
    if not target_dir.endswith("/"): target_dir += "/"
    # download file if not done yet
    trg_file = target_dir + ftp_file
    if not os.path.exists(trg_file):
        log_it("INFO", "Downloading ", trg_file)
        ftp.cwd(ftp_dir)
        f = open(trg_file, "wb")
        ftp.retrbinary("RETR " + ftp_file, f.write)
        f.close()
    else:
        log_it("INFO", "Skipped download, target file already exists", trg_file)
    ftp.quit()

# ------------------------------------------------------------------
def fetch_chunk(chunk_name, chunks_dir=chunks_dir):
# ------------------------------------------------------------------
    log_it("INFO", "Fetching chunk ", chunk_name)
    for key in ftp_dir_dict:
        gz_file = key + "_" + chunk_name + ".json.gz"
        if not chunks_dir.endswith("/"): chunks_dir += "/"
        target_dir = chunks_dir + chunk_name + "/"
        fetch_by_ftp(ftp_dir_dict[key], gz_file, target_dir)
        gunzip(target_dir + gz_file)


# ------------------------------------------------------------------
def explode_bib(chunk_name, chunks_dir=chunks_dir):
# ------------------------------------------------------------------
    log_it("INFO", "Exploding bib file for", chunk_name)

    # read json object in bib file
    chunk_dir = get_chunk_dir(chunk_name, chunks_dir)
    bib_file = chunk_dir + "bib_" + chunk_name + ".json"
    f_in = open(bib_file, "rb")
    obj = json.load(f_in)
    f_in.close()

    # extract set of publication ids
    doc_set = set()
    subdir_set = set()
    for doc in obj["article_list"]:
        id = doc["_id"]
        doc_set.add(id)
        subdir_set.add(get_pmc_subdir(id))

    save_doc_set(chunk_dir, doc_set)

    # create subdir(s) if necessary
    for subdir in subdir_set:
        target_dir = chunk_dir + subdir + "/"
        if not os.path.exists(target_dir): os.makedirs(target_dir)

    # save each bib document as a pickle file
    for doc in obj["article_list"]:
        id = doc["_id"]
        target_dir = chunk_dir + get_pmc_subdir(id) + "/"
        filename = target_dir + id +".bib.pickle"
        f_out = open(filename, "wb")
        pickle.dump(doc, f_out, protocol=3) 
        f_out.close()

    del obj
    log_it("INFO", "Saved bib.pickle files in", chunk_dir)

# ------------------------------------------------------------------
def explode_sen(chunk_name, chunks_dir=chunks_dir):
# ------------------------------------------------------------------
    log_it("INFO", "Exploding sen file", chunk_name)

    # read json object in sen file
    chunk_dir = get_chunk_dir(chunk_name, chunks_dir)
    sen_file = chunk_dir + "sen_" + chunk_name + ".json"
    f_in = open(sen_file, "rb")
    obj = json.load(f_in)
    f_in.close()

    doc_set = load_doc_set(chunk_dir)

    # save each sen document as a pickle file
    for id in doc_set:
        sentences = obj.get(id)
        if sentences is None: sentences = list()
        target_dir = chunk_dir + get_pmc_subdir(id) + "/"
        filename = target_dir + id +".sen.pickle"
        f_out = open(filename, "wb")
        pickle.dump(sentences, f_out, protocol=3) 
        f_out.close()

    del obj
    log_it("INFO", "Saved sen.pickle files in", chunk_dir)


# ------------------------------------------------------------------
def explode_ana(chunk_name, chunks_dir=chunks_dir):
# ------------------------------------------------------------------
    log_it("INFO", "Exploding ana file", chunk_name)

    # read json object in ana file
    chunk_dir = get_chunk_dir(chunk_name, chunks_dir)
    sen_file = chunk_dir + "ana_" + chunk_name + ".json"
    f_in = open(sen_file, "rb")
    obj = json.load(f_in)
    f_in.close()

    doc_set = load_doc_set(chunk_dir)

    # save each annotations document as a pickle file
    for id in doc_set:
        doc = obj.get(id)
        if doc is None: doc = dict()
        annots = doc.get("annotations")
        if annots is None: annots = list()
        target_dir = chunk_dir + get_pmc_subdir(id) + "/"
        filename = target_dir + id +".ana.pickle"
        f_out = open(filename, "wb")
        pickle.dump(annots, f_out, protocol=3) 
        f_out.close()

    del obj
    log_it("INFO", "Saved ana.pickle files in", chunk_dir)

# ------------------------------------------------------------------
def get_rebuilt_annotated_publi_object(chunk_dir, pub_id):
# ------------------------------------------------------------------
    #log_it("INFO", "Rebuilding annotated publi", pub_id)

    root_filename = chunk_dir + get_pmc_subdir(pub_id) + "/" + pub_id   

    publi = dict()
    publi["_id"] =pub_id

    filename = root_filename + ".bib.pickle"
    f_in = open(filename, "rb")
    publi["document"] = pickle.load(f_in) 
    f_in.close()

    filename = root_filename + ".sen.pickle"
    f_in = open(filename, "rb")
    publi["sentences"] = pickle.load(f_in) 
    f_in.close()

    filename = root_filename + ".ana.pickle"
    f_in = open(filename, "rb")
    publi["annotations"] = pickle.load(f_in) 
    f_in.close()

    return publi


# ------------------------------------------------------------------
def save_annotated_publications(chunk_name, chunks_dir=chunks_dir, format="pickle"):
# ------------------------------------------------------------------
    log_it("INFO", "Saving annotated publications of", chunk_name)
    t0 = datetime.datetime.now()

    chunk_dir = get_chunk_dir(chunk_name, chunks_dir)
    doc_set = load_doc_set(chunk_dir)

    # save each annotated document as a json file
    for id in doc_set:
        publi = get_rebuilt_annotated_publi_object(chunk_dir, id)
        target_dir = chunk_dir + get_pmc_subdir(id) + "/"
        if format == "json":
            filename = target_dir + id +".json"
            f_out = open(filename, "w")
            json.dump(publi, f_out, indent=4)
            f_out.close()
        else:
            filename = target_dir + id +".pickle"
            f_out = open(filename, "wb")
            pickle.dump(publi, f_out, protocol=3)
            f_out.close()

    log_it("INFO", "Saved publication json files in sub directories of", chunk_dir, duration_since=t0)

# ------------------------------------------------------------------
def load_annotated_publications(chunk_name, chunks_dir=chunks_dir, format="pickle"):
# ------------------------------------------------------------------
    log_it("INFO", "Loading annotated publications of", chunk_name)
    t0 = datetime.datetime.now()

    chunk_dir = get_chunk_dir(chunk_name, chunks_dir)
    doc_set = load_doc_set(chunk_dir)

    # save each annotated document as a json file
    for id in doc_set:
        target_dir = chunk_dir + get_pmc_subdir(id) + "/"
        if format == "json":
            filename = target_dir + id +".json"
            f_in = open(filename, "r")
            publi = json.load(f_in)
            f_in.close()
        else:
            filename = target_dir + id +".pickle"
            f_in = open(filename, "rb")
            publi = pickle.load(f_in)
            f_in.close()

    log_it("INFO", "Loaded publication", format, "files in sub directories of", chunk_dir, duration_since=t0)


# ------------------------------------------------------------------
def prepare_chunk(chunk_name, chunks_dir=chunks_dir):
# ------------------------------------------------------------------
    fetch_chunk(chunk_name, chunks_dir)
    explode_bib(chunk_name, chunks_dir)
    explode_sen(chunk_name, chunks_dir)
    explode_ana(chunk_name, chunks_dir)
    save_annotated_publications(chunk_name, chunks_dir)


# ------------------------------------------------------------------
def publi_can_be_rdfized(publi, pmcid):
# ------------------------------------------------------------------
    id = publi.get("_id")
    if id == "":
        log_it("WARNING", "no _id for", pmcid, "skipping rdfization of this publication")
        return False

    doc = publi.get("document")
    typ = doc.get("article_type")
    if typ == "correction":
        log_it("WARNING", pmcid, "is a correction, skipping rdfization of this publication")
        return False

    return True


# ------------------------------------------------------------------
def save_rdf_files(chunk_name, chunks_dir=chunks_dir):
# ------------------------------------------------------------------
    chunk_dir = get_chunk_dir(chunk_name, chunks_dir)
    rdf_dir = chunk_dir + "rdf/"
    if not os.path.exists(rdf_dir): os.makedirs(rdf_dir)
    doc_set = load_doc_set(chunk_dir)

    pub_per_file = 500
    max_pub = 100000000
    pub_no = 0

    # create a ttl file for each pmcid subset
    pmcid_subsets = get_split_lists(list(doc_set), pub_per_file)
    for pmcid_subset in pmcid_subsets:
        offset = pub_no
        t0 = datetime.datetime.now()
        log_it("INFO", "Parsing pmcid set of", chunk_name, "offset", offset)
        ttl_file = rdf_dir + "chunk_" + chunk_name + "_publiset_" + str(offset) + ".ttl"
        log_it("INFO", "Serializing to", ttl_file)
        f_out = open(ttl_file, "w")
        for pfx_line in get_prefixes():
            f_out.write(pfx_line)
        for pmcid in pmcid_subset:
            pub_no += 1
            if pub_no > max_pub: break
            jsonfile = chunk_dir + get_pmc_subdir(pmcid) + "/" + pmcid + ".pickle"
            #log_it("DEBUG", "Reading publi", jsonfile, "file no.", pub_no)
            f_in = open(jsonfile, 'rb')
            publi = pickle.load(f_in)
            f_in.close()
            if publi_can_be_rdfized(publi, pmcid):
                for l in get_triples_for_publi(publi):
                    f_out.write(l)
                for l in get_triples_for_publi_annotations(publi):
                    f_out.write(l)
        
        f_out.close()
        log_it("INFO", "Serialized", ttl_file, duration_since=t0)


# ------------------------------------------------------------------
def process_chunk(chunk_name, chunks_dir=chunks_dir):
# ------------------------------------------------------------------
    prepare_chunk(chunk_name, chunks_dir)
    save_rdf_files(chunk_name, chunks_dir)


# ------------------------------------------------------------------
def get_pmc_subdir(pmcid):
# ------------------------------------------------------------------
    return pmcid[-2:]


# ------------------------------------------------------------------
def save_doc_set(chunk_dir, doc_set):
# ------------------------------------------------------------------
    filename = chunk_dir + "doc_set.pickle"
    f_out = open(filename, "wb")
    pickle.dump(doc_set, f_out, protocol=3) 
    f_out.close()
    #log_it("DEBUG", "Saved doc_set file", filename, "len(doc_set)", len(doc_set))


# ------------------------------------------------------------------
def load_doc_set(chunk_dir):
# ------------------------------------------------------------------
    filename = chunk_dir + "doc_set.pickle"
    f_in = open(filename, "rb")
    doc_set = pickle.load(f_in) 
    f_in.close()
    return doc_set

# ------------------------------------------------------------------
def get_chunk_dir(chunk_name, chunks_dir):
# ------------------------------------------------------------------
    if not chunks_dir.endswith("/"): chunks_dir += "/"
    return chunks_dir + chunk_name + "/"


# Structure returned by https://sibils.text-analytics.ch/api/v3.2/fetch?col=pmc&ids=PMC4909023
# {
#   sibils_version: "3.2.1",
#   success: true,
#   error: "",
#   warning: "",
#   collection: "pmc",
#   sibils_article_set: [
#     {
#       _id: "PMC4909023",
#       document: {},
#       sentences: [],
#       annotations: []
#     }
#   ]
# }




# ============================================================
if __name__ == '__main__':
# ============================================================

    tmp_dir = "./dir_test/fetch_by_ftp"
    
# ------------------------------------------------------------------
    if sys.argv[1] == "fetch_by_ftp": # for test
# ------------------------------------------------------------------
        fetch_by_ftp(ftp_dir_dict["bib"], "bib_pmc23n0023.json.gz", "./dir_test/fetch_by_ftp/pmc23n0023")

# ------------------------------------------------------------------
    elif sys.argv[1] == "fetch_chunk": # for test
# ------------------------------------------------------------------
        fetch_chunk("pmc23n0023", tmp_dir)

# ------------------------------------------------------------------
    elif sys.argv[1] == "explode_bib": # for test
# ------------------------------------------------------------------
        explode_bib("pmc23n0023", tmp_dir)

# ------------------------------------------------------------------
    elif sys.argv[1] == "explode_sen": # for test
# ------------------------------------------------------------------
        explode_sen("pmc23n0023", tmp_dir)

# ------------------------------------------------------------------
    elif sys.argv[1] == "explode_ana": # for test
# ------------------------------------------------------------------
        explode_ana("pmc23n0023", tmp_dir)

# ------------------------------------------------------------------
    elif sys.argv[1] == "rebuild_one_publi": # for test
# ------------------------------------------------------------------
        publi = get_rebuilt_annotated_publi_object("./dir_test/fetch_by_ftp/pmc23n0021/", "PMC2172800")
        fname ="./dir_test/fetch_by_ftp/pmc23n0021/00/PMC2172800.json"
        f_out = open(fname, "w")
        json.dump(publi, f_out, indent=4, sort_keys=True)
        f_out.close()

# ------------------------------------------------------------------
    elif sys.argv[1] == "save_publi": # for test
# ------------------------------------------------------------------
        save_annotated_publications("pmc23n0023", tmp_dir)

# ------------------------------------------------------------------
    elif sys.argv[1] == "load_publi": # for test
# ------------------------------------------------------------------
        load_annotated_publications("pmc23n0023", tmp_dir)

# ------------------------------------------------------------------
    elif sys.argv[1] == "prepare_chunk": # for test
# ------------------------------------------------------------------
        # delete chunk data
        os.system("rm -rf " + tmp_dir)
        # build it
        t0 = datetime.datetime.now()
        chunk_name = "pmc23n0022"
        prepare_chunk(chunk_name, tmp_dir)
        # load it
        load_annotated_publications(chunk_name, tmp_dir)
        log_it("DEBUG", "build and load time", duration_since=t0)

# ------------------------------------------------------------------
    elif sys.argv[1] == "save_rdf_files": # for test
# ------------------------------------------------------------------
        t0 = datetime.datetime.now()
        chunk_name = "pmc23n0022"
        save_rdf_files(chunk_name, tmp_dir)
        log_it("DEBUG", "build and load time", duration_since=t0)

# ------------------------------------------------------------------
    elif sys.argv[1] == "process_chunk": # for test
# ------------------------------------------------------------------
        t0 = datetime.datetime.now()
        chunk_name = "pmc23n0021"
        process_chunk(chunk_name, tmp_dir)
        log_it("DEBUG", "process chunk", chunk_name, chunks_dir, duration_since=t0)

