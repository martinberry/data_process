#!/usr/bin/env bash

# example: generate train set from parallel corpus
python ./run.py --schema schema_train_default.json --workdir work_train &&

# example: generate LM traing set from mono zh corpus
python ./run.py --infile test_data/zh.txt --schema schema_lm_zh_default.json --workdir work_lm &&

# example: make BLEU score evaluation
python ./run.py --schema schema_bleu_zh_default.json --workdir workdir_bleu &&

# example: fast alignment
python ./run.py --schema schema_fast_align_default.json --workdir workdir_align &&

# example: translate document
python ./run.py --schema schema_trans_single_doc_default.json --workdir workdir_trans

if [ $? -ne 0 ]; then
    echo "!!!!!!! Failed !!!!!!!!!"
else
    echo "======= Passed ========="
fi