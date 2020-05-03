#include <iostream>
#include <algorithm>
#include <random>
#include <chrono>
#include "Deck.h"
#include "Card.h"

unsigned const seed = std::chrono::system_clock::now().time_since_epoch().count();

Deck::Deck() {
    cards.reserve(deckSize);
    for (auto rank : Card::getPossibleCardRanks()) {
        for (auto suit : Card::getPossibleCardSuits()) {
            Card card = Card(static_cast<Rank>(rank), static_cast<Suit>(suit));
            cards.push_back(card);
        }
    }
    shuffle();
}

void Deck::shuffle() {
    std::shuffle(std::begin(cards), std::end(cards), std::default_random_engine(seed));
    deckIndex = 0;
}

Card& Deck::dealCard() {
    if (!canDeal()) {
        std::cerr << "No more cards to deal.\n";
        throw 0;
    }
    return cards.at(deckIndex++);
}

bool Deck::canDeal() {
    return deckIndex < deckSize;
}