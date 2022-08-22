import argparse
import os.path
import sys

import yaml

from cobraplus_backend.cobraplus.buildgraph.build_graph4append import construct_graph_from_log
from cobraplus_backend.cobraplus.utils.graphs import ArgumentedPolyGraph
from cobraplus_backend.cobraplus.utils.profiler import Profiler
from cobraplus_backend.cobraplus.utils.utils import load_known_graph
from cobraplus_backend.cobraplus.checker.checkers import MonoBCPolyGraphChecker, MonoBCPolyGraphCheckerOptimized

# append workload without range query

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_file", type=str, default="config.ini")
    parser.add_argument("--sub_dir", type=str)
    parser.add_argument("--algo", type=int, default=-1)
    parser.add_argument("--perf_file", type=str, help="which file to store the perf results in for later figure plotting")
    parser.add_argument("--exp_name", type=str, help="only for easier figure plotting")
    args = parser.parse_args()

    with open(args.config_file) as f:
        YAML_CONFIG = yaml.load(f, Loader=yaml.FullLoader)
    SUB_DIR = args.sub_dir

    profiler = Profiler.instance()
    profiler.startTick("e2e")

    log_full_dir = os.path.join(YAML_CONFIG['JEPSEN_LOG_DIR'],
                                SUB_DIR)  # the dir which stores the logs and exported table files
    check_result_file = os.path.join(log_full_dir,
                                     "check_result.txt")  # after finishing checking, write the checking result into this file
    GRAPH_FILE = os.path.join(YAML_CONFIG['GRAPH_DIR'], SUB_DIR, "SI.graph")
    G, conn = construct_graph_from_log(YAML_CONFIG['JEPSEN_LOG_DIR'], YAML_CONFIG['GRAPH_DIR'], YAML_CONFIG['ANALYSIS_DIR'],
                                  SUB_DIR)
    # n, edges = load_known_graph(GRAPH_FILE)
    # n, edges, edge_pairs, _ = G.get_4tuples()

    # checker = Z3KnownGraphChecker()
    checker = MonoBCPolyGraphCheckerOptimized()
    # checker = Z3PolyGraphChecker()
    result = checker.check(G, conn)
    # result = checker.check(n, edges, edge_pairs)
    # result = checker.debug(n, edges, edge_pairs)
    print(f"{SUB_DIR}: {result}", flush=True)
    profiler.endTick("e2e")
    profiler.dumpPerf(args.exp_name, args.perf_file)


