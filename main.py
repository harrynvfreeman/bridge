import Bridge as b
import model as m

decks, vulnerables, dealers = b.generateRandomGames(200)
b.selfPlay(decks, vulnerables, dealers)

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