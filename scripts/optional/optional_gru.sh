#!/usr/bin/env bash

echo "Lr 0.0002"
#python3 run_custom_nmt.py --hs 300 --emb 300 --nlayers 4 --dp 0.25 --reverse True --bi True --epochs 80 -v 30000 -b 64 --train 170000 --val 1020 --test 1190 --lr 0.0002 --tok tok --tied True --rnn gru --beam 5 --pretrained True
python3 run_custom_nmt.py --hs 300 --emb 300 --nlayers 4 --dp 0.25 --reverse True --bi True --epochs 80 -v 30000 -b 64 --train 170000 --val 1020 --test 1190 --lr 0.0002 --tok tok --tied True --rnn gru --beam 5 --attn dot
python3 run_custom_nmt.py --hs 300 --emb 300 --nlayers 4 --dp 0.25 --reverse True --bi True --epochs 80 -v 30000 -b 64 --train 170000 --val 1020 --test 1190 --lr 0.0002 --tok tok --tied True --rnn gru --beam 5 --attn additive



echo "Lr 0.0001"
#python3 run_custom_nmt.py --hs 300 --emb 300 --nlayers 4 --dp 0.25 --reverse True --bi True --epochs 80 -v 30000 -b 64 --train 170000 --val 1020 --test 1190 --lr 0.0001 --tok tok --tied True --rnn gru --beam 5 --pretrained True
python3 run_custom_nmt.py --hs 300 --emb 300 --nlayers 4 --dp 0.25 --reverse True --bi True --epochs 80 -v 30000 -b 64 --train 170000 --val 1020 --test 1190 --lr 0.0001 --tok tok --tied True --rnn gru --beam 5 --attn dot
python3 run_custom_nmt.py --hs 300 --emb 300 --nlayers 4 --dp 0.25 --reverse True --bi True --epochs 80 -v 30000 -b 64 --train 170000 --val 1020 --test 1190 --lr 0.0001 --tok tok --tied True --rnn gru --beam 5 --attn additive


echo "Attention with pretrained"
python3 run_custom_nmt.py --hs 300 --emb 300 --nlayers 4 --dp 0.25 --reverse True --bi True --epochs 80 -v 30000 -b 64 --train 170000 --val 1020 --test 1190 --lr 0.0002 --tok tok --tied True --rnn gru --beam 5 --attn dot --pretrained True
#python3 run_custom_nmt.py --hs 300 --emb 300 --nlayers 4 --dp 0.25 --reverse True --bi True --epochs 80 -v 30000 -b 64 --train 170000 --val 1020 --test 1190 --lr 0.0002 --tok tok --tied True --rnn gru --beam 5 --attn additive --pretrained True
python3 run_custom_nmt.py --hs 300 --emb 300 --nlayers 4 --dp 0.25 --reverse True --bi True --epochs 80 -v 30000 -b 64 --train 170000 --val 1020 --test 1190 --lr 0.0001 --tok tok --tied True --rnn gru --beam 5 --attn dot --pretrained True
#python3 run_custom_nmt.py --hs 300 --emb 300 --nlayers 4 --dp 0.25 --reverse True --bi True --epochs 80 -v 30000 -b 64 --train 170000 --val 1020 --test 1190 --lr 0.0001 --tok tok --tied True --rnn gru --beam 5 --attn additive --pretrained True


echo "Char based"
python3 run_custom_nmt.py --hs 300 --emb 300 --nlayers 4 --dp 0.25 --reverse True --bi True --epochs 30 -v 30000 -b 64 --train 170000 --val 1020 --test 1190 --lr 0.0002 --tok tok --tied True --rnn gru --beam 5 -c True
python3 run_custom_nmt.py --hs 300 --emb 300 --nlayers 4 --dp 0.25 --reverse True --bi True --epochs 30 -v 30000 -b 64 --train 170000 --val 1020 --test 1190 --lr 0.0001 --tok tok --tied True --rnn gru --beam 5 -c True