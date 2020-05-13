#include <iostream>
#include "DdsInterface.h"
#include "./include/dll.h"
#include "Card.h"

//g++ -o DdsInterface.so -shared -fPIC DdsInterface.cpp -L. -ldds

void convertHand(int * hand, int position, ddTableDeal * tableDeal);

int numTricks(int bidSuit, int declarer, int* hand0, int* hand1, int* hand2, int* hand3) {
    
    #if defined(__linux) || defined(__APPLE__)
        SetMaxThreads(0);
    #endif
    
    ddTableDeal tableDeal;
    ddTableResults tableResults;
    int res;
    
    convertHand(hand0, 0, &tableDeal);
    convertHand(hand1, 1, &tableDeal);
    convertHand(hand2, 2, &tableDeal);
    convertHand(hand3, 3, &tableDeal);
    
    res = CalcDDtable(tableDeal, &tableResults);
    
    if (res != RETURN_NO_FAULT)
    {
      printf("DDS error\n");
      return -1;
    }
    
    int ddsBidSuit = bidSuit == 4 ? bidSuit : 3 - bidSuit;
    
    return tableResults.resTable[ddsBidSuit][declarer];
}

void convertHand(int * hand, int position, ddTableDeal * tableDeal) {
    unsigned int clubs = 0;
    unsigned int diamonds = 0;
    unsigned int hearts = 0;
    unsigned int spades = 0;
    
    for (int i = 0; i < numRanks; i++) {
        clubs = clubs + (*(hand + i) << (i + 2));
    }
    
    for (int i = 0; i < numRanks; i++) {
        diamonds = diamonds + (*(hand + i + numRanks) << (i + 2));
    }
    
    for (int i = 0; i < numRanks; i++) {
        hearts = hearts + (*(hand + i + 2*numRanks) << (i + 2));
    }
    
    for (int i = 0; i < numRanks; i++) {
        spades = spades + (*(hand + i + 3*numRanks) << (i + 2));
    }
    
    
    tableDeal->cards[position][0] = spades;
    tableDeal->cards[position][1] = hearts;
    tableDeal->cards[position][2] = diamonds;
    tableDeal->cards[position][3] = clubs;
}