import Bridge as b
import model as m

deck, vulnerable, dealer = b.generateRandomGame()

enn, pnn = m.buildModels()

h, d, hands = b.bid(deck, vulnerable, dealer, 0, enn, pnn, enn, pnn)
print(h)
print(d)
print(hands.dtype)
print(hands[1].flags['C_CONTIGUOUS'])
numTricks = b.getDoubleDummyScore(h, d, hands)
print(numTricks)