import sys
import time
from abc import ABCMeta, abstractmethod
import monosat
import z3
from cobraplus_backend.cobraplus.utils.profiler import Profiler
from cobraplus_backend.cobraplus.utils.utils import si, ci


class Checker(metaclass=ABCMeta):
    def __init__(self, output_file):
        self.output_file = output_file
        self.result = None
        self.profiler = Profiler.instance()

    def output_result_file(self):
        pass


class PolyGraphChecker(Checker):
    @abstractmethod
    def check(self, n, edges, edge_pairs, disable_uncertainty=False):
        pass


class MonoBCPolyGraphChecker(Checker):
    name = 'MonoBCPolyGraphChecker Checker'
    description = 'BC PolyGraph Checker'

    def __init__(self, output_file=None):
        super(MonoBCPolyGraphChecker, self).__init__(output_file)
        self.graph = None
        print("Using MonoBCPolyGraphChecker:")

    def _si(self, i):
        return 2*i

    def _ci(self, i):
        return 2*i + 1

    def _add_edge(self, src, dst, type):
        e = None
        if type == 'rw':
            e = self.g.addEdge(self._si(src), self._ci(dst))
        elif type in ['wr', 'ww', 'cb']:
            e = self.g.addEdge(self._ci(src), self._si(dst))
        else:
            assert False
        assert e is not None
        return e

    def check(self, n_nodes, edges, edge_pairs, ext_writes = None):
        print("MonoSAT Checking ... ")
        print("#transactions=%d" % n_nodes)
        print("#WW/RW/WR edges=%d" % len(edges))
        print("#constraints=%d" % len(edge_pairs))
        self.profiler.startTick("encoding")

        monosat.Monosat().newSolver()
        self.g = monosat.Graph()
        # nodes = []
        for i in range(n_nodes):
            internal_nid = self.g.addNode(self._si(i)) # si
            assert internal_nid == self._si(i)
            internal_nid = self.g.addNode(self._ci(i)) # ci
            assert internal_nid == self._ci(i)
            e = self.g.addEdge(self._si(i), self._ci(i))
            monosat.Assert(e)

        for src, dst, type in edges:
            if type == 'rw':
                e = self.g.addEdge(self._si(src), self._ci(dst))
                monosat.Assert(e)
            elif type in ['wr', 'ww', 'cb']:
                e = self.g.addEdge(self._ci(src), self._si(dst))
                monosat.Assert(e)
            else:
                assert False

        for (src1, dst1, type1), (src2, dst2, type2) in edge_pairs:
            if type1 == 'rw':
                e1 = self.g.addEdge(self._si(src1), self._ci(dst1))
            elif type1 in ['wr', 'ww', 'cb']:
                e1 = self.g.addEdge(self._ci(src1), self._si(dst1))
            else:
                assert False

            if type2 == 'rw':
                e2 = self.g.addEdge(self._si(src2), self._ci(dst2))
            elif type2 in ['wr', 'ww', 'cb']:
                e2 = self.g.addEdge(self._ci(src2), self._si(dst2))
            else:
                assert False

            assert e1 is not None and e2 is not None
            monosat.Assert(monosat.Xor(e1, e2))

        if ext_writes is not None:
            for k in ext_writes:
                k_ext_writes = ext_writes[k]
                for i in range(0, len(k_ext_writes)):
                    for j in range(i + 1, len(k_ext_writes)):
                        e1 = self.g.addEdge(self._ci(k_ext_writes[i]), self._si(k_ext_writes[j]))
                        e2 = self.g.addEdge(self._ci(k_ext_writes[j]), self._si(k_ext_writes[i]))
                        monosat.Assert(monosat.Xor(e1, e2))
                        # monosat.Assert(monosat.Xor(self.graph.reaches(ext_writes[i], ext_writes[j]),
                        #                            self.graph.reaches(ext_writes[j], ext_writes[i])))

        monosat.Assert(self.g.acyclic())

        self.profiler.endTick("encoding")
        self.profiler.startTick("solving")
        self.result = monosat.Solve()
        self.profiler.endTick("solving")
        return self.result

    def debug(self, n, edges, edge_pairs):
        pass


class MonoBCPolyGraphCheckerOptimized(Checker):
    name = ""

    def __init__(self, output_file="MonoBCPolyGraphCheckerOptimized.log"):
        super(MonoBCPolyGraphCheckerOptimized, self).__init__(output_file)

    def _si(self, i):
        return 2*i

    def _ci(self, i):
        return 2*i + 1

    def check(self, g, con):
        def _add_edge(G, src, dst, type):
            if type == 'rw':
                e = G.addEdge(self._si(src), self._ci(dst))
            elif type in ['wr', 'ww', 'cb']:
                e = G.addEdge(self._ci(src), self._si(dst))
            else:
                assert False
            return e

        print("Checking ... ")
        # print("#nodes=%d" % g.n_nodes)
        # print("#edges=%d" % len(g.edges))
        # print("#constraints=%d" % len(con))

        self.profiler.startTick("encoding")

        monosat.Monosat().newSolver() # TODO: if without this, solver cache make it False?
        G = monosat.Graph()
        for i in range(g.n_nodes):
            si_ = G.addNode(self._si(i))  # si
            ci_ = G.addNode(self._ci(i))  # ci
            assert si_ == self._si(i) and ci_ == self._ci(i)

            e = G.addEdge(si_, ci_)
            monosat.Assert(e)

        n_edges = 0
        for src in g.edges:
            for dst, type in g.edges[src]:
                e = _add_edge(G, src, dst, type)
                n_edges += 1
                monosat.Assert(e)

        for es1, es2 in con: # edge set 1,
            e1, e2 = [], []
            for src, dst, type in es1:
                e1.append(_add_edge(G, src, dst, type))
            for src, dst, type in es2:
                e2.append(_add_edge(G, src, dst, type))

            monosat.Assert(monosat.Xor(monosat.And(*e1), monosat.And(*e2)))

        monosat.Assert(G.acyclic())
        self.profiler.endTick("encoding")

        print("Checking ... ")
        print("#nodes=%d" % g.n_nodes)
        print("#edges=%d" % n_edges)
        print("#constraints=%d" % len(con))

        self.profiler.startTick("solving")
        self.result = monosat.Solve()
        self.profiler.endTick("solving")

        return self.result


# algo ASI+Z3
class Z301Checker(Checker):
    def __init__(self, output_file):
        super(Z301Checker, self).__init__(output_file)
        self.graph = None

    def debug(self, n, edges, edge_pairs):
        pass

    def check(self, n, edges, edge_pairs):
        self.profiler.startTick("encoding")
        solver = z3.Solver()

        v0, v1, v2 = z3.Ints('v0 v1 v2')
        Rs = []
        WRWW = z3.Function('0', z3.IntSort(), z3.IntSort(), z3.BoolSort())
        RW = z3.Function('1', z3.IntSort(), z3.IntSort(), z3.BoolSort())
        Rs.append(WRWW)
        Rs.append(RW)

        # solver.add(z3.ForAll([v0, v1], z3.Implies(WRWW(v0,v1), R_all(v0, v1))))
        # solver.add(z3.ForAll([v0, v1], z3.Implies(RW(v0,v1), R_all(v0, v1))))

        type2R = {
            'wr': WRWW,
            'ww': WRWW,
            'cb': WRWW,
            'rw': RW
        }

        # for R in Rs:
        # transitivity
        solver.add(z3.ForAll([v0, v1, v2], z3.Implies(z3.And(WRWW(v0, v1), WRWW(v1, v2)), WRWW(v0, v2))))
        # solver.add(z3.ForAll([v0, v1, v2], z3.Implies(z3.And(R(v0, v1), R(v1, v2)), R(v0, v2))))

        for src, dst, t in edges:
            R = type2R[t]
            solver.add(R(src, dst))

        for (src1, dst1, type1), (src2, dst2, type2) in edge_pairs:
            R1 = type2R[type1]
            R2 = type2R[type2]
            solver.add(z3.Xor(R1(src1,dst1), R2(src2, dst2)))
            # solver.add(z3.Xor(z3.R1(src1,dst1), z3.R2(src2, dst2)))

        # acyclic
        for i in range(n):
            solver.add(z3.Not(WRWW(i, i)))
            # solver.add(z3.Not(WRWW(i, i)))
        for i in range(n):
            for j in range(i + 1, n):
                solver.add(z3.Not(z3.And(WRWW(i, j), RW(j, i))))
                # solver.add(z3.Not(z3.And(z3.WRWW(i,j), z3.RW(j,i))))

        self.profiler.endTick("encoding")
        self.profiler.startTick("solving")
        check_result = solver.check()
        self.profiler.endTick("solving")

        self.result = True if check_result == z3.sat else False
        if not self.result:
            print("UNSAT: unsat_core:", solver.unsat_core())
        else:
            print("SAT")
        self.output_result_file()
        return self.result


# algo GSI+Z3
class Z3GeneralSIChecker(Checker):
    def __init__(self, output_file):
        super(Z3GeneralSIChecker, self).__init__(output_file)

    def _add_edge(self, solver, R, src, dst, type):
        if type in ['wr', 'ww', 'cb']:
            solver.add(R(ci(src), si(dst)))
        elif type == 'rw':
            solver.add(R(si(src), ci(dst)))
        else:
            assert False

    def check(self, n_nodes, edges, edge_pairs, ext_writes=None):
        self.profiler.startTick("encoding")
        solver = z3.Solver()

        v0, v1, v2 = z3.Ints('v0 v1 v2')
        R = z3.Function('R', z3.IntSort(), z3.IntSort(), z3.BoolSort())

        for i in range(n_nodes):
            solver.add(R(si(i), ci(i)))

        # for R in Rs:
        # transitivity
        solver.add(z3.ForAll([v0, v1, v2],
                             z3.Implies(z3.And(R(v0, v1), R(v1, v2)), R(v0, v2))))

        for src, dst, type in edges:
            self._add_edge(solver, R, src, dst, type)

        for (src1, dst1, type1), (src2, dst2, type2) in edge_pairs:
            if type1 in ['ww', 'wr', 'cb'] and type2 == 'rw':
                solver.add(z3.Xor(R(ci(src1), ci(dst1)), R(si(src2), ci(dst2))))
            elif type2 in ['ww', 'wr', 'cb'] and type1 == 'rw':
                solver.add(z3.Xor(R(ci(src2), ci(dst2)), R(si(src1), ci(dst1))))
            elif type1 in ['ww', 'wr', 'cb'] and type1 in ['ww', 'wr', 'cb']:
                assert False
            else: # both rw
                assert False

            # solver.add(z3.Xor(z3.R1(src1,dst1), z3.R2(src2, dst2)))
        for k in ext_writes:
            k_ext_writes = ext_writes[k]
            for i in range(0, len(k_ext_writes)):
                for j in range(i + 1, len(k_ext_writes)):
                    solver.add(z3.Xor(R(ci(i), si(j)), R(ci(j), (si(j)))))

        self.profiler.endTick("encoding")
        self.profiler.startTick("solving")
        check_result = solver.check()
        self.profiler.endTick("solving")

        self.result = True if check_result == z3.sat else False
        if not self.result:
            print("UNSAT: unsat_core:", solver.unsat_core())
        else:
            print("SAT")
        self.output_result_file()
        return self.result


# ASI + Mono
class MonoSAT_EdgeWeightSIChecker(Checker):
    name = "MonoSAT_EdgeWeightSIChecker without optimizations"

    def __init__(self, output_file):
        super(MonoSAT_EdgeWeightSIChecker, self).__init__(output_file)

    def debug_mono(self, n_nodes, edges, edge_pairs):
        pass

    def check(self, n_nodes, edges, edge_pairs):
        print("Checking ... ")
        print("#nodes=%d" % n_nodes)
        print("#edges=%d" % len(edges))
        print("#edge pairs=%d" % len(edge_pairs))

        self.profiler.startTick("encoding")
        # monosat.Monosat().newSolver()
        self.g = monosat.Graph()
        for i in range(n_nodes):
            internal_nid = self.g.addNode(i)
            assert internal_nid == i

        type2weight = {
            'wr': 0,
            'ww': 0,
            'cb': 0,
            'rw': 1
        }

        for src, dst, type in edges:
            e = self.g.addEdge(src, dst, type2weight[type])
            monosat.Assert(e)

        for (src1, dst1, type1), (src2, dst2, type2) in edge_pairs:
            # bv1 = monosat.BitVector(type2weight[type1])
            # bv2 = monosat.BitVector(type2weight[type2])
            e1 = self.g.addEdge(src1, dst1, type2weight[type1])
            e2 = self.g.addEdge(src2, dst2, type2weight[type2])
            monosat.Assert(monosat.Xor(e1, e2))

        for i in range(n_nodes-1):
            for j in range(i + 1, n_nodes):
                # [cheng: I think we need "no 0-anti cycles" as well,
                #         which hasn't be captured by this line, no?]
                monosat.Assert(monosat.Not(monosat.And(self.g.distance_leq(i, j, 0), self.g.distance_leq(j, i, 1))))

        self.profiler.endTick("encoding")
        self.profiler.startTick("solving")
        self.result = monosat.Solve()
        self.profiler.endTick("solving")

        return self.result


# ASI + MonoOpti
class MonoSAT_EdgeWeightSIChecker_Optimized(Checker):
    name = "Snapshot isolation checker based on edge weight without assuming ww order"

    def __init__(self, output_file):
        super(MonoSAT_EdgeWeightSIChecker_Optimized, self).__init__(output_file)

    def check(self, g, con):
        print("Checking ... ")
        print("#nodes=%d" % g.n_nodes)
        print("#edges=%d" % len(g.edges))
        print("#constraints=%d" % len(con))
        self.profiler.startTick("encoding")

        monosat.Monosat().newSolver()
        G = monosat.Graph()
        for i in range(g.n_nodes):
            internal_nid = G.addNode(i)
            assert internal_nid == i

        type2weight = {
            'wr': 0,
            'ww': 0,
            'cb': 0,
            'rw': 1
        }
        for src in g.edges:
            for dst, type in g.edges[src]:
                e = G.addEdge(src, dst, type2weight[type])
                monosat.Assert(e)

        for es1, es2 in con:
            e1, e2 = [], []
            for src, dst, type in es1: # TODO: FIXME, type?
                e1.append(G.addEdge(src, dst, type2weight[type]))
            for src, dst, type in es2:
                e2.append(G.addEdge(src, dst, type2weight[type]))

            monosat.Assert(monosat.Xor(monosat.And(*e1), monosat.And(*e2)))

        for i in range(g.n_nodes-1):
            for j in range(i + 1, g.n_nodes):
                monosat.Assert(monosat.Not(monosat.And(G.distance_leq(i, j, 0), G.distance_leq(j, i, 1))))
        self.profiler.endTick("encoding")
        self.profiler.startTick("solving")
        self.result = monosat.Solve()
        self.profiler.endTick("solving")

        return self.result
