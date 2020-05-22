import numpy as np
import tensorflow.keras as keras
import model
from pickle import dump, load
import os
import ctypes
import pathlib
from loss import custom_loss_function
import random
from tensorflow.keras.optimizers import SGD
import BridgeState

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
modelUpdateNum = 100

#forceFirstBidProb = 0.25
forceFirstBidProb = -1

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

def loadTargetEnnModel():
    try:
        ennVersion = load(open(ennVersionPath, 'rb'))
        modelPath = ennSavePath + str(ennVersion) + '.h5'
        return keras.models.load_model(modelPath), ennVersion + 1
    except FileNotFoundError:
        return model.buildEnnModel(), 0
    
def updateEnnModel(ennModel):
    try:
        ennVersion = load(open(ennVersionPath, 'rb'))
    except FileNotFoundError:
        ennVersion = -1
        
    if (ennVersion >= numModelsToSave):
        modelPathToDelete = ennSavePath + str(ennVersion - numModelsToSave) + '.h5'
        os.remove(modelPathToDelete)
    ennVersion = ennVersion + 1
    ennModel.save(ennSavePath + str(ennVersion) + '.h5')
    dump(ennVersion, open(ennVersionPath, 'wb'))
    return ennVersion
    
def loadTargetPnnModel():
    try:
        pnnVersion = load(open(pnnVersionPath, 'rb'))
        modelPath = pnnSavePath + str(pnnVersion) + '.h5'
        return keras.models.load_model(modelPath, custom_objects={'custom_loss_function': custom_loss_function}), pnnVersion + 1
    except FileNotFoundError:
        return model.buildPnnModel(), 0

def updatePnnModel(pnnModel):
    try:
        pnnVersion = load(open(pnnVersionPath, 'rb'))
    except FileNotFoundError:
        pnnVersion = -1
        
    if (pnnVersion >= numModelsToSave):
        modelPathToDelete = pnnSavePath + str(pnnVersion - numModelsToSave) + '.h5'
        os.remove(modelPathToDelete)
    pnnVersion = pnnVersion + 1
    pnnModel.save(pnnSavePath + str(pnnVersion) + '.h5')
    dump(pnnVersion, open(pnnVersionPath, 'wb'))
    return pnnVersion

def randomlySelectModels():
    try:
        version = load(open(ennVersionPath, 'rb'))
    except FileNotFoundError:
        print('Playing against random version')
        return model.buildEnnModel(), model.buildPnnModel()
    
    if version >= numModelsToSave:
        randVersion = np.random.randint(version - numModelsToSave + 1, version + 1)
    else:
        randVersion = np.random.randint(0, version + 1)
        
    ###Take out below for random
    randVersion = version
    
    print('Playing against version: ' + str(randVersion))
    ennModelPath = ennSavePath + str(randVersion) + '.h5'
    pnnModelPath = pnnSavePath + str(randVersion) + '.h5'
    ennModel = keras.models.load_model(ennModelPath)
    pnnModel = keras.models.load_model(pnnModelPath, custom_objects={'custom_loss_function': custom_loss_function})
    return ennModel, pnnModel

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
    
    targetEnnModel, version = loadTargetEnnModel()    
    targetPnnModel, version = loadTargetPnnModel()
    
    logCount = 0
    
    opponentEnnModel, opponentPnnModel = randomlySelectModels()
    
    for i in range(numMiniBatches):
        
        #pnn
        pnnRewards = []
        pnnInputValues = []
        
        #enn
        cardValues = []
        ennInputValues = []
        
        bridgeStateIndex = 0;
        for j in range(miniBatchSize):
            index = i*miniBatchSize + j
            deck = decks[index]
            vulnerable = vulnerables[index]
            dealer = dealers[index, 0]
            
            for pos in range(2):
                
                hbid, declarer, isDoubled, hands, ennInputs, pnnInputs, pnnProbs, bids, wasForced, declarers = bid(deck, vulnerable,
                                                       dealer, pos,
                                                       targetEnnModel, targetPnnModel,
                                                       opponentEnnModel, opponentPnnModel)
                declarerTeam = declarer%2
                if hbid == -1:
                    score = 0
                else:    
                    score = getDoubleDummyScore(hbid, declarer, isDoubled, vulnerable[declarerTeam], hands)

                if declarerTeam != pos:
                    score = -score
                
                #ADD WOULD BE SCORES HERE
                stateRewardArrays = []
                stateCardValueArrays = []
                for k in range(len(ennInputs)):
                    bidder = (dealer + k) % numPlayers
                    if bidder % 2 == pos:
                        rewardArray = np.zeros((numBids))
                        rewardArray[bids[k]] = score
                        stateRewardArrays.append(rewardArray)
                        pnnRewards.append(rewardArray)
                        pnnInputValues.append(pnnInputs[k])
                    
                        cardValues.append(hands[(bidder + 2) % numPlayers])
                        stateCardValueArrays.append(hands[(bidder + 2) % numPlayers])
                        ennInputValues.append(ennInputs[k])
                
                bridgeState = BridgeState.BridgeState(hbid, declarer, isDoubled, hands, deck, bids, wasForced, pnnProbs,
                                                      dealer, vulnerable, pos, score,
                                                      pnnInputs, stateRewardArrays, ennInputs, stateCardValueArrays,
                                                      declarers)
                BridgeState.save(version, bridgeStateIndex, bridgeState)
                bridgeStateIndex = bridgeStateIndex + 1
                
        npEnnInputValues = np.array(ennInputValues)
        npCardValues = np.array(cardValues)
        npPnnInputValues = np.array(pnnInputValues)
        npPnnRewards = np.array(pnnRewards)
        
        #print('Starting loss calcs')
        #test = kb.mean(kb.sum(kl.multiply([kb.constant(npPnnRewards), kb.log(kb.constant(targetPnnModel.predict(npPnnInputValues)))]), axis=-1))
        #print(kb.eval(test))
        print(npEnnInputValues.shape)
        print('Training ' + str(logCount))
        targetEnnModel.fit(x=npEnnInputValues, y=npCardValues, batch_size=128)
        targetPnnModel.fit(x=npPnnInputValues, y=npPnnRewards, batch_size=128)
        
        if i % modelUpdateNum == modelUpdateNum - 1:
            version = updateEnnModel(targetEnnModel)
            version = updatePnnModel(targetPnnModel)
            logCount = 0
            bridgeStateIndex = 0
            opponentEnnModel, opponentPnnModel = randomlySelectModels()
        
        

def bid(deck, vulnerable, dealer, pos, ennModel, pnnModel, opponentEnnModel, opponentPnnModel):
    bidder = dealer
    numPass = -1
    highestBid = -1
    isDoubled = -1
    bidIndex = -1
    lastNonPassBid = -1
    lastTeamToBid = -1
    teamToBid = bidder % 2
    declarers = [[-1, -1, -1, -1, -1], [-1, -1, -1, -1, -1]]
    
    bidFeature = np.zeros((bidFeatureSize))
    playerBids = np.zeros((numPlayers, bidFeatureSize))
    oppVulnerable = np.flip(vulnerable)
        
    ###can we vectore this?
    hands = np.zeros((numPlayers, deckSize), dtype=np.int32)
    for i in range(numPlayers):
        hands[i, deck[i::numPlayers]] =  1
    
    bids = []
    pnnProbs = []
    pnnInputs = []
    ennInputs = []
    while numPass < 3 and bidIndex < bidFeatureSize:
        ennInput = np.zeros((1, ennInputShape))
        pnnInput = np.zeros((1, pnnInputShape))
        ennInput[0, np.arange(deckSize)] = hands[bidder]
        ennInput[0, bidFeatureIndex:bidPartnerIndex] = bidFeature
        ennInput[0, bidPartnerIndex:] = playerBids[bidder - 2 if bidder - 2 >= 0 else bidder + 2]
        
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
        
        ennOutput[0, np.where(hands[bidder] == 1)] = 0
        
        pnnInput[0, 0:deckSize] = hands[bidder]
        pnnInput[0, bidFeatureIndex:bidPartnerIndex] = bidFeature
        pnnInput[0, bidPartnerIndex:ennOutputIndex] = playerBids[bidder - 2 if bidder - 2 >= 0 else bidder + 2]
        pnnInput[0, ennOutputIndex:] = ennOutput
        
        bidProbs = pnnModelToUse.predict(pnnInput)
        pnnInputs.append(pnnInput[0])
        
        #need to mask illegal moves?
        legalMoves = getLegalMoves(highestBid, lastNonPassBid, teamToBid, lastTeamToBid)
            
        #make faster?
        bidProbsNormalized = np.multiply(bidProbs[0], legalMoves)
        bidProbsNormalized = bidProbsNormalized / np.sum(bidProbsNormalized)
        
        #can letter max this vectorize to do multiple predicts at same time
        #ie p=out[i]
        bid = np.random.choice(numBids, p=bidProbsNormalized)
        if (bidIndex < 3 and bid == passBid and random.random() < forceFirstBidProb):
            wasForced = True
            legalMoves[passBid] = 0
            legalMoves[5:] = 0
            bidProbsNormalized = np.multiply(bidProbs[0], legalMoves)
            bidProbsNormalized = bidProbsNormalized / np.sum(bidProbsNormalized)
            bid = np.random.choice(numBids, p=bidProbsNormalized)
        elif (bidIndex < 3):
            wasForced = False
        
        bids.append(bid)
        pnnProbs.append(bidProbs[0, bid])
        
        if bid == passBid:
            numPass = numPass + 1
        elif bid < doubleBid:
            numPass = 0
            highestBid = bid
            isDoubled = 0;
            lastNonPassBid = bid
            lastTeamToBid = teamToBid
            if (declarers[lastTeamToBid][bid % numBidSuits] == -1):
                declarers[lastTeamToBid][bid % numBidSuits] = bidder
        else:
            numPass = 0
            lastNonPassBid = bid
            isDoubled = isDoubled + 1;
            
        if numPass < 3:
            bidIndex = getNextBidIndex(bid, bidIndex)
            playerBids[bidder, bidIndex] = 1
            bidder = (bidder + 1) % numPlayers
            teamToBid = 1 - teamToBid
            bidFeature[bidIndex] = 1
        
    return highestBid, declarers[lastTeamToBid][highestBid % numBidSuits], isDoubled, hands, ennInputs, pnnInputs, pnnProbs, bids, wasForced, declarers

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
    
###Simplify if statements to greater or less
def getNextDoubleIndex(currentBidIndex):
    blockIndex = (currentBidIndex - 3) % blockSize
    if blockIndex == 0 or blockIndex == 1 or blockIndex == 2:
        return currentBidIndex + 3 - blockIndex
    
    if blockIndex == 3 or blockIndex == 4 or blockIndex == 5:
        return currentBidIndex + 3 - (blockIndex - 3)
    
    print('ERROR ILLEGAL DOUBLE BID')

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
    
    