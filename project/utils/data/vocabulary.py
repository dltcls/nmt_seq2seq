import os
import time
import numpy as np
import torch
import torchtext
from torchtext import data, datasets
from torchtext.data import Example

from project import get_full_path
from project.utils.constants import SOS_TOKEN, EOS_TOKEN, UNK_TOKEN, PAD_TOKEN
from project.utils.data.preprocessing import generate_splits_from_datasets
from project.utils.io import SrcField
from project.utils.utils import convert
from settings import DATA_DIR_PREPRO

CHUNK_SIZES = {10: 10e2, 20: 10e3, 30:10e4, 50:10e4}


def get_vocabularies_iterators(src_lang, args):

    device = args.cuda

    #### Create torchtext fields
    ####### SRC, TRG
    voc_limit = args.v

    char_level = args.c
    corpus = args.corpus
    language_code = args.lang_code
    print("Min_freq",voc_limit)
    print("Max sequence length:", args.max_len)



    tokenizer = lambda s: s.split() if char_level == False else lambda s: list(s)

    SRC_sos_eos_pad_unk = [None, None, PAD_TOKEN, UNK_TOKEN]
    TRGsos_eos_pad_unk = [SOS_TOKEN, EOS_TOKEN, PAD_TOKEN, UNK_TOKEN]

    src_vocab = SrcField(tokenize=tokenizer, include_lengths=False,sos_eos_pad_unk=SRC_sos_eos_pad_unk)

    trg_vocab = SrcField(tokenize=tokenizer, include_lengths=False, sos_eos_pad_unk=TRGsos_eos_pad_unk)



    print("Fields created!")

    ####### create splits

    if corpus == "europarl":

        root = get_full_path(DATA_DIR_PREPRO)
        #print("Root:", root)
        data_dir = os.path.join(root, corpus, language_code, "splits")

        print("Loading data...")
        start = time.time()
        fields = (("src",src_vocab), ("trg",trg_vocab))
        exts = (".en", ".{}".format(language_code)) if src_lang == "en" else (".{}".format(language_code), ".en")
        print(exts)
        train, val, test = Seq2SeqDataset.splits(src_vocab, trg_vocab, reverse=True if src_lang!="en" else False)


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
                                                 filter_pred=lambda x: max(len(vars(x)['src']), len(vars(x)['trg'])) <= args.max_len)
        end = time.time()
        print("Duration: {}".format(convert(end - start)))
        print("Total number of sentences: {}".format((len(train) + len(val) + len(test))))

    if voc_limit > 0:
        src_vocab.build_vocab(train.src, val.src, test.src, min_freq=2, max_size=voc_limit)
        trg_vocab.build_vocab(train.trg, val.trg, test.src, min_freq=2, max_size=voc_limit)
        print("Src vocabulary created!")
    else:
        src_vocab.build_vocab(train, val, test, min_freq=2)
        trg_vocab.build_vocab(train, val, test, min_freq=2)
        print("Src vocabulary created!")




    #### Iterators

    # Create iterators to process text in batches of approx. the same length
    train_iter = data.BucketIterator(train, batch_size=args.b, device=device, repeat=False,
                                     sort_key=lambda x: (len(x.src), len(x.trg)), sort_within_batch=True, shuffle=True)
    val_iter = data.Iterator(val, batch_size=1, device=device, repeat=False, sort_key=lambda x: len(x.src))
    test_iter = data.Iterator(test, batch_size=1, device=device, repeat=False, sort_key=lambda x: len(x.src))

    #print(next(iter(train_iter)))

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


def load_embeddings(SRC, TRG, np_src_file, np_trg_file):
    '''Load English and German embeddings from saved numpy files'''
    if os.path.isfile(np_src_file) and os.path.isfile(np_trg_file):
        emb_tr_src = torch.from_numpy(np.load(np_src_file))
        emb_tr_trg = torch.from_numpy(np.load(np_trg_file))
    else:
        raise Exception('Vectors not available to load from numpy file')
    return emb_tr_src, emb_tr_trg


