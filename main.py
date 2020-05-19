import Bridge as b
import model as m
import numpy as np

def train():
    decks, vulnerables, dealers = b.generateRandomGames(100000)
    b.selfPlay(decks, vulnerables, dealers)

def test():
    targetPnnModel = b.loadTargetPnnModel()
    targetEnnModel = b.loadTargetEnnModel()
    deck, vulnerable, dealer = b.generateRandomGame()
    deck = deck.astype(np.int32)
    hbid, declarer, isDoubled, hands, ennInputs, pnnInputs, pnnProbs, bids = b.bid(deck, 0, 0, 0, targetEnnModel, targetPnnModel, targetEnnModel, targetPnnModel)
    print('Declarer is: ' + str(declarer))
    print('Doubled is: ' + str(isDoubled))
    print('Pnn probs is: ' + str(pnnProbs))
    print('High Bid is: ' + str(hbid))

    score = b.getDoubleDummyScore(hbid, declarer, isDoubled, 0, hands)
    print('Score is: ' + str(score))

train()
#test()

# targetPnnModel = m.buildPnnModel()
# bidSequence = np.zeros((1, b.pnnInputShape))
# bidSequence[0, 100] = 1
# bidSequence[0, 200] = 1
# 
# bidOutput = targetPnnModel.predict(bidSequence)
# 
# bidIndex = 14
# bidProb = bidOutput[0, 14]
# print(np.log(bidProb))
# 
# score = -120
# 
# rewardArray = np.zeros((1, b.numBids))
# rewardArray[0, bidIndex] = score
# 
# print(rewardArray)
# print(bidOutput)
# 
# test = kb.mean(kb.sum(kl.multiply([kb.constant(rewardArray), kb.log(kb.constant(bidOutput))]), axis=-1))
# print(kb.eval(test))
# 
# targetPnnModel.fit(x=bidSequence, y=rewardArray)


# enn, pnn = m.buildModels()
# 
# h, d, isDoubled, hands = b.bid(deck, vulnerable, dealer, 0, enn, pnn, enn, pnn)
# print(h)
# print(d)
# print(isDoubled)
# print(vulnerable[d%2])
# print(hands[3].dtype)
# print(hands[3].flags['C_CONTIGUOUS'])

#numTricks = b.getDoubleDummyScore(4, 7, 3,  vulnerable[d%2], hands)
#print(numTricks)  