import tensorflow.keras.backend as kb
import tensorflow.keras.layers as kl

def custom_loss_function(y_true, y_pred):
            #y_true is actually reward
        #ask reddit for advice on this!!!
        #is kb.log(y_pred) correct???

        #loss = -kb.mean(kl.multiply([y_true, kb.log(y_pred)]))
    
        #SHOULD I SUBRACT IF 1 IF I ADD TO 0???
    #return -kb.mean(kb.sum(kl.multiply([y_true, kb.log(y_pred+0.0001)]), axis=-1))
    return kb.mean(kb.sum(kl.multiply([y_true, kb.log((1 - y_pred) + 0.001)]), axis=-1))