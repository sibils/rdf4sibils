from fetcher import get_chunk_names_from_ftp, init_properties
from fetcher import chunk_rdf_dir_exists, rdf_dir, chunk_dir_exists
from fetcher import chunk_rdf_dir_status_is_loaded, chunk_rdf_dir_status_is_loading
from fetcher import set_chunk_rdf_dir_loaded_status, set_chunk_rdf_dir_loading_status
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
    if "load_chunk" in proc_and_args[0]: set_chunk_rdf_dir_loading_status(proc_and_args[1], rdf_dir)
    process = subprocess.Popen(proc_and_args)
    log_it("INFO", "MASTER", "Starting", proc_and_args, "pid", process.pid)
    status = process.wait()
    if "load_chunk" in proc_and_args[0]: set_chunk_rdf_dir_loaded_status(proc_and_args[1], rdf_dir)
    log_it("INFO", "MASTER", "Completed", proc_and_args, "pid", process.pid, "status:", status, duration_since=t0)


# ====================================================
if __name__ == "__main__":
# ====================================================

    t0 = datetime.now()
    # init properties required for get_chunk_names_from_ftp and rdf_dir
    props = init_properties("rdfizer.properties")

    rdf_dir = props.get("rdf_dir")
    chunks_dir = props.get("chunks_dir")
    chunks = get_chunk_names_from_ftp()

    if len(sys.argv) != 4:
        print("\nERROR, usage is multi_fetcher.py <num_processes> <max_tasks> <task_name>\n\n  Example: multi_fetcher.py 4 100 do_this\n")
        sys.exit()
    
    num_processes = int(sys.argv[1])
    max_task = int(sys.argv[2])
    task_name = sys.argv[3]

    log_it("INFO", "MASTER", "num_processes:", num_processes)
    log_it("INFO", "MASTER", "max_tasks:", max_task)
    log_it("INFO", "MASTER", "task_name:", task_name)
    log_it("INFO", "MASTER", "chunk list size:", len(chunks))

    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    if task_name == "process_chunk":
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
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

    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    elif task_name == "load_chunk":
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
        tasks = list()
        task_num=0
        loaded_num=0
        loading_num=0
        for chunk in chunks:
            if chunk_rdf_dir_exists(chunk, rdf_dir):
                if not chunk_rdf_dir_status_is_loading(chunk, rdf_dir) and not chunk_rdf_dir_status_is_loaded(chunk, rdf_dir):
                    task_num += 1
                    if task_num > max_task: break
                    tasks.append(["./load_chunk.sh", chunk])
                elif chunk_rdf_dir_status_is_loaded(chunk, rdf_dir):
                    loaded_num += 1
                    log_it("INFO", "MASTER", "Skipping, rdf directory already loaded, chunk", chunk)
                elif chunk_rdf_dir_status_is_loading(chunk, rdf_dir):
                    loading_num += 1
                    log_it("ERROR", "MASTER", "Skipping, rdf directory has status LOADING, chunk", chunk)
            #else:
            #    log_it("WARNING", "MASTER", "Skipping, rdf directory does NOT exist, chunk", chunk)

        log_it("INFO", "MASTER", "load tasks todo           :", len(tasks))
        log_it("INFO", "MASTER", "load tasks already loaded :", loaded_num)
        log_it("INFO", "MASTER", "load tasks loading        :", loading_num, "(should be 0)")

        pool = multiprocessing.Pool(num_processes)
        pool.map(run_proc, tasks)



    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

    log_it("INFO", "MASTER", "END", duration_since=t0)
    

    # STATS task process_chunk
    # python multi_fetcher.py 1 10 => 2023-09-19 13:27:44.569 [15264] INFO MASTER END duration 1668.287
    # python multi_fetcher.py 2 10 => 2023-09-19 14:04:19.118 [15460] INFO MASTER END duration 1005.464
    # python multi_fetcher.py 4 10 => 2023-09-19 14:15:45.146 [15622] INFO MASTER END duration 584.693
    # python multi_fetcher.py 8 10 => 2023-09-19 14:24:27.257 [15754] INFO MASTER END duration 368.748
    # python multi_fetcher.py 1 10 => 2023-09-19 14:53:20.553 [15881] INFO MASTER END duration 1681.925

    # STATS task load_chunk
    # nohup python3 multi_fetcher.py 1 6 load_chunk > load-6-chunks-p1.log 2>&1 &
    # 2023-10-06 12:06:54.429 [8375] INFO MASTER END duration 1239.69

    # nohup python3 multi_fetcher.py 2 6 load_chunk > load-6-chunks-p2.log 2>&1 & 
    # 2023-10-06 19:20:53.378 [9660] INFO MASTER END duration 661.877

    # nohup python3 multi_fetcher.py 1 32 load_chunk > load-32-chunks-p1.log 2>&1 &
    # 2023-10-06 21:04:53.690 [9902] INFO MASTER END duration 5774.725 - 1'735'376'234 triples

