SUBDIRS=(BlindW-RW-Cheng-100txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-13-00-14-26 \
BlindW-RW-Cheng-100txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-13-00-15-11 \
BlindW-RW-Cheng-100txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-13-00-15-56 \
BlindW-RW-Cheng-200txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-13-00-14-39 \
BlindW-RW-Cheng-200txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-13-00-15-24 \
BlindW-RW-Cheng-200txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-13-00-16-10 \
BlindW-RW-Cheng-400txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-13-00-14-53 \
BlindW-RW-Cheng-400txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-13-00-15-38 \
BlindW-RW-Cheng-400txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-13-00-16-24)

EXPNAMES=(100 100 100 200 200 200 400 400 400)

OUTPUT_FILE=fig13.txt
rm $OUTPUT_FILE

TIMEOUT=500s

for(( i=0;i<${#EXPNAMES[@]};i++)) do
# for i in "23"; do
    timeout $TIMEOUT python3.8 main_allcases.py --config_file config.yaml --algo 0 \
    --sub_dir heuristicOPT/${SUBDIRS[i]}/json \
    --perf_file $OUTPUT_FILE --exp_name Z3GSI_${EXPNAMES[i]} \
    --format json
done;

for(( i=0;i<${#EXPNAMES[@]};i++)) do
# for i in "23"; do
    timeout $TIMEOUT python3.8 main_allcases.py --config_file config.yaml --algo 9 \
    --sub_dir heuristicOPT/${SUBDIRS[i]}/json \
    --perf_file $OUTPUT_FILE --exp_name Z3GSI_HEU_${EXPNAMES[i]} \
    --format json
done;

for(( i=0;i<${#EXPNAMES[@]};i++)) do
# for i in "23"; do
    timeout $TIMEOUT python3.8 main_allcases.py --config_file config.yaml --algo 1 \
    --sub_dir heuristicOPT/${SUBDIRS[i]}/json \
    --perf_file $OUTPUT_FILE --exp_name Z3ASI_${EXPNAMES[i]} \
    --format json
done;

for(( i=0;i<${#EXPNAMES[@]};i++)) do
# for i in "23"; do
    timeout $TIMEOUT python3.8 main_allcases.py --config_file config.yaml --algo 10 \
    --sub_dir heuristicOPT/${SUBDIRS[i]}/json \
    --perf_file $OUTPUT_FILE --exp_name Z3ASI_HEU_${EXPNAMES[i]} \
    --format json
done;
