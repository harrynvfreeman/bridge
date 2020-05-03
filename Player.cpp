#include <iostream>
#include <vector>

#include "Deck.h"
#include "Card.h"
#include "Player.h"

Player::Player(int team, int tablePosition, int partnerTablePosition) {
    for (auto suit : Card::getPossibleCardSuits()) {
        std::unordered_set<Card, CardHasher, CardComparator> suitSet;
        hand[suit] = suitSet;
    }
    std::unordered_set<Card, CardHasher, CardComparator> noSuitSet;
    hand[none] = noSuitSet;
    this->team = team;
    this->tablePosition = tablePosition;
    this->partnerTablePosition = tablePosition;
}

void Player::dealCard(Card& card) {
    Suit suit = card.getSuit();
    hand[suit].insert(card);
    //hand.find(suit)->second.insert(card);
}

Card Player::playCard(Suit leadSuit, Suit trumpSuit, std::unordered_map<Player, Card, PlayerHasher, PlayerComparator>& trick) {
    std::vector<Card> allowableCards;
    allowableCards.reserve(deckSize);
    
    if (hand[leadSuit].size() > 0) {
        for (auto card : hand[leadSuit]) {
            allowableCards.push_back(card);
        }
    } else {
        for (auto element : hand) {
            for (auto card : element.second) {
                allowableCards.push_back(card);
            }
        }
    }
    
    Card cardToPlay = selectCard(allowableCards, trumpSuit, trick);
    hand[cardToPlay.getSuit()].erase(cardToPlay);
    return cardToPlay;
}

Card Player::selectCard(std::vector<Card>& allowableCards, Suit trumpSuit, std::unordered_map<Player, Card, PlayerHasher, PlayerComparator>& trick) {
    int index = rand() % allowableCards.size();
    return allowableCards.at(index);
}
//TODO MAKE THIS SMARTER
//TODO Actually make deck a set? Idk if it matters.  Actaully probably doesn't.
//TODO add checking for trickWinner to make sure there are 4 cards in trick

//bool for should I bid
//int for what bid would be
//make sure int returned is random if bool is false
std::pair<bool, int> Player::selectBid(bool bidOptions[], int numBidOptions) {   
    bool shouldBid = (bool)(rand() % 2);
    int bid = rand() % numBidOptions;
    int count = 0;
    while (bidOptions[bid] == false && count < 1000) {
        bid = rand() % numBidOptions;
        count++;
    }
    if (count == 1000) {
        shouldBid = false;
    }
    return std::make_pair(shouldBid, bid);
}