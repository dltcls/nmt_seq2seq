#!/usr/bin/env bash

echo "Baseline models with best parameters as baseline search"

echo "0.002"

##########################  Best 0.002, dp 0.25, layer 2, BLEU: 14,5 for Beam 5 ########################################################################################################################################
python3 run_custom_nmt.py --hs 300 --emb 300 --nlayers 2 --dp 0.25 --reverse_input True --reverse True --model_type s --epochs 80 -v 30000 -b 64 --train 170000 --val 1020 --test 1190 --lr 0.002 --tok tok --tied False
########################################################################################################################################################################################################################


##########################  Best 0.002, dp 0.25, layer 4, BLEU: 14,33 for Beam 5 ########################################################################################################################################
python3 run_custom_nmt.py --hs 300 --emb 300 --nlayers 4 --dp 0.25 --reverse_input True --reverse True --model_type s --epochs 80 -v 30000 -b 64 --train 170000 --val 1020 --test 1190 --lr 0.002 --tok tok --tied False
########################################################################################################################################################################################################################


echo "0.0002"

##########################  Best 0.0002, dp 0.25, layer 2, BLEU: 15,5 for Beam 5 ########################################################################################################################################
python3 run_custom_nmt.py --hs 300 --emb 300 --nlayers 2 --dp 0.25 --reverse_input True --reverse True --model_type s --epochs 80 -v 30000 -b 64 --train 170000 --val 1020 --test 1190 --lr 0.0002 --tok tok --tied False
########################################################################################################################################################################################################################

##########################  Best 0.0002, dp 0.25, layer 4, BLEU: 17,11 for Beam 5 ########################################################################################################################################
python3 run_custom_nmt.py --hs 300 --emb 300 --nlayers 4 --dp 0.25 --reverse_input True --reverse True --model_type s --epochs 80 -v 30000 -b 64 --train 170000 --val 1020 --test 1190 --lr 0.0002 --tok tok --tied False
########################################################################################################################################################################################################################

echo "0.0003"

##########################  Best 0.0003, dp 0.25, layer 2, BLEU: 15,73 for Beam 5 ########################################################################################################################################
python3 run_custom_nmt.py --hs 300 --emb 300 --nlayers 2 --dp 0.25 --reverse_input True --reverse True --model_type s --epochs 80 -v 30000 -b 64 --train 170000 --val 1020 --test 1190 --lr 0.0003 --tok tok --tied False
########################################################################################################################################################################################################################

##########################  Best 0.0003, dp 0.25, layer 4, BLEU: 17,93 for Beam 5 ########################################################################################################################################
python3 run_custom_nmt.py --hs 300 --emb 300 --nlayers 4 --dp 0.25 --reverse_input True --reverse True --model_type s --epochs 80 -v 30000 -b 64 --train 170000 --val 1020 --test 1190 --lr 0.0003 --tok tok --tied False
########################################################################################################################################################################################################################
