SUBDIRS=(BlindW-RW-Cheng-2000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-13-14-04-10 \
BlindW-RW-Cheng-5000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-12-13-05-17)

NAMES=(2k 5k)
EXAMPLES=(G1c G-SIb long_fork)

OUTPUT_FILE=fig15.txt
rm $OUTPUT_FILE

TIMEOUT=60s

# Viper
for(( j=0;j<${#SUBDIRS[@]};j++)) do
   for(( i=0;i<${#EXAMPLES[@]};i++)) do
# for i in "23"; do
      #  for (( k=4;k<7;k++)) do
           k=6
           timeout $TIMEOUT python3.8 main_allcases.py --config_file config.yaml --algo $k \
             --sub_dir buginjection/modified/${EXAMPLES[i]}/${SUBDIRS[j]}/json \
             --perf_file $OUTPUT_FILE --exp_name viper_${NAMES[j]}_${EXAMPLES[i]}_${k} \
             --format json
      #  done
   done;
done;

# elle
python3.8 ae/run_elle_bug_detection.py --log_folder $VIPER_HOME/history_data2/logs/buginjection/modified \
  --perf_file $OUTPUT_FILE --elle $VIPER_HOME/resources/elle-cli-0.1.3/target/elle-cli-0.1.3-standalone.jar
