from utils.utils import ci, si

# Chain heuristic
def add_from_edge_list(iter_g, edge_list):
    for e in edge_list:
        iter_g.add_edge(*e)


def pick_this_es(es, k, nid2score):
    for src, dst, t in es:
        if t in ["wr", "ww", 'cb']:
            if nid2score[ci(src)] + k < nid2score[si(dst)]:
                return True
        elif t == "rw":
            if nid2score[si(src)] + k < nid2score[ci(dst)]:
                return True
        else:
            assert False
    return False


def k_bounded_constraints(k, conn, iter_g, iter_conn, nid2score):
    num_add_edges = 0
    num_dec_conns = 0
    for es1, es2 in conn:  # edge set 1,
        ret1 = pick_this_es(es1, k, nid2score)
        ret2 = pick_this_es(es2, k, nid2score)
        if ret1 and ret2: # contradiction
            return False
        elif ret1 and (not ret2):
            iter_conn.remove((es1, es2))
            add_from_edge_list(iter_g, es1)
            num_add_edges += len(es1)
            num_dec_conns += 1
        elif ret2 and (not ret1):
            iter_conn.remove((es1, es2))
            add_from_edge_list(iter_g, es2)

            num_add_edges += len(es2)
            num_dec_conns += 1
        else:
            continue

    print(f"Added {num_add_edges} edges while removed {num_dec_conns} constraints")
    return True


# pair heuristic
