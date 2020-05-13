#include <iostream>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <vector>
#include "Card.h"
#include "Deck.h"
#include "Table.h"
#include "./include/dll.h"
#include "hands.h"

int main()
{
    //try {
    //    Table table = Table(true);
    //    table.deal(0);
    //    //table.bid();
    //    if (table.bid()) {
    //        table.play();
    //    }
    //} catch( int e ) {
    //    std::cerr << e << "\n";
    //}
    
    Table table = Table(true);
    table.deal(0);
    
    
    #if defined(__linux) || defined(__APPLE__)
        SetMaxThreads(0);
    #endif
    
    ddTableDeal tableDeal;
    ddTableResults tableResults;
    
    //for (int h = 0; h < DDS_HANDS; h++) {
    //    for (int s = 0; s < DDS_SUITS; s++) {
    //        if (h == s) {
    //            tableDeal.cards[h][s] = 32764;
    //        } else {
    //            tableDeal.cards[h][s] = 0;
    //        }
    //    }
    //}
    
    for (unsigned int h = 0; h < numPlayers; h++) {
        Player & player = table.getPlayers().at(h);
        for (auto suit : Card::getPossibleCardSuits()) {
            tableDeal.cards[h][Card::ddsSuitConvert(suit)] = player.getHandEncoding(suit);
        }
    }
    
    int res;
    char line[80];
    
    
    res = CalcDDtable(tableDeal, &tableResults);
        
    if (res != RETURN_NO_FAULT)
    {
      printf("DDS error\n");
    } else
    {
        printf("Success!\n");
    }
    
    PrintHand(line, tableDeal.cards);

    PrintTable(&tableResults);
    
    return 0;
}



//g++ -o Bridge main.cpp Card.cpp Deck.cpp Player.cpp Table.cpp -std=c++11
//./Bridge
