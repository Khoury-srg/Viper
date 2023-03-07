import glob
import os.path
import shutil
import subprocess
import time
import argparse
import json

SUBDIRS=['10s-20220518T161953.000Z', '20s-20220518T162041.000Z', '30s-20220518T162141.000Z', '40s-20220518T162252.000Z', '50s-20220518T162416.000Z', \
    '60s-20220518T162551.000Z', '70s-20220518T162740.000Z', '80s-20220518T162938.000Z', '90s-20220518T163152.000Z', '100s-20220518T163417.000Z', \
    '110s-20220518T163652.000Z', '120s-20220518T163939.000Z', '130s-20220518T164242.000Z', '140s-20220518T164556.000Z']   
    
EXPNAMES=list(range(10, 141, 10))

TIMEOUT=60

def call_with_timeout(cmd, log_dir, algo):
    print(f"Executing {' '.join(cmd)}")
    try:
        subprocess.run(cmd, stderr=subprocess.STDOUT, timeout=TIMEOUT)
    except subprocess.TimeoutExpired as e:
        print(f"{log_dir} using {algo} timeouts")
        print(e)


def elle(log_folder, output_file, elle_path):
    perf_rs = []
    for exp_dir in SUBDIRS:  # 10s-20220518T161953.000Z
        log_path = os.path.join(log_folder, exp_dir, "history.edn")
        print(f"log_folder={log_folder}, exp_dir={exp_dir}, log_path={log_path}")
        cmd = ["java", "-jar", elle_path, "--model", "list-append", "-f", "edn",
                   log_path, "-c", "snapshot-isolation"]
        t1 = time.time()
        call_with_timeout(cmd, exp_dir, "elle")
        t2 = time.time()
        dur = t2 - t1
        print(f"elle {log_path} consumes {dur}s")
        perf_rs.append(dur)

        # exp_name = exp_dir[:exp_dir.index('-')]
    with open(output_file, "a") as f:
        result_str = json.dumps({"elle": perf_rs})
        f.write(result_str + "\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--log_folder", type=str, default="config.ini")
    parser.add_argument("--perf_file", type=str, help="which file to store the performance results in for later figure plotting")
    parser.add_argument("--elle", type=str, help="the path of the elle-cli jar")
    args = parser.parse_args()
    elle(args.log_folder, args.perf_file, args.elle)
        
        