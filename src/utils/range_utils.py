# utils for range query workload
# from deprecated import deprecated
from collections import defaultdict
from enum import Enum
from functools import partial

from utils.exceptions import RejectException


def convert_rs2dict(rs):
    """
    convert the result set of range query into dict
    :param rs:
    :return:
    """
    d = {}
    for item in rs:
        d[item['id']] = extract_dead_value(item['val'])
    return d


def subset(K, k1, k2):
    if k1 is None and k2 is None:
        return K

    rs = set()
    if k1 is None and k2 is not None:
        for k in K:
            if k <= k2:
                rs.add(k)

    if k1 is not None and k2 is None:
        for k in K:
            if k1 <= k:
                rs.add(k)

    if k1 is not None and k2 is not None:
        for k in K:
            if k1 <= k <= k2:
                rs.add(k)
    return rs


def in_between(k,k1,k2):
    if k1 is not None and k2 is not None:
        return k1 <= k <= k2
    elif k1 is None and k2 is not None:
        return k <= k2
    elif k1 is not None and k2 is None:
        return k1 <= k
    else:
        return True


def is_null(NULL_VALUE, value):
    def is_null_inner(value):
        if value == NULL_VALUE:
            return True
        else:
            return False
    return is_null_inner(value)



def extract_dead_value(value):
    assert isinstance(value, int)
    return value
    # if not is_dead_value(value):
    #     return value
    # cheng's bench

    # my jepsen format
    # if isinstance(value, int):
    #     return value & 0x3FFFFFFFFFFFFFFF
    # elif isinstance(value, str):
    #     return value[1:]
    # else:
    #     assert False


class ValueType(Enum):
    READ_V = 0
    SUCC = 1
    IS_DEAD = 2
    WRITE_VALUE = 3
    READY = 4
    ACTUAL_F = 5


def get_value(mop, v_type):
    """
    The new format is compatible with the old format, it just append some extra values, so get_value function can be
    used for both formats. We don't need to implement two sets of get functions for each format.
    :r      [f k v is-dead]
    :w      [f k v succ]
    :i      new [f k v read_v is-dead succ ready actual_f];     old [f k v read_v is-dead succ]
    :d      new [f k v read_v is-dead succ ready];              old [f k v read_v is-dead succ]
    :range  [f k v rs-filtered rs-filterout],
            Note that for append range workload, rs-filterout will be [] because without DEAD values.
    """
    assert isinstance(v_type, ValueType)
    f = mop[0]

    if v_type == ValueType.READ_V:
        assert f in ['r', 'i', 'd']
        if f == 'r':
            return mop[2]
        elif f == 'i' or f == 'd':
            return mop[3]
    elif v_type == ValueType.SUCC:
        assert f in ['w', 'i', 'd']
        if f == 'w':
            # debug
            return mop[3]
        elif f == 'i' or f == 'd':
            return mop[5]
    elif v_type == ValueType.IS_DEAD:
        assert f in ['r', 'i', 'd']
        if f == 'r':
            return mop[3]
        elif f == 'i' or f == 'd':
            return mop[4]
    elif v_type == ValueType.WRITE_VALUE:
        assert f in ['w', 'i', 'd', 'append']
        return mop[2]
    elif v_type == ValueType.READY:
        assert f in ['i', 'd']
        return mop[6]
    elif v_type == ValueType.ACTUAL_F:
        assert f in ['i']
        return mop[7]
    else:
        assert False, "[get_value]: The value you want to access hasn't been defined"


def get_read_v(mop):
    return get_value(mop, ValueType.READ_V)


def get_succ(mop):
    return get_value(mop, ValueType.SUCC)


def get_is_dead(mop):
    return get_value(mop, ValueType.IS_DEAD)


def get_write_value(mop):
    return get_value(mop, ValueType.WRITE_VALUE)


def get_ready(mop):
    return get_value(mop, ValueType.READY)


def get_actual_f(mop):
    return get_value(mop, ValueType.ACTUAL_F)


def ext_writes_fn(txn):
    """
    txn format: [['w', 5, 2], ['r', 3, 4]]
    :return like {5:2, 6:7}

    depends on the format of history:
    :i [f k v read_v is-dead succ]
    """
    is_null_func = partial(is_null, 'nil')
    ext_write_map = {}
    for mop in txn:
        f, k = mop[0], mop[1]

        if f in ['w', 'i', 'd']:
            w_value = get_write_value(mop)
            succ = get_succ(mop)

            if f == 'w' or f == 'i':
                if succ:
                    ext_write_map[k] = w_value
            # elif f == 'i':
            #     read_v = get_read_v(mop)
            #     is_dead = get_is_dead(mop)
            #
            #     assert succ
            #     # to support preBench, we don't assert this any more
            #     assert is_null_func(read_v) or is_dead
            #     ext_write_map[k] = w_value
            elif f == 'd':
                assert succ
                ext_write_map[k] = w_value
            else:
                assert False
        if f == 'append':
            w_value = get_write_value(mop)
            ext_write_map[k] = w_value

    return ext_write_map


def ext_reads_fn(txn):
    """
    :param txn:
    :return:
    """
    ignore = set() # key set
    ext_reads_map = {}

    for mop in txn:
        f, k1 = mop[0], mop[1]

        if f == 'range':
            assert 5 <= len(mop) <= 6, "Wrong size of range mop, you add more items?"
            k2, read_values, dead_values = mop[2:5]
            for item in read_values:
                id, val = item['id'], item['val']
                assert k1 <= id <= k2

                if id not in ignore:
                    ext_reads_map[id] = val
                    ignore.add(id)

            for item in dead_values:
                id, val = item['id'], item['val']
                assert k1 <= id <= k2

                if id not in ignore:
                    ext_reads_map[id] = val
                    ignore.add(id)

        elif f in ['r', 'i', 'd'] and (k1 not in ignore):
            read_v = get_read_v(mop)
            ext_reads_map[k1] = read_v

            if f in ['i', 'd']:
                succ = get_succ(mop)
                assert succ, f"[mop]: {mop}"

            ignore.add(k1)
        elif f == 'w':
            succ = get_succ(mop)
            if succ:
                ignore.add(k1)
        elif f == 'append':
            ignore.add(k1)

    return ext_reads_map


def check_valid_read(k, last_rw, val, i, writes):
    # must read from last write/read of the same key
    if k in last_rw and last_rw[k] != val:
        raise RejectException("inconsistent read value as last write/read")

    # check if this is a future read
    if (k, val) in writes and writes[(k, val)] > i:
        raise RejectException("Future read error")


def check_INT(txn):
    """
    :param txn:
    :return:
    """
    last_rw = {} # store which value being read last time, the expected value the current read
    writes = {}

    for i, mop in enumerate(txn):
        f, k1 = mop[0], mop[1]

        if f == 'w':
            val = get_write_value(mop)
            # if k1 not in writes:
            #     writes[k1] = set()
            writes[(k1, val)] = i

    for i, mop in enumerate(txn):
        f, k1 = mop[0], mop[1]

        if f == 'range':
            assert 5 <= len(mop) <= 6, "Wrong size of range mop, you add more items?"
            k2, read_values, dead_values = mop[2:5]

            for item in read_values:
                id, val = item['id'], item['val']
                assert in_between(id, k1, k2)

                check_valid_read(id, last_rw, val, i, writes)
                last_rw[id] = val

            for item in dead_values:
                id, val = item['id'], item['val']
                assert k1 <= id <= k2

                check_valid_read(id, last_rw, val, i, writes)
                last_rw[id] = val
        elif f in ['r']:
            val = get_read_v(mop)
            check_valid_read(k1, last_rw, val, i, writes)

            last_rw[k1] = val
        elif f in ['d']:
            succ = get_succ(mop)
            assert succ, f"[mop]: {mop}"
            val = get_write_value(mop)
            read_val = get_read_v(mop)

            check_valid_read(k1, last_rw, read_val, i, writes)
            last_rw[k1] = val
        elif f == 'w':
            succ = get_succ(mop)
            if succ:
                val = get_write_value(mop)
                last_rw[k1] = val
        elif f == 'append':
            assert False

    return True


def ext_index(history, ext_fn):
    """
    construct a map: {k {v [txn1_id, txn2_id, ...]}}
    :param history:
    :return:
    """
    idx = {}
    # Tf's value is None
    if history[-1]['value'] is None: # if the history includes Tf, don't consider it now
        history = history[:-1]
    for id in range(1, len(history)): # traverse all the txns except T0 and Tf
        txn = history[id]['value']
        ext_map = ext_fn(txn)

        # print("id=%d\n" % id)
        for (k, v) in ext_map.items():
            if k not in idx:
                idx[k] = {v: {id}}
            elif v not in idx[k]:
                idx[k][v] = {id}
            else:
                idx[k][v].add(id)

    return idx


def all_writes_fn(txn):
    """
    identify the writes(including insertions and deletions) in a given single txn
    :param txn:
    :return: {k1: {v1: txn1, v2: txn2, ...}, k2: {v3: txn3, ...}, ...}
    """
    all_writes_map = defaultdict(dict)

    for j, mop in enumerate(txn):
        f, k = mop[0], mop[1]

        if f in ['w', 'i', 'd']:
            w_value = get_write_value(mop)
            assert w_value not in all_writes_map[k]
            
            succ = get_succ(mop)
            if succ:
                all_writes_map[k][w_value] = j
        if f == 'append':
            w_value = get_write_value(mop)
            assert w_value not in all_writes_map[k]

    return all_writes_map


def all_reads_fn(history):
    """
    identify all the reads in the history
    :param history:
    :return:
    can't keep the consistent interface of all_insert_reads/all_writes_fn because there are many reads for the same k, v
    """
    idx = defaultdict(dict)

    if history[-1]['value'] is None:  # if the history includes Tf, don't consider it now
        history = history[:-1]

    for txn_id in range(1, len(history)):  # traverse all the txns except T0 and Tf
        txn = history[txn_id]['value']

        for mop_index, mop in enumerate(txn):
            f, k1 = mop[0], mop[1]

            if f == ['i', 'd', 'r']:
                read_v = get_read_v(mop)
                if read_v not in idx[k1]:
                    idx[k1][read_v] = set()
                idx[k1][read_v].add((txn_id, mop_index))
            elif f == 'range':
                k2 = mop[2]
                read_values = mop[3]
                dead_values = mop[4]  # those DEAD VALUES, TODO: to check whether need to process here

                for item in read_values:
                    id, read_v = item['id'], item['val']
                    assert k1 <= read_v <= k2

                    if read_v not in idx[k1]:
                        idx[k1][read_v] = set()
                    idx[id][read_v].add((txn_id, mop_index))

    return idx


def all_insert_writes_fn(txn):
    """

    :param txn:
    :return:
    """
    all_insert_map = defaultdict(dict)

    for j, mop in enumerate(txn):
        f, k = mop[0], mop[1]

        if f == 'i':
            w_value = get_write_value(mop)
            assert w_value not in all_insert_map[k]
            all_insert_map[k][w_value] = j

    return all_insert_map


def all_upsert_fn(txn):
    """

    :param txn:
    :return: {k: {v: mop_index}}
    """
    all_upserts_map = defaultdict(dict)

    for j, mop in enumerate(txn):
        f, k = mop[0], mop[1]

        if f == 'w':
            write_v = get_write_value(mop)
            assert write_v not in all_upserts_map[k] # once read by an insertion mop, then new value will be set
            all_upserts_map[k][write_v] = j

    return all_upserts_map


def all_index(history, all_fn):
    """

    :param history:
    :param all_fn:
    :return:
    """
    idx = {}

    if history[-1]['value'] is None:  # if the history includes Tf, don't consider it now
        history = history[:-1]
    for txn_id in range(1, len(history)):  # traverse all the txns except T0 and Tf
        txn = history[txn_id]['value']
        all_map = all_fn(txn)  #

        for (k, v2mop_index) in all_map.items():
            for (v, mop_index) in v2mop_index.items():
                if k not in idx:
                    idx[k] = {v: (txn_id, mop_index)}
                elif v not in idx[k]:
                    idx[k][v] = (txn_id, mop_index)
                else:
                    assert False  # since all_index is only used for insert_writes, insert_reads, all_writes,
                    # so it's impossible to have multiple txn read/write the same k, v
                    # idx[k][v].add(txn_id)

    return idx


def get_all_range_queries(history):
    """
    find all the range queries in a given history, return a list of tuples (txn_id, mop_index)
    :param history:
    :return: [(txn_id, micro_op_index)...]
    """
    if history[-1]['value'] is None:
        history = history[:-1]

    queries = set()
    final_query = [-1, -1]
    for i, txn in enumerate(history):
        if i == 0:
            continue
        txn = txn['value']
        for j, mop in enumerate(txn):
            f = mop[0]
            if f == 'range':
                if len(mop) == 6:
                    assert isinstance(mop[5], bool)
                    queries.add((i, j))
                    if mop[5]:
                        final_query = (i, j)
                else:
                    queries.add((i, j))

    return queries, final_query


def all_keys(history):
    """
    K. return all the involved keys in the history
    :param history:
    :return: K, the set of all inserted keys
    """
    keys = set()
    if history[-1]['value'] is None:
        history = history[:-1]

    for i, txn in enumerate(history):
        if i == 0:
            continue
        txn = txn['value']
        for j, mop in enumerate(txn):
            f, k = mop[0], mop[1]
            if f in ['i', 'd', 'w']:
                keys.add(k)

    return keys


def k_writes_fn(ext_writes, key):
    """
    identify those txns which have ever written this key
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


def k_upserts_fn(all_upserts, key):
    """
    identify those txns which have ever written this key
    :param ext_writes:
    :param key:
    :return: a set of txn_ids which have ever written this key
    """
    w_set = set()
    if key not in all_upserts:
        return w_set

    values2writes = all_upserts[key]
    for (v, pos) in values2writes.items():
        w_set.add(pos)

    return w_set


def Tk_set_fn(ext_writes, key, exclude):
    """
    wrap k_writes_fn to exclude the Ti and Tj
    :param ext_writes:
    :param key:
    :param exclude:
    :return:
    """
    w_set = k_writes_fn(ext_writes, key)
    Tk_set = w_set - exclude
    return Tk_set






