#include <iostream>
#include <unordered_map>
#include <string>

#include "Card.h"
#include "Table.h"

const int numPlayers = 4;
const int numTeams = 2;
const int bidRanks = 7;
const int bidSuits = 5;
const int numBidOptions = bidSuits*bidRanks;
const int numTricks = deckSize / numPlayers;
const int bidRankDiff = numRanks - bidRanks + 1;

Table::Table(bool debugMode) {
    players.reserve(numPlayers);
    players.push_back(Player(0, 0, 2));
    players.push_back(Player(1, 1, 3));
    players.push_back(Player(0, 2, 0));
    players.push_back(Player(1, 3, 1));
    deck = new Deck();
    teamScores.insert(std::make_pair(0, 0));
    teamScores.insert(std::make_pair(1, 0));
    teamTricks.insert(std::make_pair(0, 0));
    teamTricks.insert(std::make_pair(1, 0));
    
    this->debugMode = debugMode;
    
    if (debugMode) {
        debugCardsPlayed.reserve(deckSize);
    }
    
    srand(time(0)); //For random bid and random card select
}

void Table::deal(int dealer) {
    
    deck->shuffle();
    int playerIndex = (dealer + 1) % numPlayers;
    this->dealer = dealer;
    while (deck->canDeal()) {
        Player& player = players.at(playerIndex);
        Card& card = deck->dealCard();
        player.dealCard(card);
        playerIndex = (playerIndex + 1) % numPlayers;
    }
    
    if (debugMode) {
        std::cerr << "\n";
        for (auto player : players) {
            std::cerr << "Player " + std::to_string(player.getTablePosition()) + " has the: \n";
            for (auto suit : player.getHand()) {
                std::cerr << "        ";
                for (auto card : suit.second) {
                    std::cerr << card.getString() << ", ";
                }
                std::cerr << "\n";
            }
        }
    }
}

bool Table::bid() {
    if (debugMode) {
        std::cerr << "Dealer is " << dealer << "\n";
    }
    
    bool bidOptions[numBidOptions] = { };
    for (int i = 0; i < numBidOptions; i++) {
        bidOptions[i] = true;
    }
    
    int playerToBidIndex = dealer;
    int lastPlayerToBidIndex = -1;
    int consecutiveNoBids = 0;
    int highestBid = -1;
    //TODO take out string conversion?
    std::unordered_map<std::string, int> declarers;
    
    while (bidOptions[numBidOptions - 1] == true &&
           ((bidOptions[0] == true && consecutiveNoBids < numPlayers)
            || (bidOptions[0] == false && consecutiveNoBids < numPlayers - 1))) {
        
        Player& playerToBid = players.at(playerToBidIndex);
        std::pair<bool, int> bid = playerToBid.selectBid(bidOptions, numBidOptions);
        if (bid.first == true) {
            consecutiveNoBids = 0;
            for (int i = 0; i <= bid.second; i++) {
                bidOptions[i] = false;
            }
            
            if (bid.second <= highestBid) {
                std::cerr << "Previous Bid Was not Higher!\n";
                throw 0;
            }
            
            highestBid = bid.second;
            std::string key = std::to_string(playerToBid.getTeam()) + "-" + std::to_string(bid.second % bidSuits);
            if (declarers.find(key) == declarers.end()) {
                declarers.insert(std::make_pair(key, playerToBid.getTablePosition()));
            }
            
            if (debugMode) {
                std::cerr << "Player " << playerToBid.getTablePosition() << " bid "
                    << bid.second / bidSuits + 1 << " " << Card::getSuitString(static_cast<Suit>(bid.second % bidSuits)) << "\n";
            }
            lastPlayerToBidIndex = playerToBidIndex;
        } else {
            if (debugMode) {
                std::cerr << "Player " << playerToBid.getTablePosition() << " passed\n";
            }
            consecutiveNoBids++;
        }
        
        playerToBidIndex = (playerToBidIndex + 1) % numPlayers;
    }
    //TODO do you need who has bid already and consecutive no bids in the algo?
    //Yes, but code that in later
    //I don't want this to be dependent on what other people bid, since I want
    //it to accomodate irrational play, so just partner's previous bid.
    
    //TODO who is declarer and dummy and in what position will have to be added in 
    
    //no one bid
    if (bidOptions[0] == true) {
        if (debugMode) {
            std::cerr << "No one bid!.\n";
        }
        return false;
    }
    
    trumpSuit = static_cast<Suit>(highestBid % bidSuits);
    bidTarget = highestBid / bidSuits + bidRankDiff; //TODO how should this be stored for training?
    
    int bidTeam = players.at(lastPlayerToBidIndex).getTeam();
    std::string key = std::to_string(bidTeam) + "-" + std::to_string(trumpSuit);
    declarer = declarers.at(key);
    dummy = (declarer + 2) % numPlayers;
    
    if (debugMode) {
        std::cerr << "Bid is " << bidTarget - bidRankDiff + 1 << " " << Card::getSuitString(trumpSuit) << ".\n";
        std::cerr << "Bid target is " << bidTarget << ".\n";
        std::cerr << "Declarer is " << declarer << ".\n";
        std::cerr << "Dummy is " << dummy << ".\n";
        std::cerr << "\n";
    }
    
    return true;
}

void Table::play() {
    teamTricks[0] = 0;
    teamTricks[1] = 0;
    
    int startingPlayer = (declarer + 1) % numPlayers;
    
    if (debugMode) {
        debugCardsPlayed.clear();
    }
    
    for (int i = 0; i < numTricks; i++) {
        if (debugMode) {
            std::cerr << "Trick " << i+1 << ": \n";
        }
        std::pair<int,int> trickResult = playTrick(startingPlayer);
        int trickWinner = trickResult.first;
        int teamWinner = trickResult.second;
        teamTricks[teamWinner] = teamTricks[teamWinner] + 1;
        startingPlayer = trickWinner + 1;
    }
    
    if (debugMode) {
        std::cerr << "\n";
        std::cerr << "Team 0 won " << teamTricks[0] << " tricks.\n";
        std::cerr << "Team 1 won " << teamTricks[1] << " tricks.\n";
        std::cerr << "\n";
    }
}

std::pair<int,int> Table::playTrick(int startingPlayer) {
    Suit leadSuit = none;
    std::unordered_map<Player, Card, PlayerHasher, PlayerComparator> trick;
    for (int i = 0; i < numPlayers; i++) {
        Player& player = players.at((startingPlayer + i) % numPlayers);
        Card card = player.playCard(leadSuit, trumpSuit, trick);
        trick.insert(std::make_pair(player, card)); 
        if (leadSuit == none) {
            leadSuit = card.getSuit();
        }
        
        if (debugMode) {
            std::cerr << "         Player " << player.getTablePosition() << " played the " << card.getString() << ".\n";
            if (debugCardsPlayed.find(card) != debugCardsPlayed.end()) {
                std::cerr << "ERROR: CARD ALREADY PLAYED\n";
                throw 0;
            }
            debugCardsPlayed.insert(card);
        }
    }
    const Player& trickWinner = determineTrickWinner(trick, leadSuit, trumpSuit);
    
    if (debugMode) {
        std::cerr << "\n         Player " << trickWinner.getTablePosition() << " won the trick.\n\n";
    }
    return std::make_pair(trickWinner.getTablePosition(), trickWinner.getTeam());
}

const Player& Table::determineTrickWinner(std::unordered_map<Player, Card, PlayerHasher, PlayerComparator>& trick, Suit leadSuit, Suit trumpSuit) {
    const Player * maxPlayer;
    const Card * maxCard;
    for (std::unordered_map<Player, Card, PlayerHasher, PlayerComparator>::iterator it = trick.begin(); it != trick.end(); it++) {
        const Player& player = it->first;
        const Card& card = it->second;
        if (maxPlayer == NULL) {
            maxPlayer = &player;
            maxCard = &card;
        } else if (isCardGreater(*maxCard, card, leadSuit, trumpSuit)) {
            maxPlayer = &player;
            maxCard = &card;
        }
    }
    
    return *maxPlayer;
}

bool Table::isCardGreater(const Card& currentCard, const Card& comparingCard, Suit leadSuit, Suit trumpSuit) {
    if (comparingCard.getSuit() != leadSuit && comparingCard.getSuit() != trumpSuit) {
        return false;
    }
    
    if (comparingCard.getSuit() == trumpSuit && currentCard.getSuit() != trumpSuit) {
        return true;
    }
    
    if (currentCard.getSuit() == trumpSuit && comparingCard.getSuit() != trumpSuit) {
        return false;
    }
    
    return comparingCard.getRank() > currentCard.getRank();
}