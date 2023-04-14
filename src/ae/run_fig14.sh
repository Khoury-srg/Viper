SUBDIRS=(history2-4-1-1-lost-updates history3-4-1-2-aborted-read history4-4-6-cyclic-information history5-4-7-read-ur-future-writes tidb-history1-read-skew)    
    
OUTPUT_FILE=fig14.txt
rm $OUTPUT_FILE

# Viper
for(( i=0;i<${#SUBDIRS[@]};i++)) do
# for(( i=0;i<3;i++)) do
    python3.8 main_allcases.py --config_file config.yaml --algo 8 \
    --sub_dir fig14/${SUBDIRS[i]} \
    --perf_file $OUTPUT_FILE --exp_name viper_${SUBDIRS[i]} --format edn
done;