from unittest import result
from game import Card
from copy import deepcopy
import numpy as np


def generateDeck():
    colors = ["red", "blue", "green", "yellow", "white"]
    values = [(1, 3), (2, 2), (3, 2), (4, 2), (5, 1)]
    deck = {}
    n = 0

    for color in colors:
        deck[color] = []
        for pair in values:
            value, count = pair[0], pair[1]
            for _ in range(0, count):
                deck[color].append(Card(id=n, color=color, value=value))
                n += 1

    return deck


def isCardKnown(card_info_dict):
    return (card_info_dict["color"] is not None) and (card_info_dict["value"]
                                                      is not None)


def isCardUnidentified(card_info_dict):
    return (card_info_dict["color"] is None) & (card_info_dict["value"] is
                                                None)


def isCardPlayable(card_info_dict, table):
    if not isCardKnown(card_info_dict):
        return False

    color = card_info_dict["color"]
    value = card_info_dict["value"]
    still_no_cards = len(table[color]) == 0

    if still_no_cards:
        return value == 1

    highest_stack_card = max((table[color]),
                             key=(lambda c: c.value),
                             default=None)
    if highest_stack_card is None:
        return False

    return (value - 1) == highest_stack_card.value


def subtractCardsFrom(my_cards, cards_to_subtract):
    result_cards = deepcopy(my_cards)

    if (len(cards_to_subtract) == 0) or (len(my_cards) == 0):
        return result_cards

    for color in my_cards.keys():
        if not (color in cards_to_subtract.keys()):
            continue
        for card_to_subtract in cards_to_subtract[color]:
            for i, my_card in enumerate(my_cards[color]):
                if result_cards[color][i] is None:
                    continue
                if (my_card.value == card_to_subtract.value) & (
                        my_card.color == card_to_subtract.color):
                    result_cards[color][i] = None
                    break

        result_cards[color] = list(
            filter(lambda c: c is not None, result_cards[color]))

    return result_cards


def getOtherPlayersCards(client):
    result_cards = {}

    for player in client.game_data["players"]:
        if player.name == client.player_name:
            continue
        hand = deepcopy(player.hand)
        for card in hand:
            if not (card.color in result_cards.keys()):
                result_cards[card.color] = []
            result_cards[card.color].append(card)

    return result_cards


def getDiscardedCards(discard_pile):
    result_cards = {}

    for card in discard_pile:
        if not (card.color in result_cards.keys()):
            result_cards[card.color] = []
        result_cards[card.color].append(card)

    return result_cards


def calculatePlayability(hint, possible_cards, table_cards):
    cards = list({x for v in possible_cards.values() for x in v})

    if hint["color"] is not None:
        cards = list(filter(lambda c: c.color == hint["color"], cards))
    if hint["value"] is not None:
        cards = list(filter(lambda c: c.value == hint["value"], cards))

    playable_cards = list(
        filter(
            lambda c: isCardPlayable(card_info_dict={
                "color": c.color,
                "value": c.value
            },
                                     table=table_cards),
            cards,
        ))

    try:
        p = len(playable_cards) / len(cards)
        return p
    except:
        return 0


def saveSolutionToFile(solution, score):
    # Txt because I want it to be human readable
    out_file = open("outputs/best_strategy.txt", "w")
    print(solution)
    print(score)
    out_file.write(f"{solution}\n{score}")
    out_file.close


def loadStrategyFromFile():
    strategy = []
    strategy_file = open("outputs/best_strategy.txt", "r")
    line = strategy_file.readline()
    strategy = [int(x) for x in line.replace("]", "").replace("[", "").split()]
    return strategy


def loadScoreFromFile():
    strategy_file = open("outputs/best_strategy.txt", "r")
    _ = strategy_file.readline()
    score = float(strategy_file.readline())
    return score


def doWeHaveBestStrategy():
    try:
        strategy_file = open("outputs/best_strategy.txt", "r")
        line = strategy_file.readline()
        if len(line) > 0:
            return True
    except:
        return False
