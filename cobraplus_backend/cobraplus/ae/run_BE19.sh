SUBDIRS=(cheng_normal-Cheng-100txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-05-18-13-26-47 cheng_normal-Cheng-200txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-05-18-13-26-58 \
    cheng_normal-Cheng-400txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-05-18-13-27-08  cheng_normal-Cheng-600txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-05-18-13-27-21     \
    cheng_normal-Cheng-800txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-05-18-13-27-35  cheng_normal-Cheng-1000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-05-18-13-27-51)    
    
EXPNAMES=(100 200 400 600 800 1000)

OUTPUT_FILE=be19.txt
rm $OUTPUT_FILE

# Viper 
for(( i=0;i<${#EXPNAMES[@]};i++)) do
    python3.8 -m cobraplus_backend.cobraplus.main_allcases --config_file cobraplus_backend/cobraplus/config.yaml --algo 6 \
    --sub_dir fig8/${SUBDIRS[i]} --strong-session \
    --perf_file $OUTPUT_FILE --exp_name viper_${EXPNAMES[i]}
done;


# dbcop/BE19
# w/o docker
# python3.8 cobraplus_backend/cobraplus/ae/run_BE19.py \
#     --log_folder $VIPER_HOME/jepsen_data/jepsen_logs/fig8 \
#     --output_folder  $VIPER_HOME/BE19_output --dbcop $VIPER_HOME/resources/dbcop/target/debug/dbcop  \
#     --translator $VIPER_HOME/resources/BE19_translator/target/debug/translator

# using docker
python3.8 cobraplus_backend/cobraplus/ae/run_BE19.py \
    --log_folder $VIPER_HOME/jepsen_data/jepsen_logs/fig8 \
    --output_folder  $VIPER_HOME/BE19_output --dbcop /dbcop/target/debug/dbcop  \
    --translator /BE19_translator/target/debug/translator

