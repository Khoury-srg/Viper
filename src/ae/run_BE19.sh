SUBDIRS=(cheng_normal-Cheng-100txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-17-50 \
cheng_normal-Cheng-200txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-18-02 \
cheng_normal-Cheng-400txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-18-17 \
cheng_normal-Cheng-600txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-18-33 \
cheng_normal-Cheng-800txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-18-53 \
cheng_normal-Cheng-1000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-SI2-2022-09-11-15-19-14)

EXPNAMES=(100 200 400 600 800 1000)

OUTPUT_FILE=be19.txt
rm $OUTPUT_FILE

TIMEOUT=300s

# Viper 
#for(( i=0;i<${#EXPNAMES[@]};i++)) do
#    python3.8 main_allcases.py --config_file config.yaml --algo 6 \
#    --sub_dir fig8/${SUBDIRS[i]}/json --strong-session \
#    --perf_file $OUTPUT_FILE --exp_name viper_${EXPNAMES[i]} \
#    --format json
#done;


# dbcop/BE19
# w/o docker
 python3.8 ae/run_BE19.py \
     --log_folder $VIPER_HOME/history_data2/logs/fig8 \
     --output_folder  $VIPER_HOME/BE19_output --dbcop $VIPER_HOME/resources/dbcop/target/debug/dbcop  \
     --translator $VIPER_HOME/resources/BE19_translator/target/debug/translator

# using docker
#python3.8 viper_backend/viper/ae/run_BE19.py \
#    --log_folder $VIPER_HOME/history_data/logs/fig8 \
#    --output_folder  $VIPER_HOME/BE19_output2 --dbcop /dbcop/target/debug/dbcop  \
#    --translator /BE19_translator/target/debug/translator

