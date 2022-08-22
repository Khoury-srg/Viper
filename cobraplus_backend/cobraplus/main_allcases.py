# we use this main function to handle all the cases, instead of create a main function for each case
from __future__ import print_function
import argparse
import copy
import os
import yaml

from cobraplus_backend.cobraplus.examples.algo import get_algo
from cobraplus_backend.cobraplus.utils.profiler import Profiler
from cobraplus_backend.cobraplus.utils.exceptions import RejectException

# example run: cd into cobraplus_backend dir and run
# python -m cobraplus.examples.wr_range_AdyaSI_main --sub-dir tidb_optimistic/tidb-leader-killing/20220224T053003.000Z -r --workload rra --table-count 3
from cobraplus_backend.cobraplus.utils.utils import ci, si


def add_from_edge_list(iter_g, edge_list):
    for e in edge_list:
        iter_g.add_edge(*e)


def pick_this_es(es, k, nid2score):
    for src, dst, type in es:
        if type in ["wr", "ww", 'cb']:
            if nid2score[ci(src)] + k < nid2score[si(dst)]:
                return True
        elif type == "rw":
            if nid2score[si(src)] + k < nid2score[ci(dst)]:
                return True
        else:
            assert False
    return False


def k_bounded_constraints(k, conn, iter_g, iter_conn, nid2score):
    num_add_edges = 0
    num_dec_conns = 0
    for es1, es2 in conn:  # edge set 1,
        ret1 = pick_this_es(es1, k, nid2score)
        ret2 = pick_this_es(es2, k, nid2score)
        if ret1 and ret2:
            return False
        elif ret1 and (not ret2):
            iter_conn.remove((es1, es2))
            add_from_edge_list(iter_g, es1)
            num_add_edges += len(es1)
            num_dec_conns += 1
        elif ret2 and (not ret1):
            iter_conn.remove((es1, es2))
            add_from_edge_list(iter_g, es2)

            num_add_edges += len(es2)
            num_dec_conns += 1
        else:
            continue

    print(f"Added {num_add_edges} edges while removed {num_dec_conns} constraints")
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_file", type=str, default="config.ini")
    parser.add_argument("--sub_dir", type=str)
    parser.add_argument("--perf_file", type=str, help="which file to store the perf results in for later figure plotting")
    parser.add_argument("--exp_name", type=str, help="only for easier figure plotting")
    parser.add_argument("--algo", type=int, default=-1)
    parser.add_argument("--strong-session", action="store_true")
    args = parser.parse_args()

    with open(args.config_file) as f:
        YAML_CONFIG = yaml.load(f, Loader=yaml.FullLoader)

    SUB_DIR = args.sub_dir
    ALGO = -1
    ALGO = YAML_CONFIG['ALGO'] if args.algo == -1 else args.algo
    graph_cls, checker_cls, graph_constructor = get_algo(ALGO)
    log_full_dir = os.path.join(YAML_CONFIG['JEPSEN_LOG_DIR'], SUB_DIR)  # the dir which stores the logs and exported table files
    check_result_file = os.path.join(log_full_dir,
                                     "check_result.txt")  # after finishing checking, write the checking result into this file

    print("New run=======================================")
    print(f"Begin verifying {SUB_DIR} using ALGO {ALGO}, strong session = {args.strong_session}")
    profiler = Profiler.instance()
    profiler.startTick("e2e")

    if ALGO in [3, 5]:
        g, conn = graph_constructor(YAML_CONFIG['JEPSEN_LOG_DIR'], YAML_CONFIG['GRAPH_DIR'],
                                    YAML_CONFIG['ANALYSIS_DIR'],
                                    SUB_DIR,
                                    args.strong_session,
                                    YAML_CONFIG['HASFINAL']) # set this hasFinal by different benchmarks
        # n, edges, edge_pairs, _ = g.get_4tuples()
        # print(f"# edges: {len(edges)}")

        # check acyclic
        checker = checker_cls(check_result_file)

        if not YAML_CONFIG['DEBUG']:
            print("Checking")
            result = checker.check(g, conn)
        else:
            print("Debugging")
            result = checker.debug(g.conn)
    elif ALGO in [0, 4]:
        # build a graph and output it to a file
        if YAML_CONFIG['REGENERATE']:
            G = graph_constructor(YAML_CONFIG['JEPSEN_LOG_DIR'], YAML_CONFIG['GRAPH_DIR'], YAML_CONFIG['ANALYSIS_DIR'],
                                  SUB_DIR,
                                  args.strong_session,
                                  YAML_CONFIG['HASFINAL'])

            # load the graph
            # n, edges, edge_pairs = graph_cls.load_from_file(
            #     "%s/%s/SI.graph" % (YAML_CONFIG['GRAPH_DIR'], SUB_DIR))
            # n, edges, edge_pairs = load_AgumentGraph_file()
            n, edges, edge_pairs, ext_writes = G.get_4tuples()
            if ALGO == 4: # if ALGO 4, we don't enforce a ww order in the checker
                ext_writes = None

            # check acyclic
            checker = checker_cls(check_result_file)

            if not YAML_CONFIG['DEBUG']:
                print("Checking")
                result = checker.check(n, edges, edge_pairs, ext_writes)
            else:
                print("Debugging")
                result = checker.debug(n, edges, edge_pairs)
    elif ALGO in [6, 8]:
        # check acyclic
        checker = checker_cls(check_result_file)

        try:
            g, conn = graph_constructor(YAML_CONFIG['JEPSEN_LOG_DIR'], YAML_CONFIG['GRAPH_DIR'],
                                    YAML_CONFIG['ANALYSIS_DIR'],
                                    SUB_DIR,
                                    args.strong_session, # if strong session, no requirement of heuristic of topo sorting??
                                    YAML_CONFIG['HASFINAL'])
            nid2score, _ = g.my_topo_sort()
            assert len(nid2score) == g.n_nodes * 2
            n_nodes_bc = g.n_nodes * 2
            k = n_nodes_bc * 0.1  # 10% * nodes in BCGraph

            result = False
            while not result and k < n_nodes_bc:
                print("Try#############")
                iter_g = copy.deepcopy(g)
                iter_conn = copy.deepcopy(conn)
                ret = k_bounded_constraints(k, conn, iter_g, iter_conn, nid2score)

                if not ret:
                    print("k is not large enough")
                    result = False
                else:
                    print(f"SAT Checker: k = {k}")
                    result = checker.check(iter_g, iter_conn)

                if k == n_nodes_bc - 1:
                    break
                else:
                    # k = k * 2 if k*2 < n_nodes_bc else n_nodes_bc - 1 # or other strategies?
                    k = k+n_nodes_bc * 0.1 if k+n_nodes_bc * 0.1 < n_nodes_bc else n_nodes_bc - 1  # or other strategies?
                    print(f"Set k={k}")
            print("#############\n")
        except RejectException as e:
            result = False       
        
    elif ALGO in [1, 2]: # 1, 2
        # build a graph and output it to a file
        if YAML_CONFIG['REGENERATE']:
            G = graph_constructor(YAML_CONFIG['JEPSEN_LOG_DIR'], YAML_CONFIG['GRAPH_DIR'], YAML_CONFIG['ANALYSIS_DIR'],
                                  SUB_DIR,
                                  args.strong_session,
                                  YAML_CONFIG['HASFINAL'])

            # load the graph
            n, edges, edge_pairs = graph_cls.load_from_file(
                "%s/%s/SI.graph" % (YAML_CONFIG['GRAPH_DIR'], SUB_DIR))
            # n, edges, edge_pairs = load_AgumentGraph_file()

            # check acyclic
            checker_cls = checker_cls(check_result_file)

            if not YAML_CONFIG['DEBUG']:
                print("Checking")
                result = checker_cls.check(n, edges, edge_pairs)
            else:
                print("Debugging")
                result = checker_cls.debug(n, edges, edge_pairs)

    print(f"{SUB_DIR}: {result}", flush=True)

    profiler.endTick("e2e")
    profiler.dumpPerf(args.exp_name, args.perf_file)
    print(f"End run {SUB_DIR} using ALGO {ALGO}, strong session = {args.strong_session}")
    print("=======================================")

