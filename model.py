from keras.models import Model
from keras.layers import Add, Input, Dense
from keras.optimizers import SGD
#from keras import regularizers
from loss import custom_loss_function
from keras import backend as kb

###Do I want to limit activation function?  See Relu keras
###https://keras.io/api/layers/activation_layers/

###Skip layer add vs concat?
###https://keras.io/api/layers/merging_layers/

###Should I use regularization???

###Switch to tf.keras!!!

###Consider binary cross entropy from_logits true
###and doing sigmoid after

###Should we do masking inside model???
###https://stackoverflow.com/questions/55669699/keras-masking-output-layer

#regConstant = 0.0001
learningRate = 0.01
#momentum = 0.9

cardShape = 52;
vulnShape = 2;
bidShape = 318;

#batchNorm = False;
#leakyRelu = False;

ennInputShape = (cardShape + vulnShape + 2*bidShape)
ennHiddenLayerSize = ennInputShape
ennHiddenLayerNum = 6
ennOutputShape = 52

pnnInputShape = ennInputShape + ennOutputShape
pnnHiddenLayerSize = pnnInputShape
pnnHiddenLayerNum = 10
pnnOutputShape = 38

def layer(x, numLayers, hiddenLayerSize):
    a = x
    skip = False
    for i in range(numLayers):
        b = Dense(hiddenLayerSize, activation='relu')(a)
        if (skip):
            a = Add()([a, b])
        else:
            a = b
        skip = not skip

    return a

def buildEnn(x):
    a = layer(x, ennHiddenLayerNum, ennHiddenLayerSize)
    out = Dense(ennOutputShape, activation='sigmoid')(a)
    return out

def buildEnnModel():
    ennInput = Input(shape=(ennInputShape, ))
    ennOutput = buildEnn(ennInput)
    ennModel = Model(inputs = [ennInput], outputs = [ennOutput])
    ennModel.compile(optimizer=SGD(lr=learningRate), loss='binary_crossentropy')
    return ennModel
    
    
def buildPnn(x):
    a = layer(x, pnnHiddenLayerNum, pnnHiddenLayerSize)
    out = Dense(pnnOutputShape, activation='softmax')(a)
    return out

def buildPnnModel():
    pnnInput = Input(shape=(pnnInputShape, ))
    pnnOutput = buildPnn(pnnInput)
    pnnModel = Model(inputs = [pnnInput], outputs = [pnnOutput])
    pnnModel.compile(optimizer=SGD(lr=learningRate), loss=custom_loss_function)
    return pnnModel

def buildModels():
    return buildEnnModel(), buildPnnModel()
