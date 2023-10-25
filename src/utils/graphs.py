from abc import ABCMeta
import random
import numpy as np
import networkx as nx

from utils.profiler import Profiler
from utils.utils import ci, si

from utils.exceptions import RejectException

seed=123
random.seed(seed)
np.random.seed(seed)


class Graph(metaclass=ABCMeta):
    def __init__(self, n_nodes):
        self.n_nodes = n_nodes
        self.edges = {}  # adj list: src => dst set

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

    # def add_edge(self, src, dst, type):
    #     assert type in self.types
    #     assert self.is_valid_node_id(src, dst)
    #     assert src != dst
    #
    #     if src not in self.edges:
    #         self.edges[src] = set()
    #     self.edges[src].add((dst, type))

    # def add_edges(self, src_list, dst_list, type):
    #     """
    #     for any s in src_list and t in dst_list, add edge s => t
    #     :param src_list:
    #     :param dst_list:
    #     :return:
    #     """
    #     # assert len(set(src_list) & set(dst_list)) == 0
    #     for src in src_list:
    #         for dst in dst_list:
    #             self.add_edge(src, dst, type)


class BCGraph(metaclass=ABCMeta):
    def __init__(self, n_nodes):
        self.n_nodes = n_nodes
        self.edges = {}  # adj list: src => dst set

        for u in range(1, self.n_nodes+1):
            self.edges[u] = set()

    def is_valid_node_id(self, *nids):
        for nid in nids:
            if 1 <= nid <= self.n_nodes:
                continue
        return True

    def add_edge(self, src, dst):
        assert self.is_valid_node_id(src, dst)
        assert src != dst
        assert src != 0

        self.edges[src].add(dst)

    def _dfs(self, u, visited, path, cycles):
        if visited[u]:
            u_last_pos = path.index(u)
            print(path[u_last_pos:])
            cycles.add(tuple(path[u_last_pos:]))
            return

        visited[u] = True
        path.append(u)
        for v in self.edges[u]:
            self._dfs(v, visited, path, cycles)
        visited[u] = False
        del path[-1]

    def my_detect_cycle(self):
        visited = [False] * (self.n_nodes + 1)
        cycles = set()
        self._dfs(1, visited, [], cycles)

        return True if len(cycles) > 0 else False

    def detect_cycle_graph_tool(self):
        from graph_tool.all import Graph, is_DAG
        profiler = Profiler.instance()

        profiler.startTick("graph conversion")
        G = Graph()
        G.add_vertex(self.n_nodes) # nid starts from 0
        for u in self.edges:
            for v in self.edges[u]:
                G.add_edge(G.vertex(u-1), G.vertex(v-1))
        profiler.endTick("graph conversion")

        profiler.startTick("solving")
        ret = is_DAG(G)
        profiler.endTick("solving")

        # return whether has cycles
        return not ret

    def _dfs_graph_color(self, u, color, pred):
        color[u] = 1 # grey
        for v in self.edges[u]:
            if color[v] == 1:
                return True
            if color[v] == 0 and self._dfs_graph_color(v, color, pred):
                pred[v] = u
                # self._dfs_graph_color(v, color, pred)
                return True
        color[u] = 2
        return False

    def detect_cycle_graph_color(self):
        profiler = Profiler.instance()
        profiler.startTick("solving")
        color = [0] * (self.n_nodes + 1) # 0: white, 1: grey, 2: black; leave an extra empty color[0]
        pred = [-1] * (self.n_nodes + 1)

        for u in range(1, self.n_nodes+1):
            if color[u] == 0:
                r = self._dfs_graph_color(u, color, pred)
                if r:
                    print(pred)
                    profiler.endTick("solving")
                    return True
        profiler.endTick("solving")
        return False


class MultiTypeKnownGraph(metaclass=ABCMeta):
    """
    known graph with edge types
    """
    def __init__(self, n_nodes):
        self.n_nodes = n_nodes
        self.edges = {}  # adj list: src => dst set
        self.types = ['wr', 'ww', 'rw']

    def is_valid_node_id(self, *nids):
        for nid in nids:
            if 0 <= nid < self.n_nodes:
                continue
        return True

    def add_edge(self, src, dst, type):
        assert type in self.types
        assert self.is_valid_node_id(src, dst)
        assert src != dst

        if src not in self.edges:
            self.edges[src] = set()
        self.edges[src].add((dst, type))

    def add_edges(self, src_list, dst_list, type):
        """
        for any s in src_list and t in dst_list, add edge s => t
        :param src_list:
        :param dst_list:
        :return:
        """
        # assert len(set(src_list) & set(dst_list)) == 0
        for src in src_list:
            for dst in dst_list:
                self.add_edge(src, dst, type)

    def output2file(self, output_file_path):
        num_edges = 0
        with open(output_file_path, 'w') as f:
            f.write("n:%d\n" % self.n_nodes)
            for src, dst_nodes in self.edges.items():
                num_edges += len(dst_nodes)
                for dst, type in dst_nodes:
                    f.write("e:%d,%d,%s\n" % (src, dst, type))
        print("wrote PolyGraph into %s" % output_file_path)
        print("#nodes=%d" % self.n_nodes)
        print("#edges=%d" % num_edges)


class ArgumentedPolyGraph:
    """
    PolyGraph with edge types: rw, wr, ww
    """
    def __init__(self, n_nodes):
        self.n_nodes = n_nodes
        self.edges = {} # adj list: src => (dst, type) set
        self.edge_pairs = set()

        self.edge_type_lookup = {} # u => v => set(type)
        self.types = ['wr', 'ww', 'rw', 'cb']
        self.ext_key2writes = {} # key => a list of txn ids

        for i in range(n_nodes):
            self.edges[i] = set()
            self.edge_type_lookup[i] = {}

    def set_edges(self, edges):
        self.edges = edges

    def set_session_order(self, histories):
        self.histories = histories

    def is_valid_node_id(self, *nids):
        for nid in nids:
            if 0 <= nid < self.n_nodes:
                continue
        return True

    def add_edge(self, src, dst, type):
        assert type in self.types
        assert self.is_valid_node_id(src, dst)
        assert src != dst
        assert dst != 0

        if type == 'rw':
            self.edges[src].add((dst, type))
            if dst not in self.edge_type_lookup[src]:
                self.edge_type_lookup[src][dst] = set()
            self.edge_type_lookup[src][dst].add(type)
        else:
            cb_types = {'wr', 'cb', 'ww'}
            other_types = cb_types - {type}
            for t in other_types:
                if (dst, t) in self.edges[src]:
                    return

            self.edges[src].add((dst, type))
            if dst not in self.edge_type_lookup[src]:
                self.edge_type_lookup[src][dst] = set()
            self.edge_type_lookup[src][dst].add(type)

        # print(f"add edge ({src}, {dst}, {type})")

    def add_edges(self, src_list, dst_list, type):
        """
        for any s in src_list and t in dst_list, add edge s => t
        :param src_list:
        :param dst_list:
        :return:
        """
        # assert len(set(src_list) & set(dst_list)) == 0
        for src in src_list:
            for dst in dst_list:
                self.add_edge(src, dst, type)

    def add_edge_pair(self, src1, dst1, type1, src2, dst2, type2):
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

        if not (((src1, dst1, type1), (src2, dst2, type2)) in self.edge_pairs or
                ((src2, dst2, type2), (src1, dst1, type1)) in self.edge_pairs):
            self.edge_pairs.add(((src1, dst1, type1), (src2, dst2, type2)))


    def get_num_pairs(self):
        return len(self.edge_pairs)

    def get_4tuples(self):
        edges_list = []
        for src, dst_nodes in self.edges.items():
            for dst, type in dst_nodes:
                edges_list.append((src, dst, type))
        return self.n_nodes, edges_list, list(self.edge_pairs), self.ext_key2writes

    def set_all_writes(self, ext_writes):
        """
        ext_writes: a dict: key => a set of txn ids
        """
        for k in ext_writes:
            curr_txns = set()
            v2txns = ext_writes[k]

            for v, txns in v2txns.items():
                curr_txns = curr_txns.union(txns)
            self.ext_key2writes[k] = list(curr_txns)

    def get_num_edges(self):
        num_edges = 0
        for src, dst_nodes in self.edges.items():
            num_edges += len(dst_nodes)

        return num_edges

    def output2file(self, output_file_path):
        num_edges = 0
        with open(output_file_path, 'w') as f:
            f.write("n:%d\n" % self.n_nodes)
            for src, dst_nodes in self.edges.items():
                num_edges += len(dst_nodes)
                for dst, type in dst_nodes:
                    f.write("e:%d,%d,%s\n" % (src, dst, type))
            for ((src1, dst1, type1), (src2, dst2, type2)) in self.edge_pairs:
                f.write("p:(%d,%d,%s) (%d,%d,%s)\n" % (src1, dst1, type1, src2, dst2, type2))
        print("wrote PolyGraph into %s" % output_file_path)
        print("#nodes=%d" % self.n_nodes)
        print("#edges=%d" % num_edges)
        print("#edge pairs=%d" % len(self.edge_pairs))

    @classmethod
    def load_from_file(cls, graph_file):
        """
        can only load poly graph with edge types
        :param graph_file:
        :return:
        """
        print("load polygraph from %s" % graph_file)
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
                src, dst, type = cls.extract_edge(content[:-1])
                assert (src, dst, type) not in edges
                edges.add((src, dst, type))
            elif symbol == "p":
                edge1, edge2 = cls.extract_edge_pair(content[:-1])
                edge1, edge2 = cls._sort(edge1, edge2)
                edge_pairs.add((edge1, edge2))
            else:
                assert False, "Line = %s should never be here" % line

        if len(constraints) == 0:
            return n, list(edges), list(edge_pairs)
        else:
            return n, list(edges), list(edge_pairs), list(constraints)

    @classmethod
    def extract_edge(cls, edge):
        """
        e:0,386,wr
        """
        tokens = edge.split(",")
        assert len(tokens) == 3, "ill-format edge: src,dst,type"
        return int(tokens[0]), int(tokens[1]), tokens[2]

    @classmethod
    def extract_edge_pair(cls, edge_pair):
        """
        p:(3654,3658,ww) (3914,3654,rw)
        """
        (edge1, edge2) = edge_pair.split(' ')
        edge1 = cls.extract_edge(edge1[1:-1])
        # if edge2[-1] == '\n':
        #     edge2 = edge2[:-1]
        edge2 = cls.extract_edge(edge2[1:-1])
        return edge1, edge2

    @classmethod
    def _sort(cls, edge1, edge2):
        if edge2[0] < edge1[0] or \
                (edge2[0] == edge1[0] and edge2[1] < edge1[1]) \
                or (edge2[0] == edge1[0] and edge2[1] == edge1[1] and edge2[2] < edge1[2]):
            edge1, edge2 = edge2, edge1
        return edge1, edge2

    @classmethod
    def to_nx_graph(self, originalG: BCGraph):
        G = nx.DiGraph()
        G.add_nodes_from(range(1, 2*originalG.n_nodes+1))

        edge_list = []
        for src, dst_nodes in originalG.edges.items():
            for dst in dst_nodes:
                edge_list.append((src, dst))

        G.add_edges_from(edge_list)
        return G

    def topological_sort(self):
        """
        topoligical sort the known graph, ie. using only edges, don't use constraints
        """
        G = self.to_BC_graph()
        sorted_array = list(nx.topological_sort(G))

        nid2score = {}
        for i in range(len(sorted_array)):
            nid2score[sorted_array[i]] = i

        assert len(nid2score) == len(sorted_array)

        return nid2score, sorted_array

    def to_BC_graph(self):
        G = BCGraph(2 * self.n_nodes)

        for i in range(self.n_nodes):
            G.add_edge(si(i), ci(i))

        for src, dst_nodes in self.edges.items():
            for dst, type in dst_nodes:
                if type in ["wr", "ww", 'cb']:
                    G.add_edge(ci(src), si(dst))
                elif type == 'rw':
                    G.add_edge(si(src), ci(dst))
                else:
                    assert False

        return G

    def _my_to_BC_graph_w_session_order(self):
        G = BCGraph(2*self.n_nodes)

        for i in range(self.n_nodes):
            G.add_edge(si(i), ci(i))

        for src, dst_nodes in self.edges.items():
            for dst, type in dst_nodes:
                if type in ["wr", "ww", 'cb']:
                    G.add_edge(ci(src), si(dst))
                elif type == 'rw':
                    G.add_edge(si(src), ci(dst))
                else:
                    assert False
                # f.write("e:%d,%d,%s\n" % (src, dst, type))

        # session order
        assert self.histories is not None
        for tid in range(len(self.histories)):  # thread
            txns = self.histories[tid]
            for i in range(len(txns) - 1):
                G.add_edge(ci(txns[i]['id']), si(txns[i + 1]['id']))

        return G

    def my_topo_sort(self):
        G = self._my_to_BC_graph_w_session_order()

        in_degrees = {u: 0 for u in range(1, G.n_nodes+1)}
        for src in G.edges:
            for dst in G.edges[src]:
                in_degrees[dst] += 1

        Q = [u for u in range(1, G.n_nodes+1) if in_degrees[u] == 0]
        sorted_arr = [] # sorted begin/commit events

        while Q:
            u = Q.pop(0)
            sorted_arr.append(u)

            for v in G.edges[u]:
                in_degrees[v] -= 1
                if in_degrees[v] == 0:
                    Q.append(v)

        if len(sorted_arr) != G.n_nodes:
            G = self.to_BC_graph()
            in_degrees = {u: 0 for u in range(1, G.n_nodes + 1)}
            for src in G.edges:
                for dst in G.edges[src]:
                    in_degrees[dst] += 1

            Q = [u for u in range(1, G.n_nodes + 1) if in_degrees[u] == 0]
            sorted_arr = []

            while Q:
                u = Q.pop(0)
                sorted_arr.append(u)

                for v in G.edges[u]:
                    in_degrees[v] -= 1
                    if in_degrees[v] == 0:
                        Q.append(v)

            # assert len(sorted_arr) == G.n_nodes, "Mismatch: topological sort result vs G.n_nodes"
            if len(sorted_arr) != G.n_nodes:
                nxG = self.to_nx_graph(G)
                cycle = nx.find_cycle(nxG)
                print(f"found a cycle: {cycle} in known BCgraph")
                raise RejectException("")

        #
        nid2rank = {}
        for i in range(len(sorted_arr)):
            assert G.is_valid_node_id(sorted_arr[i])
            nid2rank[sorted_arr[i]] = i

        assert len(nid2rank) == len(sorted_arr)
        return nid2rank, sorted_arr

