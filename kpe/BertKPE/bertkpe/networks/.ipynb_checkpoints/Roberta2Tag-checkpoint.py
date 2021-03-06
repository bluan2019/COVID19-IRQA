import torch
import logging
import numpy as np
from torch import nn
import torch.nn.functional as F
from torch.nn import CrossEntropyLoss
from ..transformers import RobertaForTokenClassification

logger = logging.getLogger()



class RobertaForSeqTagging(RobertaForTokenClassification):
    def forward(self, input_ids, attention_mask, valid_ids, active_mask, valid_output, labels=None):
        
        # --------------------------------------------------------------------------------
        # Bert Embedding Outputs
        outputs = self.roberta(input_ids=input_ids,
                               attention_mask=attention_mask)
        
        sequence_output = outputs[0]
        
        # --------------------------------------------------------------------------------
        # Valid Outputs : get first token vector  
        batch_size = sequence_output.size(0)
        for i in range(batch_size):
            valid_num = sum(valid_ids[i]).item()

            vectors = sequence_output[i][valid_ids[i] == 1]
            valid_output[i, :valid_num].copy_(vectors)

        # --------------------------------------------------------------------------------
        # Dropout
        sequence_output = self.dropout(valid_output)
        logits = self.classifier(sequence_output)
        
        # --------------------------------------------------------------------------------
        # Active Logits
        active_loss = active_mask.view(-1) == 1 # [False, True, ...]
        active_logits = logits.view(-1, self.num_labels)[active_loss] # False

        if labels is not None:
            loss_fct = CrossEntropyLoss()
            active_labels = labels.view(-1)[active_loss]
            loss = loss_fct(active_logits, active_labels)
            return loss
        else:
            return active_logits
        
# class BertForSeqTagging(BertForTokenClassification):
            
#     def forward(self, input_ids, attention_mask, valid_ids, active_mask, labels=None):
        
#         outputs = self.bert(input_ids=input_ids,
#                             attention_mask=attention_mask)
#         sequence_output = outputs[0]
        
#         batch_size, max_len, feature_dim = sequence_output.shape
#         valid_output = torch.zeros(batch_size, max_len, feature_dim,
#                                    dtype=torch.float32, device='cuda')
#         # get valid outputs : first tokens
#         for i in range(batch_size):
#             k = -1
#             for j in range(max_len):
#                 if valid_ids[i][j].item() == 1:
#                     k += 1
#                     valid_output[i][k] = sequence_output[i][j]
                    
#         sequence_output = self.dropout(valid_output)
#         logits = self.classifier(sequence_output)

#         active_loss = active_mask.view(-1) == 1 # [False, True, ...]
#         active_logits = logits.view(-1, self.num_labels)[active_loss] # False

#         if labels is not None:
#             loss_fct = CrossEntropyLoss()
#             active_labels = labels.view(-1)[active_loss]
#             loss = loss_fct(active_logits, active_labels)
#             return loss
#         else:
#             return active_logits