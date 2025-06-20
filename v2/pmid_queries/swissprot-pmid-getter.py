import gzip
import re
import subprocess
import sys

if len(sys.argv) < 2 : 
    print("Error, usage is : python rhea-pmid-getter.py <output_dir>")
    sys.exit(1)

outdir = sys.argv[1]
if not outdir.endswith("/") : outdir += "/"

filein = "uniprot_sprot.dat.gz"

print("downloading", filein, "file from ftp site...")

remotefile = "https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/complete/" + filein

subprocess.run(['wget', remotefile]) 

print("parsing", filein, "...")

pmid_set = set()
line_no = 0
with gzip.open(filein, 'rt', encoding='utf-8') as file:
    for line in file:
        line_no += 1
        line = line.strip()
        if line.startswith("RX   PubMed="):  # from RX lines we get pmid count: 269576
            pmid = line[12:].split(";")[0]
            pmid_set.add(pmid)
        elif "PubMed" in line:               # from RX lines + lines containing PubMed: we get pmid count: 269584
            pattern = r"PubMed:[0-9]+"
            for match in re.findall(pattern, line):            
                pmid = match[7:]
                pmid_set.add(pmid)
        if line_no % 1000000 == 0: print("line:", line_no, "pmid count:", len(pmid_set))
print("line:", line_no, "pmid count:", len(pmid_set))

fileout = outdir + "swissprot-pmid.txt"
print("saving pmids...")
f_out = open(fileout, "w")
for pmid in pmid_set:
    f_out.write("".join([pmid, "\n"]))
f_out.close
print("saved pmids in", fileout)
print("archiving", filein, "in", outdir)
print("end")
