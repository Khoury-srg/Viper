import glob
import os.path
import shutil
import subprocess
import time
import argparse
import json

SUBDIRS=["BlindW-RW-Cheng-2000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-13-14-04-10",
         "BlindW-RW-Cheng-5000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-12-13-05-17"]

SIZES=["2k", "5k"]
EXAMPLES=["G1c", "G-SIb", "long_fork"]

TIMEOUT = 60


def call_with_timeout(cmd, log_dir, algo):
    print(f"Executing {' '.join(cmd)}")
    try:
        subprocess.run(cmd, stderr=subprocess.STDOUT, timeout=TIMEOUT)
    except subprocess.TimeoutExpired as e:
        print(f"{log_dir} using {algo} timeouts")
        print(e)


def elle(log_folder, output_file, elle_path):
    perf_rs = {}
    for i, exp_dir in enumerate(SUBDIRS):  # 10s-20220518T161953.000Z
        for anomaly in EXAMPLES:
            exp_name = f"Elle_{SIZES[i]}_{anomaly}"
            log_path = os.path.join(log_folder, anomaly, exp_dir, "jepsen", "history.edn")
            print(f"log_folder={log_folder}, exp_dir={exp_dir}, log_path={log_path}")
            cmd = ["java", "-jar", elle_path, "--model", "rw-register", "-f", "edn",
                   log_path, "-c", "snapshot-isolation"]
            t1 = time.time()
            call_with_timeout(cmd, exp_dir, "elle")
            t2 = time.time()
            dur = t2 - t1
            print(f"elle {log_path} consumes {dur}s")
            perf_rs[exp_name] = dur
    with open(output_file, "a") as f:
        result_str = json.dumps(perf_rs)
        f.write(result_str + "\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--log_folder", type=str)
    parser.add_argument("--perf_file", type=str,
                        help="which file to store the performance results in for later figure plotting")
    parser.add_argument("--elle", type=str, help="the path of the elle-cli jar")
    args = parser.parse_args()
    elle(args.log_folder, args.perf_file, args.elle)

