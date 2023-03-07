from utils.utils import ci, si


def add_from_edge_list(iter_g, edge_list):
    for e in edge_list:
        iter_g.add_edge(*e)


def pick_this_edge_pair(edge, k, nid2rank):
    src, dst, t = edge
    if t in ["wr", "ww", 'cb']:
        if nid2rank[ci(src)] + k < nid2rank[si(dst)]:
            return True
    elif t == "rw":
        if nid2rank[si(src)] + k < nid2rank[ci(dst)]:
            return True
    else:
        assert False

    return False


def k_bounded_constraints(k, G, iter_G, nid2rank):
    num_add_edges = 0
    num_dec_conns = 0
    _, _, conn, _ = G.get_4tuples()
    _, _, iter_conn, _ = iter_G.get_4tuples()

    for e1, e2 in conn:  # edge set 1,
        ret1 = pick_this_edge_pair(e1, k, nid2rank)
        ret2 = pick_this_edge_pair(e2, k, nid2rank)
        if ret1 and ret2: # contradiction
            return False
        elif ret1 and (not ret2):
            iter_conn.remove((e1, e2))
            iter_G.add_edge(*e1)
            num_add_edges += len(e1)
            num_dec_conns += 1
        elif ret2 and (not ret1):
            iter_conn.remove((e1, e2))
            iter_G.add_edge(*e2)

            num_add_edges += len(e2)
            num_dec_conns += 1
        else:
            continue

    print(f"Added {num_add_edges} edges while removed {num_dec_conns} constraints")
    return True