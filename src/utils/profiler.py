import time
import json


class Profiler(object):
    _instance = None
    _counter = {}
    _start_time = {}
    _total_time = {}

    def __init__(self):
        raise RuntimeError('Call instance() instead')

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            # Put any initialization here.
        return cls._instance

    def startTick(cls, tag: str):
        assert isinstance(tag, str)
        if tag not in cls._counter:
            cls._counter[tag] = 0
            cls._total_time[tag] = 0

        if tag in cls._start_time:
            cls.endTick(tag)

        cur_time = time.time()
        cls._start_time[tag] = cur_time
        return cur_time

    def endTick(cls, tag:str):
        assert tag in cls._start_time
        cur_time = time.time()
        duration = cur_time - cls._start_time[tag]

        cls._total_time[tag] += duration
        cls._counter[tag] += 1

        del cls._start_time[tag]
        return cur_time

    def setSolveResult(cls, result:bool):
        cls._total_time["sat"] = result

    def dumpPerf(cls, exp_name, perf_file):
        tags = list(cls._start_time.keys())
        for tag in tags:
            cls.endTick(tag)
        print("=========================")
        for tag, duration in cls._total_time.items():
            if tag != "sat":
                print("%s: %.2f s" % (tag, duration))
            else:
                print("%s: %r" % (tag, duration))
        print("=========================")

        with open(perf_file, "a") as f:
            result_str = json.dumps({f"{exp_name}": cls._total_time})
            f.write(result_str + "\n")


