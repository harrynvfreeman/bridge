#include <iostream>
#include "Utils.h"
#include "Card.h"

int calcWinningScore(int bidSuit, int bidRank, int numTricksWon, int overTricks, int isDoubled, int vulnerable);
int calcLosingScore(int bidSuit, int underTricks, int isDoubled, int vulnerable);
int calcSuitScore(int bidSuit, int bidRank, int numTricksWon, int isDouble);
int calcGameSlamScore(int bidSuit, int bidRank, int vulnerable);
int calcGameBonus(int bidSuit, int bidRank, int isDoubled, int vulnerable);

const int bidOffset = 6;
int calcDuplicateScore(int bidSuit, int bidRank, int numTricksWon, int isDoubled, int vulnerable) {
    int bidTarget = bidRank + bidOffset;
    int overTricks = numTricksWon - bidTarget;
    if (overTricks >= 0) {
        return calcWinningScore(bidSuit, bidRank, numTricksWon, overTricks, isDoubled, vulnerable);
    } else {
        return calcLosingScore(bidSuit, 0-overTricks, isDoubled, vulnerable);
    }
}

int calcWinningScore(int bidSuit, int bidRank, int numTricksWon, int overTricks, int isDoubled, int vulnerable) {
    int suitScore = calcSuitScore(bidSuit, bidRank, numTricksWon, isDoubled);
    int gameSlamScore = calcGameSlamScore(bidSuit, bidRank, vulnerable);
    
    if (isDoubled == 0) {
        return suitScore + gameSlamScore;
    }
    
    int gameBonus = calcGameBonus(bidSuit, bidRank, isDoubled, vulnerable);
    
    if (isDoubled == 1) {
        return (suitScore << 1) + (100 << vulnerable)*overTricks + gameBonus + gameSlamScore;
    }
    
    return (suitScore << 2) - 50 + (200 << vulnerable)*overTricks + gameBonus + gameSlamScore;
    
}

//isDoubled: 0 for not, 1 for doubled, 2 for redoubled
int calcLosingScore(int bidSuit, int underTricks, int isDoubled, int vulnerable) {
    if (isDoubled == 0) {
        return vulnerable ? -100*underTricks : -50*underTricks;
    }
    
    int shift = isDoubled - 1;
    switch (underTricks) {
        case 1:
            return (vulnerable ? -200 : -100) << shift;
        case 2:
            return (vulnerable ? -500 : -300) << shift;
        case 3:
        case 4:
        case 5:
        case 6:
        case 7:
        case 8:
        case 9:
        case 10:
        case 11:
        case 12:
        case 13:
            return (-((vulnerable ? 800 : 500) + 300*(underTricks-3))) << shift;
        default:
            std::cerr << "Invalid undertricks number: " << underTricks << "\n";
            throw 0;
    }
}

int calcSuitScore(int bidSuit, int bidRank, int numTricksWon, int isDouble) {
    int multipland = (isDouble > 0) ? bidRank : numTricksWon - bidOffset;
    switch (bidSuit) {
        case clubs:
        case diamonds:
            return 50 + multipland*20;
        case hearts:
        case spades:
            return 50 + multipland*30;
        case none:
            return 60 + multipland*30;
        default:
            std::cerr << "Invalid suit to calculate score: " << bidSuit << "\n";
            throw 0; 
    }
}

int calcGameSlamScore(int bidSuit, int bidRank, int vulnerable) {
    //CAN REMOVE ONCE TESTING DONE
    if (bidRank == 0 || bidRank > 7) {
        std::cerr << "Invalid bid rank. Did you convert properly? " << bidRank << "\n";
    }
    
    if (bidSuit < hearts && bidRank < 5) {
        return 0;
    }
    
    if (bidSuit < none && bidRank < 4) {
        return 0;
    }
    
    if (bidSuit == none && bidRank < 3) {
        return 0;
    }
    
    if (bidRank < 6) {
        return vulnerable ? 450 : 250;
    }
    
    if (bidRank == 6) {
        return vulnerable ? 1200 : 750;
    }
    
    return vulnerable ? 1950 : 1250;
}

int calcGameBonus(int bidSuit, int bidRank, int isDoubled, int vulnerable) {
    if (isDoubled == 0) {
        return 0;
    }
    
    int gameBonusVal = vulnerable ? 450 : 250;
    switch(bidSuit) {
        case clubs:
        case diamonds:
            return bidRank >= 4-isDoubled ? gameBonusVal : 0;
        case hearts:
        case spades:
            return bidRank >= 3-isDoubled ? gameBonusVal : 0;
        case none:
            return bidRank >= 2-isDoubled ? gameBonusVal : 0;
        default:
            std::cerr << "Invalid suit to calculate game bonus: " << bidSuit << "\n";
            throw 0;
    }
}