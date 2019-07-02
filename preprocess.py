"""

Script for preprocessing raw bilingual corpus files from OPUS

Please download file from the OPUS section: "Statistics and TMX/Moses Downloads", either in txt or tmx format file.
Extract the dataset, put the text or tmx file in a directory and pass this as an argument.

Default path is: data/raw/<corpus_name>/<lang_code>

Ex:

python preprocess.py --lang_code de --type tmx --corpus europarl --max_len 30 --min_len 2 --path data/raw/europarl/de --file de-en.tmx

Filtering by length...
Total samples:  1053263
1053263
Reducing the vocabulary...
Total samples:  1052761
"""
import argparse
import os
import time

from tmx2corpus import FileOutput

from project.experiment.setup_experiment import str2bool
from project.utils.preprocessing import TMXConverter, get_custom_tokenizer, split_data, persist_txt
from project.utils.utils import convert
from settings import DATA_DIR_PREPRO, DATA_DIR_RAW


def data_prepro_parser():
    parser = argparse.ArgumentParser(description='Neural Machine Translation')
    parser.add_argument("--lang_code", default="de", type=str)
    parser.add_argument("--type", default="tmx", type=str, help="TMX or TXT")
    parser.add_argument("--corpus", default="europarl", type=str, help="Corpus name")
    parser.add_argument("--max_len", default=30, type=int, help="Filter sequences with a length <= max_len")
    parser.add_argument("--min_len", default=1, type=int, help="Filter sequences with a length >= min_len")
    parser.add_argument('--path', default="data/raw/europarl/de", help="Path to raw data files")
    parser.add_argument('--file', default="de-en.tmx", help="File name after extraction")
    parser.add_argument('--v', type=str2bool, default="False", help="Either vocabulary should be reduced by replacing some repeating tokens with labels.\nNumbers are replaced with NUM, Persons names are replaced with PERSON. Require: Spacy!")

    return parser



if __name__ == '__main__':
    #### preprocessing pipeline for tmx files

    parser = data_prepro_parser().parse_args()
    corpus_name = parser.corpus
    lang_code = parser.lang_code
    file_type = parser.type
    path_to_raw_file = parser.path
    reduce_vocab = parser.v
    max_len, min_len = parser.max_len, parser.min_len

    COMPLETE_PATH = os.path.join(path_to_raw_file, parser.file)

    STORE_PATH = os.path.join(os.path.expanduser(DATA_DIR_PREPRO), corpus_name, lang_code, "splits", str(max_len))

    assert file_type in ["tmx", "txt"]

    if file_type == "tmx":
        start = time.time()
        FILE = os.path.join(DATA_DIR_RAW, corpus_name, lang_code)
        output_file_path = os.path.join(DATA_DIR_PREPRO, corpus_name, lang_code)
        files = [file for file in os.listdir(output_file_path) if file.startswith("bitext.tok") or file.startswith("bitext.tok")]
        if len(files) >= 2:
            print("TMX file already preprocessd!")
        else:
            ### This conversion uses standard tokenizers, which splits sentences on spaces and punctuation, this is very fast
            converter = TMXConverter(output=FileOutput(output_file_path))
            tokenizers = [get_custom_tokenizer("", "w", "fast"), get_custom_tokenizer("", "w", "fast")]
            converter.add_tokenizers(tokenizers)
            converter.convert([COMPLETE_PATH]) #---> bitext.en, bitext.de, bitext.tok.de, bitext.tok.en
            print("Converted lines:", converter.output_lines)

        src_lines = [line.strip("\n") for line in
                     open(os.path.join(output_file_path, "bitext.tok.en"), mode="r",
                          encoding="utf-8").readlines() if line]
        trg_lines = [line.strip("\n") for line in
                     open(os.path.join(output_file_path, "bitext.tok.de"), mode="r",
                          encoding="utf-8").readlines() if line]



        if max_len > 0 or min_len > 0:
            files = ['.'.join(file.split(".")[:2]) for file in os.listdir(STORE_PATH) if file.endswith("tok.en") or file.endswith("tok."+lang_code)]
            if files:
                print("File already reduced by length!")
            else:
                print("Filtering by length...")
                filtered_src_lines, filtered_trg_lines = [], []
                for src_l, trg_l in zip(src_lines, trg_lines):
                    if src_l != "" and trg_l != "":
                        src_l_s, trg_l_s = src_l.split(" "), trg_l.split(" ")
                        if (len(src_l_s) <= max_len and len(src_l_s) >= min_len) and (len(trg_l_s) <= max_len and len(trg_l_s) >= min_len):
                            filtered_src_lines.append(' '.join(src_l_s))
                            filtered_trg_lines.append(' '.join(trg_l_s))
                assert len(filtered_src_lines) == len(filtered_trg_lines)

                src_lines, trg_lines = filtered_src_lines, filtered_trg_lines
                train_data, val_data, test_data = split_data(src_lines, trg_lines)
                persist_txt(train_data, STORE_PATH, "train.tok", exts=(".en", ".de"))
                persist_txt(val_data, STORE_PATH, "val.tok", exts=(".en", ".de"))
                persist_txt(test_data, STORE_PATH, "test.tok", exts=(".en", ".de"))



        if reduce_vocab:
            #### This really takes long. Start only if a reduction is really needed :-)
            print("Reducing the vocabulary...")
            #### tokenize with spacy if available
            files = ['.'.join(file.split(".")[:2]) for file in os.listdir(STORE_PATH) if file.endswith("clean.en") or file.endswith("clean."+lang_code)]
            if files:
                print("File already cleaned!")
            else:
                src_lang_tokenizer = get_custom_tokenizer("en", "w")
                trg_lang_tokenizer = get_custom_tokenizer(lang_code, "w")
                if src_lang_tokenizer.type == "spacy" and trg_lang_tokenizer.type == "spacy":
                    src_lang_tokenizer.set_mode(False)
                    trg_lang_tokenizer.set_mode(False)
                    src_lines = [src_lang_tokenizer.tokenize(line) for line in src_lines]
                    trg_lines = [trg_lang_tokenizer.tokenize(line) for line in trg_lines]

                    take_src_lines, take_trg_lines = [],[]
                    for src_l, trg_l in zip(src_lines, trg_lines):
                        if src_l != "" and trg_l != "":
                            take_src_lines.append(src_l)
                            take_trg_lines.append(trg_l)
                    assert len(take_trg_lines) == len(take_trg_lines)
                    train_data, val_data, test_data = split_data(take_src_lines, take_trg_lines)
                    persist_txt(train_data, STORE_PATH, "train.clean", exts=(".en", ".de"))
                    persist_txt(val_data, STORE_PATH, "val.clean", exts=(".en", ".de"))
                    persist_txt(test_data, STORE_PATH, "test.clean", exts=(".en", ".de"))
                else:
                    print("This only works with Spacy. Please install spacy for EN and {}".format(lang_code.upper()))

        print("Total time:", convert(time.time() - start))
    else:
        #TODO
        pass

