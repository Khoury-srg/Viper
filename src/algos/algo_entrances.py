import copy

from utils.exceptions import RejectException
from optimization import pair_heuristic, chain_heuristic

from utils.profiler import Profiler


def main_algo3_5(YAML_CONFIG, SUB_DIR, args, check_result_file, graph_cls, checker_cls, graph_constructor, format):
    try:
        g, conn = graph_constructor(YAML_CONFIG['LOG_DIR'], YAML_CONFIG['GRAPH_DIR'],
                                    YAML_CONFIG['ANALYSIS_DIR'],
                                    SUB_DIR,
                                    args.strong_session,
                                    YAML_CONFIG['HASFINAL'],
                                    format)  # set this hasFinal by different benchmarks

        # check acyclic
        checker = checker_cls(check_result_file)

        print("Checking")
        result = checker.check(g, conn)
    except RejectException as e:
        result = False

    return result


def main_algo_0_1_2_4(YAML_CONFIG, SUB_DIR, strong_session, check_result_file, graph_cls, checker_cls, graph_constructor, format, ALGO, ww_order, debug):
    # check acyclic
    checker = checker_cls(check_result_file)
    # build a graph and output it to a file
    try:
        G = graph_constructor(YAML_CONFIG['LOG_DIR'], YAML_CONFIG['GRAPH_DIR'], YAML_CONFIG['ANALYSIS_DIR'],
                              SUB_DIR,
                              strong_session,
                              YAML_CONFIG['HASFINAL'],
                              format)
        n, edges, edge_pairs, ext_writes = G.get_4tuples()
        if ALGO in [1, 2] and not ww_order:
            ext_writes = None
        # if ALGO == 4:  # if ALGO 4, we don't enforce a ww order in the checker
        #     ext_writes = None

        print("Checking")
        if debug:
            result = checker.debug(n, edges, edge_pairs, ext_writes)
        else:
            result = checker.check(n, edges, edge_pairs, ext_writes)
    except RejectException as e:
        result = False

    return result


def main_algo_6_8_12(YAML_CONFIG, SUB_DIR, args, check_result_file, graph_cls, checker_cls, graph_constructor, format):
    # check acyclic
    checker = checker_cls(check_result_file)
    profiler = Profiler.instance()

    try:
        # build a ArgumentedPolyGraph with empty constraints and get the constraints as an extra variable
        g, conn = graph_constructor(YAML_CONFIG['LOG_DIR'], YAML_CONFIG['GRAPH_DIR'],
                                    YAML_CONFIG['ANALYSIS_DIR'],
                                    SUB_DIR,
                                    args.strong_session,
                                    # if strong session, no requirement of heuristic of topo sorting??
                                    YAML_CONFIG['HASFINAL'],
                                    format)
        nid2rank, _ = g.my_topo_sort()
        assert len(nid2rank) == g.n_nodes * 2
        n_nodes_bc = g.n_nodes * 2
        k = n_nodes_bc * 0.1  # 10% * nodes in BCGraph
        ith_k = 1

        result = False
        while not result and k < n_nodes_bc:
            print("Trying k=%d" % k)
            profiler.startTick("k_%d=%d" % (ith_k, k))
            iter_g = copy.deepcopy(g)
            iter_conn = copy.deepcopy(conn)
            ret = chain_heuristic.k_bounded_constraints(k, conn, iter_g, iter_conn, nid2rank)

            if not ret:
                print("k is not large enough")
                result = False
            else:
                print(f"SAT Checker: k = {k}")
                result = checker.check(iter_g, iter_conn)

            profiler.endTick("k_%d=%d" % (ith_k, k))
            ith_k += 1
            if k == n_nodes_bc - 1:
                break
            else:
                # k = k * 2 if k*2 < n_nodes_bc else n_nodes_bc - 1 # or other strategies?
                k = k + n_nodes_bc * 0.1 if k + n_nodes_bc * 0.1 < n_nodes_bc else n_nodes_bc - 1  # or other strategies?
                print(f"Set k={k}")
        print("#############\n")
    except RejectException as e:
        result = False
        print(e)

    return result


def main_algo_0_1_2_heuristic(YAML_CONFIG, SUB_DIR, args, check_result_file,
                              graph_cls, checker_cls, graph_constructor, format, ALGO, ww_order):
    checker = checker_cls(check_result_file)
    profiler = Profiler.instance()

    try:
        # build a ArgumentedPolyGraph with empty constraints and get the constraints as an extra variable
        G = graph_constructor(YAML_CONFIG['LOG_DIR'], YAML_CONFIG['GRAPH_DIR'], YAML_CONFIG['ANALYSIS_DIR'],
                              SUB_DIR,
                              args.strong_session,
                              YAML_CONFIG['HASFINAL'],
                              format)
        # this G already contains constraints
        nid2rank, _ = G.my_topo_sort()
        assert len(nid2rank) == G.n_nodes * 2
        n_nodes_bc = G.n_nodes * 2
        k = n_nodes_bc * 0.1  # 10% * nodes in BCGraph
        ith_k = 1

        result = False
        while not result and k < n_nodes_bc:
            print("Trying k=%d" % k)
            profiler.startTick("k_%d=%d" % (ith_k, k))
            iter_G = copy.deepcopy(G)
            ret = pair_heuristic.k_bounded_constraints(k, G, iter_G, nid2rank)

            if not ret:
                print("k is not large enough")
                result = False
            else:
                print(f"SAT Checker: k = {k}")
                tmp_n, tmp_edges, tmp_cons, tmp_ext_writes = iter_G.get_4tuples()
                if not ww_order and ALGO in [10, 11]:
                    tmp_ext_writes = None
                result = checker.check(tmp_n, tmp_edges, tmp_cons, tmp_ext_writes)

            profiler.endTick("k_%d=%d" % (ith_k, k))
            ith_k += 1

            if k == n_nodes_bc - 1:
                break
            else:
                # k = k * 2 if k*2 < n_nodes_bc else n_nodes_bc - 1 # or other strategies?
                k = k + n_nodes_bc * 0.1 if k + n_nodes_bc * 0.1 < n_nodes_bc else n_nodes_bc - 1  # or other strategies?
                print(f"Set k={k}")
        print("#############\n")
    except RejectException as e:
        result = False

    return result




