import numpy as np
import random
import utils
import SmartClient
from copy import deepcopy

DECK = utils.generateDeck()

## RULES FUNCTIONS


def playIfCertain(client: SmartClient):
    """play a card with fully known information that is playable"""
    table_cards = client.game_data["tableCards"]

    for i, card_dict in enumerate(client.knowledge):
        if utils.isCardKnown(card_dict) and utils.isCardPlayable(
                card_dict, table_cards):
            return client.generatePlayMove(index=i), False

    return None, True


def playJustHintedCard(client: SmartClient):
    """play the card that was hinted more recently"""
    table_cards = client.game_data["tableCards"]

    if client.last_hinted_card is None:
        return None, True

    if utils.isCardPlayable(client.knowledge[client.last_hinted_card],
                            table_cards):
        return client.generatePlayMove(index=client.last_hinted_card), False

    return None, True


def hintPlayableCard(client: SmartClient):
    """give an hint about a playable card, choose randomly if value or color"""
    if client.game_data["usedNoteTokens"] >= 8:
        return None, True

    table_cards = client.game_data["tableCards"]

    for player in client.game_data["players"]:
        if player.name == client.player_name:
            continue
        for card in player.hand:
            if utils.isCardPlayable({
                    "color": card.color,
                    "value": card.value
            },
                                    table=table_cards):
                hint = random.choice([("color", card.color),
                                      ("value", card.value)])
                return client.generateHintMove(hint_type=hint[0],
                                               dest=player.name,
                                               payload=hint[1]), False

    return None, True


def hintValuePlayableCard(client: SmartClient):
    """give an hint about value of a playable card"""
    if client.game_data["usedNoteTokens"] >= 8:
        return None, True

    table_cards = client.game_data["tableCards"]

    for player in client.game_data["players"]:
        if player.name == client.player_name:
            continue
        for card in player.hand:
            if utils.isCardPlayable({
                    "color": card.color,
                    "value": card.value
            },
                                    table=table_cards):
                hint = ("value", card.value)
                return client.generateHintMove(hint_type=hint[0],
                                               dest=player.name,
                                               payload=hint[1]), False

    return None, True


def hintColorPlayableCard(client: SmartClient):
    """give an hint about color of a playable card"""
    if client.game_data["usedNoteTokens"] >= 8:
        return None, True

    table_cards = client.game_data["tableCards"]

    for player in client.game_data["players"]:
        if player.name == client.player_name:
            continue
        for card in player.hand:
            if utils.isCardPlayable({
                    "color": card.color,
                    "value": card.value
            },
                                    table=table_cards):
                hint = ("color", card.color)
                return client.generateHintMove(hint_type=hint[0],
                                               dest=player.name,
                                               payload=hint[1]), False

    return None, True


def discardUseless(client: SmartClient):
    """discard a fully known and unplayable card"""
    if client.game_data["usedNoteTokens"] == 0:
        return None, True

    table_cards = client.game_data["tableCards"]

    for i, card_dict in enumerate(client.knowledge):
        if utils.isCardKnown(card_dict) & (not utils.isCardPlayable(
                card_dict, table_cards)):
            return client.generateDiscardMove(index=i), False

    return None, True


def hintOnes(client: SmartClient):
    """hint about a player's ones in hand"""
    if client.game_data["usedNoteTokens"] >= 8:
        return None, True

    player_names = client.game_data["player_names"]
    next_player = (player_names.index(client.player_name) +
                   1) % len(player_names)
    dest = client.game_data["player_names"][next_player]

    command = client.generateHintMove(hint_type="value", dest=dest, payload=1)

    if not ("hint" in command):
        return None, True

    return command, False


def hintFives(client: SmartClient):
    """hint about a player's fives in hand"""
    if client.game_data["usedNoteTokens"] >= 8:
        return None, True

    player_names = client.game_data["player_names"]
    next_player = (player_names.index(client.player_name) +
                   1) % len(player_names)
    dest = client.game_data["player_names"][next_player]

    command = client.generateHintMove(hint_type="value", dest=dest, payload=5)

    if not ("hint" in command):
        return None, True

    return command, False


def hintRandom(client: SmartClient):
    """give a random hint"""
    if client.game_data["usedNoteTokens"] >= 8:
        return None, True

    command = client.generateHintMove(random_move=True)
    err = not ("hint" in command)

    return command, err


def playRandomMove(client: SmartClient):
    """just play a random legal move"""
    move = client.generate_random_move()
    err = not (("hint" in move) or ("play" in move) or ("discard" in move))
    return move, err


def probablySafePlayMove(threshold):
    """play a card which is probably safe to play up to a given threshold"""

    def evaluator(client: SmartClient):
        cards = DECK
        cards = utils.subtractCardsFrom(cards, client.game_data["tableCards"])
        cards = utils.subtractCardsFrom(cards,
                                        utils.getOtherPlayersCards(client))
        cards = utils.subtractCardsFrom(
            cards, utils.getDiscardedCards(client.game_data["discardPile"]))

        best_move = (-1, -1)
        for i, _ in enumerate(client.knowledge):
            p = utils.calculatePlayability(
                client.knowledge[i],
                possible_cards=cards,
                table_cards=client.game_data["tableCards"])
            if (p >= threshold) & (p > best_move[1]):
                best_move = (i, p)

        if best_move[0] == -1:
            return None, True

        return client.generatePlayMove(index=best_move[0]), False

    return evaluator


def certainlySafePlayMove(client):
    """same to probablySafePlayMove() but with threshold = 1"""
    return probablySafePlayMove(1)(client)


def probablySafePlayMoveWithStormTokensLeft(threshold):
    """same to probablySafePlayMove() but only if we have still at least one chance of error -> we can take bigger risks"""

    def evaluator(client: SmartClient):
        if client.game_data["usedStormTokens"] < 2:
            return probablySafePlayMove(threshold)(client)

        return None, True

    return evaluator


def discardOldestCard(client):
    """discard card which has been in player's hand the longer"""
    if client.game_data["usedNoteTokens"] == 0:
        return None, True

    index, _ = min(enumerate(client.knowledge),
                   key=(lambda item: item[1]["last_update"]))

    return client.generateDiscardMove(index=index), False


def discardUnidentifiedCard(client):
    """discard a card we don't know anything about"""
    if client.game_data["usedNoteTokens"] == 0:
        return None, True

    for i, card in enumerate(client.knowledge):
        if utils.isCardUnidentified(card):
            return client.generateDiscardMove(index=i), False

    return None, True


def discardOldestUnidentifiedCard(client):
    """same as discardUnidentifiedCard but we discard the one which has been in player's hand the longer"""
    if client.game_data["usedNoteTokens"] == 0:
        return None, True

    hand = deepcopy(client.knowledge)
    for i, c in enumerate(hand):
        hand[i]["index"] = i
    no_info = list(filter(lambda card: utils.isCardUnidentified(card), hand))

    if len(no_info) == 0:
        return None, True
    oldest_unidentified_card = min(no_info,
                                   key=lambda card: card["last_update"])

    return client.generateDiscardMove(
        index=oldest_unidentified_card["index"]), False


def probablySafeDiscardMove(threshold):
    """discard a card which is probably safe to discard up to a given threshold"""

    def evaluator(client: SmartClient):
        # make set of all cards
        # then subtract cards on table, in other player's hands & in discard pile
        cards = DECK
        cards = utils.subtractCardsFrom(cards, client.game_data["tableCards"])
        cards = utils.subtractCardsFrom(cards,
                                        utils.getOtherPlayersCards(client))
        cards = utils.subtractCardsFrom(
            cards, utils.getDiscardedCards(client.game_data["discardPile"]))

        # calc playability probability of each card in own hand (over the refined set)
        # keep track of card with highest playability probability vs. threshold
        useless_move = (-1, -1)
        for i, _ in enumerate(client.knowledge):
            p = 1 - utils.calculatePlayability(
                client.knowledge[i],
                possible_cards=cards,
                table_cards=client.game_data["tableCards"])
            if (p >= threshold) & (p > useless_move[1]):
                useless_move = (i, p)

        # none of the cards fulfilled the threshold
        if useless_move[0] == -1:
            return None, True

        return client.generatePlayMove(index=useless_move[0]), False

    return evaluator


################################################################################################

RULES = np.array([
    playIfCertain,  # 0
    playJustHintedCard,  # 1
    hintPlayableCard,  # 2
    hintValuePlayableCard,  # 3
    hintColorPlayableCard,  # 4
    hintOnes,  # 5
    hintFives,  # 6
    discardUseless,  # 7
    hintRandom,  # 8
    playRandomMove,  # 9
    certainlySafePlayMove,  # 10
    probablySafePlayMove(0.8),  # 11
    probablySafePlayMove(0.65),  # 12
    probablySafePlayMove(0.5),  # 13
    probablySafePlayMoveWithStormTokensLeft(0.6),  # 14
    probablySafePlayMoveWithStormTokensLeft(0.4),  # 15
    probablySafePlayMoveWithStormTokensLeft(0.2),  # 16
    discardOldestUnidentifiedCard,  # 17
    discardOldestCard,  # 18
    discardUnidentifiedCard,  # 19
    playRandomMove,  # 20
    probablySafeDiscardMove(0.8),  # 21
    probablySafeDiscardMove(0.65),  # 22
    probablySafeDiscardMove(0.5),  # 23
])
DEFAULT_ORDER = list(range(0, len(RULES)))


def getRulesInOrder(order):
    return RULES[order]
