from keras.models import  Sequential
from keras.layers import  Dense, LSTM, BatchNormalization, Dropout, Layer
import keras.ops as K

class Attention(Layer):
    def __init__(self,**kwargs):
        super(Attention,self).__init__(**kwargs)

    def build(self,input_shape):
        self.W=self.add_weight(name="att_weight",shape=(input_shape[-1],1),initializer="normal")
        self.b=self.add_weight(name="att_bias",shape=(input_shape[1],1),initializer="zeros")        
        super(Attention, self).build(input_shape)

    def call(self,x):
        et=K.squeeze(K.tanh(K.dot(x,self.W)+self.b),axis=-1)
        at=K.softmax(et)
        at=K.expand_dims(at,axis=-1)
        output=x*at
        return K.sum(output,axis=1)

    def compute_output_shape(self,input_shape):
        return (input_shape[0],input_shape[-1])

    def get_config(self):
        return super(Attention,self).get_config()

N_INPUT = 4

def build_model(lstm_units = [50], dropout = 0.1, use_batchnorm = True):
    model = Sequential()

    for i, units in enumerate(lstm_units):

        if i == 0:
           model.add(LSTM(
                units, 
                dropout=dropout,
                recurrent_dropout=dropout,
                return_sequences=True,
                input_shape=(N_INPUT,1)
            ))
        else:
            model.add(LSTM(
                units,
                dropout=dropout,
                recurrent_dropout=dropout,
                return_sequences= True
            ))


        if use_batchnorm:
            model.add(BatchNormalization())

    model.add(Dropout(dropout))

    model.add(Attention())

    model.add(Dense(1,activation='sigmoid',trainable=True))

    return model
