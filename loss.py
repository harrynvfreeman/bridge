import keras.backend as kb
import keras.layers as kl

def custom_loss_function(y_true, y_pred):
    #y_true is actually reward
    #ask reddit for advice on this!!!
    #is kb.log(y_pred) correct???

    loss = -kb.mean(kl.multiply([y_true, kb.log(y_pred)]))
    
    return loss