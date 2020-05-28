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
numTeams = 2
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
bidOffset = 6

miniBatchSize = 100
modelUpdateNum = 100

forceFirstBidProb = 0.20
#forceFirstBidProb = -1
highestForceRank = 2

rng = np.random.default_rng()

libfile = pathlib.Path().absolute() / "Ddsinterface.so"
c_lib = ctypes.CDLL(libfile)

c_lib.calcScore.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                       np.ctypeslib.ndpointer(dtype=np.int32),
                       np.ctypeslib.ndpointer(dtype=np.int32),
                       np.ctypeslib.ndpointer(dtype=np.int32),
                       np.ctypeslib.ndpointer(dtype=np.int32)]
c_lib.calcScore.restype = ctypes.c_int

c_lib.getMaxTricks.argtypes = [np.ctypeslib.ndpointer(dtype=np.int32),
                       np.ctypeslib.ndpointer(dtype=np.int32),
                       np.ctypeslib.ndpointer(dtype=np.int32),
                       np.ctypeslib.ndpointer(dtype=np.int32),
                       np.ctypeslib.ndpointer(dtype=np.int32)]
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
    bridgeStateIndex = 0;
    
    opponentEnnModel, opponentPnnModel = randomlySelectModels()
    
    for i in range(numMiniBatches):
        
        #pnn
        pnnInputValues = []
        pnnRewards = []
        
        #enn
        ennInputValues = []
        cardValues = []
        
        batchDecks = np.zeros((2*miniBatchSize, deckSize), dtype=np.int32)
        batchDecks[0:miniBatchSize] = decks[i*miniBatchSize:(i+1)*miniBatchSize]
        batchDecks[miniBatchSize:] = decks[i*miniBatchSize:(i+1)*miniBatchSize]
        
        batchVulnerables = np.zeros((2*miniBatchSize, vulnSize), dtype=np.int32)
        batchVulnerables[0:miniBatchSize] = vulnerables[i*miniBatchSize:(i+1)*miniBatchSize]
        batchVulnerables[miniBatchSize:] = vulnerables[i*miniBatchSize:(i+1)*miniBatchSize]
        
        batchDealers = np.zeros((2*miniBatchSize, 1), dtype=np.int32)
        batchDealers[0:miniBatchSize] = dealers[i*miniBatchSize:(i+1)*miniBatchSize]
        batchDealers[miniBatchSize:] = dealers[i*miniBatchSize:(i+1)*miniBatchSize]
        
        batchPossitions = np.zeros((2*miniBatchSize), dtype=np.int32)
        batchPossitions[miniBatchSize:] = 1
        
        highestBids, declarers, doubleEncodings, hands, ennInputs, pnnInputs, pnnProbs, bids, forceBids, declarersFull = bidParallel(
            2*miniBatchSize, batchDecks, batchVulnerables, batchDealers, batchPossitions, targetEnnModel, targetPnnModel,
            opponentEnnModel, opponentPnnModel)
        print(hands.shape)
        
        for j in range(2*miniBatchSize):
            hbid = highestBids[j]
            declarer = declarers[j]
            isDoubled = doubleEncodings[j]
            subHands = hands[j]
            subEnnInputs = ennInputs[j]
            subPnnInputs = pnnInputs[j]
            subPnnProbs = pnnProbs[j]
            subBids = bids[j]
            subForceBids = forceBids[j]
            deck = batchDecks[j]
            vulnerable = batchVulnerables[j]
            dealer = batchDealers[j, 0]
            pos = batchPossitions[j]
            
            declarerTeam = declarer%2
            if hbid == -1:
                score = 0
            else:    
                score = getDoubleDummyScore(hbid, declarer, isDoubled, vulnerable[declarerTeam], subHands)
                if score == -1:
                    raise ValueError('Get Double Dummy Score Failed')

            if declarerTeam != pos:
                score = -score
                
            #ADD WOULD BE SCORES HERE
            stateRewardArrays = []
            stateCardValueArrays = []
            for k in range(len(subEnnInputs)):
                bidder = (dealer + k) % numPlayers
                if bidder % 2 == pos and score != 0:
                    rewardArray = np.zeros((numBids))
                    rewardArray[subBids[k]] = score
                    pnnRewards.append(rewardArray)
                    stateRewardArrays.append(rewardArray)
                    pnnInputValues.append(subPnnInputs[k])
                    
                    cardValues.append(subHands[(bidder + 2) % numPlayers])
                    stateCardValueArrays.append(subHands[(bidder + 2) % numPlayers])
                    ennInputValues.append(subEnnInputs[k])
                
            bridgeState = BridgeState.BridgeState(hbid, declarer, isDoubled, subHands, deck, subBids, subForceBids, subPnnProbs,
                                                    dealer, vulnerable, pos, score,
                                                    subPnnInputs, stateRewardArrays, subEnnInputs, stateCardValueArrays,
                                                    declarersFull[j])
            
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
        if (npEnnInputValues.shape[0] > 0):
            print('Training ' + str(logCount))
            targetEnnModel.fit(x=npEnnInputValues, y=npCardValues, batch_size=128)
            targetPnnModel.fit(x=npPnnInputValues, y=npPnnRewards, batch_size=128)
        else:
            print('Not Training ' + str(logCount))
        logCount = logCount + 1
        
        if i % modelUpdateNum == modelUpdateNum - 1:
            version = updateEnnModel(targetEnnModel)
            version = updatePnnModel(targetPnnModel)
            logCount = 0
            bridgeStateIndex = 0
            opponentEnnModel, opponentPnnModel = randomlySelectModels()
        
def bidParallel(numBidSequences, decks, vulnerables, dealers, positions, targetEnnModel, targetPnnModel, opponentEnnModel, opponentPnnModel):
    bidders = dealers[:, 0]
    numPasses = np.zeros((numBidSequences), dtype=np.int32) - 1
    shouldBid = np.ones((numBidSequences), dtype=np.int32)
    highestBids = np.zeros((numBidSequences), dtype=np.int32) - 1
    doubleEncodings = np.zeros((numBidSequences), dtype=np.int32) - 1
    bidIndeces = np.zeros((numBidSequences), dtype=np.int32) - 1
    lastNonPassBids = np.zeros((numBidSequences), dtype=np.int32) - 1
    lastTeamsToBid = np.zeros((numBidSequences), dtype=np.int32) - 1
    teamsToBid = bidders % 2
    declarers = np.zeros((numBidSequences, numTeams, numBidSuits), dtype=np.int32) - 1
    declarersToReturn = np.zeros((numBidSequences), dtype=np.int32)
    
    bidFeatures = np.zeros((numBidSequences, bidFeatureSize))
    playerBids = np.zeros((numBidSequences, numPlayers, bidFeatureSize))
    
    hands = np.zeros((numBidSequences, numPlayers, deckSize), dtype=np.int32)
    for i in range(numBidSequences):
        for j in range(numPlayers):
            hands[i, j, decks[i, j::numPlayers]] =  1
      
    bids = []
    forceBids = []
    pnnProbs = []
    pnnInputs = []
    ennInputs = []
    
    for i in range(numBidSequences):
        bids.append([])
        forceBids.append([])
        pnnProbs.append([])
        ennInputs.append([])
        pnnInputs.append([])
    
    while np.sum(shouldBid) > 0:
        targetBidIndeces = ((bidders % numTeams) == positions) & shouldBid
        numTargetBids = np.sum(targetBidIndeces)
        targetEnnInputs = np.zeros((numTargetBids, ennInputShape))
        targetPnnInputs = np.zeros((numTargetBids, pnnInputShape))
        
        opponentBidIndeces = ((bidders % numTeams) != positions) & shouldBid
        numOpponentBids = np.sum(opponentBidIndeces)
        opponentEnnInputs = np.zeros((numOpponentBids, ennInputShape))
        opponentPnnInputs = np.zeros((numOpponentBids, pnnInputShape))
        
        targetInputIndex = 0
        opponentInputIndex = 0
        for i in range(numBidSequences):
            if targetBidIndeces[i] == True:
                targetEnnInputs[targetInputIndex, 0:deckSize] = hands[i, bidders[i]]
                targetEnnInputs[targetInputIndex, deckSize:bidFeatureIndex] = vulnerables[i]
                targetEnnInputs[targetInputIndex, bidFeatureIndex:bidPartnerIndex] = bidFeatures[i]
                targetEnnInputs[targetInputIndex, bidPartnerIndex:] = playerBids[i, bidders[i] - 2 if bidders[i] - 2
                                                                                 >= 0 else bidders[i] + 2]
                
                targetPnnInputs[targetInputIndex, 0:deckSize] = hands[i, bidders[i]]
                targetPnnInputs[targetInputIndex, deckSize:bidFeatureIndex] = vulnerables[i]
                targetPnnInputs[targetInputIndex, bidFeatureIndex:bidPartnerIndex] = bidFeatures[i]
                targetPnnInputs[targetInputIndex, bidPartnerIndex:ennOutputIndex] = playerBids[i, bidders[i] - 2 if bidders[i] - 2
                                                                                 >= 0 else bidders[i] + 2]
                ennInputs[i].append(targetEnnInputs[targetInputIndex])
                targetInputIndex = targetInputIndex + 1
                
            if opponentBidIndeces[i] == True:
                opponentEnnInputs[opponentInputIndex, 0:deckSize] = hands[i, bidders[i]]
                opponentEnnInputs[opponentInputIndex, deckSize:bidFeatureIndex] = np.flip(vulnerables[i])
                opponentEnnInputs[opponentInputIndex, bidFeatureIndex:bidPartnerIndex] = bidFeatures[i]
                opponentEnnInputs[opponentInputIndex, bidPartnerIndex:] = playerBids[i, bidders[i] - 2 if bidders[i] - 2
                                                                                 >= 0 else bidders[i] + 2]
                
                opponentPnnInputs[opponentInputIndex, 0:deckSize] = hands[i, bidders[i]]
                opponentPnnInputs[opponentInputIndex, deckSize:bidFeatureIndex] = np.flip(vulnerables[i])
                opponentPnnInputs[opponentInputIndex, bidFeatureIndex:bidPartnerIndex] = bidFeatures[i]
                opponentPnnInputs[opponentInputIndex, bidPartnerIndex:ennOutputIndex] = playerBids[i, bidders[i] - 2 if bidders[i] - 2
                                                                                 >= 0 else bidders[i] + 2]
                ennInputs[i].append(opponentEnnInputs[opponentInputIndex])
                opponentInputIndex = opponentInputIndex + 1
        
        if numTargetBids > 0:
            targetEnnOutputs = targetEnnModel.predict(targetEnnInputs)
        
        if numOpponentBids > 0:
            opponentEnnOutputs = opponentEnnModel.predict(opponentEnnInputs)
        
        targetInputIndex = 0
        opponentInputIndex = 0
        for i in range(numBidSequences):
            if targetBidIndeces[i] == True:
                targetEnnOutputs[targetInputIndex, np.where(hands[i, bidders[i]] == 1)] = 0
                targetPnnInputs[targetInputIndex, ennOutputIndex:] = targetEnnOutputs[targetInputIndex]
                pnnInputs[i].append(targetPnnInputs[targetInputIndex])
                targetInputIndex = targetInputIndex + 1
                
            if opponentBidIndeces[i] == True:
                opponentEnnOutputs[opponentInputIndex, np.where(hands[i, bidders[i]] == 1)] = 0
                opponentPnnInputs[opponentInputIndex, ennOutputIndex:] = opponentEnnOutputs[opponentInputIndex]
                pnnInputs[i].append(opponentPnnInputs[opponentInputIndex])
                opponentInputIndex = opponentInputIndex + 1
                
        if numTargetBids > 0:
            targetBidProbs = targetPnnModel.predict(targetPnnInputs)
            
        if numOpponentBids > 0:
            opponentBidProbs = opponentPnnModel.predict(opponentPnnInputs)
        
        targetInputIndex = 0
        opponentInputIndex = 0
        for i in range(numBidSequences):
            if shouldBid[i] == 1:
                if targetBidIndeces[i] == True:
                    bidProbs = targetBidProbs[targetInputIndex]
                    targetInputIndex = targetInputIndex + 1
                    shouldForceBid = False
                elif opponentBidIndeces[i] == True:
                    bidProbs = opponentBidProbs[opponentInputIndex]
                    opponentInputIndex = opponentInputIndex + 1
                    shouldForceBid = False
                    if (bidIndeces[i] < 3 and bidIndeces[i] > 0 and bidders[i] % 2 != positions[i]
                        and random.random() < forceFirstBidProb):
                        shouldForceBid = True
                
                legalMoves = getLegalMoves(highestBids[i], lastNonPassBids[i], teamsToBid[i], lastTeamsToBid[i])
                bidProbsNormalized = np.multiply(bidProbs, legalMoves)
                bidProbsNormalized = bidProbsNormalized / np.sum(bidProbsNormalized)
                bid = np.random.choice(numBids, p=bidProbsNormalized)
                forceBid = False
                
                if (shouldForceBid and bid == passBid):
                    maxTricks = getMaxTricks(hands[i])
                    #bidderMaxTricks = maxTricks[bidders[i]]
                    legalMoves[:] = 0
                    canForceBid = False
                    for j in range(numBidSuits):
                        maxSuitTrick = maxTricks[bidders[i], j] - bidOffset
                        for k in range(min(maxSuitTrick, highestForceRank)):
                            legalMoves[j + numBidSuits*k] = 1
                            canForceBid = True
                            
                    if canForceBid:
                        bidProbsNormalized = np.multiply(bidProbs, legalMoves)
                        bidProbsNormalized = bidProbsNormalized / np.sum(bidProbsNormalized)
                        bid = np.random.choice(numBids, p=bidProbsNormalized)
                        forceBid = True
                
                bids[i].append(bid)
                forceBids[i].append(forceBid)
                pnnProbs[i].append(bidProbs[bid])
                
                if bid == passBid:
                    numPasses[i] = numPasses[i] + 1
                elif bid < doubleBid:
                    numPasses[i] = 0
                    highestBids[i] = bid
                    doubleEncodings[i] = 0;
                    lastNonPassBids[i] = bid
                    lastTeamsToBid[i] = teamsToBid[i]
                    if (declarers[i, lastTeamsToBid[i], bid % numBidSuits] == -1):
                        declarers[i, lastTeamsToBid[i], bid % numBidSuits] = bidders[i]
                else:
                    numPasses[i] = 0
                    lastNonPassBids[i] = bid
                    doubleEncodings[i] = doubleEncodings[i] + 1;
            
                if numPasses[i] < 3:
                    bidIndeces[i] = getNextBidIndex(bid, bidIndeces[i])
                    playerBids[i, bidders[i], bidIndeces[i]] = 1
                    bidders[i] = (bidders[i] + 1) % numPlayers
                    teamsToBid[i] = 1 - teamsToBid[i]
                    bidFeatures[i, bidIndeces[i]] = 1
                else:
                    shouldBid[i] = 0
                declarersToReturn[i] = declarers[i, lastTeamsToBid[i], highestBids[i] % numBidSuits]
                
    print('Returning')
    return highestBids, declarersToReturn, doubleEncodings, hands, ennInputs, pnnInputs, pnnProbs, bids, forceBids, declarers

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

def getMaxTricks(hands):
    result = np.zeros((numBidSuits*numPlayers), dtype=np.int32)
    c_lib.getMaxTricks(hands[0], hands[1], hands[2], hands[3], result)
    if (result[0] == -1):
        raise ValueError('DDS Error get max tricks')
    
    modifiedResult = np.zeros((numPlayers, numBidSuits), dtype=np.int32)
    for i in range(numBidSuits*numPlayers):
        modifiedResult[i % numPlayers, i // numPlayers] = result[i]
    return modifiedResult

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
        if (bidIndex < 3 and bid == passBid and bidder % 2 != pos and random.random() < forceFirstBidProb):
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
    
    