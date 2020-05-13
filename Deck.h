#ifndef DECK_H
#define DECK_H

#include <vector>
#include "Card.h"

class Deck
{
    private:
        std::vector<Card> cards;
        int deckIndex;
    
    public:
        Deck();
        Card& dealCard();
        void shuffle();
        bool canDeal();
};

#endif
