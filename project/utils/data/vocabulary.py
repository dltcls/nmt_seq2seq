import os
import time
import numpy as np
import torch
import torchtext
from torchtext import data, datasets
from torchtext.data import Example, Field, TabularDataset

from project import get_full_path
from project.utils.constants import SRC_LABEL, TRG_LABEL, SOS_TOKEN, EOS_TOKEN, UNK_TOKEN, PAD_TOKEN
from project.utils.data.preprocessing import generate_splits_from_datasets
from project.utils.utils import convert
from settings import DATA_DIR_PREPRO

CHUNK_SIZES = {10: 10e2, 20: 10e3, 30:10e4, 50:10e4}


class TranslationReversibleField(torchtext.data.Field):

    def __init__(self, **kwargs):
        ### Create vocabulary object
        super(TranslationReversibleField, self).__init__(**kwargs)

    def build_vocab(self, *args, **kwargs):
        super(TranslationReversibleField, self).build_vocab(*args, **kwargs)
        self.sos_id = self.vocab.stoi[self.init_token]
        self.eos_id = self.vocab.stoi[self.eos_token]
        self.pad_id = self.vocab.stoi[self.pad_token]

        self.unk_id = self.vocab.stoi[self.unk_token]

    def reverse(self, batch):
        """
        Readapted from: https://github.com/pytorch/text/blob/master/torchtext/data/field.py
        Reverses the given batch back to the sentences (strings)
        """
        if self.include_lengths:
            batch = batch[0]  # if lenghts are included, batch is a tuple containing an array of all the lengths

        if not self.batch_first:
            ### batch needs to be transposed, if shape is seq_len x batch
            batch = batch.t()

        with torch.cuda.device_of(batch):
            batch = batch.tolist()

        batch = [[self.vocab.itos[ind] for ind in ex] for ex in batch]

        def trim(sent, token):
            """
            Removes from the given sentence the given token
            :param sent:
            :param token:
            :return: tokenized sentence array without the given token
            """
            sentence = []
            for word in sent:
                if word == token:
                    break
                sentence.append(word)
            return sentence

        batch = [trim(ex, self.vocab.itos[self.eos_id]) for ex in batch]

        def filter_special(token):
            return token not in (self.init_token, self.pad_token)

        batch = [filter(filter_special, ex) for ex in batch]

        return [' '.join(ex) for ex in batch]  ## Reverse tokenization by joining the words


class TSVTranslationCorpus(torchtext.data.Dataset):
    allowed_formats = ["csv", "tsv"]

    """
    Defines a reader from CSV/TSV datasets.
    It uses `pandas` as parsing libraries.

    Code readapted from Dataset/TabularDataset class by TorchText: 
    https://github.com/pytorch/text/blob/master/torchtext/data/dataset.py
    """

    def __init__(self, path, format, fields, filter_query=None,
                 sep="\t", chunks = 10e3, **kwargs):
        try:
            import pandas as pd
        except:
            ImportError("Please install pandas and rerun!")

        def _make_example(chunk, src_label, trg_label):
            sub_df = chunk[[src_label, trg_label]]
            sub_df_vals = sub_df.values
            for row in sub_df_vals:
                yield self.make_example(row, fields)

        format = format.lower()
        self.fields = fields
        self.src_field, self.trg_field = self.fields
        print("Src field label:", self.src_field[0])
        print("Trg field label:", self.trg_field[0])
        self.make_example = {
            'json': Example.fromJSON, 'dict': Example.fromdict,
            'tsv': Example.fromCSV, 'csv': Example.fromCSV}[format]

        if format not in TSVTranslationCorpus.allowed_formats:
            raise ValueError("Format not accepted!")
        if format == "tsv" and sep != "\t":
            raise ValueError("Separator must be tab for tsv files!")



        load_path = os.path.expanduser(path)
        chunk_examples = []

        for chunk in pd.read_csv(load_path, sep=sep, index_col=False, chunksize=chunks):
            if filter_query:
                if isinstance(filter_query, str):
                    chunk = chunk.query(filter_query)
                elif isinstance(filter_query, list):
                    for query in filter_query:
                        if isinstance(query, str):
                            chunk = chunk.query(query)

            chunk_examples.extend(_make_example(chunk, self.src_field[0], self.trg_field[0]))

        if fields:
            if isinstance(fields, dict):
                fields, field_dict = [], fields
                for field in field_dict.values():
                    if isinstance(field, list):
                        fields.extend(field)
                    else:
                        fields.append(field)

        super(TSVTranslationCorpus, self).__init__(chunk_examples, fields, **kwargs)


    @classmethod
    def splits(cls, path=None, root=DATA_DIR_PREPRO, train="train.tsv", validation="val.tsv", test="test.tsv", chunk_size_train = 10e3, max_sent_len = 30,
               **kwargs):

        assert os.path.isdir(path), "Directory: %s does not exist! Please generate splits, before creating datasets!" %path

        train_data = None if train is None else cls(
            os.path.join(path, train), chunks=chunk_size_train, **kwargs)
        val_data = None if validation is None else cls(
            os.path.join(path, validation), **kwargs)
        test_data = None if test is None else cls(
            os.path.join(path, test), **kwargs)
        return tuple(d for d in (train_data, val_data, test_data)
                     if d is not None)


def prepare_dataset_iterators(corpus="europarl", language_code="de",
                              src_l="de", v = 0, min_freq=5, max_sent_len=25,
                              batch_size=64, char_level=False,
                              include_lengths=False, device="cuda"):

    #### Create torchtext fields
    ####### SRC, TRG

    src_lang = "en" if src_l == "en" else language_code
    trg_lang = "en" if src_l == language_code else language_code

    print("Src lang:", src_lang)
    print("Trg lang:", trg_lang)
    print("Min_freq", min_freq)
    print("Max sequence length:", max_sent_len)


    tokenizer = lambda s: s.split() if char_level == False else lambda s: list(s)

    src_vocab = TranslationReversibleField(tokenize=tokenizer, include_lengths=include_lengths,  pad_token=PAD_TOKEN, unk_token=UNK_TOKEN)

    trg_vocab = TranslationReversibleField(tokenize=tokenizer, include_lengths=include_lengths, init_token=SOS_TOKEN, eos_token=EOS_TOKEN, pad_token=PAD_TOKEN, unk_token=UNK_TOKEN)

    fields = [(SRC_LABEL, src_vocab), (TRG_LABEL, trg_vocab)] if src_lang == "en" else [(TRG_LABEL, src_vocab), (SRC_LABEL, trg_vocab)]

    print("Fields created!")
    print(fields)

    ####### create splits

    queries = []

    if corpus == "europarl":
        root = get_full_path(DATA_DIR_PREPRO)
        #print("Root:", root)
        data_dir = os.path.join(root, corpus, language_code)
        #print("Datadir:", data_dir)
        if max_sent_len:
            data_dir = os.path.join(data_dir, str(max_sent_len))
         #   print("Datadir:", data_dir)

        if not os.path.isdir(data_dir):
            print("No files preprocessed with the given maximum length of {}. Generating split files...".format(
                max_sent_len))
            generate_splits_from_datasets(max_len=max_sent_len, language_code=language_code)

        else:
            files = os.listdir(data_dir)
            sp_fn = ["train.tsv", "val.tsv", "test.tsv"]
            already_splitted = [x in files for x in sp_fn].count(True)
            if already_splitted != 3:
                print("Some split files are missing. Generating split files...".format(
                    max_sent_len))
                generate_splits_from_datasets(max_len=max_sent_len, language_code=language_code)


        print("Loading data...")
        start = time.time()

        train, val, test = TabularDataset.splits(path=data_dir, train='train.tsv',
                                                 validation='val.tsv', test="test.tsv",
                                                 format='tsv',
                                                fields=fields)

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
                                                 filter_pred=lambda x: max(len(vars(x)['src']), len(vars(x)['trg'])) <= max_sent_len)
        end = time.time()
        print("Duration: {}".format(convert(end - start)))
        print("Total number of sentences: {}".format((len(train) + len(val) + len(test))))

    if v > 0:
        src_vocab.build_vocab(train.src, val.src, test.src, min_freq=min_freq, max_size=v)
        trg_vocab.build_vocab(train.trg, val.trg, test.src, min_freq=min_freq, max_size=v)
        print("Src vocabulary created!")
    else:
        src_vocab.build_vocab(train.src, val.src, test.src, min_freq=min_freq)
        trg_vocab.build_vocab(train.trg, val.trg, test.src, min_freq=min_freq)
        print("Src vocabulary created!")




    #### Iterators

    # Create iterators to process text in batches of approx. the same length
    train_iter = data.BucketIterator(train, batch_size=batch_size, device=device, repeat=False,
                                     sort_key=lambda x: len(x.src), sort_within_batch=True, shuffle=True)
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

