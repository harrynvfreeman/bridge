#ifndef CARD_H
#define CARD_H

#include <string>
#include <vector>

const int deckSize = 52;
const int numRanks = 13;
const int handSize = 13;

enum Rank {
    two = 2,
    three = 3,
    four = 4,
    five = 5,
    six = 6,
    seven = 7,
    eight = 8,
    nine = 9,
    ten = 10,
    jack = 11,
    queen = 12,
    king = 13,
    ace = 14
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
        
        static std::string const getSuitString(Suit suit);
        
        static std::string const getRankString(Rank rank);
        
        static std::string const getString(Suit suit, Rank rank);
        
        std::string const getString();
        
        static int ddsSuitConvert(Suit suit);
        
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
