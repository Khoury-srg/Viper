import glob
import os.path
import shutil
import subprocess
import time
import argparse
import json

SUBDIRS=["cheng_normal-Cheng-100txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-17-50"
#     ,
# "cheng_normal-Cheng-200txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-18-02",
# "cheng_normal-Cheng-400txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-18-17",
# "cheng_normal-Cheng-600txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-18-33",
# "cheng_normal-Cheng-800txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-18-53",
# "cheng_normal-Cheng-1000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-19-14"
         ]

EXPNAMES=[100, 200, 400, 800, 1000]
TIMEOUT=180


def call_with_timeout(cmd, log_dir, algo):
    print(f"Executing {' '.join(cmd)}")
    try:
        subprocess.run(cmd, stderr=subprocess.STDOUT, timeout=TIMEOUT)
    except subprocess.TimeoutExpired as e:
        print(f"{log_dir} using {algo} timeouts")
        print(e)


def run_BE19(dbcop_path, translator_path, log_folder, output_folder):
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    for exp_dir in SUBDIRS:
        curr_exp_output_dir = os.path.join(output_folder, exp_dir)
        if not os.path.exists(curr_exp_output_dir):
            os.mkdir(curr_exp_output_dir)
        cobra_log_dir = os.path.join(log_folder, exp_dir, "log")  #
        BE19_log_dir = os.path.join(log_folder, exp_dir, "BE19")
        
        BE19_output_dir = os.path.join(output_folder, exp_dir, "output_dir")
        BE19_output_dir_sat = os.path.join(output_folder, exp_dir, "output_sat_dir")
        print(f"cobra_log_dir={cobra_log_dir}, BE19_log_dir={BE19_log_dir}, \
            BE19_output_dir={BE19_output_dir}, BE19_output_dir_sat={BE19_output_dir_sat}")

        # translate histories
        if not os.path.exists(BE19_log_dir):
            os.mkdir(BE19_log_dir)
        # subprocess.run([translator_path, cobra_log_dir, BE19_log_dir],
        #     capture_output=True)

        # checking
        if not os.path.exists(BE19_output_dir):
            os.mkdir(BE19_output_dir)
        if not os.path.exists(BE19_output_dir_sat):
            os.mkdir(BE19_output_dir_sat)

        # OLD_DBCOP="/home/windkl/git_repos/CobraHome/CobraVerifier/bsl/BE19/dbcop-master/target/debug/dbcop"
        NEW_DBCOP = dbcop_path
        cmd = [NEW_DBCOP, "verify", "--cons", "si",
                            "--out_dir", BE19_output_dir,
                            "--ver_dir", BE19_log_dir]
        call_with_timeout(cmd, BE19_log_dir, "BE19")

        cmd = [NEW_DBCOP, "verify", "--cons", "si",
                            "--out_dir", BE19_output_dir_sat,
                            "--ver_dir", BE19_log_dir, "--sat"]
        call_with_timeout(cmd, BE19_log_dir, "BE19-sat")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--log_folder", type=str)
    parser.add_argument("--output_folder", type=str)
    parser.add_argument("--dbcop", type=str, help="the path of the executable dbcop")
    parser.add_argument("--translator", type=str, help="the path of the executable translator")
    args = parser.parse_args()
    run_BE19(args.dbcop, args.translator, args.log_folder, args.output_folder)
    print("Done.")
        
        