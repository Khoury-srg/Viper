SUBDIRS=(
normal-Cheng-5000txns-8oppertxn-threads24-keys10000-I0-D0-R90-U10-RANGEE0-SI2-2022-09-13-21-44-16 \
C-Twitter-Twitter-5000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-users1000-2022-09-11-20-00-42 \
normal-Cheng-5000txns-8oppertxn-threads24-keys2000-I0-D0-R90-U10-RANGEE0-SI2-2022-09-12-23-18-33 \
normal-TPCC-5000txns-8oppertxn-threads24-I20-D20-R20-U20-RANGEE20-SI2-2022-09-12-20-33-46 \
C-RUBIS-Rubis-5000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-users20000-2022-09-11-20-01-35)
#
EXPNAMES=(BlindW-RM-10k C-Twitter BlindW-RM-2k C-TPCC C-RUBiS) # C-TPCC

OUTPUT_FILE=fig11.txt
rm $OUTPUT_FILE

TIMEOUT=600s #

# Viper
for(( i=0;i<${#EXPNAMES[@]};i++)) do
# for(( i=0;i<3;i++)) do
    timeout $TIMEOUT python3.8 main_allcases.py --config_file config.yaml --algo 6 \
    --sub_dir fig11/${SUBDIRS[i]}/json \
    --perf_file $OUTPUT_FILE --exp_name viper_${EXPNAMES[i]}
done;

for(( i=0;i<${#EXPNAMES[@]};i++)) do
# for(( i=0;i<3;i++)) do
    timeout $TIMEOUT python3.8 main_allcases.py --config_file config.yaml --algo 5 \
    --sub_dir fig11/${SUBDIRS[i]}/json \
    --perf_file $OUTPUT_FILE --exp_name viperwoP_${EXPNAMES[i]}
done;

for(( i=0;i<${#EXPNAMES[@]};i++)) do
# for(( i=0;i<2;i++)) do
    timeout $TIMEOUT python3.8 main_allcases.py --config_file config.yaml --algo 4 \
    --sub_dir fig11/${SUBDIRS[i]}/json \
    --perf_file $OUTPUT_FILE --exp_name viperwoPO_${EXPNAMES[i]}
done;