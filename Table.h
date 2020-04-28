#ifndef TABLE_H
#define TABLE_H

#include <vector>
#include <unordered_map>

#include "Player.h"
#include "Deck.h"

class Table
{
    private:
        std::vector<Player> players;
        std::unordered_map<int, int> teamScores;
        std::unordered_map<int, int> teamTricks;
        Deck* deck;
        Suit trumpSuit = none;
        int dealer = 0;
        
        std::pair<int,int> playTrick(int startingPlayer);
        const Player& determineTrickWinner(std::unordered_map<Player, Card, PlayerHasher, PlayerComparator>& trick, Suit leadSuit, Suit trumpSuit);
        bool isCardGreater(const Card& currentCard, const Card& comparingCard, Suit leadSuit, Suit trumpSuit);
        
    
    public:
        Table();
        //~Table();  TODO
        void deal();
        void play();
        std::vector<Player>& getPlayers() { return players; }
        std::unordered_map<int, int>& getTeamScores() { return teamScores; }
        std::unordered_map<int, int>& getTeamTricks() { return teamTricks; }
};

#endif