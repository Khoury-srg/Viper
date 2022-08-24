SUBDIRS=(cheng_normal-Cheng-100txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-05-18-13-26-47 cheng_normal-Cheng-200txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-05-18-13-26-58 \
    cheng_normal-Cheng-400txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-05-18-13-27-08  cheng_normal-Cheng-600txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-05-18-13-27-21     \
    cheng_normal-Cheng-800txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-05-18-13-27-35  cheng_normal-Cheng-1000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-05-18-13-27-51    \
    cheng_normal-Cheng-1500txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-05-18-13-28-09 cheng_normal-Cheng-2000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-05-18-13-28-30    \
    cheng_normal-Cheng-2500txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-05-18-13-28-58 cheng_normal-Cheng-3000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-05-18-13-29-29    \
    cheng_normal-Cheng-3500txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-05-18-13-30-02 cheng_normal-Cheng-4000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-05-18-13-30-41    \
    cheng_normal-Cheng-4500txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-05-18-13-31-24 cheng_normal-Cheng-5000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-05-18-13-32-11    \
    cheng_normal-Cheng-5500txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-05-18-13-33-02 cheng_normal-Cheng-6000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-05-18-13-33-56    \
    cheng_normal-Cheng-6500txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-05-18-13-34-55 cheng_normal-Cheng-7000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-05-18-13-35-59    \
    cheng_normal-Cheng-7500txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-05-18-13-37-07 cheng_normal-Cheng-8000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-05-18-13-38-19    \
    cheng_normal-Cheng-8500txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-05-18-13-39-36 cheng_normal-Cheng-9000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-05-18-13-40-57    \
    cheng_normal-Cheng-9500txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-05-18-13-42-22 cheng_normal-Cheng-10000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-05-18-13-43-52)    
    
EXPNAMES=(100 200 400 600 800 1000 1500 2000 2500 3000 3500 4000 4500 5000 5500 6000 6500 7000 7500 8000 8500 9000 9500 10000)

OUTPUT_FILE=fig8.txt
rm $OUTPUT_FILE

TIMEOUT=500s

# Viper
for(( i=0;i<${#EXPNAMES[@]};i++)) do
# for i in "23"; do
    timeout $TIMEOUT python3.8 -m cobraplus_backend.cobraplus.main_allcases --config_file cobraplus_backend/cobraplus/config.yaml --algo 6 \
    --sub_dir fig8/${SUBDIRS[i]}/jepsen \
    --perf_file $OUTPUT_FILE --exp_name viper_${EXPNAMES[i]}
done;

# GSI_Z3
# natural baselines are too slow to run check large histories, to save time, only run for the first 5 histories. They all time out for histories > 1k in my test.
# for(( i=0;i<${#EXPNAMES[@]};i++)) do
for(( i=0;i<5;i++)) do
    timeout $TIMEOUT python3.8 -m cobraplus_backend.cobraplus.main_allcases --config_file cobraplus_backend/cobraplus/config.yaml --algo 0 \
    --sub_dir fig8/${SUBDIRS[i]}/jepsen \
    --perf_file $OUTPUT_FILE --exp_name gsiz3_${EXPNAMES[i]}
done;

# ASI_Z3
# for(( i=0;i<${#EXPNAMES[@]};i++)) do
for(( i=0;i<5;i++)) do
    timeout $TIMEOUT python3.8 -m cobraplus_backend.cobraplus.main_allcases --config_file cobraplus_backend/cobraplus/config.yaml --algo 1 \
    --sub_dir fig8/${SUBDIRS[i]}/jepsen \
    --perf_file $OUTPUT_FILE --exp_name asiz3_${EXPNAMES[i]}
done;

# ASI_Mono
# for(( i=0;i<${#EXPNAMES[@]};i++)) do
for(( i=0;i<5;i++)) do
    timeout $TIMEOUT python3.8 -m cobraplus_backend.cobraplus.main_allcases --config_file cobraplus_backend/cobraplus/config.yaml --algo 2 \
    --sub_dir fig8/${SUBDIRS[i]}/jepsen \
    --perf_file $OUTPUT_FILE --exp_name asimono_${EXPNAMES[i]}
done;

# ASI_Mono_Optimized
# for(( i=0;i<${#EXPNAMES[@]};i++)) do
for(( i=0;i<5;i++)) do
    timeout $TIMEOUT python3.8 -m cobraplus_backend.cobraplus.main_allcases --config_file cobraplus_backend/cobraplus/config.yaml --algo 3 \
    --sub_dir fig8/${SUBDIRS[i]}/jepsen \
    --perf_file $OUTPUT_FILE --exp_name asimonoo${EXPNAMES[i]}
done;

