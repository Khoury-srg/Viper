import json
from functools import partial

import edn_format
from edn_format import Keyword

from utils import range_utils
from utils.profiler import Profiler
from utils.utils import convert_readv


def construct_single_txn4wrrange_edn(line, txn_id):
    """
    param: workload ? what are the difference and effect?
    param: mywrapper ? when should use wrapper and when not?
    param: NORMAL_WR ? is relative to append, what is the difference or effect?
    """
    # Note: NORMAL_WR means whether it is the original wr format in Jepsen, [:r k v], [:w k v],
    # without further information for each mop
    is_null = partial(range_utils.is_null, 'nil')
    try:
        cur_txn_dict = edn_format.loads(line)
    except (edn_format.exceptions.EDNDecodeError, AttributeError) as e:
        print(f"Txn {txn_id} wrong format: {line}")
        raise e

    assert cur_txn_dict[Keyword('type')] == Keyword("ok") and cur_txn_dict[Keyword('f')] == Keyword('txn')
    value = []
    for micro_op in cur_txn_dict[Keyword('value')]:
        parsed_micro_op = []

        d = {Keyword('w'): 'w', Keyword('r'): 'r', Keyword('i'): 'i', Keyword('d'): 'd', Keyword('range'): 'range'}
        # b = {}
        if micro_op[0] in d:
            parsed_micro_op.append(d[micro_op[0]])  # mop type
            parsed_micro_op.append(micro_op[1])  # k1
        else:
            # set-SI
            continue

        if parsed_micro_op[0] == 'range':
            parsed_micro_op.append(micro_op[2])  # k2
            for i in range(2):
                kvs = []  # key value pairs
                for record in micro_op[3 + i]:
                    id = record[Keyword('id')]
                    val = record[Keyword('val')]
                    cur_record = {'id': id, 'val': val}
                    kvs.append(cur_record)
                parsed_micro_op.append(kvs)
        else:  # r w i d
            if parsed_micro_op[0] == 'r':
                read_v = micro_op[2]
                read_v = 'nil' if read_v is None else read_v
                parsed_micro_op.append(read_v)
                is_dead = micro_op[3]
                parsed_micro_op.append(is_dead)
            else:  # w i d
                v = micro_op[2]
                parsed_micro_op.append(v)

                if parsed_micro_op[0] in ['w', 'd']:
                    read_v = convert_readv(micro_op[3])
                    parsed_micro_op.append(read_v)
                    if len(micro_op)  >= 5:
                        parsed_micro_op.append(micro_op[4])
                        parsed_micro_op.append(micro_op[5])
                else:  # i
                    assert False

        value.append(parsed_micro_op)

    txn = {"value": value, "id": txn_id}
    return txn


def construct_single_txn4wrrange_json(lines, txn_id):
    """
    param: workload ? what are the difference and effect?
    param: mywrapper ? when should use wrapper and when not?
    param: NORMAL_WR ? is relative to append, what is the difference or effect?
    """
    # Note: NORMAL_WR means whether it is the original wr format in Jepsen, [:r k v], [:w k v],
    # without further information for each mop
    profiler = Profiler.instance()
    # {:type :ok :f :txn :value [[:r  7241 - 8068482120162306138    false]]}
    profiler.startTick("json")
    unparsed_txns = json.loads(lines)
    profiler.endTick("json")

    parsed_txns = []
    profiler.startTick("other parsing")
    for unparsed_txn in unparsed_txns:
        unparsed_txn['id'] = txn_id # parsed
        txn_id += 1
        parsed_txns.append(unparsed_txn)

    profiler.endTick("other parsing")
    return parsed_txns, txn_id


def construct_all_txns_json(logs, callback):
    """
    logs: list, each element is lines of txns
    workload: a string like 'ra'
    callback: a function used to parse each line in lines and get a parse txn
    """
    all_histories = []
    full_history = [{'id': 0, 'value': None}]  # T0
    # final_txn_index = None
    profiler = Profiler.instance()

    txn_id = 1
    for i in range(len(logs)):
        # if i % (len(logs) * 0.05) == 0:
        #     print(f"Parsing log progress: {i*100.0/len(logs)}%")

        lines = logs[i] # a list
        assert txn_id == len(full_history)
        history_this_log, txn_id = callback(lines, txn_id)  # line, txn_id, workload, NORMAL_WR = False

        full_history.extend(history_this_log)

        all_histories.append(history_this_log)

    return full_history, all_histories


def construct_all_txns_edn(logs, callback):
    """
    logs: list, each element is lines of txns
    workload: a string like 'ra'
    callback: a function used to parse each line in lines and get a parse txn
    """
    all_histories = []
    full_history = [{'id': 0, 'value': None}]  # T0
    # final_txn_index = None

    txn_id = 1
    for i in range(len(logs)):
        # print(f"Parsing log {i}")
        lines = logs[i]
        history_this_log = []

        for j in range(len(lines)):
            # wrapper should be set for downgrade, should be None for non-downgrade
            assert txn_id == len(full_history)
            cur_txn = callback(lines[j], txn_id)  # line, txn_id, workload, NORMAL_WR = False
            # if hasFinal and len(cur_txn['value']) == 1 and cur_txn['value'][0][0] == 'range' \
            #         and isinstance(cur_txn['value'][0][5], bool) and cur_txn['value'][0][5]: # TODO: Tricky part
            #     final_txn_index = (i, j)
            #     continue
            history_this_log.append(cur_txn)
            full_history.append(cur_txn)
            txn_id += 1
        all_histories.append(history_this_log)

    # if hasFinal:
    #     assert final_txn_index is not None, "Can't find final transaction"
    #     full_history.append(final_txn_index)
    return full_history, all_histories


if __name__ == '__main__':
    # str = """{:type :ok :f :txn :value [[:range 4882 4892 [{:id 4884, :sk 4884, :val 28kNTU0utxKF7FvuJBRrM5a8JOGfmIG7jpMDoXKzp3We3Gp53POXafFnaodoqAGx4UsYN4pbxBBViODvAq9yLaJHxy2eXF7h4EUa5nfcCYrsW896qODi4y8kmooC52e8peiMGTSrzmDE}] []]]}"""
    str = ""
    cur_txn_dict = edn_format.loads(str)
