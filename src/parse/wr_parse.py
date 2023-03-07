import edn_format
from edn_format import Keyword


def construct_single_txn4wr(line, id):
    cur_txn_dict = edn_format.loads(line)
    assert cur_txn_dict[Keyword('type')] == Keyword("ok")
    value = []
    for micro_op in cur_txn_dict[Keyword('value')]:
        curr_micro_op = ['nil', micro_op[1], micro_op[2]]

        if micro_op[0] == Keyword('w') or micro_op[0] == Keyword('i'):
            curr_micro_op[0] = 'w'
        else:
            curr_micro_op[0] = 'r'

        if curr_micro_op[2] is None:
            curr_micro_op[2] = 'nil'

        value.append(curr_micro_op)

    txn = {"value": value, "id": id}
    return txn


def is_final_txn(cur_txn):
    # if final txn is in a format of range query:
    # if len(cur_txn['value']) == 1 and cur_txn['value'][0][0] == 'range' \
    #     and isinstance(cur_txn['value'][0][5], bool) and cur_txn['value'][0][5]:
    if len(cur_txn['value']) == 1 and cur_txn['value'][0][0] == 'range' \
            and isinstance(cur_txn['value'][0][5], bool) and cur_txn['value'][0][5]:
        return True
    else:
        return False


def construct_all_txns(lines, hasFinal):
    # final_txn = None
    max_txn_length = 0
    final_txn_index = -1
    history = [{'id': 0, 'value': None}]
    for i in range(len(lines)):
        cur_txn = construct_single_txn4wr(lines[i], i + 1)
        if len(cur_txn['value']) > max_txn_length:
            final_txn_index = i+1
            max_txn_length = len(cur_txn['value'])

        history.append(cur_txn)

    #
    # assert final_txn is not None, "Can't find final transaction"
    # history.append(final_txn)
    if hasFinal:
        history[-1], history[final_txn_index] = history[final_txn_index], history[-1]
        # swap id
        history[-1]['id'], history[final_txn_index]['id'] = history[final_txn_index]['id'], history[-1]['id']
    return history