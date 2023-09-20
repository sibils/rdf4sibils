from fetcher import get_chunk_names_from_ftp, init_properties, chunk_rdf_dir_exists, rdf_dir
from utils import log_it
from datetime import datetime

import multiprocessing
import subprocess
import os
import sys


# ----------------------------------------------------
def run_proc(proc_and_args):
# ----------------------------------------------------

    t0 = datetime.now()
    log_it("INFO", "MASTER", "Must do", proc_and_args)
    process = subprocess.Popen(proc_and_args)
    log_it("INFO", "MASTER", "Starting", proc_and_args, "pid", process.pid)
    status = process.wait()
    log_it("INFO", "MASTER", "Completed", proc_and_args, "pid", process.pid, "status:", status, duration_since=t0)


# ====================================================
if __name__ == "__main__":
# ====================================================

    t0 = datetime.now()
    # init properties required for get_chunk_names_from_ftp and rdf_dir
    props = init_properties("rdfizer.properties")

    rdf_dir = props.get("rdf_dir")
    chunks = get_chunk_names_from_ftp()

    if len(sys.argv) != 3:
        print("\nERROR, usage is multi_fetcher.py <num_processes> <max_tasks>\n\n  Example: multi_fetcher.py 4 100\n")
        sys.exit()
    
    num_processes = int(sys.argv[1])
    max_task = int(sys.argv[2])

    log_it("INFO", "MASTER", "num_processes:", num_processes)
    log_it("INFO", "MASTER", "max_tasks:", max_task)
    log_it("INFO", "MASTER", "chunk list size:", len(chunks))

    tasks = list()
    task_num=0
    for chunk in chunks:
        if chunk_rdf_dir_exists(chunk, rdf_dir):
            log_it("INFO", "MASTER", "Skipping, rdf directory exists for chunk", chunk)
        else:
            task_num += 1
            if task_num > max_task: break
            tasks.append(["python", "fetcher.py", "process_chunk", chunk])

    pool = multiprocessing.Pool(num_processes)
    pool.map(run_proc, tasks)

    log_it("INFO", "MASTER", "END", duration_since=t0)
    

    # TODOs
    # - OK - num proc as command argument
    # - OK - clean most files in chunks except downloaded ones
    # - OK - skip tasks already done (chunk name processing based on rdf subdir existence)
    # STATS
    # python multi_fetcher.py 1 10 => 2023-09-19 13:27:44.569 [15264] INFO MASTER END duration 1668.287
    # python multi_fetcher.py 2 10 => 2023-09-19 14:04:19.118 [15460] INFO MASTER END duration 1005.464
    # python multi_fetcher.py 4 10 => 2023-09-19 14:15:45.146 [15622] INFO MASTER END duration 584.693
    # python multi_fetcher.py 8 10 => 2023-09-19 14:24:27.257 [15754] INFO MASTER END duration 368.748
    # python multi_fetcher.py 1 10 => 2023-09-19 14:53:20.553 [15881] INFO MASTER END duration 1681.925

    # with orjson instead of json
    # python multi_fetcher.py 4 10 =>  
    # python multi_fetcher.py 8 10 => 
