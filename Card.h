#ifndef CARD_H
#define CARD_H

#include <vector>

const int deckSize = 52;
const int numSuits = 4;
const int numRanks = 13;
const int handSize = 13;

enum Rank {
    two = 0,
    three = 1,
    four = 2,
    five = 3,
    six = 4,
    seven = 5,
    eight = 6,
    nine = 7,
    ten = 8,
    jack = 9,
    queen = 10,
    king = 11,
    ace = 12
};

enum Suit
{
    clubs = 0,
    diamonds = 1,
    hearts = 2,
    spades = 3,
    none = 4
};

class Card
{
    private:
        Rank rank;
        Suit suit;
    
    public:
        Card(Rank rank, Suit suit);
        
        Rank getRank() const { return rank; }
        
        Suit getSuit() const { return suit; }
        
        static std::vector<Suit> const getPossibleCardSuits();
        
        static std::vector<Rank> const getPossibleCardRanks();
};

struct CardHasher
{
  size_t
  operator()(const Card & obj) const
  {
    return std::hash<std::string>()(std::to_string(obj.getSuit()) + "-" + std::to_string(obj.getRank()));
  }
};

struct CardComparator
{
  bool
  operator()(const Card & obj1, const Card & obj2) const
  {
    if (obj1.getRank() == obj2.getRank() && obj1.getSuit() == obj2.getSuit())
      return true;
    return false;
  }
};

#endif