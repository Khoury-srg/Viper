# -*- coding: UTF-8 -*-

from functools import partial

from utils.exceptions import RejectException
from utils.profiler import Profiler
from utils.utils import load_logs_json, load_logs_edn
from parse.wr_range_parse import construct_all_txns_json, construct_all_txns_edn, \
    construct_single_txn4wrrange_edn, construct_single_txn4wrrange_json
from utils import utils
from utils.range_utils import ext_index, ext_writes_fn, ext_reads_fn, \
    get_all_range_queries, all_index, all_keys, all_upsert_fn, convert_rs2dict, subset, \
    k_writes_fn, Tk_set_fn, in_between, k_upserts_fn
from utils.graphs import ArgumentedPolyGraph
from utils import constants, range_utils


def process_final_state(G, ext_writes, Tf, rs_dict):
    num_edges = 0
    for k, v in rs_dict.items():
        write_txns = list(utils.get_in(ext_writes, k, v))
        assert len(write_txns) <= 1

        if len(write_txns) == 0:  # no txn write this v, it should be read nil
            # we don't do this assertion to allow preBench
            # assert is_null(v), f"value {k}:{v} can't find its write"
            G.add_edge(0, Tf, 'wr')  # add edges from T0 to all read_txns
            num_edges += 1
            # for those txns which also wrote key k:
            k_writes = Tk_set_fn(ext_writes, k, {0, Tf})
            assert len(k_writes) == 0, "No txn can happen after Tf"
            # G.add_edges([Tj], k_writes, 'rw')
        elif len(write_txns) == 1:
            G.add_edge(write_txns[0], Tf, 'wr')  # e.g. [3] -> [5,2,1]
            num_edges += 1

            Ti = write_txns[0]
            Tk_set = Tk_set_fn(ext_writes, k, {Ti, Tf})  # ?
            for Tk in Tk_set:
                G.add_edge(Tk, Ti, 'ww')
                num_edges += 1

    for i in range(G.n_nodes-1):
        G.add_edge(i, Tf, 'cb') # commits before
    print(f"Final State added {num_edges} edges")


def construct_graph_from_log(logs_folder:str, graphs_folder:str, analysis_folder:str,
                             sub_dir:str, strong_session:bool=False, hasFinal:bool=False, log_format="json"):
    """
    construct graph from log without supporting range query
    :param logs_folder:
    :param graphs_folder:
    :param sub_dir: like "wr/10-100-10", wr_cyclic_10
    :param consider_final_wr:
    :return: None
    :output: write 2 files: poly.graph and history.log.
    history.log is the transaction log of all the committed transactions(failed and info txns are filtered).
    It contains all the nodes of the polygraph.
    """
    is_null = partial(range_utils.is_null, constants.NULL_VALUE)
    LOG_SUB_DIR, LOG_FILE, \
    POLY_GRAPH_SUB_DIR, POLY_GRAPH_FILE, \
    ANALYSIS_SUB_DIR, ANALYSIS_FILE \
        = utils.compute_file_path(logs_folder, sub_dir, graphs_folder, analysis_folder, 'SI')

    if log_format == "json":
        construction_function_whole_history = construct_all_txns_json
        construction_function_single_txn = construct_single_txn4wrrange_json
        load_func = load_logs_json
    else:
        construction_function_whole_history = construct_all_txns_edn
        construction_function_single_txn = construct_single_txn4wrrange_edn
        load_func = load_logs_edn

    utils.mk_dirs(POLY_GRAPH_SUB_DIR, ANALYSIS_SUB_DIR)  # create corresponding dirs in case of not existing
    profiler = Profiler.instance()

    # read log, filter
    normal_logs = load_func(LOG_SUB_DIR)

    # parse, get the history and write it to file
    # no downgrade
    profiler.startTick("parsing")
    full_history, histories = construction_function_whole_history(normal_logs, construction_function_single_txn)

    # find the final txn Tf, swap it to the end of the array
    profiler.endTick("parsing")

    # an intermediate history representation which filters out all the failed txns
    profiler.startTick("IO")
    utils.output_history(ANALYSIS_FILE, full_history)
    profiler.endTick("IO")
    num_txn = len(full_history)  # may include Tf or not
    print("%d txns in total" % num_txn)

    profiler.startTick("constructing_graph")
    G = ArgumentedPolyGraph(num_txn)
    G.set_session_order(histories)

    # session order
    if strong_session:
        for tid in range(len(histories)):  # thread
            txns = histories[tid]
            for i in range(len(txns) - 1):
                G.add_edge(txns[i]['id'], txns[i + 1]['id'], 'cb')

    # wr dependency
    ext_writes = ext_index(full_history, ext_writes_fn)  # only consider successful writes
    ext_reads = ext_index(full_history, partial(ext_reads_fn))
    initial_state = utils.initial_state(full_history)
    # assert initial_state

    for i in range(1, num_txn):
        G.add_edge(0, i, 'cb')

    wr_num_edges, rw_num_edges = 0, 0
    for (k, values2reads) in ext_reads.items():
        # values2reads: a dict: a value => a set of txns
        for (v, read_txns) in values2reads.items():
            # current iter: k, v, txns which read v of k
            write_txns = list(utils.get_in(ext_writes, k, v))
            if len(write_txns) == 0:  # no txn write this v, it should be read nil
                # we don't do this assertion to allow preBench
                # assert is_null(v), f"value {k}:{v} can't find its write"
                if initial_state is None or (k in initial_state and initial_state[k] == v):
                    G.add_edges([0], read_txns, 'wr')  # add edges from T0 to all read_txns
                    wr_num_edges += len(read_txns)

                    # for those txns which also wrote key k:
                    k_writes = k_writes_fn(ext_writes, k)
                    for Tj in read_txns:
                        tmp = k_writes - {Tj}
                        G.add_edges([Tj], tmp, 'rw')
                        rw_num_edges += len(tmp)
                else:
                    if not is_null(v):
                        raise RejectException(f"dirty read {k}: {v}")
            elif len(write_txns) == 1:
                G.add_edges(write_txns, read_txns, 'wr')  # e.g. [3] -> [5,2,1]
                wr_num_edges += len(read_txns)

                for Tj in read_txns:
                    Ti = write_txns[0]
                    Tk_set = Tk_set_fn(ext_writes, k, {Ti, Tj})  # ?
                    for Tk in Tk_set:
                        G.add_edge_pair(Tk, Ti, 'ww', Tj, Tk, 'rw')
            else:
                assert False, "There shouldn't be two txns writing the same value for the same key!"
    print(f"WR added {wr_num_edges} WR edges, {rw_num_edges} RW edges")

    G.set_all_writes(ext_writes)
    for k in G.ext_key2writes:
        k_ext_writes = G.ext_key2writes[k]
        for i in range(0, len(k_ext_writes)):
            for j in range(i + 1, len(k_ext_writes)):
                G.add_edge_pair(k_ext_writes[i], k_ext_writes[j], 'ww', k_ext_writes[j], k_ext_writes[i], 'ww')

    # range query preparation
    # all_writes = all_index(full_history, all_writes_fn)  # include all writes, successful or not
    all_upserts = all_index(full_history, all_upsert_fn)  # include all insert_reads, successful or not
    K = all_keys(full_history)
    # first_ins, di_pairs, last_del = di_pairs_fn(history, all_writes)
    queries, _ = get_all_range_queries(full_history)

    # final write wr dependencies
    if hasFinal:
        Tf = num_txn - 1
        # ['range', None, None, ['id': key, 'val': val}] [] true]
        final_query = full_history[-1]['value'][0]
        query_result, dead_result = final_query[3:5]
        query_rs_dict = convert_rs2dict(query_result)
        dead_rs_dict = convert_rs2dict(dead_result)
        process_final_state(G, ext_writes, Tf, query_rs_dict)
        process_final_state(G, ext_writes, Tf, dead_rs_dict)

    wr_num_edges = 0
    # range query issue
    for query_txn_index, query_mop_index in queries:
        # [':range' k1 k2 [{'id': 8, 'val': 3}, {'id': 68, 'val': 1}] [{'id': 8, 'val': 3}, {'id': 68, 'val': 1}]]
        query = full_history[query_txn_index]['value'][query_mop_index]
        k1, k2, query_result, dead_result = query[1:5]

        # keys in query_result
        q_keyset = set(map(lambda m: m['id'], query_result))  # returned
        dead_keys = set(map(lambda m: m['id'], dead_result))  # filtered
        other_keys = subset(K, k1, k2) - q_keyset - dead_keys  # not return by db

        # all dead keys and returned keys should be between k1 and k2
        for k in q_keyset | dead_keys:
            assert in_between(k, k1, k2)

        for k in other_keys:  # this query must be before any upsert of k
            k_upserts_pos = k_upserts_fn(all_upserts, k)
            for ins_pos in k_upserts_pos:
                # if Tk's txn is the same with q's txn, then more find-grained comparason is needed
                if query_txn_index == ins_pos[0]:
                    if query_mop_index >= ins_pos[1]:
                        raise RejectException("")
                else:  # else, q -> first_insert
                    G.add_edge(query_txn_index, ins_pos[0], 'rw')  # use -1 to denote nil
                    wr_num_edges += 1

    print(f"Range Query added {wr_num_edges} edges")

    G.set_all_writes(ext_writes)
    profiler.endTick("constructing_graph")
    # write PolyGraph to file
    profiler.startTick("IO")
    G.output2file(POLY_GRAPH_FILE)
    profiler.endTick("IO")
    return G

