#include <iostream>

#include "Card.h"

Card::Card(Rank rank, Suit suit) {
    this->rank = rank;
    this->suit = suit;
}

std::vector<Suit> const Card::getPossibleCardSuits() {
    std::vector<Suit> suits;
    suits.push_back(clubs);
    suits.push_back(diamonds);
    suits.push_back(hearts);
    suits.push_back(spades);
    
    return suits;
}

std::vector<Rank> const Card::getPossibleCardRanks() {
    std::vector<Rank> ranks;
    ranks.push_back(two);
    ranks.push_back(three);
    ranks.push_back(four);
    ranks.push_back(five);
    ranks.push_back(six);
    ranks.push_back(seven);
    ranks.push_back(eight);
    ranks.push_back(nine);
    ranks.push_back(ten);
    ranks.push_back(jack);
    ranks.push_back(queen);
    ranks.push_back(king);
    ranks.push_back(ace);
    
    return ranks;
}