import re
import sys
from collections import defaultdict

import edn_format
from edn_format import Keyword

NULL_VALUE=[]


def is_null(val):
    return True if val == NULL_VALUE else False


def parse_single_txn(line, txn_id):
    try:
        cur_txn_dict = edn_format.loads(line)
    except edn_format.exceptions.EDNDecodeError as e:
        print(f"Txn {txn_id} wrong format.")
        raise e

    assert cur_txn_dict[Keyword('type')] == Keyword("ok") and cur_txn_dict[Keyword('f')] == Keyword('txn')
    txn_value = []

    for mop in cur_txn_dict[Keyword('value')]:
        curr_micro_op = []

        d = {Keyword('append'): 'append', Keyword('r'): 'r'}
        assert mop[0] in d, f"{mop[0]} is not valid"
        curr_micro_op.append(d[mop[0]])  # mop type
        curr_micro_op.append(mop[1])  # k1

        read_v = mop[2]
        if curr_micro_op[0] == 'r':
            read_v = 'nil' if (read_v is None or read_v == []) else read_v

        curr_micro_op.append(read_v)
        txn_value.append(curr_micro_op)

    txn = {"value": txn_value, "id": txn_id, "thread": cur_txn_dict[Keyword('process')]}
    return txn


def parse(lines):
    full_history = [{'id': 0, 'value': None}]  # T0
    histories = defaultdict(list)
    tids = set()
    for i in range(len(lines)):
        cur_txn = parse_single_txn(lines[i], i + 1)
        full_history.append(cur_txn)

        tids.add(cur_txn['thread'])
        histories[cur_txn['thread']].append(cur_txn)

    tids = list(tids)
    tid2index = {}
    for i, tid in enumerate(tids):
        tid2index[tid] = i

    histories_list = [None] * len(tids)
    for tid, history in histories.items():
        histories_list[tid2index[tid]] = history
    return full_history, histories_list

