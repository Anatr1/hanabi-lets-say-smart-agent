import os
import random
import pickle
import time
import GameData
from sys import stdout
from constants import *
from copy import deepcopy

CLIENT_STATUSES = ["Lobby", "Game", "GameHint"]
GAME_MOVES = ["play", "discard", "hint"]

EXIT_COMMAND = "exit"
SHOW_COMMAND = "show"
READY_COMMAND = "ready"
HINT_COMMAND = "hint"
DISCARD_COMMAND = "discard"
PLAY_COMMAND = "play"


class Client:

    def __init__(self, player_name, ip, port):
        self.player_name = player_name
        self.ip = ip
        self.port = port
        self.ready = False
        self.all_ready = False
        self.current_status = CLIENT_STATUSES[0]
        self.game_data = {
            "player": None,
            "usedStormTokens": 0,
            "usedNoteTokens": 0,
            "players": [],
            "player_names": []
        }
        self.sent_ready_command = False
        self.running = True

        # To store information received in hints
        self.knowledge = []
        for _ in range(0, 5):
            self.knowledge.append({
                "color": None,
                "value": None,
                "last_update": time.time()
            })

    def connectToServer(self, _socket):
        """starts connection with the server"""

        request = GameData.ClientPlayerAddData(self.player_name)
        _socket.connect((self.ip, self.port))
        _socket.send(request.serialize())

        data = GameData.GameData.deserialize(_socket.recv(DATASIZE))
        if type(data) is GameData.ServerPlayerConnectionOk:
            # print("Connection accepted by the server. Welcome " + self.player_name)
            _socket.send(
                GameData.ClientPlayerStartRequest(
                    self.player_name).serialize())

    def receiveDataFromServer(self, data, _socket):
        """receives and processes incoming data from game server"""
        data_ok = False
        invalid_action = False

        if type(data) is GameData.ServerPlayerStartRequestAccepted:
            data_ok = True
            data = _socket.recv(DATASIZE)
            data = GameData.GameData.deserialize(data)

        if type(data) is GameData.ServerStartGameData:
            data_ok = True
            _socket.send(
                GameData.ClientPlayerReadyData(self.player_name).serialize())
            self.current_status = CLIENT_STATUSES[1]
            self.all_ready = True
            self.game_data["player"] = data.players[0]
            self.game_data["player_names"] = data.players

        if type(data) is GameData.ServerGameStateData:
            data_ok = True
            self.game_data["tableCards"] = deepcopy(data.tableCards)
            self.game_data["usedStormTokens"] = data.usedStormTokens
            self.game_data["usedNoteTokens"] = data.usedNoteTokens
            self.game_data["currentPlayer"] = data.currentPlayer
            self.game_data["players"] = data.players
            self.game_data["discardPile"] = data.discardPile
        if type(data) is GameData.ServerActionInvalid:
            data_ok = True
            invalid_action = True
            print("Invalid action performed. Reason:")
            print(data.message)
        if type(data) is GameData.ServerActionValid:
            data_ok = True
        if type(data) is GameData.ServerPlayerMoveOk:
            data_ok = True
        if type(data) is GameData.ServerPlayerThunderStrike:
            data_ok = True
            self.game_data["usedStormTokens"] += 1
        if type(data) is GameData.ServerHintData:
            data_ok = True
        if type(data) is GameData.ServerInvalidDataReceived:
            data_ok = True
            invalid_action = True
            print(data.data)
        if type(data) is GameData.ServerGameOver:
            data_ok = True
            # print(f"Stopping {self.player_name}")
            stdout.flush()
            self.dumpResults()
            self.running = False
        if not data_ok:
            print("Unknown or unimplemented data type: " + str(type(data)))
            invalid_action = True

        stdout.flush()

        return invalid_action

    def listen(self, _socket):
        """listens for server responses"""
        data = _socket.recv(DATASIZE)
        if not data:
            return None
        data = GameData.GameData.deserialize(data)
        for field in vars(data).keys():
            self.game_data[field] = getattr(data, field, None)

        invalid_action = self.receiveDataFromServer(data, _socket)
        return data, invalid_action

    def dumpResults(self):
        """outputs player data to a binary file"""
        try:
            binary_file = open(f"outputs/{self.player_name}", "wb")
            pickle.dump(self, binary_file)
            binary_file.close()
        except Exception as e:
            print(e)
            print(f"{self.player_name} output dump went wrong.")

    def isMyTurn(self):
        """checks if it is now the player's turn"""
        return self.game_data["player"] == self.player_name

    def getColorsFromPlayerHand(self, player_name):
        """queries hand of given players to get colors"""
        for player in self.game_data["players"]:
            if player.name == player_name:
                return list(set(map(lambda c: c.color, player.hand)))

        return []

    def getValuesFromPlayerHand(self, player_name):
        """queries hand of given players to get values"""
        for player in self.game_data["players"]:
            if player.name == player_name:
                return list(set(map(lambda c: c.value, player.hand)))

        return []

    def playMove(self, move, _socket):
        """plays the given move"""
        if (move != "show") and self.ready and not self.isMyTurn():
            return

        if move is None:
            return

        if move == "exit":
            self.run = False
            os._exit(0)
        elif move == "show" and self.current_status == CLIENT_STATUSES[1]:
            _socket.send(
                GameData.ClientGetGameStateRequest(
                    self.player_name).serialize())
        elif move.split(" ")[
                0] == "discard" and self.current_status == CLIENT_STATUSES[1]:
            try:
                cardStr = move.split(" ")
                cardOrder = int(cardStr[1])
                _socket.send(
                    GameData.ClientPlayerDiscardCardRequest(
                        self.player_name, cardOrder).serialize())
            except:
                pass
        elif move.split(" ")[
                0] == "play" and self.current_status == CLIENT_STATUSES[1]:
            try:
                cardStr = move.split(" ")
                cardOrder = int(cardStr[1])
                _socket.send(
                    GameData.ClientPlayerPlayCardRequest(
                        self.player_name, cardOrder).serialize())
            except:
                pass
        elif move.split(" ")[
                0] == "hint" and self.current_status == CLIENT_STATUSES[1]:
            try:
                destination = move.split(" ")[2]
                t = move.split(" ")[1].lower()
                value = move.split(" ")[3].lower()
                if t == "value":
                    value = int(value)
                _socket.send(
                    GameData.ClientHintData(self.player_name, destination, t,
                                            value).serialize())
            except:
                pass
        else:
            print("Unknown move: " + move)
        stdout.flush()

    def generatePlayMove(self, index=None, random_move=False):
        """generates a PLAY move with given parameters"""
        max_rand = 4
        if len(self.game_data["players"]) >= 4:
            max_rand = 3

        if random_move:
            index = random.randint(0, max_rand)

        if index not in range(max_rand + 1):
            print("Invalid card index!")
            return None

        self.knowledge[index] = {
            "color": None,
            "value": None,
            "last_update": time.time()
        }

        # print(f"-----play {index}-----")
        return f"play {index}"

    def generateDiscardMove(self, index=None, random_move=False):
        """generates a DISCARD move with given parameters"""
        max_rand = 4
        if len(self.game_data["players"]) >= 4:
            max_rand = 3

        if self.game_data["usedNoteTokens"] == 0:
            return "show"

        if random_move:
            index = random.randint(0, max_rand)

        if index not in range(max_rand + 1):
            print("Invalid card index!")
            return None

        self.knowledge[index] = {
            "color": None,
            "value": None,
            "last_update": time.time()
        }

        # print(f"-----discard {index}-----")
        return f"discard {index}"

    def generateHintMove(self,
                         hint_type=None,
                         dest=None,
                         payload=None,
                         random_move=False):
        """generates a HINT move with given parameters"""
        if self.game_data["usedNoteTokens"] == 8:
            return "show"

        if random_move:
            try:
                players = list(
                    filter(lambda n: n != self.player_name,
                           self.game_data["player_names"]))
                dest = random.choice(players)
                hint_type = random.choice(["color", "value"])

                if hint_type == "color":
                    colors = self.getColorsFromPlayerHand(dest)
                    payload = random.choice(colors)
                else:
                    values = self.getValuesFromPlayerHand(dest)
                    payload = random.choice(values)

                # print(f"-------hint {hint_type} {dest} {payload}------")
                return f"hint {hint_type} {dest} {payload}"

            except Exception as err:
                print(err)
                return "show"
        else:
            if not ((payload in self.getColorsFromPlayerHand(dest))
                    or payload in self.getValuesFromPlayerHand(dest)):
                # print("Unvalid Hint! Defaulting to show")
                return "show"

            # print(f"-------hint {hint_type} {dest} {payload}------")
            return f"hint {hint_type} {dest} {payload}"
