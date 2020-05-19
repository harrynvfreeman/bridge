import numpy as np
import keras
from model import buildModels
from pickle import dump, load
import os
import ctypes
import pathlib
import keras.backend as kb
import keras.layers as kl
from loss import custom_loss_function
from keras.optimizers import SGD

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
modelUpdateNum = 40

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

def loadTargetPnnModel():
    pnnVersion = load(open(pnnVersionPath, 'rb'))
    modelPath = pnnSavePath + str(pnnVersion) + '.h5'
    return keras.models.load_model(modelPath, custom_objects={'custom_loss_function': custom_loss_function})

def randomlySelectModels():
    version = load(open(ennVersionPath, 'rb'))
    if version >= numModelsToSave:
        randVersion = np.random.randint(version - numModelsToSave + 1, version)
    else:
        randVersion = np.random.randint(0, version + 1)
        
    ennModelPath = ennSavePath + str(randVersion) + '.h5'
    pnnModelPath = pnnSavePath + str(randVersion) + '.h5'
    ennModel = keras.models.load_model(ennModelPath, custom_objects={'custom_loss_function': custom_loss_function})
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
    
    targetEnnModel = loadTargetEnnModel()
    
    targetEnnModel.compile(optimizer=SGD(lr=0.1), loss='binary_crossentropy')
    
    targetPnnModel = loadTargetPnnModel()
    
    targetPnnModel.compile(optimizer=SGD(lr=0.1, clipnorm=2), loss=custom_loss_function)
    
    opponentEnnModel, opponentPnnModel = randomlySelectModels()
    #opponentEnnModel = loadTargetEnnModel()
    #opponentPnnModel = loadTargetPnnModel()
    
    #numMiniBatches
    for i in range(numMiniBatches):
        
        #pnn
        pnnRewards = []
        pnnInputValues = []
        
        #enn
        cardValues = []
        ennInputValues = []
        
        #miniBatchSize
        for j in range(miniBatchSize):
            index = i*miniBatchSize + j
            deck = decks[index]
            vulnerable = vulnerables[index]
            dealer = dealers[index, 0]
            #print("Dealer is: " + str(dealer))
            for pos in range(2):
                #print(" Playing for team: " + str(pos))
                hbid, declarer, isDoubled, hands, ennInputs, pnnInputs, pnnProbs, bids = bid(deck, vulnerable, dealer, pos,
                                                       targetEnnModel, targetPnnModel,
                                                       opponentEnnModel, opponentPnnModel)
                declarerTeam = declarer%2
                #print(" Declarer is: " + str(declarer))
                #print(" Suit is: " + str(hbid % 5))
                #print(" Bid is: " + str((hbid // 5) + 1))
                if hbid == -1:
                    score = 0
                else:    
                    score = getDoubleDummyScore(hbid, declarer, isDoubled, vulnerable[declarerTeam], hands)
                #print('Hbid is ' + str(hbid) + ' with prob ' + str(pnnProbs) + ' and score is ' + str(score))
                #print(" Score is: " + str(score))
                if declarerTeam != pos:
                    score = -score
                #print(" Score for pos team is: " + str(score))
                #print("score is: " + str(score))
                #print(" Starting Bid Scores")
                
                for k in range(len(ennInputs)):
                    bidder = (dealer + k) % numPlayers
                    #print("     Bidder is: " + str(bidder))
                    if bidder % 2 == pos:
                        rewardArray = np.zeros((numBids))
                        rewardArray[bids[k]] = score
                        #if bidder % 2 == pos:
                            #rewardArray[bids[k]] = score
                        #else:
                            #rewardArray[bids[k]] = -score
                        #print("         Reward is: " + str(score))
                        #print("         Prob of  is: " + str(pnnProbs[k]))
                        pnnRewards.append(rewardArray)
                        pnnInputValues.append(pnnInputs[k])
                    
                        cardValues.append(hands[(bidder + 2) % numPlayers])
                        ennInputValues.append(ennInputs[k])
                                        
        npEnnInputValues = np.array(ennInputValues)
        npCardValues = np.array(cardValues)
        npPnnInputValues = np.array(pnnInputValues)
        npPnnRewards = np.array(pnnRewards)
        
        #print('Starting loss calcs')
        #test = kb.mean(kb.sum(kl.multiply([kb.constant(npPnnRewards), kb.log(kb.constant(targetPnnModel.predict(npPnnInputValues)))]), axis=-1))
        #print(kb.eval(test))
        
        targetEnnModel.fit(x=npEnnInputValues, y=npCardValues, batch_size=128)
        #should we shuffle?
        targetPnnModel.fit(x=npPnnInputValues, y=npPnnRewards, batch_size=128)
        
        if i % modelUpdateNum == modelUpdateNum - 1:
            updateEnnModel(targetEnnModel)
            updatePnnModel(targetPnnModel)
            opponentEnnModel, opponentPnnModel = randomlySelectModels()
            #opponentEnnModel = loadTargetEnnModel()
            #opponentPnnModel = loadTargetPnnModel()
        
        

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
            #print("Bidder is " + str(bidder) + " and is using target")
            ennInput[0, deckSize:bidFeatureIndex] = vulnerable
            pnnInput[0, deckSize:bidFeatureIndex] = vulnerable
            ennModelToUse = ennModel
            pnnModelToUse = pnnModel
        else:
            #print("Bidder is " + str(bidder) + " and is NOT using target")
            ennInput[0, deckSize:bidFeatureIndex] = oppVulnerable
            pnnInput[0, deckSize:bidFeatureIndex] = oppVulnerable
            ennModelToUse = opponentEnnModel
            pnnModelToUse = opponentPnnModel
        
        ennOutput = ennModelToUse.predict(ennInput)
        ennInputs.append(ennInput[0])
        
        ###Do we do this?
        ennOutput[0, np.where(hands[bidder] == 1)] = 0
        ###TAKING THIS OUT FOR NOW.  How do we normalize?
        #ennOutput[0] = ennOutput[0] / np.sum(ennOutput[0])
        
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
        #print('     bid is ' + str(bid) + ' with prob ' + str(bidProbs[0, bid]) + ' with norm prob ' + str(bidProbsNormalized[bid]))
        bids.append(bid)
        pnnProbs.append(bidProbs[0, bid])
        
        if bid == passBid:
            numPass = numPass + 1
            #print("Bid is Pass")
        elif bid < doubleBid:
            numPass = 0
            highestBid = bid
            isDoubled = 0;
            lastNonPassBid = bid
            lastTeamToBid = teamToBid
            if (declarers[bid % numBidSuits] == -1):
                declarers[bid % numBidSuits] = bidder
            #print("Bid is " + str((bid//5) + 1) + " of " + str(bid%5))
        else:
            numPass = 0
            lastNonPassBid = bid
            isDoubled = isDoubled + 1;
            #print("Bid is (re)double")
            
        if numPass < 3:
            bidIndex = getNextBidIndex(bid, bidIndex)
            playerBids[bidder, bidIndex] = 1
            bidder = (bidder + 1) % numPlayers
            teamToBid = 1 - teamToBid
            bidFeature[bidIndex] = 1
        
    return highestBid, declarers[highestBid % numBidSuits], isDoubled, hands, ennInputs, pnnInputs, pnnProbs, bids

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
    
    