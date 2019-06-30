#!/usr/bin/env bash

echo "Starting script.........."

echo "DE_EN"

echo "Sutskever"

echo "====================================="

python3 run_custom_nmt.py --hs 500 --emb 500 --nlayers 4 --dp 0.5 --reverse_input True --reverse True --model_type s --epochs 70 -v 30000  --train 250000 --val 25000 --test 2500 -b 64


echo "====================================="

python3 run_custom_nmt.py --hs 500 --emb 500 --nlayers 4 --dp 0.0 --reverse_input True --reverse True --model_type s --epochs 70 -v 30000 --train 250000 --val 25000 --test 2500 -b 64

echo "====================================="

python3 run_custom_nmt.py --hs 500 --emb 500 --nlayers 4 --dp 0.25 --reverse_input True --reverse True --model_type s --epochs 70 -v 30000 --train 250000 --val 25000 --test 2500 -b 64

echo "====================================="


echo "====================================="


echo "CUSTOM"

echo "Bidirectional"

echo "====================================="

python3 run_custom_nmt.py --hs 500 --emb 500 --nlayers 4 --dp 0.5 --bi True --model_type custom --reverse True --epochs 70 -v 30000 --train 250000 --val 25000 --test 2500 -b 64

echo "====================================="

python3 run_custom_nmt.py --hs 500 --emb 500 --nlayers 4 --dp 0.0 --bi True --model_type custom  --reverse True --epochs 70 -v 30000  --train 250000 --val 25000 --test 2500 -b 64

echo "====================================="

python3 run_custom_nmt.py --hs 500 --emb 500 --nlayers 4 --dp 0.25 --bi True --model_type custom --reverse True --epochs 70 -v 30000 --train 250000 --val 25000 --test 2500 -b 64
echo "====================================="


echo "====================================="

