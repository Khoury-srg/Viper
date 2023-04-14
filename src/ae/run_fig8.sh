SUBDIRS=(
cheng_normal-Cheng-100txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-17-50 \
cheng_normal-Cheng-200txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-18-02 \
cheng_normal-Cheng-400txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-18-17 \
cheng_normal-Cheng-600txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-18-33 \
cheng_normal-Cheng-800txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-18-53 \
cheng_normal-Cheng-1000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-19-14   \
cheng_normal-Cheng-1500txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-19-39   \
cheng_normal-Cheng-2000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-20-11 \
cheng_normal-Cheng-2500txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-20-49 \
cheng_normal-Cheng-3000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-21-34 \
cheng_normal-Cheng-3500txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-22-25  \
cheng_normal-Cheng-4000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-23-21  \
cheng_normal-Cheng-4500txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-24-25  \
cheng_normal-Cheng-5000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-25-36 
#cheng_normal-Cheng-5500txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-26-51 \
#cheng_normal-Cheng-6000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-28-14 \
#cheng_normal-Cheng-6500txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-29-44 \
#cheng_normal-Cheng-7000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-31-22 \
#cheng_normal-Cheng-7500txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-33-04 \
#cheng_normal-Cheng-8000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-34-53
#cheng_normal-Cheng-8500txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-36-47 \
#cheng_normal-Cheng-9000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-38-48 \
#cheng_normal-Cheng-9500txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-40-56\
# cheng_normal-Cheng-10000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-43-10 \
)

EXAMPLES=(
100 200 400 600 800 1000 1500 2000 2500 3000 3500 4000 4500 5000 \
# 5500 6000 6500 7000 7500 8000 8500 9000 9500 10000
)

OUTPUT_FILE=fig8.txt
rm $OUTPUT_FILE

TIMEOUT=7200s

# Viper
for(( i=0;i<${#EXAMPLES[@]};i++)) do
# for i in "23"; do
    timeout $TIMEOUT python3.8 main_allcases.py --config_file config.yaml --algo 6 \
    --sub_dir fig8/${SUBDIRS[i]}/json \
    --perf_file $OUTPUT_FILE --exp_name viper_${EXAMPLES[i]} \
    --format json
done;
#
## GSI_Z3
## for(( i=0;i<${#EXAMPLES[@]};i++)) do
#for(( i=0;i<5;i++)) do
#    timeout $TIMEOUT python3.8 main_allcases.py --config_file config.yaml --algo 0 \
#    --sub_dir fig8/${SUBDIRS[i]}/json \
#    --perf_file $OUTPUT_FILE --exp_name gsiz3_${EXAMPLES[i]} \
#    --format json
#done;
#
## ASI_Z3
## for(( i=0;i<${#EXAMPLES[@]};i++)) do
#for(( i=0;i<5;i++)) do
#    timeout $TIMEOUT python3.8 main_allcases.py --config_file config.yaml --algo 1 \
#    --sub_dir fig8/${SUBDIRS[i]}/json \
#    --perf_file $OUTPUT_FILE --exp_name asiz3_${EXAMPLES[i]} \
#    --format json
#done;

# Z3 ASI + ww order
#for(( i=0;i<5;i++)) do
#    timeout $TIMEOUT python3.8 main_allcases.py --config_file config.yaml --algo 1 \
#    --sub_dir fig8/${SUBDIRS[i]}/json \
#    --perf_file $OUTPUT_FILE --exp_name asiz3W_${EXAMPLES[i]} \
#    --format json --ww_order
#done;

# ASI_Mono
#for(( i=0;i<${#EXAMPLES[@]};i++)) do
#for(( i=0;i<5;i++)) do
#    timeout $TIMEOUT python3.8 main_allcases.py --config_file config.yaml --algo 2 \
#    --sub_dir fig8/${SUBDIRS[i]}/json \
#    --perf_file $OUTPUT_FILE --exp_name asimono_${EXAMPLES[i]} \
#    --format json
#done;
#
## ASI_Mono + ww order
## for(( i=0;i<${#EXAMPLES[@]};i++)) do
#for(( i=0;i<5;i++)) do
#    timeout $TIMEOUT python3.8 main_allcases.py --config_file config.yaml --algo 2 \
#    --sub_dir fig8/${SUBDIRS[i]}/json \
#    --perf_file $OUTPUT_FILE --exp_name asimonoW_${EXAMPLES[i]} \
#    --format json --ww_order
#done;
#
## ASI_Mono_Optimized
## for(( i=0;i<${#EXAMPLES[@]};i++)) do
#for(( i=0;i<5;i++)) do
#    timeout $TIMEOUT python3.8 main_allcases.py --config_file config.yaml --algo 3 \
#    --sub_dir fig8/${SUBDIRS[i]}/json \
#    --perf_file $OUTPUT_FILE --exp_name asimonoo_${EXAMPLES[i]} \
#    --format json
#done;

