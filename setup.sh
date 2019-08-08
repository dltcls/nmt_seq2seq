#!/usr/bin/env bash

### create environment
## Uncomment this if you want to automatically setup a virutal environment
#python3 -m venv env
#echo "Activating environment"
#source "env/bin/activate"

### Requirements for the project ####
pip install torch torchtext
pip install -U spacy
python3 -m spacy download en
python3 -m spacy download de
python3 -m spacy download xx #multilanguage model,
pip install dill
pip install nltk
pip install numpy pandas matplotlib
pip install HTMLParser
