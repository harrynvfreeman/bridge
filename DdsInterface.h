extern "C"
int numTricks(int bidSuit, int declarer, int* hand0, int* hand1, int* hand2, int* hand3);

extern "C"
int calcScore(int bidSuit, int bidRank, int declarer, int isDoubled, int vulnerable, int* hand0, int* hand1, int* hand2, int* hand3);

extern "C"
void initialize();

extern "C"
void getMaxTricks(int* hand0, int* hand1, int* hand2, int* hand3, int* result);