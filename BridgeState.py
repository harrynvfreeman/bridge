from pickle import dump, load
import os

savePath = ('./bridgeStates/')

# 0 - 1 club
# 1 - 1 diamond
# 2 - 1 heart
# 3 - 1 spade
# 4 - 1 no trump
# 5 - 2 club
# .
# .
# .
# 30 - 7 club
# 31 - 7 diamond
# 32 - 7 heart
# 33 - 7 spade
# 34 - 7 no trump
# 35 - pass
# 36 - double
# 37 - redouble

class BridgeState:
    def __init__(self, hbid, declarer, isDoubled, hands, deck, bids, wasForced, pnnProbs, dealer, vulnerable, pos, score,
                 pnnInputs, rewardArray, ennInputs, cardValues, declarers):
        self.hbid = hbid
        self.declarer = declarer
        self.isDoubled = isDoubled
        self.hands = hands
        self.deck = deck
        self.bids = bids
        self.wasForced = wasForced
        self.pnnProbs = pnnProbs
        self.dealer = dealer
        self.vulnerable = vulnerable
        self.pos = pos
        self.score = score
        self.pnnInputs = pnnInputs
        self.rewardAray = rewardArray
        self.ennInputs = ennInputs
        self.cardValues = cardValues
        self.declarers = declarers

def save(version, index, bridgeState):
    if bridgeState.score == 0:
        path = savePath + str(version) + '/draw/state_' + index
    elif bridgeState.score > 0:
        path = savePath + str(version) + '/win/state_' + index
    else:
        path = savePath + str(version) + '/loss/state_' + index
        
    os.makedirs(os.path.dirname(path), exist_ok=True)
    dump(bridgeState, open(path, 'wb'))

        