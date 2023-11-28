from __future__ import print_function
import copy
import shutil
from typing import List, Any, Dict

import networkx as nx
import os


def mk_dirs(*dirs):
    for dir in dirs:
        if os.path.exists(dir):
            shutil.rmtree(dir)
        os.makedirs(dir)


def listRightIndex(bitmap, value):
    n = bitmap.size()
    if value == 1:
        for i in range(n):
            if bitmap.test(i):
                return i
        return -1
    elif value == 0:
        for i in range(n):
            if not bitmap.test(i):
                return i
        return -1


def incr(bitmap):
    last_zero_pos = listRightIndex(bitmap, 0)
    bitmap.set(last_zero_pos)

    for i in range(last_zero_pos):
        bitmap.reset(i)


# ====== load file =====
def extract_edge(edge):
    tokens = edge.split(",")
    assert len(tokens) == 2, "ill-format edge: a,b"
    return (int(tokens[0]), int(tokens[1]))


def extract_edge_pair(edge_pair):
    (edge1, edge2) = edge_pair.split(' ')
    edge1 = extract_edge(edge1[1:-1])
    if edge2[-1] == '\n':
        edge2 = edge2[:-1]
    edge2 = extract_edge(edge2[1:-1])
    return edge1, edge2


def _sort(edge1, edge2):
    if edge2[0] < edge1[0] or (edge2[0] == edge1[0] and edge2[1] < edge1[1]):
        edge1, edge2 = edge2, edge1
    return edge1, edge2


def load_known_graph(graph_file):
    """
    can only load known graph, for append workload
    :param graph_file:
    :return:
    """
    with open(graph_file) as f:
        lines = f.readlines()

    n = 0
    edges = []
    for line in lines:
        if line == "":
            continue

        elems = line.split(':')
        assert len(elems) == 2, "ill-format log"
        symbol = elems[0]
        content = elems[1]

        if symbol == "n":
            assert n == 0, "multiple n in file"
            n = int(content)
        elif symbol == "e":
            e = extract_edge(content)
            edges.append(e)
        else:
            print("Line = %s" % line)
            assert False, "should never be here"

    return n, edges


def load_polygraph_file(graph_file):
    """
    can only load poly graph
    :param graph_file:
    :return:
    """
    print ("load polygraph from %s" % graph_file)
    with open(graph_file) as f:
        lines = f.readlines()

    n = 0
    edges = set()
    edge_pairs = set()
    constraints = set()
    for line in lines:
        if line == "":
            continue

        elems = line.split(':')
        assert len(elems) == 2, "ill-format log"
        symbol = elems[0]
        content = elems[1]

        if symbol == "n":
            assert n == 0, "multiple n in file"
            n = int(content)
        elif symbol == "e":
            e = extract_edge(content)
            assert e not in edges
            edges.add(e)
        elif symbol == "p":
            edge1, edge2 = extract_edge_pair(content)
            edge1, edge2 = _sort(edge1, edge2)
            edge_pairs.add((edge1, edge2))
        elif symbol == 'c':
            try:
                n1, n2, n3 = content.strip().split(',')
                n1, n2, n3 = int(n1), int(n2), int(n3)
                constraints.add((n1, n2, n3))
            except Exception as e:
                print(line)
                print()
                raise e
        else:
            assert False, "Line = %s should never be here" % line

    if len(constraints) == 0:
        return n, list(edges), list(edge_pairs)
    else:
        return n, list(edges), list(edge_pairs), list(constraints)


def load_SSG_SI_graph(graph_file):
    """
    can only load SI SSG which has a label with each edge
    :param graph_file:
    :return:
    """
    print("load SSG from %s" % graph_file)
    with open(graph_file) as f:
        lines = f.readlines()

    n = 0

    # edges: dict: edge type => edge set, edge type is the key wrritten
    # edge_pairs: dict: edge type => edge pair set
    edges = {}
    edge_pairs = {}
    min_key, max_key = None, None
    ext_writes = {}

    for line in lines:
        if line == "":
            continue

        elems = line.split(':')
        symbol = elems[0]
        content = elems[1]

        if symbol == "n":
            assert n == 0, "multiple n in file"
            assert len(elems) == 2, "ill-format log"
            n = int(content)
        elif symbol == 'k':  # k:3,5
            assert len(elems) == 2, "ill-format log"
            min_key, max_key = extract_edge(content)
        elif symbol == "e": # e:57,308:2
            assert len(elems) == 3, "ill-format log"
            label = int(elems[2])
            e = extract_edge(content)
            if label not in edges:
                edges[label] = set()
            assert e not in edges[label]
            edges[label].add((e[0], e[1]))
        elif symbol == "p": # p:(109,157) (577,109):2
            assert len(elems) == 3, "ill-format log"
            label = int(elems[2])
            edge1, edge2 = extract_edge_pair(content)
            edge1, edge2 = _sort(edge1, edge2)
            if label not in edge_pairs:
                edge_pairs[label] = set()
            assert ((edge1, edge2) not in edge_pairs[label])
            edge_pairs[label].add((edge1, edge2))
        elif symbol.isdigit() or symbol[0]=='-':
            k = int(symbol)
            # print("content:", content)
            txns = content.strip().split(" ")
            # print("txns:", txns)
            txns = list(map(lambda x: int(x), txns))
            for txn in txns:
                if k not in ext_writes:
                    ext_writes[k] = set()
                ext_writes[k].add(txn)
        else:
            assert False, "Line = %s should never be here" % line

    return n, edges, edge_pairs, min_key, max_key, ext_writes


def load_nx_graph(graph_file):
    """

    :param graph_file:
    :return: PolyGraph
    """
    n, edges, _ = load_polygraph_file(graph_file)

    # construct networkx DiGraph object
    G = nx.DiGraph()
    G.add_nodes_from(list(range(n)))
    G.add_edges_from(edges)

    return G


class Graph:
    def __init__(self, n_nodes, edges=None):
        self.nodes = list(range(n_nodes))
        # self.edges = [[0] * n_nodes] * n_nodes
        if edges is None:
            self.edges = {} # cobraplusbackend => dst set
        else:
            self.edges = copy.deepcopy(edges)

    def add_edge(self, src, dst):
        assert src in self.nodes and dst in self.nodes
        assert src != dst
        if src in self.edges:
            self.edges[src].add(dst)
        else:
            self.edges[src] = set([dst])  # set in case of dupliacte

    def add_edges(self, edge_list):
        """

        :param edge_list: [(s1, d1), (s2,d2), ...]
        :return:
        """
        for u, v in edge_list:
            self.add_edge(u, v)

    def output2file(self, output_file_path):
        with open(output_file_path, 'w') as f:
            f.write("n:%d\n" % len(self.nodes))
            for src, dst_nodes in self.edges.items():
                for dst in dst_nodes:
                    f.write("e:%d,%d\n" % (src, dst))


class PolyGraph:
    def __init__(self, n_nodes):
        self.n_nodes = n_nodes
        # self.nodes = [] # list of integers
        self.edges = {} # adj list: src => dst set
        self.edge_pairs = set()

    # def add_node(self, node):
    #     self.nodes.append(node)
    #
    # def add_nodes(self, nodes):
    #     self.nodes.extend(nodes)

    def is_valid_node_id(self, *nids):
        for nid in nids:
            if 0 <= nid < self.n_nodes:
                continue
        return True

    def add_edge(self, src, dst):
        assert self.is_valid_node_id(src, dst)
        assert src != dst

        if src not in self.edges:
            self.edges[src] = set()
        self.edges[src].add(dst)

    def add_edges(self, src_list, dst_list):
        """
        for any s in src_list and t in dst_list, add edge s => t
        :param src_list:
        :param dst_list:
        :return:
        """
        # assert len(set(src_list) & set(dst_list)) == 0
        for src in src_list:
            for dst in dst_list:
                self.add_edge(src, dst)

    def add_edge_pair(self, src1, dst1, src2, dst2):
        """
        add this pair only if not exist
        :param src1:
        :param dst1:
        :param src2:
        :param dst2:
        :return:
        """
        assert self.is_valid_node_id(src1, dst1, src2, dst2)
        assert src1 != dst1 and src2 != dst2

        if not (((src1, dst1), (src2, dst2)) in self.edge_pairs or ((src2, dst2), (src1, dst1)) in self.edge_pairs):
            self.edge_pairs.add(((src1, dst1), (src2, dst2)))

    def get_num_pairs(self):
        return len(self.edge_pairs)

    def incude_nx_graph(self, bit_map, disable_uncertainty=False):
        if not hasattr(self, 'nxG'):
            G = nx.DiGraph()
            G.add_nodes_from(list(range(self.n_nodes)))
            edges = []
            for u, vs in self.edges.items():
                for v in vs:
                    edges.append((u, v))
            G.add_edges_from(edges)
            self.nxG = G

        G = copy.deepcopy(self.nxG)

        if not disable_uncertainty:
            edge_pairs = list(self.edge_pairs)
            for i in range(len(edge_pairs)):
                ((u1, v1), (u2, v2)) = edge_pairs[i]
                if bit_map.test(i):
                    G.add_edge(u2, v2)
                else:
                    G.add_edge(u1, v1)
        return G

    def induce_graph(self, bit_map, disable_uncertainty):
        """

        :param edge_pairs: in binary format, 0 for the left edge and 1 for the right edge
        :return: a Graph object
        """
        assert len(bit_map.tostring()) >= len(self.edge_pairs)
        if not hasattr(self, 'iG'):
            edges = copy.deepcopy(self.edges)
            graph = Graph(self.n_nodes, edges)
            self.iG = graph

        graph = copy.deepcopy(self.iG)

        if not disable_uncertainty:
            edge_pairs = list(self.edge_pairs)
            for i in range(len(edge_pairs)):
                ((u1, v1), (u2, v2)) = edge_pairs[i]
                if bit_map.test(i):
                    graph.add_edge(u2, v2)
                else:
                    graph.add_edge(u1, v1)

        return graph

    def output2file(self, output_file_path):
        num_edges = 0
        with open(output_file_path, 'w') as f:
            f.write("n:%d\n" % self.n_nodes)
            for src, dst_nodes in self.edges.items():
                num_edges += len(dst_nodes)
                for dst in dst_nodes:
                    f.write("e:%d,%d\n" % (src, dst))
            for ((src1, dst1), (src2, dst2)) in self.edge_pairs:
                f.write("p:(%d,%d) (%d,%d)\n" % (src1, dst1, src2, dst2))
        print("wrote PolyGraph into %s" % output_file_path)
        print("#nodes=%d" % self.n_nodes)
        print("#edges=%d" % num_edges)
        print("#edge pairs=%d" % len(self.edge_pairs))


def get_in(nested_dict, k, v):
    """
    read a nested dict
    :param nested_dict:
    :param k:
    :param v:
    :return:
    """
    if k in nested_dict and v in nested_dict[k]:
        return nested_dict[k][v]
    else:
        return set()


def output_history(output_path, history):
    """
    after constructing the history object, write it into a file
    :param output_path:
    :param history:
    :return:
    """
    with open(output_path, 'w') as f:
        print(history, file=f)
    print ("wrote history into %s\n" % output_path)


def compute_file_path(logs_folder, sub_dir, graphs_folder, analysis_folder, isolation_level):
    """
    compute the path of output dir and output file
    :param logs_folder:
    :param sub_dir:
    :param graphs_folder:
    :param analysis_folder:
    :return:
    """
    isolation_level2graph_file = {'serializability': 'poly.graph',
                                  'SI': 'SI.graph'}
    log_sub_dir = "%s/%s" % (logs_folder, sub_dir)
    log_file = "%s/history.edn" % log_sub_dir
    poly_graph_sub_dir = "%s/%s" % (graphs_folder, sub_dir)
    poly_graph_file = f"{poly_graph_sub_dir}/{isolation_level2graph_file[isolation_level]}"
    analysis_sub_dir = "%s/%s" % (analysis_folder, sub_dir)
    analysis_file = "%s/history.log" % analysis_sub_dir
    return log_sub_dir, log_file, poly_graph_sub_dir, poly_graph_file, analysis_sub_dir, analysis_file


def convert_readv(v):
    if v is None:
        v = 'nil'
    return v

def extract_AgumentGraph_edge(edge):
    """
    e:0,386,wr
    """
    tokens = edge.split(",")
    assert len(tokens) == 3, "ill-format edge: src,dst,type"
    return int(tokens[0]), int(tokens[1]), tokens[2]


def extract_AgumentGraph_edge_pair(edge_pair):
    """
    p:(3654,3658,ww) (3914,3654,rw)
    """
    (edge1, edge2) = edge_pair.split(' ')
    edge1 = extract_AgumentGraph_edge(edge1[1:-1])
    # if edge2[-1] == '\n':
    #     edge2 = edge2[:-1]
    edge2 = extract_AgumentGraph_edge(edge2[1:-1])
    return edge1, edge2


def _sort_two_edges(edge1, edge2):
    if edge2[0] < edge1[0] or \
            (edge2[0] == edge1[0] and edge2[1] < edge1[1]) \
            or (edge2[0] == edge1[0] and edge2[1] == edge1[1] and edge2[2] < edge1[2]):
        edge1, edge2 = edge2, edge1
    return edge1, edge2


def load_AgumentGraph_file(graph_file):
    """
    can only load poly graph
    :param graph_file:
    :return:
    """
    print ("load polygraph from %s" % graph_file)
    with open(graph_file) as f:
        lines = f.readlines()

    n = 0
    edges = set()
    edge_pairs = set()
    constraints = set()
    for line in lines:
        if line == "":
            continue

        elems = line.split(':')
        assert len(elems) == 2, "ill-format log"
        symbol = elems[0]
        content = elems[1]

        if symbol == "n":
            assert n == 0, "multiple n in file"
            n = int(content)
        elif symbol == "e":
            src, dst, type = extract_AgumentGraph_edge(content[:-1])
            assert (src, dst, type) not in edges
            edges.add((src, dst, type))
        elif symbol == "p":
            edge1, edge2 = extract_AgumentGraph_edge_pair(content[:-1])
            edge1, edge2 = _sort_two_edges(edge1, edge2)
            edge_pairs.add((edge1, edge2))
        else:
            assert False, "Line = %s should never be here" % line

    if len(constraints) == 0:
        return n, list(edges), list(edge_pairs)
    else:
        return n, list(edges), list(edge_pairs), list(constraints)


def si(i):
    return 2*i+1


def ci(i):
    return 2*i + 2


def si2(i):
    if i == 0:
        return 0
    else:
        return 2*i-1


def ci2(i):
    if i == 0:
        return 0
    else:
        return 2*i


def load_logs_json(LOG_DIR):
    """
    final_state_log: the log content of final txn
    other_logs: log contents of other threads
    """
    other_logs = []

    files = os.listdir(LOG_DIR)
    for file in files: # J14.log
        file_full_path = os.path.join(LOG_DIR, file)
        if not os.path.isdir(file_full_path) and (file.startswith("J") or file.startswith("history.edn")):
            # only open text files, ignore dirs
            with open(file_full_path) as f:
                lines = f.read()
                # TODO: for CobraBench histories, we don't need this.
                # lines = list(filter(lambda line: ":ok" in line, lines))
                # if hasFinal and len(lines) == 1:
                #     final_state_log = lines
                # else:
                # lines = lines.replace(":type :ok :f :txn ", '')
                # lines = lines.replace("] [", "], [")
                # lines = lines.replace(":r", '"r"').replace(":w", '"w"').replace(":value", '"value":')
                # lines = lines.replace(":w", '"w"')
                # lines = re.sub(":", , lines);
                lines = lines.replace("\n", ',')
                assert lines[-1] == ','
                lines = "["+ lines[:-1] + "]"
                other_logs.append(lines)

    return other_logs


def is_edn_log(file_full_path, filename):
    return not os.path.isdir(file_full_path) and (filename.startswith("Jep") or filename.startswith("history.edn"))


def load_logs_edn(LOG_DIR):
    """
    final_state_log: the log content of final txn
    other_logs: log contents of other threads
    """
    all_logs = []

    files = os.listdir(LOG_DIR)
    for file in files: # J14.log
        file_full_path = os.path.join(LOG_DIR, file)
        if is_edn_log(file_full_path):
            # only open text files, ignore dirs
            with open(file_full_path) as f:
                lines = f.readlines()
                if not file.startswith("Jep"):
                    lines = list(filter(lambda line: ":ok" in line, lines))
                all_logs.append(lines)

    return all_logs


def create_dirs(logs_folder, graphs_folder, analysis_folder, sub_dir):
    log_sub_dir, log_file, \
    poly_graph_sub_dir, poly_graph_file, \
    analysis_sub_dir, analysis_file \
        = compute_file_path(logs_folder, sub_dir, graphs_folder, analysis_folder, 'SI')

    mk_dirs(poly_graph_sub_dir, analysis_sub_dir)  # create corresponding dirs in case of not existing

    return log_sub_dir, log_file, \
            poly_graph_sub_dir, poly_graph_file, \
            analysis_sub_dir, analysis_file


def initial_state(full_history) -> Dict:
    if full_history[0]['value'] is None: # this history doesn't include an initial txn that captures the initial database state
        return None

    # ops must be a series of write operations
    write_ops = full_history[0]['value']
    writes = {}
    wop: List[Any]

    for wop in write_ops:
        f, k, v, succ = wop
        assert succ, "the write op in the initial txn must succeed"
        assert f == 'w'
        writes[k] = v

    return writes