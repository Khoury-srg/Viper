SUBDIRS=(twitter-Twitter-5000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-users1000-2022-05-16-22-29-36 \
    cheng_RM-Cheng-5000txns-8oppertxn-threads24-I0-D0-R90-U10-RANGEE0-2022-05-17-15-53-50  \
    tpcc-TPCC-5000txns-8oppertxn-threads24-I20-D20-R20-U20-RANGEE20-2022-05-17-22-22-01 \
    rubis-Rubis-5000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-users20000-2022-05-17-22-25-19)    
    
EXPNAMES=(C-Twitter BlindW-RM C-TPCC C-RUBiS)

OUTPUT_FILE=fig11.txt
rm $OUTPUT_FILE

TIMEOUT=600s # 

# Viper
for(( i=0;i<${#EXPNAMES[@]};i++)) do
# for(( i=0;i<3;i++)) do
    timeout $TIMEOUT python3.8 -m cobraplus_backend.cobraplus.main_allcases --config_file cobraplus_backend/cobraplus/config.yaml --algo 6 \
    --sub_dir fig11/${SUBDIRS[i]}/jepsen \
    --perf_file $OUTPUT_FILE --exp_name viper_${EXPNAMES[i]}
done;

for(( i=0;i<${#EXPNAMES[@]};i++)) do
# for(( i=0;i<3;i++)) do
    timeout $TIMEOUT python3.8 -m cobraplus_backend.cobraplus.main_allcases --config_file cobraplus_backend/cobraplus/config.yaml --algo 5 \
    --sub_dir fig11/${SUBDIRS[i]}/jepsen \
    --perf_file $OUTPUT_FILE --exp_name viperwoP_${EXPNAMES[i]}
done;

for(( i=0;i<${#EXPNAMES[@]};i++)) do
# for(( i=0;i<2;i++)) do
    timeout $TIMEOUT python3.8 -m cobraplus_backend.cobraplus.main_allcases --config_file cobraplus_backend/cobraplus/config.yaml --algo 4 \
    --sub_dir fig11/${SUBDIRS[i]}/jepsen \
    --perf_file $OUTPUT_FILE --exp_name viperwoPO_${EXPNAMES[i]}
done;