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

    if len(sys.argv) != 5:
        print("\nERROR, usage is multi_fetcher.py <collection.subcoll> <num_processes> <max_tasks> <task_name>\n\n  Example: multi_fetcher.py pmc.baseline 4 100 do_this\n")
        sys.exit()

    t0 = datetime.now()
    # init properties required for get_chunk_names_from_ftp and rdf_dir
    context = sys.argv[1]
    props = init_properties("rdfizer" + context + "properties")

    rdf_dir = props.get("rdf_dir")
    chunks_dir = props.get("chunks_dir")
    chunks = get_chunk_names_from_ftp()
    
    num_processes = int(sys.argv[2])
    max_task = int(sys.argv[3])
    task_name = sys.argv[4]

    log_it("INFO", "MASTER", "context         :", context)
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
                tasks.append(["python", "fetcher.py", context, "process_chunk", chunk])

        pool = multiprocessing.Pool(num_processes)
        pool.map(run_proc, tasks)

    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

    # Obsolete or to be used in particular cases 
    # but requires some adaptation regarding context (collection.subcoll)
    # We rather use shell scripts only for load of chunks

    elif task_name == "load_chunk" and "think twice before running it" == "okay":
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

# TODO_OK : add missing ones in load list

# isql-vt 1111 dba $DBA_PW "EXEC=ld_dir ('/share/rdf/ttl/pmc23n0221', 'chunk_pmc23n0221_publiset_1000.ttl', 'http://sibils.org/rdf') ;"
# isql-vt 1111 dba $DBA_PW "EXEC=ld_dir ('/share/rdf/ttl/pmc23n0221', 'chunk_pmc23n0221_publiset_1500.ttl', 'http://sibils.org/rdf') ;"
# isql-vt 1111 dba $DBA_PW "EXEC=ld_dir ('/share/rdf/ttl/pmc23n0221', 'chunk_pmc23n0221_publiset_2000.ttl', 'http://sibils.org/rdf') ;"
# isql-vt 1111 dba $DBA_PW "EXEC=ld_dir ('/share/rdf/ttl/pmc23n0221', 'chunk_pmc23n0221_publiset_2500.ttl', 'http://sibils.org/rdf') ;"
# isql-vt 1111 dba $DBA_PW "EXEC=ld_dir ('/share/rdf/ttl/pmc23n0221', 'chunk_pmc23n0221_publiset_3000.ttl', 'http://sibils.org/rdf') ;"
# isql-vt 1111 dba $DBA_PW "EXEC=ld_dir ('/share/rdf/ttl/pmc23n0221', 'chunk_pmc23n0221_publiset_0.ttl', 'http://sibils.org/rdf') ;"

# done

# and other unloaded files before crash:

# /share/rdf/ttl/pmc23n0557/chunk_pmc23n0557_publiset_*.ttl                         http://sibils.org/rdf                                                             0           NULL                 NULL                 NULL        NULL        NULL
# /share/rdf/ttl/pmc23n0558/chunk_pmc23n0558_publiset_*.ttl                         http://sibils.org/rdf                                                             0           NULL                 NULL                 NULL        NULL        NULL
# /share/rdf/ttl/pmc23n0559/chunk_pmc23n0559_publiset_*.ttl                         http://sibils.org/rdf                                                             0           NULL                 NULL                 NULL        NULL        NULL
# /share/rdf/ttl/pmc23n0560/chunk_pmc23n0560_publiset_*.ttl                         http://sibils.org/rdf                                                             0           NULL                 NULL                 NULL        NULL        NULL
# /share/rdf/ttl/pmc23n0561/chunk_pmc23n0561_publiset_*.ttl                         http://sibils.org/rdf                                                             0           NULL                 NULL                 NULL        NULL        NULL
# /share/rdf/ttl/pmc23n0562/chunk_pmc23n0562_publiset_*.ttl                         http://sibils.org/rdf                                                             0           NULL                 NULL                 NULL        NULL        NULL
# /share/rdf/ttl/pmc23n0563/chunk_pmc23n0563_publiset_*.ttl                         http://sibils.org/rdf                                                             0           NULL                 NULL                 NULL        NULL        NULL
# /share/rdf/ttl/pmc23n0564/chunk_pmc23n0564_publiset_*.ttl                         http://sibils.org/rdf                                                             0           NULL                 NULL                 NULL        NULL        NULL
# /share/rdf/ttl/pmc23n0565/chunk_pmc23n0565_publiset_*.ttl                         http://sibils.org/rdf                                                             0           NULL                 NULL                 NULL        NULL        NULL
# /share/rdf/ttl/pmc23n0566/chunk_pmc23n0566_publiset_*.ttl                         http://sibils.org/rdf                                                             0           NULL                 NULL                 NULL        NULL        NULL
# /share/rdf/ttl/pmc23n0567/chunk_pmc23n0567_publiset_*.ttl                         http://sibils.org/rdf                                                             0           NULL                 NULL                 NULL        NULL        NULL
# /share/rdf/ttl/pmc23n0568/chunk_pmc23n0568_publiset_*.ttl                         http://sibils.org/rdf                                                             0           NULL                 NULL                 NULL        NULL        NULL
# /share/rdf/ttl/pmc23n0569/chunk_pmc23n0569_publiset_*.ttl                         http://sibils.org/rdf                                                             0           NULL                 NULL                 NULL        NULL        NULL
# /share/rdf/ttl/pmc23n0570/chunk_pmc23n0570_publiset_*.ttl                         http://sibils.org/rdf                                                             0           NULL                 NULL                 NULL        NULL        NULL
# /share/rdf/ttl/pmc23n0571/chunk_pmc23n0571_publiset_*.ttl                         http://sibils.org/rdf                                                             0           NULL                 NULL                 NULL        NULL        NULL
# /share/rdf/ttl/pmc23n0572/chunk_pmc23n0572_publiset_*.ttl                         http://sibils.org/rdf                                                             0           NULL                 NULL                 NULL        NULL        NULL
# /share/rdf/ttl/pmc23n0573/chunk_pmc23n0573_publiset_*.ttl                         http://sibils.org/rdf                                                             0           NULL                 NULL                 NULL        NULL        NULL
# /share/rdf/ttl/pmc23n0574/chunk_pmc23n0574_publiset_*.ttl                         http://sibils.org/rdf                                                             0           NULL                 NULL                 NULL        NULL        NULL
# /share/rdf/ttl/pmc23n0575/chunk_pmc23n0575_publiset_*.ttl                         http://sibils.org/rdf                                                             0           NULL                 NULL                 NULL        NULL        NULL
# /share/rdf/ttl/pmc23n0576/chunk_pmc23n0576_publiset_*.ttl                         http://sibils.org/rdf                                                             0           NULL                 NULL                 NULL        NULL        NULL
# /share/rdf/ttl/pmc23n0577/chunk_pmc23n0577_publiset_*.ttl                         http://sibils.org/rdf                                                             0           NULL                 NULL                 NULL        NULL        NULL
# /share/rdf/ttl/pmc23n0578/chunk_pmc23n0578_publiset_*.ttl                         http://sibils.org/rdf                                                             0           NULL                 NULL                 NULL        NULL        NULL
# /share/rdf/ttl/pmc23n0579/chunk_pmc23n0579_publiset_*.ttl                         http://sibils.org/rdf                                                             0           NULL                 NULL                 NULL        NULL        NULL
# /share/rdf/ttl/pmc23n0581/chunk_pmc23n0581_publiset_*.ttl                         http://sibils.org/rdf                                                             0           NULL                 NULL                 NULL        NULL        NULL


# cat > load_some.sh

# export DBA_PW=Gx3DWCyHsj3bVY3MU2nR

# ./load_chunk.sh pmc23n0557 &
# sleep 1
# ./load_chunk.sh pmc23n0558 &
# wait
# isql-vt 1111 dba $DBA_PW "EXEC=checkpoint;"

# ./load_chunk.sh pmc23n0559
# sleep 1
# ./load_chunk.sh pmc23n0561
# wait
# isql-vt 1111 dba $DBA_PW "EXEC=checkpoint;"

# ./load_chunk.sh pmc23n0562
# sleep 1
# ./load_chunk.sh pmc23n0563
# wait
# isql-vt 1111 dba $DBA_PW "EXEC=checkpoint;"

# ./load_chunk.sh pmc23n0564
# sleep 1
# ./load_chunk.sh pmc23n0565
# wait
# isql-vt 1111 dba $DBA_PW "EXEC=checkpoint;"

# ./load_chunk.sh pmc23n0566
# sleep 1
# ./load_chunk.sh pmc23n0567
# wait
# isql-vt 1111 dba $DBA_PW "EXEC=checkpoint;"

# ./load_chunk.sh pmc23n0568
# sleep 1
# ./load_chunk.sh pmc23n0569
# wait
# isql-vt 1111 dba $DBA_PW "EXEC=checkpoint;"

# ./load_chunk.sh pmc23n0570
# sleep 1
# ./load_chunk.sh pmc23n0571
# wait
# isql-vt 1111 dba $DBA_PW "EXEC=checkpoint;"

# ./load_chunk.sh pmc23n0572
# sleep 1
# ./load_chunk.sh pmc23n0573
# wait
# isql-vt 1111 dba $DBA_PW "EXEC=checkpoint;"

# ./load_chunk.sh pmc23n0575
# sleep 1
# ./load_chunk.sh pmc23n0577

# wait
# isql-vt 1111 dba $DBA_PW "EXEC=checkpoint;"

# => OK

# reset ll_state to 0 for 5 files and load them again:

# ll_file                                                                           ll_state    ll_started           ll_done
# VARCHAR NOT NULL                                                                  INTEGER     TIMESTAMP            TIMESTAMP
# _______________________________________________________________________________

# /share/rdf/ttl/pmc23n0221/chunk_pmc23n0221_publiset_0.ttl                         1           2023.11.1 15:43.15 116133000  NULL
# /share/rdf/ttl/pmc23n0221/chunk_pmc23n0221_publiset_1000.ttl                      1           2023.11.1 15:43.16 140777000  NULL
# /share/rdf/ttl/pmc23n0221/chunk_pmc23n0221_publiset_1500.ttl                      1           2023.11.1 15:43.17 147724000  NULL
# /share/rdf/ttl/pmc23n0221/chunk_pmc23n0221_publiset_2500.ttl                      1           2023.11.1 15:43.18 147367000  NULL
# /share/rdf/ttl/pmc23n0221/chunk_pmc23n0221_publiset_3000.ttl                      1           2023.11.1 15:43.19 154189000  NULL


# OK - nohup isql-vt 1111 dba Gx3DWCyHsj3bVY3MU2nR "EXEC=update DB.DBA.load_list set ll_state=0 where ll_state=1;"
# OK - nohup isql-vt 1111 dba Gx3DWCyHsj3bVY3MU2nR "EXEC=rdf_loader_run();"
# OK - nohup isql-vt 1111 dba Gx3DWCyHsj3bVY3MU2nR "EXEC=rdf_loader_run();"
# OK - nohup isql-vt 1111 dba Gx3DWCyHsj3bVY3MU2nR "EXEC=rdf_loader_run();"

# OK - nohup isql-vt 1111 dba Gx3DWCyHsj3bVY3MU2nR "EXEC=checkpoint;" &

# => OK: load files in load list
# => OK: set correct status: LOADED
# => OK: rm corresponding ttl (keep only lz4 files)
# => OK: reset properly load status of files remaining to be loaded

# refactoring of loading system: load_chunk.sh

# concept: le load d'un chunk est une tâche qui effectue toutes les opérations dont 
# le load qui est effectué par N processes isql-vt, le checkpoint est optionnel
# les fichiers LOADING, LOADED, LOAD_ERROR sont écrit par le script

# Quelques loads faits selon cette nouvelle méthode:
# 1) Il y a un temps mort (env. 5 minutes entre le moment où le load est terminé et où le chckpoint commence.
# Le checkpoint est initié juste après le load slon mon log, mais 5 minutes après selon le log de virtuoso.
# 2) Le premier load_chunk.sh apres un restart virtuoso est souvent très lent (30 minutes)
# 3) chunks loadés selon cette méthode: pmc23n0979 -> pmc23n0983

# ONGOING 4) chunks en cours de load selon cette méthode via load_some.sh: pmc23n0984 -> pmc23n0987 

# Ideas for improvements:
# - use gz rather lz4 and let virtuoso decompress on the fly => less IO READs
# - write more concise ttl files: smaller uuid strings for blank nodes, use more , and ; 
# - go back to declare multiple chunks to virtuoso before starting N rdf_load() processes
# - use a python wrapper to communicate with isql ?


# superpam@sibils-sparql:~/work/rdf4sibils/ttl/pmc23n0001$ time lz4 -d -m *.lz4
# real	0m26.308s
# user	0m4.669s
# sys	0m7.523s


# superpam@sibils-sparql:~/work/rdf4sibils/ttl/pmc23n0001$ time gzip *.ttl
# real	2m8.732s
# user	2m3.538s
# sys	0m4.400s

# superpam@sibils-sparql:~/work/rdf4sibils/ttl/pmc23n0001$ time gunzip *.ttl.gz
# real	0m47.925s
# user	0m25.690s
# sys	0m3.623s


# superpam@sibils-sparql:~/work/rdf4sibils/ttl/pmc23n0001$ time gzip --fast *.ttl
# real	0m54.888s
# user	0m49.084s
# sys	0m4.002s

# superpam@sibils-sparql:~/work/rdf4sibils/ttl/pmc23n0001$ time gunzip --fast *.ttl.gz
# real	0m42.435s
# user	0m26.264s
# sys	0m4.736s


# superpam@sibils-sparql:~/work/rdf4sibils/ttl/pmc23n0001$ time lz4 -d -m *.lz4
# real	0m24.556s
# user	0m4.746s
# sys	0m7.759s

# superpam@sibils-sparql:~/work/rdf4sibils/ttl/pmc23n0001$ time lz4 -m *.ttl
# real	0m16.012s
# user	0m8.266s
# sys	0m4.232s

#             lz4     gz (fast)
# compress    16      54
# decompress  25      42


# let's try to generate gz (fast) files for N chunks, then declare the gz files 
# to virtuoso, then load them with 5 processes, then checkout

# superpam@sibils-sparql:~/work/rdf4sibils$ ./load_experimental.sh ttl/pmc23n091*
# Mon  6 Nov 14:43:55 CET 2023 - decompressing lz4 files in ttl/pmc23n0910
# Mon  6 Nov 14:44:34 CET 2023 - gzipping ttl files in ttl/pmc23n0910
# Mon  6 Nov 14:45:41 CET 2023 - decompressing lz4 files in ttl/pmc23n0911
# Mon  6 Nov 14:46:17 CET 2023 - gzipping ttl files in ttl/pmc23n0911
# Mon  6 Nov 14:47:24 CET 2023 - decompressing lz4 files in ttl/pmc23n0912
# Mon  6 Nov 14:47:53 CET 2023 - gzipping ttl files in ttl/pmc23n0912
# Mon  6 Nov 14:49:01 CET 2023 - decompressing lz4 files in ttl/pmc23n0913
# Mon  6 Nov 14:49:35 CET 2023 - gzipping ttl files in ttl/pmc23n0913
# Mon  6 Nov 14:50:47 CET 2023 - decompressing lz4 files in ttl/pmc23n0914
# Mon  6 Nov 14:51:16 CET 2023 - gzipping ttl files in ttl/pmc23n0914
# Mon  6 Nov 14:52:25 CET 2023 - decompressing lz4 files in ttl/pmc23n0915
# Mon  6 Nov 14:52:59 CET 2023 - gzipping ttl files in ttl/pmc23n0915
# Mon  6 Nov 14:54:09 CET 2023 - decompressing lz4 files in ttl/pmc23n0916
# Mon  6 Nov 14:54:40 CET 2023 - gzipping ttl files in ttl/pmc23n0916
# Mon  6 Nov 14:55:51 CET 2023 - decompressing lz4 files in ttl/pmc23n0917
# Mon  6 Nov 14:56:27 CET 2023 - gzipping ttl files in ttl/pmc23n0917
# client_loop: send disconnect: Broken pipe

# => 7 CHUNKS decompressed / recompressed in 12 minutes => 1.7m ou 102 sec / chunk

# ./compress_lz4_to_gz.sh ttl/pmc23n091*
# ./declare_gz_files.sh ttl/pmc23n091*
# nohup ./load_gz_files.sh 5 > load-gz-files-5.log 2>&1 &
# => OK 

# nohup ./cdl.sh 5 ttl/pmc23n092* > load-gz-files-pmc23n092-star-5.log 2>&1 &
# => OK, environ 1h

# nohup ./doit.sh 6 > doit-pmc23n09-3-4-5-6-7-8-9-0-star-6.log 2>&1 &
# started      : Mon  6 Nov 23:17:31 CET 2023
# ended        : Tue  7 Nov 10:20:03 CET 2023 - INFO doit done
# duration     : env. 11 hours fpr 80 chunks => 8min 15sec / chunk (incl. compress / decompress and checkout) 
# virtuoso log : no error
# isql-vt      : all have ll_state=2 and ll_error is null

# => OK

# chunks remaining to load: n06* n07* n08* n10*

# ./compress_lz4_to_gz.sh ttl/pmc23n06* &
# ./compress_lz4_to_gz.sh ttl/pmc23n07* &
# ./compress_lz4_to_gz.sh ttl/pmc23n08* &
# ./compress_lz4_to_gz.sh ttl/pmc23n10* &
# TODO => OK

# max_proc=6
# ./declare_load_gz_files.sh $max_proc ttl/pmc23n06*
# ./declare_load_gz_files.sh $max_proc ttl/pmc23n07*
# ./declare_load_gz_files.sh $max_proc ttl/pmc23n08*
# ./declare_load_gz_files.sh $max_proc ttl/pmc23n10*

# in 

# nohup ./action.sh > dlgz-06-07-08-20.log > 2>&1 &
# TODO => OK
# started  : Wed  8 Nov 08:54:22 CET 2023 - INFO max_proc: 6
# ended    : Thu  9 Nov 13:59:26 CET 2023 - INFO ./action.sh done
# duration : env. 29 hours for 400 chunks and 4 checkpoints = 4min 21sec / chunk (with 6 processes)


# load these missing in pmc23n05* chunks, see more_action.sh (recompress to gz, declare, load, single checkpoint)

# nohup ./more_action.sh > gz-decl-load-058-059.log 2>&1 &
# TODO => OK
# started  : Thu  9 Nov 19:11:25 CET 2023
# ended    : Fri 10 Nov 10:46:53 CET 2023 - INFO ./more_action.sh done
# duration : env. 15.5 hours for 19 chunks and 1 checkout = 49min / chunk (with 6 processes)

# note: these chunks have probably been loaded twice by error
    #   2 pmc23n0978
    #   2 pmc23n0979
    #   2 pmc23n0980
    #   2 pmc23n0981
    #   2 pmc23n0982
    #   2 pmc23n0983
    #   2 pmc23n0984
    #   2 pmc23n0985
    #   2 pmc23n0986
    #   2 pmc23n0987


# status after loading full 2023 PMC baseline

# [pmichel@lin-202 rdf4sibils]$ python sparql_client.py query sparql/graph-stats.rq 
# HEAD	graph	tripleCount

# ROWS	http://sibils.org/rdf	91'509'722'989
# ROWS	http://sibils.org/rdf/concepts	196'197'351
# ROWS	http://sibils.org/rdf/ontology	756

# META	query_file	 sparql/graph-stats.rq
# META	query_template	 None
# META	success	 True
# META	duration[s]	 403.11
# META	count	 8
# END


# [pmichel@lin-202 rdf4sibils]$ python sparql_client.py query sparql/publi-stats.rq 
# HEAD	publi_class	publi_count
# ROWS	:BriefReport	102973
# ROWS	:CaseReport	238615
# ROWS	:MeetingReport	12790
# ROWS	:Publication	440632
# ROWS	:ReviewArticle	436618
# ROWS	:Editorial	90072
# ROWS	:Letter	95545
# ROWS	:JournalArticle	3651216  
# META	query_file	 sparql/publi-stats.rq
# META	query_template	 None
# META	success	 True
# META	duration[s]	 0.505
# META	count	 8
# END



