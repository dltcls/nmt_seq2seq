"""
This class defines the Attention Layer to use when training the model with the attention mechanism.

Code integrated from this repository:
https://github.com/lukemelas/Machine-Translation
under the courtesy of the author
"""

import torch.nn as nn

class Attention(nn.Module):
    def __init__(self, bidirectional=False, attn_type='dot', h_dim=300):
        super(Attention, self).__init__()
        if attn_type not in ['dot', 'none']:
            raise Exception('Incorrect attention type')
        self.bidirectional = bidirectional
        self.attn_type = attn_type
        self.h_dim = h_dim
        self.softmax = nn.Softmax(dim=1)

    def attention(self, encoder_outputs, decoder_outputs):
        '''Produces context and attention distribution'''
        # If no attention, return context of zeros
        if self.attn_type == 'none':
            return None

        # Deal with bidirectional encoder, move batches first
        if self.bidirectional:
            encoder_outputs = encoder_outputs.contiguous().\
                view(encoder_outputs.size(0), encoder_outputs.size(1), 2, -1).\
                sum(2).view(encoder_outputs.size(0), encoder_outputs.size(1), -1)
        encoder_outputs = encoder_outputs.transpose(0, 1)
        decoder_outputs = decoder_outputs.transpose(0, 1)

        # DOT ATTENTION
        attn = encoder_outputs.bmm(decoder_outputs.transpose(1, 2))
        # Compute scores
        attn = self.softmax(attn).transpose(1,2)

        # Compute the context
        context = attn.bmm(encoder_outputs)
        context = context.transpose(0,1)

        return context, attn

    def forward(self, out_e, out_d):
        '''Produces context using attention distribution'''
        context, attn = self.attention(out_e, out_d)
        return context

    def get_visualization(self, in_e, out_e, out_d):
        '''Gives attention distribution for visualization'''
        context, attn = self.attention(out_e, out_d)
        return attn

