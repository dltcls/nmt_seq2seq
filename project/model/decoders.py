import torch
from torch import nn
import torch.functional as F

from project.model.layers import MaxoutLinearLayer


class Decoder(nn.Module):
    def __init__(self, trg_vocab_size, embedding, h_dim, num_layers, dropout_p=0.0, rnn_cell="lstm"):
        super(Decoder, self).__init__()
        self.vocab_size, self.embedding_size = trg_vocab_size, embedding
        self.num_layers = num_layers
        self.h_dim = h_dim
        self.dropout_p = dropout_p

        # Create word embedding, LSTM
        self.embedding = nn.Embedding(self.vocab_size, self.embedding_size)

        if rnn_cell.lower() == "lstm":
            self.rnn = nn.LSTM(self.embedding_size, self.h_dim, self.num_layers,
                               dropout=self.dropout_p if self.num_layers > 1 else 0)
        else:
            self.rnn = nn.GRU(self.embedding_size, self.h_dim, self.num_layers,
                              dropout=self.dropout_p if self.num_layers > 1 else 0)

        self.dropout = nn.Dropout(self.dropout_p)

    def forward(self, x, h0, context=None):
        print("X:", x.shape)
        print("H", h0[0].shape)
        # Embed text and pass through GRU
        x = self.embedding(x)
        print("EMBE", x.shape)
        x = self.dropout(x)
        out, h = self.rnn(x, h0)
        print("OUT", out.shape)

        return out, h


class ContextDecoder(Decoder):
    def __init__(self, trg_vocab_size, emb_size, h_dim, num_layers, dropout_p=0.0):
        super().__init__(trg_vocab_size, emb_size, h_dim, num_layers, dropout_p, rnn_cell="gru")

        self.rnn = nn.GRU(self.embedding.embedding_dim + h_dim, h_dim, num_layers=num_layers,
                          dropout=dropout_p if num_layers > 1 else 0)

        self.dropout = nn.Dropout(dropout_p)

    def forward(self, x, h0, context=None, val=False):
        print("Context", h0.shape) ## 1,1,100
        print(x.shape)
        if not val:
            x = x.unsqueeze(0)
        print(x.shape)

        embedded = self.dropout(self.embedding(x))  # [1,64,500] - seq_len, bs, emb_size, 1,1,emb_size
        print(embedded.size())

        emb_con = torch.cat((embedded, context), dim=2)

        output, h = self.rnn(emb_con, h0)  # 1,64,500
        print(output.size())

        output = torch.cat((embedded.squeeze(0), h.squeeze(0), context.squeeze(0)),
                           dim=1)
        print(output.size()) # 64, 1500

        return output, h
