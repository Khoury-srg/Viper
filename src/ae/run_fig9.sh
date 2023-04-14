SUBDIRS=(10s-20220518T161953.000Z 20s-20220518T162041.000Z 30s-20220518T162141.000Z 40s-20220518T162252.000Z 50s-20220518T162416.000Z \
    60s-20220518T162551.000Z 70s-20220518T162740.000Z 80s-20220518T162938.000Z 90s-20220518T163152.000Z 100s-20220518T163417.000Z \
    110s-20220518T163652.000Z 120s-20220518T163939.000Z 130s-20220518T164242.000Z 140s-20220518T164556.000Z)    
    
EXPNAMES=($(seq 10 10 140))

OUTPUT_FILE=fig9.txt
rm $OUTPUT_FILE

# elle
python3.8 ae/run_elle.py --log_folder $VIPER_HOME/history_data2/logs/fig9 --perf_file fig9.txt \
   --elle $VIPER_HOME/resources/elle-cli-0.1.3/target/elle-cli-0.1.3-standalone.jar


# Viper
for(( i=0;i<${#EXPNAMES[@]};i++)) do
# for(( i=0;i<1;i++)) do
    python3.8 main_allcases.py --config_file config.yaml --algo 8 \
    --sub_dir fig9/${SUBDIRS[i]} \
    --perf_file $OUTPUT_FILE --exp_name viper_${EXPNAMES[i]} \
    --format edn
done;
