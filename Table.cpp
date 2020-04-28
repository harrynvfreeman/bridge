#include <iostream>
#include <unordered_map>

#include "Card.h"
#include "Table.h"

const int numPlayers = 4;
const int numTricks = deckSize / numPlayers;

Table::Table() {
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
}

void Table::deal() {
    std::cerr << "Beginning Deal.\n";
    deck->shuffle();
    int playerIndex = (dealer + 1) % numPlayers;
    while (deck->canDeal()) {
        Player& player = players.at(playerIndex);
        Card& card = deck->dealCard();
        player.dealCard(card);
        playerIndex = (playerIndex + 1) % numPlayers;
    }
    std::cerr << "Done Deal.\n";
    std::cerr << "----------------------\n";
}

void Table::play() {
    teamTricks[0] = 0;
    teamTricks[1] = 0;
    std::cerr << "Beginning Play.\n";
    std::cerr << "----------------------\n";
    int startingPlayer = (dealer + 1) % numPlayers;
    for (int i = 0; i < numTricks; i++) {
        std::cerr << "Playing Trick " << i << " .\n";
        std::pair<int,int> trickResult = playTrick(startingPlayer);
        int trickWinner = trickResult.first;
        int teamWinner = trickResult.second;
        teamTricks[teamWinner] = teamTricks[teamWinner] + 1;
        startingPlayer = trickWinner + 1;
        std::cerr << "----------------------\n";
    }
    std::cerr << "Play Ended.\n";
    std::cerr << "Team 0 won " << teamTricks[0] << " tricks.\n";
    std::cerr << "Team 1 won " << teamTricks[1] << " tricks.\n";
    std::cerr << "----------------------\n";
}

std::pair<int,int> Table::playTrick(int startingPlayer) {
    Suit leadSuit = none;
    std::unordered_map<Player, Card, PlayerHasher, PlayerComparator> trick;
    for (int i = 0; i < numPlayers; i++) {
        Player& player = players.at((startingPlayer + i) % numPlayers);
        Card card = player.playCard(leadSuit, trumpSuit, trick);
        std::cerr << "Player " << player.getTablePosition() << " played the " << card.getRank() << " of " << card.getSuit() << ".\n";
        trick.insert(std::make_pair(player, card)); 
        if (leadSuit == none) {
            leadSuit = card.getSuit();
        }
    }
    const Player& trickWinner = determineTrickWinner(trick, leadSuit, trumpSuit);
    std::cerr << "Player " << trickWinner.getTablePosition() << " won the trick.\n";
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