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

std::string const Card::getSuitString(Suit suit) {
    switch(suit) {
        case clubs:
            return "Clubs";
        case diamonds:
            return "Diamonds";
        case hearts:
            return "Hearts";
        case spades:
            return "Spades";
        case none:
            return "No Trump";
        default:
            std::cerr << "Invalid suit: " << std::to_string(suit) << "\n";
            throw 0;
    }
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

std::string const Card::getRankString(Rank rank) {
    switch(rank) {
        case two:
            return "2";
        case three:
            return "3";
        case four:
            return "4";
        case five:
            return "5";
        case six:
            return "6";
        case seven:
            return "7";
        case eight:
            return "8";
        case nine:
            return "9";
        case ten:
            return "10";
        case jack:
            return "Jack";
        case queen:
            return "Queen";
        case king:
            return "King";
        case ace:
            return "Ace";
        default:
            std::cerr << "Invalid rank: " << std::to_string(rank) << "\n";
            throw 0;
    }
}

std::string const Card::getString(Suit suit, Rank rank) {
    return getRankString(rank) + " of " + getSuitString(suit);
}

std::string const Card::getString() {
    return getString(suit, rank);
}