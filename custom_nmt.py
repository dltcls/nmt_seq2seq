import os, datetime, time, sys

import torch
import torch.nn as nn

from project.experiment.setup import experiment_parser
from project.model.models import Seq2Seq
from project.utils.constants import SOS_TOKEN, EOS_TOKEN, PAD_TOKEN, UNK_TOKEN
from project.utils.data.vocabulary import get_vocabularies_iterators, print_data_info
from project.utils.training import validate, train_model
from project.utils.utils import convert, Logger
from settings import MODEL_STORE
import math


def main():
    args = experiment_parser().parse_args()
    device = "cuda" if (args.cuda and torch.cuda.is_available()) else "cpu"
    args.cuda = device
    print("Running experiment on:", device)

   # args.corpus = "europarl"

    lang_code = args.lang_code
    src_lang = lang_code if args.reverse else "en"
    trg_lang = "en" if src_lang == lang_code else lang_code
    model_type = "custom"
    args.model_type = model_type

    args.reduce = [200000, 20000, 5000]
    args.epochs = 50

    print("Language combination ({}-{})".format(src_lang, trg_lang))

    lang_comb = "{}_{}".format(src_lang, trg_lang)
    layers = args.nlayers
    direction = "bi" if args.bi else "uni"

    experiment_path = os.path.join(MODEL_STORE, lang_comb, model_type, str(layers),
                                   direction,
                                   datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))
    os.makedirs(experiment_path, exist_ok=True)


    # Load and process data
    time_data = time.time()
    SRC, TRG, train_iter, val_iter, test_iter, train_data, val_data, test_data = \
        get_vocabularies_iterators(src_lang, args)

    print('Loaded data. |SRC| = {}, |TRG| = {}, Time: {}.'.format(len(SRC.vocab), len(TRG.vocab), convert(time.time() - time_data)))

    args.src_vocab_size = len(SRC.vocab)
    args.trg_vocab_size = len(TRG.vocab)
    data_logger = Logger(path=experiment_path, file_name="data.log")
    print_data_info(data_logger, train_data, val_data, test_data, SRC, TRG, args.corpus)

    # Load embeddings if available
    # Create model

    if args.bi and args.reverse_input:
        args.reverse_input = False

    tokens_bos_eos_pad_unk = [TRG.vocab.stoi[SOS_TOKEN], TRG.vocab.stoi[EOS_TOKEN], TRG.vocab.stoi[PAD_TOKEN], TRG.vocab.stoi[UNK_TOKEN]]
    ### src_vocab_size, trg_vocab_size, emb_size, h_dim, num_layers, dropout_p, bi, rnn_type="lstm", tokens_bos_eos_pad_unk=[0, 1, 2, 3],  device=DEFAULT_DEVICE
    model = Seq2Seq(args, tokens_bos_eos_pad_unk)

    # Load pretrained model
    if args.model is not None and os.path.isfile(args.model):
        model.load_state_dict(torch.load(args.model))
        print('Loaded pretrained model.')

    model = model.to(device)

    # Create weight to mask padding tokens for loss function
    weight = torch.ones(len(TRG.vocab))
    weight[TRG.vocab.stoi[PAD_TOKEN]] = 0
    weight = weight.to(device)

    # Create loss function and optimizer
    criterion = nn.CrossEntropyLoss(weight=weight)
    optimizer = torch.optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=args.lr)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=30, factor=0.25, verbose=True,
                                                           cooldown=6)

    # Create directory for logs, create logger, log hyperparameters
    logger = Logger(experiment_path)
    logger.log('COMMAND ' + ' '.join(sys.argv), stdout=False)
    logger.log('ARGS: {}\nOPTIMIZER: {}\nLEARNING RATE: {}\nSCHEDULER: {}\nMODEL: {}\n'.format(args, optimizer, args.lr,
                                                                                               vars(scheduler), model),
               stdout=False)
    # Train, validate, or predict{math.exp(avg_val_loss):7.3f}

    results_logger = Logger(experiment_path, file_name="results.log")
    start_time = time.time()

    #train_iter, val_iter, model, criterion, optimizer, scheduler, epochs, logger=None, device=DEFAULT_DEVICE
    train_model(train_iter, val_iter, model, criterion, optimizer, scheduler,TRG=TRG, epochs=args.epochs, logger=logger, device=device)

    ### Evaluation on test set
    beam_size = 1
    logger.log("Validation of test set - Beam size: {}".format(beam_size))
    val_loss, bleu= validate(val_iter=test_iter, model=model, criterion=criterion, device=device, TRG=TRG, beam_size=1)
    logger.log(
        f'\t Val. Loss: {val_loss:.3f} |  Val. PPL: {math.exp(val_loss):7.3f} | Val. BLEU: {bleu:.3f}')

   # beam_size = 2
   # logger.log("Validation of test set - Beam size: {}".format(beam_size))
   # validate(test_iter, model, TRG, logger, device, test_set=True)

    beam_size = 5
    logger.log("Validation of test set - Beam size: {}".format(beam_size))
    val_loss, bleu = validate(val_iter=test_iter, model=model, criterion=criterion, device=device, TRG=TRG, beam_size=5)
    logger.log(
        f'\t Val. Loss: {val_loss:.3f} |  Val. PPL: {math.exp(val_loss):7.3f} | Val. BLEU: {bleu:.3f}')

    logger.log('Finished in {}'.format(convert(time.time() - start_time)))
    return


if __name__ == '__main__':
    print(' '.join(sys.argv))
    main()
