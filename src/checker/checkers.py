from abc import ABCMeta, abstractmethod
import monosat
import z3
from utils.profiler import Profiler
from utils.utils import si, ci
from utils import utils

MONO_BV_WIDTH = 10


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


# algo 0: GSI+Z3
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

    def check(self, n_nodes, edges, edge_pairs):
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
            elif type1 in ['ww', 'wr', 'cb'] and type2 in ['ww', 'wr', 'cb']:
                assert src1 == dst2 and src2 == dst1 , "must be a pair of ww edges"
                solver.add(z3.Xor(R(ci(src1), si(dst1)), R(ci(dst1), (si(src1)))))
            else:  # both rw
                assert False

            # solver.add(z3.Xor(z3.R1(src1,dst1), z3.R2(src2, dst2)))
        # for k in ext_writes:
        #     k_ext_writes = ext_writes[k]
        #     for i in range(0, len(k_ext_writes)):
        #         for j in range(i + 1, len(k_ext_writes)):
        #             solver.add(z3.Xor(R(ci(i), si(j)), R(ci(j), (si(j)))))
        smt_nodes = list(range(si(0), ci(n_nodes) - 1))
        for i in smt_nodes:
            solver.add(z3.Not(R(i, i)))

        self.profiler.endTick("encoding")
        self.profiler.startTick("solving")
        check_result = solver.check()
        self.profiler.endTick("solving")

        self.result = True if check_result == z3.sat else False
        if not self.result:
            print("UNSAT")
        else:
            print("SAT")
            # model = solver.model()
            # smt_nodes = list(range(si(0), ci(n_nodes)-1))
            # for i in smt_nodes:
            #     for j in smt_nodes:
            #         if i != j and model.evaluate(R(i,j)):
            #             print(f"R({i}, {j}) = {model.evaluate(R(i,j))}")

        self.output_result_file()
        return self.result

# algo 1: ASI+Z3
class Z301Checker(Checker):
    def __init__(self, output_file):
        super(Z301Checker, self).__init__(output_file)
        self.graph = None

    def _create_time_deps(self, begin_timestamps, commit_timestamps, u, v, t):
        if t == 'rw':
            time_dep = begin_timestamps[u] < commit_timestamps[v]
        else:
            time_dep = commit_timestamps[u] < begin_timestamps[v]
        return time_dep

    def check(self, n, edges, edge_pairs, ext_writes=None):
        self.profiler.startTick("encoding")
        solver = z3.Solver()

        v0, v1, v2 = z3.Ints('v0 v1 v2')
        WRWW = z3.Function('WRWW', z3.IntSort(), z3.IntSort(), z3.BoolSort())
        RW = z3.Function('RW', z3.IntSort(), z3.IntSort(), z3.BoolSort())

        type2R = {
            'wr': WRWW,
            'ww': WRWW,
            'cb': WRWW,
            'rw': RW
        }

        # time preceding order
        bc_timestamps = []
        begin_timestamps = []
        commit_timestamps = []
        for i in range(n):
            bi = z3.Int("b%d" % i)
            ci = z3.Int("c%d" % i)
            solver.add(bi < ci)

            begin_timestamps.append(bi)
            commit_timestamps.append(ci)
            bc_timestamps.append(bi)
            bc_timestamps.append(ci)

        # timestamps total order
        solver.add(z3.Distinct(*bc_timestamps))

        # for R in Rs:
        # transitivity
        solver.add(z3.ForAll([v0, v1, v2], z3.Implies(z3.And(WRWW(v0, v1), WRWW(v1, v2)), WRWW(v0, v2))))

        # known edges
        for src, dst, t in edges:
            R = type2R[t]
            solver.add(R(src, dst))

            time_dep = self._create_time_deps(begin_timestamps, commit_timestamps, src, dst, t)
            solver.add(time_dep)

        # constraints
        for (src1, dst1, type1), (src2, dst2, type2) in edge_pairs:
            R1 = type2R[type1]
            R2 = type2R[type2]

            time_dep1 = self._create_time_deps(begin_timestamps, commit_timestamps, src1, dst1, type1)
            time_dep2 = self._create_time_deps(begin_timestamps, commit_timestamps, src2, dst2, type2)
            solver.add(z3.Xor(z3.And(R1(src1, dst1), time_dep1), z3.And(R2(src2, dst2), time_dep2)))
            # solver.add(z3.Xor(R1(src1, dst1), R2(src2, dst2)))

        # acyclic
        ## no cycles with no anti-dependency edges
        for i in range(n):
            solver.add(z3.Not(WRWW(i, i)))

        ## no cycles with exactly one anti-dependency edge
        for i in range(n):
            for j in range(i + 1, n):
                solver.add(z3.Not(z3.And(WRWW(i, j), RW(j, i))))

        if ext_writes is not None:
            for k in ext_writes:
                k_ext_writes = ext_writes[k]
                for i in range(0, len(k_ext_writes)):
                    for j in range(i + 1, len(k_ext_writes)):
                        solver.add(z3.Xor(WRWW(i, j), WRWW(j, i)))

        self.profiler.endTick("encoding")
        self.profiler.startTick("solving")
        check_result = solver.check()
        self.profiler.endTick("solving")

        self.result = True if check_result == z3.sat else False
        if not self.result:
            print("UNSAT")
        else:
            print("SAT")
        self.output_result_file()
        return self.result


# algo 2: ASI + Mono
class MonoSAT_EdgeWeightSIChecker(Checker):
    name = "MonoSAT_EdgeWeightSIChecker without optimizations"

    def __init__(self, output_file):
        super(MonoSAT_EdgeWeightSIChecker, self).__init__(output_file)

    def _create_time_deps(self, begin_timestamps, commit_timestamps, u, v, t):
        if t == 'rw':
            time_dep = begin_timestamps[u] < commit_timestamps[v]
        else:
            time_dep = commit_timestamps[u] < begin_timestamps[v]
        return time_dep

    def check(self, n_nodes, edges, edge_pairs, ext_writes=None):
        from monosat import Assert, BitVector, And, Xor, Not, Solve, Graph, Monosat
        print("Checking ... ")
        print("#nodes=%d" % n_nodes)
        print("#edges=%d" % len(edges))
        print("#edge pairs=%d" % len(edge_pairs))

        self.profiler.startTick("encoding")
        Monosat().newSolver()
        self.g = Graph()

        # assign edge weights by edge types.
        type2weight = {
            'wr': 0,
            'ww': 0,
            'cb': 0,
            'rw': 1
        }

        # time preceding order
        bc_timestamps = []
        begin_timestamps = []
        commit_timestamps = []
        for i in range(n_nodes):
            internal_nid = self.g.addNode()
            assert internal_nid == i

            bi = BitVector(MONO_BV_WIDTH)
            ci = BitVector(MONO_BV_WIDTH)
            Assert(bi < ci)

            begin_timestamps.append(bi)
            commit_timestamps.append(ci)
            bc_timestamps.append(bi)
            bc_timestamps.append(ci)

        # timestamps total order
        for i in range(len(bc_timestamps)):
            for j in range(i + 1, len(bc_timestamps)):
                # Assert(Xor(bc_timestamps[i] < bc_timestamps[j], bc_timestamps[i] > bc_timestamps[j]))
                Assert(bc_timestamps[i] != bc_timestamps[j])

        # time-precedes order should respect edges
        for src, dst, t in edges:
            assert src != dst
            e = self.g.addEdge(src, dst, type2weight[t])
            Assert(e)

            # time preceding order
            time_dep = self._create_time_deps(begin_timestamps, commit_timestamps, src, dst, t)
            Assert(time_dep)

        for (src1, dst1, type1), (src2, dst2, type2) in edge_pairs:
            assert src1 != dst1 and src2 != dst2
            e1 = self.g.addEdge(src1, dst1, type2weight[type1])
            e2 = self.g.addEdge(src2, dst2, type2weight[type2])
            # Assert(Xor(e1, e2))

            time_dep1 = self._create_time_deps(begin_timestamps, commit_timestamps, src1, dst1, type1)
            time_dep2 = self._create_time_deps(begin_timestamps, commit_timestamps, src2, dst2, type2)

            Assert(Xor(And(e1, time_dep1), And(e2, time_dep2)))

        if ext_writes is not None:
            for k in ext_writes:
                k_ext_writes = ext_writes[k]
                for i in range(0, len(k_ext_writes)):
                    for j in range(i + 1, len(k_ext_writes)):
                        e1 = self.g.addEdge(k_ext_writes[i], k_ext_writes[j], type2weight['ww'])
                        e2 = self.g.addEdge(k_ext_writes[j], k_ext_writes[i], type2weight['ww'])
                        Assert(Xor(e1, e2))

        for i in range(n_nodes - 1):
            for j in range(i + 1, n_nodes):
                Assert(Not(monosat.And(self.g.distance_leq(i, j, 0), self.g.distance_leq(j, i, 1))))
        # for i in range(n_nodes):
        #     # Assert(Not(self.g.reaches(i, i, 1)))
        #     Assert(Not(self.g.distance_leq(i, i, 1)))

        self.profiler.endTick("encoding")
        self.profiler.startTick("solving")
        self.result = Solve()
        self.profiler.endTick("solving")

        return self.result


# algo 3: ASI + MonoOpti
class MonoSAT_EdgeWeightSIChecker_Optimized(Checker):
    name = "Snapshot isolation checker based on edge weight without assuming ww order"

    def __init__(self, output_file):
        super(MonoSAT_EdgeWeightSIChecker_Optimized, self).__init__(output_file)

    def _create_time_deps(self, begin_timestamps, commit_timestamps, u, v, t):
        if t == 'rw':
            time_dep = begin_timestamps[u] < commit_timestamps[v]
        else:
            time_dep = commit_timestamps[u] < begin_timestamps[v]
        return time_dep

    def check(self, g, conn):
        from monosat import Assert, BitVector, And, Xor, Graph, Not, Solve
        print("Checking ... ")
        n_nodes = g.n_nodes
        print("#nodes=%d" % g.n_nodes)
        print("#edges=%d" % len(g.edges))
        print("#constraints=%d" % len(conn))
        self.profiler.startTick("encoding")
        monosat.Monosat().newSolver()
        G = Graph()

        # time preceding order
        bc_timestamps = []
        begin_timestamps = []
        commit_timestamps = []
        for i in range(n_nodes):
            internal_nid = G.addNode()
            assert internal_nid == i

            bi = BitVector(MONO_BV_WIDTH)
            ci = BitVector(MONO_BV_WIDTH)
            Assert(bi < ci)

            begin_timestamps.append(bi)
            commit_timestamps.append(ci)
            bc_timestamps.append(bi)
            bc_timestamps.append(ci)

        # timestamps total order
        for i in range(len(bc_timestamps)):
            for j in range(i + 1, len(bc_timestamps)):
                # Assert(Xor(bc_timestamps[i] < bc_timestamps[j], bc_timestamps[j] < bc_timestamps[i]))
                Assert(bc_timestamps[i] != bc_timestamps[j])

        type2weight = {
            'wr': 0,
            'ww': 0,
            'cb': 0,
            'rw': 1
        }

        for src in g.edges:
            for dst, t in g.edges[src]:
                e = G.addEdge(src, dst, type2weight[t])
                Assert(e)

                # time preceding order
                time_dep = self._create_time_deps(begin_timestamps, commit_timestamps, src, dst, t)
                Assert(time_dep)

        for es1, es2 in conn:
            e1, e2 = [], []

            for src, dst, t in es1:
                e1.append(G.addEdge(src, dst, type2weight[t]))
                # time preceding order
                time_dep1 = self._create_time_deps(begin_timestamps, commit_timestamps, src, dst, t)
            for src, dst, t in es2:
                e2.append(G.addEdge(src, dst, type2weight[t]))
                # time preceding order
                time_dep2 = self._create_time_deps(begin_timestamps, commit_timestamps, src, dst, t)

            # Assert(Xor(And(*e1), And(*e2)))
            Assert(Xor(And(*e1, time_dep1), And(*e2, time_dep2)))

        # for i in range(n_nodes):
        #     Assert(Not(G.distance_leq(i, i, 1)))
        for i in range(n_nodes - 1):
            for j in range(i + 1, n_nodes):
                # [cheng: I think we need "no 0-anti cycles" as well,
                #         which hasn't be captured by this line, no?]
                monosat.Assert(monosat.Not(monosat.And(G.distance_leq(i, j, 0), self.g.distance_leq(j, i, 1))))

        self.profiler.endTick("encoding")
        self.profiler.startTick("solving")
        self.result = Solve()
        self.profiler.endTick("solving")

        return self.result


# algo 4
class MonoBCPolyGraphChecker(Checker):
    name = 'MonoBCPolyGraphChecker Checker'
    description = 'BC PolyGraph Checker'

    def __init__(self, output_file=None):
        super(MonoBCPolyGraphChecker, self).__init__(output_file)
        self.graph = None
        print("Using MonoBCPolyGraphChecker:")

    def _si(self, i):
        return 2 * i - 1 if i != 0 else 0

    def _ci(self, i):
        return 2 * i if i != 0 else 0

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

    def check(self, n_nodes, edges, edge_pairs, ext_writes=None):
        from monosat import Assert, Xor, Solve, Graph
        print("MonoSAT Checking ... ")
        print("#transactions=%d" % n_nodes)
        print("#WW/RW/WR edges=%d" % len(edges))
        print("#constraints=%d" % len(edge_pairs))
        self.profiler.startTick("encoding")
        monosat.Monosat().newSolver()
        self.g = Graph()
        # nodes = []
        for i in range(n_nodes):
            internal_nid = self.g.addNode()  # si
            assert internal_nid == self._si(i)

            if i != 0:
                internal_nid = self.g.addNode()  # ci
                assert internal_nid == self._ci(i)
                e = self.g.addEdge(self._si(i), self._ci(i))
                Assert(e)

        for src, dst, type in edges:
            if type == 'rw':
                e = self.g.addEdge(self._si(src), self._ci(dst))
                Assert(e)
            elif type in ['wr', 'ww', 'cb']:
                e = self.g.addEdge(self._ci(src), self._si(dst))
                Assert(e)
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
            Assert(Xor(e1, e2))

        if ext_writes is not None:
            for k in ext_writes:
                k_ext_writes = ext_writes[k]
                for i in range(0, len(k_ext_writes)):
                    for j in range(i + 1, len(k_ext_writes)):
                        e1 = self.g.addEdge(self._ci(k_ext_writes[i]), self._si(k_ext_writes[j]))
                        e2 = self.g.addEdge(self._ci(k_ext_writes[j]), self._si(k_ext_writes[i]))
                        Assert(Xor(e1, e2))
                        # Assert(Xor(self.graph.reaches(ext_writes[i], ext_writes[j]),
                        #                            self.graph.reaches(ext_writes[j], ext_writes[i])))

        Assert(self.g.acyclic())

        self.profiler.endTick("encoding")
        self.profiler.startTick("solving")
        self.result = Solve()
        self.profiler.endTick("solving")
        return self.result

    def debug(self, n, edges, edge_pairs, ext_writes=None):
        def which_edge(R, src, dst, t):
            if t == 'rw':
                return R(utils.si(src), utils.ci(dst))
            elif t in ['wr', 'ww', 'cb']:
                return R(utils.ci(src), utils.si(dst))
            else:
                assert False

        def _add_edge(assumptions, R, src, dst, t):
            clause = which_edge(R, src, dst, t)
            assumptions.append(clause)

        solver = z3.Solver()
        # set_core_minimize(solver)

        assumptions = []

        v0, v1, v2 = z3.Ints('v0 v1 v2')
        # create relations
        R = z3.Function('R0', z3.IntSort(), z3.IntSort(), z3.BoolSort())

        # intra-deps
        for i in range(n):  # note this range limit is different from the one above
            assumptions.append(R(utils.si(i), utils.ci(i)))
        # acyclic
        for i in range(1, n * 2 + 1):
            assumptions.append(z3.Not(R(i, i)))

        # transitivity
        solver.add(z3.ForAll([v0, v1, v2], z3.Implies(z3.And(R(v0, v1), R(v1, v2)), R(v0, v2))))

        # edges
        for src, dst, t in edges:
            _add_edge(assumptions, R, src, dst, t)

        # edge pairs
        for ([src1, dst1, t1], [src2, dst2, t2]) in edge_pairs:
            e1 = which_edge(R, src1, dst1, t1)
            e2 = which_edge(R, src2, dst2, t2)
            assumptions.append(z3.Xor(e1, e2))

        # ww total order
        if ext_writes is not None:
            for k in ext_writes:
                k_ext_writes = ext_writes[k]
                for i in range(0, len(k_ext_writes)):
                    for j in range(i + 1, len(k_ext_writes)):
                        e1 = which_edge(R, utils.ci(k_ext_writes[i]), utils.si(k_ext_writes[j]), 'ww')
                        e2 = which_edge(R, utils.ci(k_ext_writes[j]), utils.si(k_ext_writes[i]), 'ww')
                        assumptions.append(z3.Xor(e1, e2))

        check_result = solver.check(*assumptions)

        self.result = True if check_result == z3.sat else False

        if not self.result:
            print("UNSAT: unsat_core:", solver.unsat_core())
        else:
            print("SAT")
        return self.result


# algo 5, 6: Viper
class MonoBCPolyGraphCheckerOptimized(Checker):
    name = ""

    def __init__(self, output_file="MonoBCPolyGraphCheckerOptimized.log"):
        super(MonoBCPolyGraphCheckerOptimized, self).__init__(output_file)

    def _si(self, i):
        return 2 * i - 1 if i != 0 else 0

    def _ci(self, i):
        return 2 * i if i != 0 else 0

    def check(self, g, con):
        from monosat import Assert, And, Xor, Solve, Graph

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

        monosat.Monosat().newSolver()  # TODO: if without this, solver cache make it False?
        G = Graph()
        for i in range(g.n_nodes):
            internal_nid = G.addNode()  # si
            assert internal_nid == self._si(i)

            if i != 0:
                internal_nid = G.addNode()  # ci
                assert internal_nid == self._ci(i)
                e = G.addEdge(self._si(i), self._ci(i))
                Assert(e)

        n_edges = 0
        for src in g.edges:
            for dst, type in g.edges[src]:
                e = _add_edge(G, src, dst, type)
                n_edges += 1
                Assert(e)

        for es1, es2 in con:  # edge set 1,
            e1, e2 = [], []
            for src, dst, type in es1:
                e1.append(_add_edge(G, src, dst, type))
            for src, dst, type in es2:
                e2.append(_add_edge(G, src, dst, type))

            Assert(Xor(And(*e1), And(*e2)))

        Assert(G.acyclic())
        self.profiler.endTick("encoding")

        print("Checking ... ")
        print("#nodes=%d" % g.n_nodes)
        print("#edges=%d" % n_edges)
        print("#constraints=%d" % len(con))

        self.profiler.startTick("solving")
        self.result = Solve()
        self.profiler.endTick("solving")

        return self.result
