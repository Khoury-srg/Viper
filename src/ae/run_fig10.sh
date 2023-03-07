SUBDIRS=(C-Twitter-Twitter-5000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-users1000-2022-09-11-20-00-42 \
     Range-IDH-YCSBT-5000txns-8oppertxn-threads24-I35-D35-R10-U10-RANGEE10-SI2-2022-09-11-19-59-46 \
     normal-Cheng-5000txns-8oppertxn-threads24-keys10000-I0-D0-R90-U10-RANGEE0-SI2-2022-09-13-21-44-16 \
     normal-Cheng-5000txns-8oppertxn-threads24-keys2000-I0-D0-R90-U10-RANGEE0-SI2-2022-09-12-23-18-33 \
     BlindW-RW-Cheng-5000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-19-57-29 \
     normal-TPCC-5000txns-8oppertxn-threads24-I20-D20-R20-U20-RANGEE20-SI2-2022-09-12-20-33-46 \
     C-RUBIS-Rubis-5000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-users20000-2022-09-11-20-01-35  \
     Range-RQH-YCSBT-5000txns-8oppertxn-threads24-I13-D12-R13-U12-RANGEE50-SI2-2022-09-11-20-00-06 \
     Range-B-YCSBT-5000txns-8oppertxn-threads24-I20-D20-R20-U20-RANGEE20-SI2-2022-09-11-20-00-23)

EXPNAMES=(C-Twitter Range-IDH BlindW-RM-10k BlindW-RM-2k BlindW-RW C-TPCC C-RUBiS Range-RQH Range-B) # C-TPCC

OUTPUT_FILE=fig10.txt
rm $OUTPUT_FILE

# Viper
for(( i=0;i<${#EXPNAMES[@]};i++)) do
# for(( i=0;i<3;i++)) do
    python3.8 main_allcases.py --config_file config.yaml --algo 6 \
    --sub_dir fig10/${SUBDIRS[i]}/json \
    --perf_file $OUTPUT_FILE --exp_name viper_${EXPNAMES[i]}
done;