# -*- coding: UTF-8 -*-
from collections import defaultdict
from functools import partial

from utils.exceptions import RejectException
from utils import utils
from utils.graphs import ArgumentedPolyGraph
from utils.profiler import Profiler
from parse.append_parse import parse
from utils.range_utils import ext_reads_fn, ext_index


def k_writes_fn(ext_writes, key):
    """

    :param ext_writes:
    :param key:
    :return: a set of txn_ids which have ever written this key
    """
    w_set = set()
    if key not in ext_writes:
        return w_set

    values2writes = ext_writes[key]
    for (v, writes) in values2writes.items():
        w_set = w_set | writes

    return w_set


def Tk_set_fn(ext_writes, key, exclude):
    w_set = k_writes_fn(ext_writes, key)
    Tk_set = w_set - exclude
    return Tk_set


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
        chains[k].remove(chain1)
        chains[k].remove(chain2)
        chains[k].add(chain1 + chain2)

    # return chains


def coalesce(chain1, chain2, key, readfrom):
    # if chain1
    ES1 = gen_chain2chain_edges(chain1, chain2, key, readfrom)
    ES2 = gen_chain2chain_edges(chain2, chain1, key, readfrom)
    # print(f"chain1={chain1}, chain2={chain2}: ES1={ES1}, ES2={ES2}")
    return ES1, ES2


def gen_chain2chain_edges(chain1, chain2, key, readfrom):
    edge_set = set()
    edge_set.add((chain1[-1], chain2[0], 'ww'))

    if (key, chain1[-1]) not in readfrom:
        return tuple(edge_set)

    for read_txn in readfrom[(key, chain1[-1])]:
        edge_set.add((read_txn, chain2[0], 'rw'))
    return tuple(edge_set)


def construct_encoding(full_history, histories, strong_session):
    g, readfrom, wwpairs, ext_writes = create_knowngraph(full_history, histories, strong_session)
    constraints = gen_constraints(g, readfrom, wwpairs, ext_writes, full_history)
    return g, constraints


def ext_writes_fn(full_history):
    all_writes = {}
    for i, txn in enumerate(full_history):
        if full_history[i]['id'] == 0:
            continue

        for mop in txn['value']:
            f, k, v = mop
            if f == 'append':
                if k not in all_writes:
                    all_writes[k] = {v: {i}}
                elif v not in all_writes[k]:
                    all_writes[k][v] = {i}
                else:
                    all_writes[k][v].add(i)

    return all_writes


def add_wwpairs(wwpairs, k, txn1, txn2):
    wwpairs[(k, txn1)] = txn2


def create_knowngraph(full_history, histories, strong_session:bool=False):
    """
    without any constraints, only contains nodes and all deterministic edges.

    @return g
    @return readfrom: Dict[(key, write txn) => a txn set which contains all the txns which read from that write txn],
    @return wwpairs: <Key, Tx> => Tx
    @return ext_writes
    history: [{'id': 1, 'value': txn}]
    txn: [['r', 10, 'nil'], ['r', 7, 'nil']]
    """
    profiler = Profiler.instance()
    num_txns = len(full_history)
    print(f"#Txns={num_txns}")
    G = ArgumentedPolyGraph(num_txns)

    # session order?
    G.set_session_order(histories)
    # session order
    if strong_session:
        for tid in range(len(histories)):  # thread
            txns = histories[tid]
            for i in range(len(txns) - 1):
                G.add_edge(txns[i]['id'], txns[i + 1]['id'], 'cb')

    readfrom = defaultdict(set) # Dict[(key, write txn) => a txn set which contains all the txns which read from that write txn],
    wwpairs = {}

    # wr dependency
    ext_writes = ext_writes_fn(full_history)
    # ext_writes = ext_index(full_history, ext_writes_fn) # Dict[key, Dict[value, a set of txns]] # only consider successful writes
    ext_reads = ext_index(full_history, partial(ext_reads_fn))

    for i in range(1, num_txns):
        G.add_edge(0, i, 'cb')

    for (k, values2reads) in ext_reads.items():
        k_writes = k_writes_fn(ext_writes, k)
        # values2reads: a dict: a value => a set of txns
        for (v, read_txns) in values2reads.items():
            # current iter: k, v, txns which read v of k
            if v == 'nil':
                write_txns = list(utils.get_in(ext_writes, k, v))
                assert len(write_txns) == 0

                G.add_edges([0], read_txns, 'wr')  # T0 -> all read txns readtxn
                # for any Tk which writes op[1], readtxn -> Tk

                for read_txn in read_txns:
                    tmp = k_writes - {read_txn}
                    G.add_edges([read_txn], tmp, 'rw')
                    readfrom[(k, 0)].add(read_txn)

                assert (k, 0) not in wwpairs
            else:
                write_txns = list(utils.get_in(ext_writes, k, v[-1]))
                if len(write_txns) != 1: # reject
                    raise RejectException("can't find the corresponding write")
                    # profiler.dumpPerf()
                    # exit(0)
                assert len(write_txns) == 1
                Tj = write_txns[0]

                G.add_edges([Tj], read_txns, 'wr')  # e.g. [3] -> [5,2,1]

                for read_txn in read_txns:
                    readfrom[(k, write_txns[0])].add(read_txn)

                    if read_txn in k_writes:
                        if (k, write_txns[0]) in wwpairs:
                            if wwpairs[(k, write_txns[0])] != read_txn:
                                raise RejectException("versions diverge")
                                # print("versions diverge")
                                # profiler.dumpPerf()
                                # exit(0)

                        add_wwpairs(wwpairs, k, write_txns[0], read_txn)
                        # wwpairs[(k, write_txns[0])] = read_txn

                for i in range(len(v) - 1):
                    txn_is = list(utils.get_in(ext_writes, k, v[i]))
                    txn_js = list(utils.get_in(ext_writes, k, v[i + 1]))
                    assert len(txn_is) == 1 and len(txn_js) == 1

                    if txn_js[0] != txn_is[0]:
                        if (k, txn_is[0]) in wwpairs:
                            if wwpairs[(k, txn_is[0])] != txn_js[0]:
                                raise RejectException("versions diverge")
                                # profiler.dumpPerf()
                                # exit(0)
                        add_wwpairs(wwpairs, k, txn_is[0], txn_js[0])
                        # wwpairs[(k, txn_is[0])] = txn_js[0]

                for Ti in read_txns:
                    tmp = k_writes - {Ti, Tj}
                    for Tk in tmp:
                        txn_k = full_history[Tk]
                        for op_tk in txn_k['value']:
                            if op_tk[0] == 'append' and op_tk[1] == k:
                                # compare the read result of Ti and the write of op_tk
                                if op_tk[2] in v:
                                    pass
                                    # G.add_edge(Tk, Tj, 'wr')  # not necessary
                                else:
                                    G.add_edge(Ti, Tk, 'rw')

    return G, readfrom, wwpairs, ext_writes


def construct_graph_from_log(logs_folder, graphs_folder, analysis_folder,
                              sub_dir, strong_session=False, hasFinal=False, log_format="edn"):
    assert log_format == "edn", "append workload only allows edn format currently"
    LOG_SUB_DIR, LOG_FILE, \
    POLY_GRAPH_SUB_DIR, POLY_GRAPH_FILE, \
    ANALYSIS_SUB_DIR, ANALYSIS_FILE \
        = utils.create_dirs(logs_folder, graphs_folder, analysis_folder, sub_dir)

    profiler = Profiler.instance()
    profiler.startTick("parsing")

    with open(LOG_FILE) as f:
        lines = f.readlines()
    lines = list(filter(lambda line: ":ok" in line, lines))
    full_history, histories = parse(lines)
    num_txn = len(full_history)
    profiler.endTick("parsing")

    profiler.startTick("IO")
    utils.output_history(ANALYSIS_FILE, full_history)
    profiler.endTick("IO")

    profiler.startTick("constructing_graph")
    g, con = construct_encoding(full_history, histories, strong_session)

    profiler.endTick("constructing_graph")

    # G.set_all_writes(ext_writes)

    # profiler.startTick("IO")
    # profiler.endTick("IO")
    return g, con
