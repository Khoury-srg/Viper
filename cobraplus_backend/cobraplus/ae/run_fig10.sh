SUBDIRS=(twitter-Twitter-5000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-users1000-2022-05-16-22-29-36 \
    ycsbt_id-YCSBT-5000txns-8oppertxn-threads24-I35-D35-R10-U10-RANGEE10-2022-05-17-15-55-32 \
    cheng_RM-Cheng-5000txns-8oppertxn-threads24-I0-D0-R90-U10-RANGEE0-2022-05-17-15-53-50          \
    cheng_normal-Cheng-5000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-05-18-13-32-11        \
    tpcc-TPCC-5000txns-8oppertxn-threads24-I20-D20-R20-U20-RANGEE20-2022-05-17-22-22-01               \
    rubis-Rubis-5000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-users20000-2022-05-17-22-25-19  \
    ycsbt_range-YCSBT-5000txns-8oppertxn-threads24-I13-D12-R13-U12-RANGEE50-2022-05-17-15-55-20  \
    ycsbt_normal-YCSBT-5000txns-8oppertxn-threads24-I20-D20-R20-U20-RANGEE20-2022-05-16-22-29-21)    
    
EXPNAMES=(C-Twitter Range-IDH BlindW-RM BlindW-RW C-TPCC C-RUBiS Range-RQH Range-B)

OUTPUT_FILE=fig10.txt
rm $OUTPUT_FILE

# Viper
for(( i=0;i<${#EXPNAMES[@]};i++)) do
# for(( i=0;i<3;i++)) do
    python3.8 -m cobraplus_backend.cobraplus.main_allcases --config_file cobraplus_backend/cobraplus/config.yaml --algo 6 \
    --sub_dir fig10/${SUBDIRS[i]}/jepsen \
    --perf_file $OUTPUT_FILE --exp_name viper_${EXPNAMES[i]}
done;