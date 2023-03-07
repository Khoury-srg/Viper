# we use this main function to handle all the cases, instead of create a main function for each case
from __future__ import print_function
import argparse
import os
import yaml

from algos.algo import get_algo
from algos.algo_entrances import main_algo3_5, main_algo_6_8_12, \
    main_algo_0_1_2_4, main_algo_0_1_2_heuristic
from utils.profiler import Profiler


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_file", type=str, default="config.yaml")
    parser.add_argument("--sub_dir", type=str)
    parser.add_argument("--perf_file", type=str, help="which file to store the perf results in for later figure "
                                                      "plotting")
    parser.add_argument("--exp_name", type=str, help="only for easier figure plotting")
    parser.add_argument("--algo", type=int, default=-1)
    parser.add_argument("--format", type=str, default="json", choices=["edn", "json"])
    parser.add_argument("--strong-session", action="store_true")
    parser.add_argument("--ww_order", action="store_true")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    if args.algo == 8 and args.format == "json":
        assert False, "ALGO 8 doesn't support json format"

    with open(args.config_file) as f:
        YAML_CONFIG = yaml.load(f, Loader=yaml.FullLoader)

    SUB_DIR = args.sub_dir
    ALGO = -1
    ALGO = YAML_CONFIG['ALGO'] if args.algo == -1 else args.algo
    graph_cls, checker_cls, graph_constructor = get_algo(ALGO)
    log_full_dir = os.path.join(YAML_CONFIG['LOG_DIR'], SUB_DIR)  # the dir which stores the logs and exported table files
    check_result_file = os.path.join(log_full_dir,
                                     "check_result.txt")  # after finishing checking, write the checking result into this file

    print("New run=======================================")
    print(f"Begin verifying {SUB_DIR} using ALGO {ALGO}, strong session = {args.strong_session}")
    profiler = Profiler.instance()
    profiler.startTick("e2e")

    if ALGO in [3, 5]:
        result = main_algo3_5(YAML_CONFIG, SUB_DIR, args, check_result_file, graph_cls, checker_cls,
                              graph_constructor, args.format)
    elif ALGO in [0, 1, 2, 4]:
        result = main_algo_0_1_2_4(YAML_CONFIG, SUB_DIR, args.strong_session, check_result_file, graph_cls, checker_cls,
                                   graph_constructor, args.format, ALGO, args.ww_order, args.debug)
    elif ALGO in [6, 8, 12]:
        result = main_algo_6_8_12(YAML_CONFIG, SUB_DIR, args, check_result_file, graph_cls, checker_cls, graph_constructor, args.format)
    elif ALGO in [9, 10, 11]:
        result = main_algo_0_1_2_heuristic(YAML_CONFIG, SUB_DIR, args, check_result_file,
                              graph_cls, checker_cls, graph_constructor, args.format, ALGO, args.ww_order)
    else:
        assert False, "Please provide a valid algo type"

    print(f"{SUB_DIR}: {result}", flush=True)
    profiler.endTick("e2e")
    profiler.setSolveResult(result)
    profiler.dumpPerf(args.exp_name, args.perf_file)
    print(f"End run {SUB_DIR} using ALGO {ALGO}, strong session = {args.strong_session}")
    print("=======================================")

