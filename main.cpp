#include <iostream>
#include <vector>
#include "Card.h"
#include "Deck.h"
#include "Table.h"

int main()
{
    //Card card = Card(two, spades);
    //std::cout << card.getSuit() << "\n";
    
    //Deck deck = Deck();
    //for (int i = 0; i < 52; i++) {
    //    Card card = deck.dealCard();
    //    std::cout << card.getRank() << " of " << card.getSuit() << "\n";
    //}
    
    Table table = Table();
    table.deal();
    table.play();
    
    return 0;
}

//g++ -o Bridge main.cpp Card.cpp Deck.cpp Player.cpp Table.cpp -std=c++11
//./Bridge