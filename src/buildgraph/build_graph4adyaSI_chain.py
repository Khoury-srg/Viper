# -*- coding: UTF-8 -*-
from functools import partial

from utils.exceptions import RejectException
from utils.profiler import Profiler
from utils.utils import load_logs_json, load_logs_edn
from parse.wr_range_parse import construct_all_txns_json, construct_all_txns_edn, \
    construct_single_txn4wrrange_edn, construct_single_txn4wrrange_json
from utils.range_utils import ext_index, ext_writes_fn, ext_reads_fn, \
    get_all_range_queries, all_index, all_keys, all_writes_fn, all_upsert_fn, convert_rs2dict, subset, \
    k_writes_fn, Tk_set_fn, in_between, k_upserts_fn
from utils.graphs import ArgumentedPolyGraph
from collections import defaultdict
from utils import utils, range_utils, constants


def process_final_state(G, ext_writes, Tf, rs_dict, readfrom, wwpairs):
    num_edges = 0
    for k, v in rs_dict.items():
        write_txns = list(utils.get_in(ext_writes, k, v))
        assert len(write_txns) <= 1

        if len(write_txns) == 0:  # no txn write this v, it should be read nil
            # we don't do this assertion to allow preBench
            # assert is_null(v), f"value {k}:{v} can't find its write"
            G.add_edge(0, Tf, 'wr')  # add edges from T0 to all read_txns
            readfrom[(k, 0)].add(Tf)
            num_edges += 1

            # for those txns which also wrote key k:
            k_writes = Tk_set_fn(ext_writes, k, {0, Tf})
            assert len(k_writes) == 0, "No txn can happen after Tf"
            # G.add_edges([Tj], k_writes, 'rw')
        elif len(write_txns) == 1:
            G.add_edge(write_txns[0], Tf, 'wr')  # e.g. [3] -> [5,2,1]
            readfrom[(k, write_txns[0])].add(Tf)
            num_edges += 1

            Ti = write_txns[0]
            Tk_set = Tk_set_fn(ext_writes, k, {Ti, Tf})  # ?
            for Tk in Tk_set:
                G.add_edge(Tk, Ti, 'ww')
                num_edges += 1
                # wwpairs[(k, Tk)] = Ti

    for i in range(G.n_nodes-1):
        G.add_edge(i, Tf, 'cb') # commits before
    # print(f"Final State added {num_edges} edges")


def construct_encoding(full_history, histories, strong_session, hasFinal):
    g, readfrom, wwpairs, ext_writes = create_knowngraph(full_history, histories, strong_session, hasFinal)
    constraints = gen_constraints(g, readfrom, wwpairs, ext_writes, full_history)
    return g, constraints


def create_knowngraph(full_history, histories, strong_session:bool=False, hasFinal = False):
    """
    without any constraints, only contains nodes and all deterministic edges.

    @return g
    @return readfrom: Dict[(key, write txn) => a txn set which contains all the txns which read from that write txn],
    @return wwpairs: <Key, Tx> => Tx
    @return ext_writes
    history: [{'id': 1, 'value': txn}]
    txn: [['r', 10, 'nil'], ['r', 7, 'nil']]
    """
    is_null = partial(range_utils.is_null, constants.NULL_VALUE)
    num_txns = len(full_history)
    # print(f"#Txns={num_txns}")
    g = ArgumentedPolyGraph(num_txns)

    g.set_session_order(histories)
    # session order
    if strong_session:
        for tid in range(len(histories)):  # thread
            txns = histories[tid]
            for i in range(len(txns) - 1):
                g.add_edge(txns[i]['id'], txns[i + 1]['id'], 'cb')

    readfrom = defaultdict(set) # Dict[(key, write txn) => a txn set which contains all the txns which read from that write txn],
    wwpairs = {}
    initial_state = utils.initial_state(full_history)

    # wr dependency
    ext_writes = ext_index(full_history, ext_writes_fn) # Dict[key, Dict[value, a set of txns]] # only consider successful writes
    ext_reads = ext_index(full_history, partial(ext_reads_fn))

    for i in range(1, num_txns):
        g.add_edge(0, i, 'cb')

    wr_num_edges, rw_num_edges = 0, 0
    for (k, values2reads) in ext_reads.items():
        # values2reads: a dict: a value => a set of txns
        for (v, read_txns) in values2reads.items():
            # current iter: k, v, txns which read v of k
            write_txns = list(utils.get_in(ext_writes, k, v))

            if len(write_txns) == 0:  # no txn write this v, it should be read nil
                # we don't assume v=='nil' to allow prebench, all writes in preBench can be considered by T0
                # assert is_null(v), f"value {k}: {v} can't find its write"
                if initial_state is None or (k in initial_state and initial_state[k] == v):
                    # initial_state is None: we don't have any information of initial state, assume reads from preBench
                    g.add_edges([0], read_txns, 'wr')  # add edges from T0 to all read_txns
                    wr_num_edges += len(read_txns)

                    for read_txn in read_txns:
                        readfrom[(k, 0)].add(read_txn)

                    # for those txns which also wrote key k:
                    k_writes = k_writes_fn(ext_writes, k)
                    for Tj in read_txns:
                        tmp = k_writes - {Tj}
                        g.add_edges([Tj], tmp, 'rw')
                        rw_num_edges += len(tmp)
                else:
                    if not is_null(v):
                        raise RejectException(f"dirty read {k}: {v}")
            elif len(write_txns) == 1:
                g.add_edges(write_txns, read_txns, 'wr')  # e.g. [3] -> [5,2,1]
                wr_num_edges += len(read_txns)

                for read_txn in read_txns:
                    readfrom[(k, write_txns[0])].add(read_txn)
            else:
                assert False, "There shouldn't be two txns writing the same value for the same key!"

    # print(f"WR added {wr_num_edges} WR edges, {rw_num_edges} RW edges")
    # all_writes = all_index(history, all_writes_fn)
    for k in ext_reads:
        k_writes = k_writes_fn(ext_writes, k)

        for v, read_txns in ext_reads[k].items():
            write_txns = list(utils.get_in(ext_writes, k, v))
            assert len(write_txns) <= 1, "Two transactions wrote the same value to a key"

            for read_txn in read_txns:
                if read_txn in k_writes: # if this read txn also writes this key
                    if len(write_txns) == 0:
                        assert (k, 0) not in wwpairs
                        # wwpairs[(k, 0)] = read_txn
                    elif len(write_txns) == 1:
                        # assert
                        if (k, write_txns[0]) in wwpairs:
                            raise RejectException("versions diverge")
                        wwpairs[(k, write_txns[0])] = read_txn

    if hasFinal:
        # final write wr dependencies
        Tf = num_txns - 1
        # ['range', None, None, ['id': key, 'val': val}] [] true]
        final_query = full_history[-1]['value'][0]
        query_result, dead_result = final_query[3:5]
        query_rs_dict = convert_rs2dict(query_result)
        dead_rs_dict = convert_rs2dict(dead_result)
        process_final_state(g, ext_writes, Tf, query_rs_dict, readfrom, wwpairs)
        process_final_state(g, ext_writes, Tf, dead_rs_dict, readfrom, wwpairs)

    wr_num_edges = 0
    # range query preparation
    all_writes = all_index(full_history, all_writes_fn)  # include all writes, successful or not
    # all_inserts_writes = all_index(history, all_insert_writes_fn) # include all inserts_writes, successful or not
    all_upserts = all_index(full_history,
                            all_upsert_fn)  # include all insert_reads, successful or not    K = all_keys(full_history)
    K = all_keys(full_history)
    queries, _ = get_all_range_queries(full_history)
    # range query constraints
    for txn_index, mop_index in queries:
        # [':range' k1 k2 [{'id': 8, 'val': 3}, {'id': 68, 'val': 1}] [{'id': 8, 'val': 3}, {'id': 68, 'val': 1}]]
        query = full_history[txn_index]['value'][mop_index]
        k1, k2, query_result, dead_result = query[1], query[2], query[3], query[4]
        query_rs_dict = convert_rs2dict(query_result)
        dead_rs_dict = convert_rs2dict(dead_result)

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
                if txn_index == ins_pos[0]:
                    if txn_index >= ins_pos[1]:
                        raise RejectException("")
                else:  # else, q -> first_insert
                    g.add_edge(txn_index, ins_pos[0], 'rw')  # use -1 to denote nil
                    wr_num_edges += 1

    # print(f"Range Query added {wr_num_edges} edges")
    return g, readfrom, wwpairs, ext_writes


def gen_constraints(g, readfrom, wwpairs, ext_writes, history):
    chains = defaultdict(set) # Dict[key, Set(Tuple)]

    for k in ext_writes:
        k_writes = k_writes_fn(ext_writes, k)
        for txn in k_writes:
            chains[k].add((txn,))
        # chains[k].add((0,))

    # K = all_keys(history)
    # for k in K:
    #     chains[k].add((0,)) # T0

    combine_writes(chains, wwpairs)
    infer_rw_edges(chains, readfrom, g)

    constraints = set()
    for k, chainset in chains.items():
        chain_list = list(chainset)
        n_chain = len(chainset)
        for i in range(n_chain-1):
            for j in range(i+1, n_chain):
                coalesced_cons_pair = coalesce(chain_list[i], chain_list[j], k, readfrom)
                constraints.add(coalesced_cons_pair)

    return constraints


def combine_writes(chains, wwpairs):
    """
    combine multiple single-txn chains into a longer chain
    """
    def find_chain_by_last_txn(chains, k, tx):
        for chain in chains[k]:
            if chain[-1] == tx:
                return chain

        # didn't find, then assert tx=0
        assert False, f"chains={chains}, k={k}, tx={tx}"
        # assert tx == 0, f"chains={chains}, k={k}, tx={tx}"

    def find_chain_by_first_txn(chains, k, tx):
        for chain in chains[k]:
            if chain[0] == tx:
                return chain
        assert False, f"chains={chains}, k={k}, tx={tx}"

    for (k, tx1), tx2 in wwpairs.items():
        chain1 = find_chain_by_last_txn(chains, k, tx1)
        chain2 = find_chain_by_first_txn(chains, k, tx2)
        # print(f"k={k}")
        if chain1 == chain2:
            raise RejectException("cyclic dependency")
        chains[k].remove(chain1)
        chains[k].remove(chain2)
        chains[k].add(chain1 + chain2)

    # return chains


def infer_rw_edges(chains, readfrom, g):
    num_edges = 0
    for k, chainset in chains.items():
        for chain in chainset:
            for i in range(0, len(chain)-1):
                for read_txn in readfrom[(k, chain[i])]:
                    if read_txn != chain[i+1]:
                        g.add_edge(read_txn, chain[i+1], 'rw')
                        num_edges += 1

    # print(f"Infer RW edges added {num_edges} edges")


def coalesce(chain1, chain2, key, readfrom):
    # if chain1
    ES1 = gen_chain2chain_edges(chain1, chain2, key, readfrom)
    ES2 = gen_chain2chain_edges(chain2, chain1, key, readfrom)
    # print(f"chain1={chain1}, chain2={chain2}: ES1={ES1}, ES2={ES2}")
    return ES1, ES2


def gen_chain2chain_edges(chain1, chain2, key, readfrom):
    edge_set = set()
    edge_set.add((chain1[-1], chain2[0], 'ww'))

    # if the last write in chain1 wasn't read by any transaction
    if (key, chain1[-1]) not in readfrom:
        return tuple(edge_set)

    # if the last write in chain1 was read by some transactions
    for read_txn in readfrom[(key, chain1[-1])]:
        edge_set.add((read_txn, chain2[0], 'rw'))
    return tuple(edge_set)


def construct_graph_from_log(logs_folder, graphs_folder, analysis_folder,
                             sub_dir, strong_session, hasFinal, log_format="edn"):
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
    log_sub_dir, log_file, \
    poly_graph_sub_dir, poly_graph_file, \
    analysis_sub_dir, analysis_file = \
        utils.create_dirs(logs_folder, graphs_folder, analysis_folder, sub_dir)
    profiler = Profiler.instance()

    # read logs, filter
    if log_format == "json":
        construction_function_whole_history = construct_all_txns_json
        construction_function_single_txn = construct_single_txn4wrrange_json
        load_func = load_logs_json
    else:
        construction_function_whole_history = construct_all_txns_edn
        construction_function_single_txn = construct_single_txn4wrrange_edn
        load_func = load_logs_edn
    print("Loading log file...")
    profiler.startTick("IO")
    normal_logs = load_func(log_sub_dir)

    profiler.endTick("IO")
    print("Loading Done")

    # normal_logs, final_txn_log = load_logs(log_sub_dir, hasFinal)
    # parse, get the history and write it to file
    profiler.startTick("parsing")
    full_history, histories = construction_function_whole_history(normal_logs, construction_function_single_txn)

    # history = construct_all_txns(lines, construct_single_txn4wrrange)
    # an intermediate history representation which filters out all the failed txns
    profiler.endTick("parsing")

    profiler.startTick("IO")
    utils.output_history(analysis_file, full_history)
    profiler.endTick("IO")

    profiler.startTick("constructing_graph")
    g, con = construct_encoding(full_history, histories, strong_session, hasFinal)
    profiler.endTick("constructing_graph")

    return g, con

