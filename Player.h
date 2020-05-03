#ifndef PLAYER_H
#define PLAYER_H

#include <unordered_map>
#include <unordered_set>
#include "Card.h"

struct PlayerHasher;
struct PlayerComparator;

class Player
{
    private:
        std::unordered_map<int, std::unordered_set<Card, CardHasher, CardComparator>> hand;
        int team;
        int tablePosition;
        int partnerTablePosition;
        
        Card selectCard(std::vector<Card>& allowableCards, Suit trumpSuit, std::unordered_map<Player, Card, PlayerHasher, PlayerComparator>& trick);
        
    
    public:
        Player(int team, int tablePosition, int partnerTablePosition);
        void dealCard(Card& card);
        Card playCard(Suit leadSuit, Suit trumpSuit, std::unordered_map<Player, Card, PlayerHasher, PlayerComparator>& trick);
        std::pair<bool, int> selectBid(bool bidOptions[], int numBidOptions);
        
        int getTablePosition() const { return tablePosition; }
        int getPartnerTablePosition() const { return partnerTablePosition; }
        int getTeam() const { return team; }
        
        std::unordered_map<int, std::unordered_set<Card, CardHasher, CardComparator>>& getHand() { return hand; }
};

struct PlayerHasher
{
  size_t
  operator()(const Player & obj) const
  {
    return std::hash<std::string>()(std::to_string(obj.getTablePosition()));
  }
};

struct PlayerComparator
{
  bool
  operator()(const Player & obj1, const Player & obj2) const
  {
    if (obj1.getTablePosition() == obj2.getTablePosition())
      return true;
    return false;
  }
};


#endif