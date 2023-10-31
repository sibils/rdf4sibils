from fetcher import get_chunk_names_from_ftp, init_properties
from fetcher import chunk_rdf_dir_exists, rdf_dir, chunk_dir_exists
from fetcher import chunk_rdf_dir_status_is_loaded, chunk_rdf_dir_status_is_loading, chunk_rdf_dir_status_is_load_error 
from fetcher import set_chunk_rdf_dir_loaded_status, set_chunk_rdf_dir_loading_status, set_chunk_rdf_dir_load_error_status 
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
    if status == 0:
        if "load_chunk" in proc_and_args[0]: set_chunk_rdf_dir_loaded_status(proc_and_args[1], rdf_dir)
        log_it("INFO", "MASTER", "Completed", proc_and_args, "pid", process.pid, "status:", status, duration_since=t0)
    else:
        if "load_chunk" in proc_and_args[0]: set_chunk_rdf_dir_load_error_status(proc_and_args[1], rdf_dir)
        log_it("ERROR", "MASTER", "Completed with error", proc_and_args, "pid", process.pid, "status:", status, duration_since=t0)


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

    log_it("INFO", "MASTER", "num_processes   :", num_processes)
    log_it("INFO", "MASTER", "max_tasks       :", max_task)
    log_it("INFO", "MASTER", "task_name       :", task_name)
    log_it("INFO", "MASTER", "chunk list size :", len(chunks))

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

        # perform a checkpoint
        t0cp = datetime.now()
        log_it("INFO", "MASTER", "Performing a checkpoint")
        process = subprocess.Popen(["./checkpoint.sh"])
        status = process.wait()
        log_it("INFO", "MASTER", "Performed checkpoint", "status:", status, duration_since=t0cp)


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

    # nohup python3 multi_fetcher.py 2 32 load_chunk > load-32-chunks-p2.log 2>&1 &
    # 2023-10-07 17:15:43.698 [13191] INFO MASTER END duration 3249.467 - 1'735'376'234 triples

    # nohup python3 multi_fetcher.py 4 32 load_chunk > load-32-chunks-p4.log 2>&1 &
    # 2023-10-07 20:00:03.617 [13962] INFO MASTER END duration 1954.277 - 1'735'376'234 triples

    # nohup python3 multi_fetcher.py 8 32 load_chunk > load-32-chunks-p8.log 2>&1 &
    # 2023-10-08 12:11:43.141 [16218] INFO MASTER END duration 1245.354 - 1'735'376'234 triples



    # nohup python3 multi_fetcher.py 8 200 load_chunk > load-200-chunks-p8.log 2>&1 &
    # 2023-10-08 22:41:46.615 [17497] INFO MASTER END duration 12099.219 - ???



    # rdfizer  : python get_termino_rdf.py onto
    # rdfizer  : get_termino_rdf.py data
    # rdfizer  : nohup python3 multi_fetcher.py 8 200 process_chunk > process-200-chunks-p8.log 2>&1 &
    # 2023-10-11 16:12:38.533 [3186] INFO MASTER END duration 6672.545
    
    # endpoint : nohup python3 multi_fetcher.py 6 200 load_chunk > load-200-chunks-p6.log 2>&1 &
    # 2023-10-11 20:16:12.709 [5204] INFO MASTER END duration 14228.64 - 15'687'143'650 triples

    # ... sentence IRI broken !

    # rdfizer  : nohup python3 multi_fetcher.py 8 200 process_chunk > process-200-chunks-p8.log 2>&1 &
    # 2023-10-12 03:07:21.023 [6497] INFO MASTER END duration 7065.069

    # endpoint : ./load_onto_terms.sh => OK
    # endpoint : nohup python3 multi_fetcher.py 6 200 load_chunk > load-200-chunks-p6.log 2>&1 &
    # 2023-10-12 13:50:45.078 [9709] INFO MASTER END duration 15692.394


    # ... sentence was still IRI broken !

    # rdfizer  : nohup python3 multi_fetcher.py 8 200 process_chunk > process-200-chunks-p8.log 2>&1 &
    # 2023-10-13 13:56:25.497 [11166] INFO MASTER END duration 7596.963

    # endpoint : ./load_onto_terms.sh => OK
    # endpoint : nohup python3 multi_fetcher.py 8 200 load_chunk > load-200-chunks-p8.log 2>&1 &
    # 2023-10-13 17:47:03.317 [15549] INFO MASTER END duration 13703.871

    # ... with clean term IRIs

    # rdfizer  : python get_termino_rdf.py onto
    # rdfizer  : cd ontology; ./build-sibils-ontology.sh ; cd ..
    # rdfizer  : python get_termino_rdf.py data > get-termino-rdf-data.log 2>&1 &
    # rdfizer  : nohup python3 multi_fetcher.py 8 200 process_chunk > process-200-chunks-p8.log 2>&1 &
    # ...
    # endpoint : ./load_onto_terms.sh
    # endpoint : nohup python3 multi_fetcher.py 8 200 load_chunk > load-200-chunks-p8.log 2>&1 &

    # ... with shell wrapper and multiple checkpoints

    # nohup ./load_program.sh 6 30 7 > load-program-6-30-7.log 2>&1 &
    # started  Thu 19 Oct 18:38:17 CEST 2023
    # ended    Thu 19 Oct 23:32:38 CEST 2023
    # duration 4h54
    # HEAD	graph	tripleCount
    # ROWS	http://sibils.org/rdf	17'389'665'741
    # ROWS	http://sibils.org/rdf/concepts	196'197'351
    # ROWS	http://sibils.org/rdf/ontology	756

    # going on with more chunks...

    # rdfizer  : nohup python3 multi_fetcher.py 8 750 process_chunk > process-750-chunks-p8.log 2>&1 &
    # started  : Fri 20 Oct 15:33 CEST 2023
    # ended    : 2023-10-20 23:59:50.269
    # duration : env 8h
    # status   : not completed, no space left on device
    # chunks list        : 1027
    # chunks completed   : 692 (all status: 0)
    # chunks skipped     : 292
    # correction skipped : 44754
    # chunks dir         : 991
    # rdf dir            : 990

    # got more HD space
    # rdfizer  : nohup python3 multi_fetcher.py 6 60 process_chunk > process-60-chunks-p6.log 2>&1 &
    # started  : 2023-10-31 15:21:56.540
    # ended    : 2023-10-31 16:20:00.374 [63165] INFO MASTER END duration 3483.83
    # duration : < 1 hour
    # chunks list        : 1027
    # chunks completed   :   55
    # chunks skipped     :  972
    # chunks dir         : 1027
    # rdf dir            : 1027
    # status   : OK

    # we now have the full baseline of the pmc collection, let's try to load it
    # nohup ./load_program.sh 6 42 20 > load-program-6-42-20.log 2>&1 &
    # started  : 
    # ended    :
    # duration :
    # HEAD	graph	tripleCount
    # ...

# Only these were loaded for this chunk (deadlock in virtuoso ! see log):

# *** Error 40001: [Virtuoso Driver][Virtuoso Server]SR172: Transaction deadlocked
# at line 0 of Top-Level:
# ld_dir ('/share/rdf/ttl/pmc23n0221', '*.ttl', 'http://sibils.org/rdf') 
# /share/rdf/ttl/pmc23n0221/chunk_pmc23n0221_publiset_3500.ttl                      http://sibils.org/rdf                                                             2           2023.10.31 16:59.34 573098000  2023.10.31 17:16.58 59771000  0           NULL        NULL
# /share/rdf/ttl/pmc23n0221/chunk_pmc23n0221_publiset_4000.ttl                      http://sibils.org/rdf                                                             2           2023.10.31 16:59.36 573375000  2023.10.31 17:16.58 386626000  0           NULL        NULL
# /share/rdf/ttl/pmc23n0221/chunk_pmc23n0221_publiset_4500.ttl                      http://sibils.org/rdf                                                             2           2023.10.31 16:59.37 596780000  2023.10.31 17:17.15 612665000  0           NULL        NULL
# /share/rdf/ttl/pmc23n0221/chunk_pmc23n0221_publiset_500.ttl                       http://sibils.org/rdf                                                             2           2023.10.31 17:16.49 479971000  2023.10.31 17:17.32 5765000  0           NULL        NULL
# /share/rdf/ttl/pmc23n0223/chunk_pmc23n0223_publiset_0.ttl                         http://sibils.org/rdf                                                             2           2023.10.31 16:59.31 659266000  2023.10.31 17:16.54 792882000  0           NULL        NULL
