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

