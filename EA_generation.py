# this is the run script for our own data(MP and zinc), try to predict IE and EA 
from __future__ import print_function
import tensorflow as tf
import numpy as np 
import sys
np.set_printoptions(threshold=sys.maxsize)
import pandas as pd
from molecule_feature_prediction.feature import molecules
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error
import SSVAE


beta=10000.
 
# include only fourty 39 characters
char_set=[" ", "@", "H", "N", "S", "o", "i", "6", "I", "]", "P", "5", ")", "4", "8", "B", "F", 
           "3", "9", "c", "-", "2", "p", "0", "n", "C", "(", "=", "+", "#", "1", "/", "7", 
           "s", "O", "[", "Cl", "Br", "\\"] 




ls_smi_MP = pd.read_csv('MP_clean_canonize_cut.csv')['smiles'].tolist()
ls_smi_zinc = pd.read_csv('zinc_30W.csv')['smiles'].tolist()
arr_IE_EA = pd.read_csv('MP_clean_canonize_cut.csv')[['IE','EA']].values

X_L, Xs_L = molecules(ls_smi_MP).one_hot_RNN(char_set=char_set)
# print(X_L.shape[0],len(ls_smi_MP_new))

X_U, Xs_U = molecules(ls_smi_zinc).one_hot_RNN(char_set=char_set)
# print(X_U.shape[0],len(ls_smi_zinc_new))

np.random.seed(0)
perm_L = np.random.permutation(X_L.shape[0])
np.random.seed(0)
perm_U = np.random.permutation(X_U.shape[0])

trnX_L, valX_L, tstX_L = np.split(X_L[perm_L], [int(len(X_L)*0.8), int(len(X_L)*0.9)])
trnXs_L, valXs_L, tstXs_L = np.split(Xs_L[perm_L], [int(len(Xs_L)*0.8), int(len(X_L)*0.9)])
trnY_L, valY_L, tstY_L = np.split(arr_IE_EA[perm_L], [int(len(arr_IE_EA)*0.8), int(len(arr_IE_EA)*0.9)])
print(trnY_L.shape)

trnX_U, valX_U, tstX_U = np.split(X_U[perm_U], [int(len(X_U)*0.8), int(len(X_U)*0.9)])
trnXs_U, valXs_U, tstXs_U = np.split(Xs_U[perm_U], [int(len(Xs_U)*0.8), int(len(Xs_U)*0.9)])

scaler_Y = StandardScaler()
scaler_Y.fit(arr_IE_EA)
trnY_L=scaler_Y.transform(trnY_L)
valY_L=scaler_Y.transform(valY_L)

## model training
print('::: model training')

seqlen_x = trnX_L.shape[1]
dim_x = trnX_L.shape[2]
dim_y = trnY_L.shape[1]
dim_z = 100
dim_h = 250

n_hidden = 3
batch_size = 200

model = SSVAE.Model(seqlen_x = seqlen_x, dim_x = dim_x, dim_y = dim_y, dim_z = dim_z, dim_h = dim_h,
                    n_hidden = n_hidden, batch_size = batch_size, beta = float(beta), char_set = char_set)

with model.session:
    model.load_model(model_name='./model.ckpt',Y=trnY_L)

    for i in [0,2,3,4,5]:
        ls_smi_conditional = [] 
        yid = 1    # 0.IE   1.EA 
        ytarget = i
        ytarget_transform = (ytarget-scaler_Y.mean_[yid])/np.sqrt(scaler_Y.var_[yid])
        
        print('this is for conditional sampling')

        for t in range(1000):
            smi = model.sampling_conditional(yid, ytarget_transform) 
            print(smi)
            ls_smi_conditional.append(smi)

        data_conditional = pd.DataFrame(ls_smi_conditional, columns=['SMILES']).drop_duplicates()
        data_conditional.to_csv("conditional_smi_EA_"+str(i)+".csv", index=False)
        
