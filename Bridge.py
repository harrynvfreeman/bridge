import numpy as np
from model import buildModels
from pickle import dump, load
import os
import ctypes
import pathlib

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

rng = np.random.default_rng()

libfile = pathlib.Path().absolute() / "Ddsinterface.so"
c_lib = ctypes.CDLL(libfile)
c_lib.numTricks.argtypes = [ctypes.c_int, ctypes.c_int, np.ctypeslib.ndpointer(dtype=np.int32),
                       np.ctypeslib.ndpointer(dtype=np.int32), np.ctypeslib.ndpointer(dtype=np.int32),
                       np.ctypeslib.ndpointer(dtype=np.int32)]
c_lib.numTricks.restype = ctypes.c_int

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

def updatePnnModel(pnnModel):
    pnnVersion = load(open(pnnVersionPath, 'rb'))
    if (pnnVersion >= numModelsToSave):
        modelPathToDelete = pnnSavePath + str(pnnVersion - numModelsToSave) + '.h5'
        os.remove(modelPathToDelete)
    pnnVersion = pnnVersion + 1
    pnnModel.save(pnnSavePath + str(pnnVersion) + '.h5')
    dump(pnnVersion, open(pnnVersionPath, 'wb'))

#Step 1 is generating random games
def generateRandomGame():
    deck = rng.choice(52, size=52, replace=False)
    vulnerable = np.random.randint(0, 2, size=2)
    dealer = np.random.randint(0,4)
    return deck, vulnerable, dealer


def generateRandomGames(numGames):
    decks = np.zeros((numGames, deckSize))
    vulnerables = np.zeros((numGames, vulnSize))
    dealers = np.zeros((numGames, 1))
    
    for i in range(numGames):
        deck, vulnerable, dealer = generateRandomGame()
        decks[i] = deck
        vulnerables[i] = vulnerable
        dealers[i] = dealer
        
    return decks, vulnerables, dealers

def bid(deck, vulnerable, dealer, pos, ennModel, pnnModel, opponentEnnModel, opponentPnnModel):
    bidder = dealer
    numPass = -1
    highestBid = -1
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
    
    while numPass < 3 and bidIndex < bidFeatureSize:
        
        ennInput[0, 0:deckSize] = hands[bidder]
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
        
        ###Do we do this?
        ennOutput[0, hands[bidder]] = 0
        ennOutput[0] = ennOutput[0] / np.sum(ennOutput[0])
        
        pnnInput[0, 0:deckSize] = hands[bidder]
        pnnInput[0, bidFeatureIndex:bidPartnerIndex] = bidFeature
        pnnInput[0, bidPartnerIndex:ennOutputIndex] = bids[bidder - 2 if bidder - 2 >= 0 else bidder + 2]
        pnnInput[0, ennOutputIndex:] = ennOutput
        
        bidProbs = pnnModelToUse.predict(pnnInput)
        
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
            lastNonPassBid = bid
            lastTeamToBid = teamToBid
            if (declarers[bid % numBidSuits] == -1):
                declarers[bid % numBidSuits] = bidder
        else:
            numPass = 0
            lastNonPassBid = bid
            
        if numPass < 3:
            bidder = (bidder + 1) % numPlayers
            teamToBid = 1 - teamToBid
            bidIndex = getNextBidIndex(bid, bidIndex)
            bidFeature[bidIndex] = 1
            bids[bidder, bidIndex] = 1
        
    return highestBid, declarers[highestBid % numBidSuits], hands

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

def getDoubleDummyScore(bid, declarer, hands):
    return c_lib.numTricks(bid % numBidSuits, declarer, hands[0], hands[1], hands[2], hands[3])
    
    