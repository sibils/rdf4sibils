import datetime
import os
import gzip


# ------------------------------------------------------------------
def log_it(*things, duration_since=None):
# ------------------------------------------------------------------
    t1 = datetime.datetime.now()
    now = t1.isoformat().replace('T',' ')[:23]
    pid = "[" + str(os.getpid()) + "]"
    if duration_since is not None:
        duration = round((t1 - duration_since).total_seconds(),3)
        print(now, pid, *things, "duration", duration, flush=True)
    else:
        print(now, pid, *things, flush=True)

# ------------------------------------------------------------------
def gunzip(gz_file):
# ------------------------------------------------------------------
    log_it("INFO", "Uncompressing ", gz_file)
    f_in = gzip.open(gz_file, 'rb')
    decompressed_file = gz_file[0:-3]
    f_out = open(decompressed_file, 'wb')
    f_out.write(f_in.read())
    f_out. close()
    f_in. close()

# ------------------------------------------------------------------
def get_properties(filename):
# ------------------------------------------------------------------
    f_in = open(filename)
    props = dict()
    while True:
        line = f_in.readline()
        if line == "": break
        line = line.strip()
        nv = line.split("=")
        if len(nv)!=2: continue
        name = nv[0].strip()
        if name.startswith("#"): continue
        value = nv[1].strip()
        props[name]=value
    f_in.close()
    return props




