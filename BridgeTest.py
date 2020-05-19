import Bridge
import numpy as np

def bidTestAllPass():
    deck = np.arange(52)
    vulnerable = np.array([0, 1])
    dealer = 0
    
    ennPredictValues = np.zeros((4, 1, Bridge.deckSize))
    ennPredictValues[0, 0, 0:13] = 1
    ennPredictValues[1, 0, 10:23] = 1
    ennPredictValues[2, 0, 20:33] = 1
    ennPredictValues[3, 0, 30:43] = 1
    ennModel = DummyModel(ennPredictValues)
    
    pnnPredictValues = np.zeros((4, 1, Bridge.numBids))
    pnnPredictValues[:, 0, 35] = 1
    pnnModel = DummyModel(pnnPredictValues)
    
    hBid, declarer, isDoubled, hands, ennInputs, pnnInputs, pnnProbs, bids = Bridge.bid(deck, vulnerable, dealer, 0,
                                                                        ennModel, pnnModel, ennModel, pnnModel)
    assert (hBid == -1),"Incorrect highest bid"
    assert (declarer == -1),"Incorrect declarer"
    assert (isDoubled == -1),"Incorrect double value"
    
    for i in range(4):
        for j in range(52):
            if j % 4 == i:
                assert (hands[i, j] == 1),"Incorrect card in hand. Expected 0"
            else:
                assert (hands[i, j] == 0),"Incorrect card in hand. Expected 1"
                
    deckInputExpected = np.zeros((Bridge.deckSize))
    vulnInputExpected = np.zeros((Bridge.vulnSize))
    bidFeatureExpected = np.zeros((Bridge.bidFeatureSize))
    bidPartnerExpected = np.zeros((Bridge.bidFeatureSize))
    
    ennInputsExpected = np.zeros((Bridge.ennInputShape))
    pnnInputsExpected = np.zeros((Bridge.pnnInputShape))
    
    ###First Bid
    deckInputExpected[0::4] = 1
    vulnInputExpected[1] = 1
    
    ennInputsExpected[0:52] = deckInputExpected
    ennInputsExpected[52:54] = vulnInputExpected
    ennInputsExpected[54:372] = bidFeatureExpected
    ennInputsExpected[372:] = bidPartnerExpected
    
    np.testing.assert_array_equal(ennInputsExpected, ennInputs[0])
    
    pnnInputsExpected[0:690] = ennInputsExpected
    pnnInputsExpected[690:703] = 1
    pnnInputsExpected[690::4] = 0
    
    np.testing.assert_array_equal(pnnInputsExpected, pnnInputs[0])
    
    ###Second
    deckInputExpected[:] = 0
    deckInputExpected[1::4] = 1
    vulnInputExpected[:] = [1, 0]
    bidFeatureExpected[0] = 1
    
    ennInputsExpected[0:52] = deckInputExpected
    ennInputsExpected[52:54] = vulnInputExpected
    ennInputsExpected[54:372] = bidFeatureExpected
    ennInputsExpected[372:] = bidPartnerExpected
    
    np.testing.assert_array_equal(ennInputsExpected, np.array(ennInputs[1]))
    
    pnnInputsExpected[0:690] = ennInputsExpected
    pnnInputsExpected[690:703] = 0
    pnnInputsExpected[700:713] = 1
    pnnInputsExpected[691::4] = 0
    
    np.testing.assert_array_equal(pnnInputsExpected, np.array(pnnInputs[1]))
    
    ###Third
    deckInputExpected[:] = 0
    deckInputExpected[2::4] = 1
    vulnInputExpected[:] = [0, 1]
    bidFeatureExpected[1] = 1
    bidPartnerExpected[0] = 1
    
    ennInputsExpected[0:52] = deckInputExpected
    ennInputsExpected[52:54] = vulnInputExpected
    ennInputsExpected[54:372] = bidFeatureExpected
    ennInputsExpected[372:] = bidPartnerExpected
        
    np.testing.assert_array_equal(ennInputsExpected, np.array(ennInputs[2]))
    
    pnnInputsExpected[0:690] = ennInputsExpected
    pnnInputsExpected[700:713] = 0
    pnnInputsExpected[710:723] = 1
    pnnInputsExpected[692::4] = 0
    
    np.testing.assert_array_equal(pnnInputsExpected, np.array(pnnInputs[2]))
    
    ###Fourth
    deckInputExpected[:] = 0
    deckInputExpected[3::4] = 1
    vulnInputExpected[:] = [1, 0]
    bidFeatureExpected[2] = 1
    bidPartnerExpected[0] = 0
    bidPartnerExpected[1] = 1
    
    ennInputsExpected[0:52] = deckInputExpected
    ennInputsExpected[52:54] = vulnInputExpected
    ennInputsExpected[54:372] = bidFeatureExpected
    ennInputsExpected[372:] = bidPartnerExpected
    
    np.testing.assert_array_equal(ennInputsExpected, np.array(ennInputs[3]))
    
    pnnInputsExpected[0:690] = ennInputsExpected
    pnnInputsExpected[710:723] = 0
    pnnInputsExpected[720:733] = 1
    pnnInputsExpected[693::4] = 0
    
    np.testing.assert_array_equal(pnnInputsExpected, np.array(pnnInputs[3]))
    
    assert (pnnProbs[0] == pnnProbs[1] and pnnProbs[1] ==
            pnnProbs[2] and pnnProbs[2] == pnnProbs[3] and pnnProbs[3] == 1),"Incorrect Prob Returned"
    
    assert (bids[0] == bids[1] and bids[1] ==
            bids[2] and bids[2] == bids[3] and bids[3] == 35),"Incorrect Bid Returned"
    
    print('SUCCESS')

def bidTestSequence():
    #E: Pass
    #S: Pass
    #W: 2 Clubs
    #N: Pass
    #E: 3 Hearts
    #S: Double
    #W: 4 Spades
    #N: Double
    #E: Redouble
    #S: 5 Diamonds
    #W: 6 Hearts
    #N: Double
    #E: Pass
    #S: Pass
    #W: Pass
    
    deck = np.arange(52)
    vulnerable = np.array([0, 0])
    dealer = 1
    
    pnnPredictValues = np.zeros((15, 1, Bridge.numBids))
    pnnPredictValues[0, 0, 35] = 1
    pnnPredictValues[1, 0, 35] = 1
    pnnPredictValues[2, 0, 5] = 1
    pnnPredictValues[3, 0, 35] = 1
    pnnPredictValues[4, 0, 12] = 1
    pnnPredictValues[5, 0, 36] = 1
    pnnPredictValues[6, 0, 18] = 1
    pnnPredictValues[7, 0, 36] = 1
    pnnPredictValues[8, 0, 37] = 1
    pnnPredictValues[9, 0, 21] = 1
    pnnPredictValues[10, 0, 27] = 1
    pnnPredictValues[11, 0, 36] = 1
    pnnPredictValues[12, 0, 35] = 1
    pnnPredictValues[13, 0, 35] = 1
    pnnPredictValues[14, 0, 35] = 1
    
    pnnModelPos = DummyModel(pnnPredictValues[1::2])
    pnnModelOpponent = DummyModel(pnnPredictValues[0::2])
    
    ennPredictValues = np.zeros((15, 1, Bridge.deckSize))

    ennModelPos = DummyModel(ennPredictValues[1::2])
    ennModelOpponent = DummyModel(ennPredictValues[0::2])
    
    hBid, declarer, isDoubled, hands, ennInputs, pnnInputs, pnnProbs, bids = Bridge.bid(deck, vulnerable, dealer, 0,
                                                                        ennModelPos, pnnModelPos, ennModelOpponent, pnnModelOpponent)
    
    assert (hBid == 27),"Incorrect highest bid"
    assert (declarer == 1),"Incorrect declarer"
    assert (isDoubled == 1),"Incorrect double value"
    
    npEnnInputs = np.array(ennInputs)
    npPnnInputs = np.array(pnnInputs)
    
    np.testing.assert_array_equal(npEnnInputs, npPnnInputs[:, 0:690])
    
    #E: Pass
    bidFeatureExpected = np.zeros((Bridge.bidFeatureSize))
    bidPartnerExpected = np.zeros((4, Bridge.bidFeatureSize))
    
    np.testing.assert_array_equal(npEnnInputs[0, 54:372], bidFeatureExpected)
    np.testing.assert_array_equal(npEnnInputs[0, 372:], bidPartnerExpected[1])
    
    #S: Pass    
    bidFeatureExpected[0] = 1
    
    np.testing.assert_array_equal(npEnnInputs[1, 54:372], bidFeatureExpected)
    np.testing.assert_array_equal(npEnnInputs[1, 372:], bidPartnerExpected[2])
    
    #W: 2 Clubs    
    bidFeatureExpected[1] = 1
    bidPartnerExpected[3, 0] = 1
    
    np.testing.assert_array_equal(npEnnInputs[2, 54:372], bidFeatureExpected)
    np.testing.assert_array_equal(npEnnInputs[2, 372:], bidPartnerExpected[3])
    
    #N: Pass
    bidFeatureExpected[48] = 1
    bidPartnerExpected[0, 1] = 1
    
    np.testing.assert_array_equal(npEnnInputs[3, 54:372], bidFeatureExpected)
    np.testing.assert_array_equal(npEnnInputs[3, 372:], bidPartnerExpected[0])
    
    #E: 3 Hearts
    bidFeatureExpected[49] = 1
    bidPartnerExpected[1, 48] = 1
    
    np.testing.assert_array_equal(npEnnInputs[4, 54:372], bidFeatureExpected)
    np.testing.assert_array_equal(npEnnInputs[4, 372:], bidPartnerExpected[1])
    
    #S: Double
    bidFeatureExpected[111] = 1
    bidPartnerExpected[2, 49] = 1
    
    np.testing.assert_array_equal(npEnnInputs[5, 54:372], bidFeatureExpected)
    np.testing.assert_array_equal(npEnnInputs[5, 372:], bidPartnerExpected[2])
    
    #W: 4 Spades
    bidFeatureExpected[114] = 1
    bidPartnerExpected[3, 111] = 1
    
    np.testing.assert_array_equal(npEnnInputs[6, 54:372], bidFeatureExpected)
    np.testing.assert_array_equal(npEnnInputs[6, 372:], bidPartnerExpected[3])
    
    #N: Double
    bidFeatureExpected[165] = 1
    bidPartnerExpected[0, 114] = 1
    
    np.testing.assert_array_equal(npEnnInputs[7, 54:372], bidFeatureExpected)
    np.testing.assert_array_equal(npEnnInputs[7, 372:], bidPartnerExpected[0])
    
    #E: Redouble
    bidFeatureExpected[168] = 1
    bidPartnerExpected[1, 165] = 1
    
    np.testing.assert_array_equal(npEnnInputs[8, 54:372], bidFeatureExpected)
    np.testing.assert_array_equal(npEnnInputs[8, 372:], bidPartnerExpected[1])
    
    #S: 5 Diamonds
    bidFeatureExpected[171] = 1
    bidPartnerExpected[2, 168] = 1

    np.testing.assert_array_equal(npEnnInputs[9, 54:372], bidFeatureExpected)
    np.testing.assert_array_equal(npEnnInputs[9, 372:], bidPartnerExpected[2])
    
    #W: 6 Hearts
    bidFeatureExpected[192] = 1
    bidPartnerExpected[3, 171] = 1

    np.testing.assert_array_equal(npEnnInputs[10, 54:372], bidFeatureExpected)
    np.testing.assert_array_equal(npEnnInputs[10, 372:], bidPartnerExpected[3])
    
    #N: Double
    bidFeatureExpected[246] = 1
    bidPartnerExpected[0, 192] = 1

    np.testing.assert_array_equal(npEnnInputs[11, 54:372], bidFeatureExpected)
    np.testing.assert_array_equal(npEnnInputs[11, 372:], bidPartnerExpected[0])
    
    #E: Pass
    bidFeatureExpected[249] = 1
    bidPartnerExpected[1, 246] = 1

    np.testing.assert_array_equal(npEnnInputs[12, 54:372], bidFeatureExpected)
    np.testing.assert_array_equal(npEnnInputs[12, 372:], bidPartnerExpected[1])
    
    #S: Pass
    bidFeatureExpected[250] = 1
    bidPartnerExpected[2, 249] = 1

    np.testing.assert_array_equal(npEnnInputs[13, 54:372], bidFeatureExpected)
    np.testing.assert_array_equal(npEnnInputs[13, 372:], bidPartnerExpected[2])
    
    #W: Pass
    bidFeatureExpected[251] = 1
    bidPartnerExpected[3, 250] = 1

    np.testing.assert_array_equal(npEnnInputs[14, 54:372], bidFeatureExpected)
    np.testing.assert_array_equal(npEnnInputs[14, 372:], bidPartnerExpected[3])
    
    print('SUCCESS')
    
class DummyModel:
    def __init__(self, predict_values):
        self.predict_values = predict_values
        self.predict_index = 0
        self.inputs = []
        
    def predict(self, input):
        self.inputs.append(input)
        self.predict_index = self.predict_index + 1
        return self.predict_values[self.predict_index - 1]
    
bidTestAllPass()
bidTestSequence()