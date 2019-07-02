import os
import time

import dill
import numpy as np
import torch
from torchtext import data, datasets

from project import get_full_path
from project.utils.constants import SOS_TOKEN, EOS_TOKEN, UNK_TOKEN, PAD_TOKEN
from project.utils.io import SrcField, Seq2SeqDataset
from project.utils.utils import convert
from settings import DATA_DIR_PREPRO

CHUNK_SIZES = {10: 10e2, 20: 10e3, 30:10e4, 50:10e4}


def get_vocabularies_iterators(src_lang, experiment, data_dir = None, max_len=30):

    device = experiment.get_device()

    #### Create torchtext fields
    ####### SRC, TRG
    voc_limit = experiment.voc_limit

    char_level = experiment.char_level
    corpus = experiment.corpus
    language_code = experiment.lang_code
    reduce = experiment.reduce
    print("Vocabulary limit:",voc_limit)
  #  print("Max sequence length:", experiment.max_len)

    reverse_input = experiment.reverse_input
    print("Source reversed:", reverse_input)

    ### Define tokenizers ####
    if char_level:
        src_tokenizer = lambda s: list(s)
        trg_tokenizer = lambda s: list(s)
    else:
        if reverse_input:
            src_tokenizer = lambda s: s.split()[::-1]
            trg_tokenizer = lambda s: s.split()

        else:
            src_tokenizer = lambda s: s.split()
            trg_tokenizer = lambda s: s.split()

    SRC_sos_eos_pad_unk = [None, None, PAD_TOKEN, UNK_TOKEN]
    TRGsos_eos_pad_unk = [SOS_TOKEN, EOS_TOKEN, PAD_TOKEN, UNK_TOKEN]

    if reverse_input:
        src_vocab = SrcField(tokenize=src_tokenizer, include_lengths=False,sos_eos_pad_unk=SRC_sos_eos_pad_unk, pad_first=True)
    else:
        src_vocab = SrcField(tokenize=src_tokenizer, include_lengths=False, sos_eos_pad_unk=SRC_sos_eos_pad_unk)

    trg_vocab = SrcField(tokenize=trg_tokenizer, include_lengths=False, sos_eos_pad_unk=TRGsos_eos_pad_unk)

    print("Fields created!")

    ####### create splits

    if corpus == "europarl":

        root = get_full_path(DATA_DIR_PREPRO)
        #print("Root:", root)
        if not data_dir:
            data_dir = os.path.join(root, corpus, language_code, "splits", str(max_len)) # local directory

        print("Loading data...")
        start = time.time()
       # exts = (".en", ".{}".format(language_code)) if src_lang == "en" else (".{}".format(language_code), ".en")
        file_type = experiment.tok
        exts = ("."+experiment.get_src_lang(), "."+experiment.get_trg_lang())
        train, val, test = Seq2SeqDataset.splits(fields=(src_vocab, trg_vocab),
                                                 exts=exts, train="train."+file_type, validation="val."+file_type, test="test."+file_type,
                                                 path=data_dir, reduce=reduce, reverse_input=False, truncate=experiment.truncate)


        end = time.time()
        print("Duration: {}".format(convert(end - start)))
        print("Total number of sentences: {}".format((len(train) + len(val) + len(test))))

    else:
        print("Loading data...")
        start = time.time()
        path = get_full_path(DATA_DIR_PREPRO, "iwslt")
        os.makedirs(path, exist_ok=True)
        exts = (".en", ".de") if src_lang == "en" else (".de", ".en")
        train, val, test = datasets.IWSLT.splits(root=path,
                                                 exts=exts, fields=(src_vocab, trg_vocab),
                                                 filter_pred=lambda x: max(len(vars(x)['src']), len(vars(x)['trg'])) <= experiment.truncate)
        end = time.time()
        print("Duration: {}".format(convert(end - start)))
        print("Total number of sentences: {}".format((len(train) + len(val) + len(test))))

    if voc_limit > 0:
        src_vocab.build_vocab(train, val, test, min_freq=5, max_size=voc_limit)
        trg_vocab.build_vocab(train, val, test, min_freq=5, max_size=voc_limit)
        print("Src vocabulary created!")
    else:
        src_vocab.build_vocab(train, val, test, min_freq=5)
        trg_vocab.build_vocab(train, val, test, min_freq=5)
        print("Src vocabulary created!")




    #### Iterators

    # Create iterators to process text in batches of approx. the same length
    train_iter = data.BucketIterator(train, batch_size=experiment.batch_size, device=device, repeat=False, sort_key=lambda x: (len(x.src)))

   # val_batch_size = experiment.batch_size//2 if experiment.batch_size >=2 else experiment.batch_size
    val_iter = data.BucketIterator(val, experiment.val_batch_size, device=device, repeat=False, sort_key=lambda x: (len(x.src)), shuffle=False)
    print(val_iter.batch_size)
    test_iter = data.Iterator(test, batch_size=1, device=device, repeat=False, sort_key=lambda x: (len(x.src)), shuffle=False)

    return src_vocab, trg_vocab, train_iter, val_iter, test_iter, train, val, test


def print_data_info(logger, train_data, valid_data, test_data, src_field, trg_field, corpus):
    """ This prints some useful stuff about our data sets. """
    if corpus == "":
        corpus_name = "IWLST"
    else:
        corpus_name = corpus
    logger.log("Dataset in use: {}".format(corpus_name.upper()))

    logger.log("Data set sizes (number of sentence pairs):")
    logger.log('train {}'.format(len(train_data)))
    logger.log('valid {}'.format(len(valid_data)))
    logger.log('test {}'.format(len(test_data)))

    logger.log("First training example:")
    logger.log("src: {}".format(" ".join(vars(train_data[0])['src'])))
    logger.log("trg: {}".format(" ".join(vars(train_data[0])['trg'])))

    logger.log("Most common words (src):")
    logger.log("\n".join(["%10s %10d" % x for x in src_field.vocab.freqs.most_common(10)]))
    logger.log("Most common words (trg):")
    logger.log("\n".join(["%10s %10d" % x for x in trg_field.vocab.freqs.most_common(10)]))

    logger.log("First 10 words (src):")
    logger.log("\n".join(
        '%02d %s' % (i, t) for i, t in enumerate(src_field.vocab.itos[:10])))
    logger.log("First 10 words (trg):")
    logger.log("\n".join(
        '%02d %s' % (i, t) for i, t in enumerate(trg_field.vocab.itos[:10])))

    logger.log("Number of source words (types): {}".format(len(src_field.vocab)))
    logger.log("Number of target words (types): {}".format(len(trg_field.vocab)))


