import time
from abc import ABC, abstractmethod

import monosat


class DirectChecker(ABC):
    def __init__(self):
        self.result = None
        self.t1 = self.t2 = self.t3 = None

    def output_result_file(self):
        if self.result is not None:
            sat = "SAT" if self.result else "UNSAT"
            # output to stdout
            print(sat)
            print(f"acyclic graph? [{str(self.result)}]: {self.output_file}")
            print("time cost: constraints: %.2f; solving: %.2f s" % ((self.t2 - self.t1), (self.t3 - self.t2)))
        else:
            print("result hasn't been got yet")

    @abstractmethod
    def check(self, n_nodes, edges, edge_pairs, min_key, max_key):
        pass

    # @abstractmethod
    # def debug(self, n_nodes, edges, edge_pairs, min_key, max_key, ext_writes):
    #     pass


class MonoSATSISSGDirectChecker(DirectChecker):
    """
    assume there is a read before each write, so we don't need to enforce a total order explicitly
    """
    name = "Snapshot isolation checker based on SSG method, assumeing ww order"

    def __init__(self, output_file):
        super(DirectChecker, self).__init__(output_file)

    def check(self, n_nodes, edges, edge_pairs, min_key, max_key):
        """
        edges: set
        """
        assert max_key >= min_key, "max_key should be greater than or equal to min_key"
        self.t1 = time.time()

        # full_dir = self.output_file[:self.output_file.index("/check")]
        # print(f"checking {full_dir}")
        print("MonoSAT Checking ... ")
        print("#nodes=%d" % n_nodes)
        print("#edges=%d" % len(edges))
        print("#edge pairs=%d" % len(edge_pairs))
        self.t1 = time.time()

        monosat.Monosat().newSolver()
        self.graph = monosat.Graph()
        # nodes = []
        for node in range(n_nodes):
            self.graph.addNode()
            # nodes.append(self.graph.addNode())

        for node_pair in edges:
            edge = self.graph.addEdge(*node_pair)
            # edge is just a symbolic edge, meaning that the edge is included in G iff edge is True, so we need to assert the edge is True in the following
            # edge = self.graph.addEdge(nodes[node_pair[0]], nodes[node_pair[1]])
            monosat.Assert(edge)

        for constraint in edge_pairs:
            e1 = self.graph.addEdge(*(constraint[0]))
            e2 = self.graph.addEdge(*(constraint[1]))
            # e1 = self.graph.addEdge(nodes[constraint[0][0]], nodes[constraint[0][1]])
            # e2 = self.graph.addEdge(nodes[constraint[1][0]], nodes[constraint[1][1]])
            monosat.Assert(monosat.And(monosat.Or(e1, e2), monosat.Or(monosat.Not(e1), monosat.Not(e2))))  # XOR
            # monosat.Assert(monosat.Xor(e1, e2))

        monosat.Assert(self.graph.acyclic())

        self.t2 = time.time()
        self.result = monosat.Solve()
        self.t3 = time.time()
        print(f"MonoSAT Checking Done: Time cost: {self.t3 - self.t2}; result= {self.result}")
        return self.result, self.t3 - self.t2

    def debug(self, n, edges, edge_pairs, min_key, max_key):
        """
        used for find the minimum subset of contraints which cannot be satisfied as the same time
        """
        assert max_key >= min_key, "max_key should be greater than or equal to min_key"
        solver = z3.Solver()
        assumptions = []

        v0, v1, v2 = z3.Ints('v0 v1 v2')
        # create relcations
        Rs = {}
        for key in range(min_key, max_key + 1):
            # each function R corresponds to a type of edges
            R = z3.Function('%d' % key, z3.IntSort(), z3.IntSort(), z3.BoolSort())
            Rs[key] = R
            # acyclic
            for i in range(n):
                assumptions.append(z3.Not(R(i, i)))

        for key in range(min_key, max_key + 1):
            R = Rs[key]
            # transitivity
            solver.add(z3.ForAll([v0, v1, v2], z3.Implies(z3.And(R(v0, v1), R(v1, v2)), R(v0, v2))))

            # edges
            if key in edges:
                for src, dst in edges[key]:
                    assumptions.append(R(src, dst))
            # edge pairs
            if key in edge_pairs:
                for ([src1, dst1], [src2, dst2]) in edge_pairs[key]:
                    assumptions.append(z3.Xor(R(src1, dst1), R(src2, dst2)))

        self.t2 = time.time()
        check_result = solver.check(*assumptions)
        self.t3 = time.time()

        self.result = True if check_result == z3.sat else False

        if not self.result:
            print("UNSAT: unsat_core:", solver.unsat_core())
        else:
            print("SAT")
        print(f"Checking duration: {self.t3 - self.t2}s")
        return self.result