import numpy as np
import keras
from model import buildModels
from pickle import dump, load
import os
import ctypes
import pathlib
from loss import custom_loss_function

deckSize = 52
vulnSize = 2
numPlayers = 4
numModelsToSave = 100
ennSavePath = ('./ennModels/ennModel_')
ennVersionPath = ('./ennModels/version')
pnnSavePath = ('./pnnModels/pnnModel_')
pnnVersionPath = ('./pnnModels/version')
###Remove duplicate copies below from model.py
bidFeatureSize = 318
ennInputShape = (deckSize + vulnSize + 2*bidFeatureSize)
pnnInputShape = ennInputShape + deckSize
bidFeatureIndex = deckSize + vulnSize
bidPartnerIndex = bidFeatureIndex + bidFeatureSize
ennOutputIndex = bidPartnerIndex + bidFeatureSize
numBids = 38
passBid = 35
doubleBid = 36
redoubleBid = 37
blockSize = 9
numBidSuits = 5

miniBatchSize = 100

rng = np.random.default_rng()

libfile = pathlib.Path().absolute() / "Ddsinterface.so"
c_lib = ctypes.CDLL(libfile)
c_lib.calcScore.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                       np.ctypeslib.ndpointer(dtype=np.int32),
                       np.ctypeslib.ndpointer(dtype=np.int32),
                       np.ctypeslib.ndpointer(dtype=np.int32),
                       np.ctypeslib.ndpointer(dtype=np.int32)]
c_lib.calcScore.restype = ctypes.c_int
c_lib.initialize()

def saveInitialModels():
    ennModel, pnnModel = buildModels()
    ennVersion = 0
    pnnVersion = 0
    ennModel.save(ennSavePath + str(ennVersion) + '.h5')
    pnnModel.save(pnnSavePath + str(pnnVersion) + '.h5')
    dump(ennVersion, open(ennVersionPath, 'wb'))
    dump(pnnVersion, open(pnnVersionPath, 'wb'))
    
def updateEnnModel(ennModel):
    ennVersion = load(open(ennVersionPath, 'rb'))
    if (ennVersion >= numModelsToSave):
        modelPathToDelete = ennSavePath + str(ennVersion - numModelsToSave) + '.h5'
        os.remove(modelPathToDelete)
    ennVersion = ennVersion + 1
    ennModel.save(ennSavePath + str(ennVersion) + '.h5')
    dump(ennVersion, open(ennVersionPath, 'wb'))
    
def randomlySelectEnnModel():
    ennVersion = load(open(ennVersionPath, 'rb'))
    if ennVersion >= numModelsToSave:
        randVersion = np.random.randint(ennVersion - numModelsToSave + 1, ennVersion)
    else:
        randVersion = np.random.randint(0, ennVersion + 1)
        
    modelPath =ennSavePath + str(randVersion) + '.h5'
    return keras.models.load_model(modelPath, custom_objects={'custom_loss_function': custom_loss_function})

def loadTargetEnnModel():
    ennVersion = load(open(ennVersionPath, 'rb'))
    modelPath = ennSavePath + str(ennVersion) + '.h5'
    return keras.models.load_model(modelPath, custom_objects={'custom_loss_function': custom_loss_function})

def updatePnnModel(pnnModel):
    pnnVersion = load(open(pnnVersionPath, 'rb'))
    if (pnnVersion >= numModelsToSave):
        modelPathToDelete = pnnSavePath + str(pnnVersion - numModelsToSave) + '.h5'
        os.remove(modelPathToDelete)
    pnnVersion = pnnVersion + 1
    pnnModel.save(pnnSavePath + str(pnnVersion) + '.h5')
    dump(pnnVersion, open(pnnVersionPath, 'wb'))

def randomlySelectPnnModel():
    pnnVersion = load(open(pnnVersionPath, 'rb'))
    if pnnVersion >= numModelsToSave:
        randVersion = np.random.randint(pnnVersion - numModelsToSave + 1, pnnVersion)
    else:
        randVersion = np.random.randint(0, pnnVersion + 1)
        
    modelPath =pnnSavePath + str(randVersion) + '.h5'
    return keras.models.load_model(modelPath, custom_objects={'custom_loss_function': custom_loss_function})

def loadTargetPnnModel():
    pnnVersion = load(open(pnnVersionPath, 'rb'))
    modelPath = pnnSavePath + str(pnnVersion) + '.h5'
    return keras.models.load_model(modelPath, custom_objects={'custom_loss_function': custom_loss_function})
    

#Step 1 is generating random games
def generateRandomGame():
    deck = rng.choice(52, size=52, replace=False)
    vulnerable = np.random.randint(0, 2, size=2)
    dealer = np.random.randint(0,4)
    return deck, vulnerable, dealer


def generateRandomGames(numGames):
    decks = np.zeros((numGames, deckSize), dtype=np.int32)
    vulnerables = np.zeros((numGames, vulnSize), dtype=np.int32)
    dealers = np.zeros((numGames, 1), dtype=np.int32)
    
    for i in range(numGames):
        deck, vulnerable, dealer = generateRandomGame()
        decks[i] = deck
        vulnerables[i] = vulnerable
        dealers[i] = dealer
        
    return decks, vulnerables, dealers

def selfPlay(decks, vulnerables, dealers):
    numMiniBatches = decks.shape[0] // miniBatchSize
    
    targetEnnModel = loadTargetEnnModel()
    targetPnnModel = loadTargetPnnModel()
    
    for i in range(numMiniBatches):
        
        opponentEnnModel = randomlySelectEnnModel()
        opponentPnnModel = randomlySelectPnnModel()
        
        #pnn
        rValues = []
        pnnInputValues = []
        
        #enn
        cardValues = []
        ennInputValues = []
        
        for j in range(miniBatchSize):
            index = i*miniBatchSize + j
            deck = decks[index]
            vulnerable = vulnerables[index]
            dealer = dealers[index, 0]
            
            for pos in range(2):
                hbid, declarer, isDoubled, hands, ennInputs, pnnInputs = bid(deck, vulnerable, dealer, pos,
                                                       targetEnnModel, targetPnnModel,
                                                       opponentEnnModel, opponentPnnModel)
                declarerTeam = declarer%2
                score = getDoubleDummyScore(hbid, declarer, isDoubled, vulnerable[declarerTeam], hands)
                
                for k in range(len(ennInputs)):
                    bidder = (dealer + k) % numPlayers
                    bidderScore = score if bidder % 2 == declarer % 2 else 0 - score
                    
                    rValues.append(bidderScore)
                    pnnInputValues.append(pnnInputs[k])
                    
                    cardValues.append(hands[bidder])
                    ennInputValues.append(ennInputs[k])
                
        npEnnInputValues = np.array(ennInputValues)
        npCardValues = np.array(cardValues)
        npPnnInputValues = np.array(pnnInputValues)
        npRValues = np.array(rValues)
        
        #print(npEnnInputValues.shape)
        #print(npPnnInputValues.shape)
        #print(npCardValues.shape)
        #print(npRValues.shape)
        
        targetEnnModel.fit(x=np.array(ennInputValues), y=np.array(cardValues))
        targetPnnModel.fit(x=np.array(pnnInputValues), y=np.array(rValues))
        
        if i % 100 == 99:
            updateEnnModel(targetEnnModel)
            updatePnnModel(targetPnnModel)
        
        

def bid(deck, vulnerable, dealer, pos, ennModel, pnnModel, opponentEnnModel, opponentPnnModel):
    bidder = dealer
    numPass = -1
    highestBid = -1
    isDoubled = -1
    bidIndex = -1
    lastNonPassBid = -1
    lastTeamToBid = -1
    teamToBid = bidder % 2
    declarers = [-1, -1, -1, -1, -1]
    
    bidFeature = np.zeros((bidFeatureSize))
    bids = np.zeros((numPlayers, bidFeatureSize))
    oppVulnerable = np.flip(vulnerable)
        
    ###can we vectore this?
    hands = np.zeros((numPlayers, deckSize), dtype=np.int32)
    for i in range(numPlayers):
        hands[i, deck[i::numPlayers]] =  1
    
    
    ennInput = np.zeros((1, ennInputShape))
    pnnInput = np.zeros((1, pnnInputShape))
    
    ennInputs = []
    pnnInputs = []
    while numPass < 3 and bidIndex < bidFeatureSize:

        ennInput[0, np.arange(deckSize)] = hands[bidder]
        ennInput[0, bidFeatureIndex:bidPartnerIndex] = bidFeature
        ennInput[0, bidPartnerIndex:] = bids[bidder - 2 if bidder - 2 >= 0 else bidder + 2]
        
        if (bidder % 2 == pos):
            ennInput[0, deckSize:bidFeatureIndex] = vulnerable
            pnnInput[0, deckSize:bidFeatureIndex] = vulnerable
            ennModelToUse = ennModel
            pnnModelToUse = pnnModel
        else:
            ennInput[0, deckSize:bidFeatureIndex] = oppVulnerable
            pnnInput[0, deckSize:bidFeatureIndex] = oppVulnerable
            ennModelToUse = opponentEnnModel
            pnnModelToUse = opponentPnnModel
        
        ennOutput = ennModelToUse.predict(ennInput)
        ennInputs.append(ennInput[0])
        
        ###Do we do this?
        ennOutput[0, hands[bidder]] = 0
        ennOutput[0] = ennOutput[0] / np.sum(ennOutput[0])
        
        pnnInput[0, 0:deckSize] = hands[bidder]
        pnnInput[0, bidFeatureIndex:bidPartnerIndex] = bidFeature
        pnnInput[0, bidPartnerIndex:ennOutputIndex] = bids[bidder - 2 if bidder - 2 >= 0 else bidder + 2]
        pnnInput[0, ennOutputIndex:] = ennOutput
        
        bidProbs = pnnModelToUse.predict(pnnInput)
        pnnInputs.append(pnnInput[0])
        
        #need to mask illegal moves?
        legalMoves = getLegalMoves(highestBid, lastNonPassBid, teamToBid, lastTeamToBid)
        #make faster?
        bidProbs[0] = np.multiply(bidProbs[0], legalMoves)
        bidProbs[0] = bidProbs[0] / np.sum(bidProbs[0])
        
        #can letter max this vectorize to do multiple predicts at same time
        #ie p=out[i]
        bid = np.random.choice(numBids, p=bidProbs[0])
        
        if bid == passBid:
            numPass = numPass + 1
        elif bid < doubleBid:
            numPass = 0
            highestBid = bid
            isDoubled = 0;
            lastNonPassBid = bid
            lastTeamToBid = teamToBid
            if (declarers[bid % numBidSuits] == -1):
                declarers[bid % numBidSuits] = bidder
        else:
            numPass = 0
            lastNonPassBid = bid
            isDoubled = isDoubled + 1;
            
        if numPass < 3:
            bidder = (bidder + 1) % numPlayers
            teamToBid = 1 - teamToBid
            bidIndex = getNextBidIndex(bid, bidIndex)
            bidFeature[bidIndex] = 1
            bids[bidder, bidIndex] = 1
        
    return highestBid, declarers[highestBid % numBidSuits], isDoubled, hands, ennInputs, pnnInputs

###speed up by avoid np.zeros (take out)
def getLegalMoves(highestBid, lastNonPassBid, teamToBid, lastTeamToBid):
    legalMoves = np.zeros((numBids))
    for i in range(highestBid + 1, passBid):
        legalMoves[i] = 1
    
    legalMoves[passBid] = 1
    
    if (highestBid > - 1 and lastNonPassBid < doubleBid and teamToBid != lastTeamToBid):
        legalMoves[doubleBid] = 1
    elif (highestBid > -1 and lastNonPassBid == doubleBid and teamToBid == lastTeamToBid):
        legalMoves[redoubleBid] = 1
    return legalMoves
    
def getNextPassIndex(currentBidIndex):
    if currentBidIndex < 2:
        return currentBidIndex + 1
    
    blockIndex = (currentBidIndex - 3) % blockSize
    
    if blockIndex == 0:
        return currentBidIndex + 1
    if blockIndex == 1:
        return currentBidIndex + 1
    if blockIndex == 2:
        return currentBidIndex + 2
    if blockIndex == 3:
        return currentBidIndex + 1
    if blockIndex == 4:
        return currentBidIndex + 1
    if blockIndex == 5:
        return currentBidIndex + 2
    if blockIndex == 6:
        return currentBidIndex + 1
    if blockIndex == 7:
        return currentBidIndex + 1
    if blockIndex == 8:
        return currentBidIndex + 2
    
def getNextDoubleIndex(currentBidIndex):
    blockIndex = (currentBidIndex - 3) % blockSize
    return currentBidIndex + 3 - blockIndex

def getNextBidIndex(bid, currentBidIndex):
    if bid < passBid:
        return bid*blockSize + 3
    
    if bid == passBid:
        return getNextPassIndex(currentBidIndex)
    
    return getNextDoubleIndex(currentBidIndex)

def getDoubleDummyScore(bid, declarer, isDoubled, vulnerable, hands):
    if bid == -1:
        return 0
    
    return c_lib.calcScore(bid % numBidSuits, (bid // numBidSuits) + 1,  declarer, isDoubled, vulnerable,
                           hands[0], hands[1], hands[2], hands[3])
    
    