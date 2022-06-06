"""
A "Smart" agent that plays according to a rule set that it has evolved during training?
"""
from sys import argv
from time import sleep
from multiprocessing import Lock, Process
from Client import *
import socket
import rules
import utils


class SmartClient(Client):

    def __init__(self,
                 player_name,
                 ip,
                 port,
                 rules_order=None,
                 load_strategy_from_file=False,
                 print_to_console=False):
        Client.__init__(self, player_name, ip, port)
        if rules_order is not None:
            self.rules_order = rules_order
        elif load_strategy_from_file:
            self.rules_order = utils.loadStrategyFromFile()
        else:
            self.rules_order = rules.DEFAULT_ORDER

        self.last_hinted_card = None
        self.print_to_console = print_to_console

    def generate_random_move(self):
        """Generates a random valid move"""
        if len(self.game_data["players"]) == 0:
            return "show"

        valid = False
        while not valid:
            move = random.choice(GAME_MOVES)
            if move == "discard" and self.game_data["usedNoteTokens"] == 0:
                continue
            if move == "hint" and self.game_data["usedNoteTokens"] == 8:
                continue
            valid = True

        if move == "play":
            return self.generatePlayMove(random_move=True)
        elif move == "discard":
            return self.generateDiscardMove(random_move=True)
        elif move == "hint":
            return self.generateHintMove(random_move=True)

    def receiveHint(self, hintFromServer):
        """receive and process an hint from the server"""
        if not type(hintFromServer) is GameData.ServerHintData:
            pass
        elif self.player_name == hintFromServer.destination:
            for pos in hintFromServer.positions:
                self.knowledge[pos][hintFromServer.type] = hintFromServer.value
                self.last_hinted_card = pos
        else:
            pass

    def start(self, _lock):
        """Runs player instance"""

        policy = rules.getRulesInOrder(self.rules_order)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

            self.connectToServer(s)
            self.ready = True

            while self.running:
                hint, _ = self.listen(s)

                if not self.running:
                    self.dumpResults()
                    break

                self.receiveHint(hint)

                # Wait for other players to join
                if self.ready & (not self.all_ready):
                    continue

                try:
                    _lock.acquire()
                    self.playMove("show", s)
                    data, _ = self.listen(s)
                except:
                    print(
                        f"{self.player_name} crashed while waiting for its turn"
                    )
                finally:
                    _lock.release()

                if self.isMyTurn():
                    _lock.acquire()
                    try:
                        self.playMove("show", s)
                        data, _ = self.listen(s)
                        self.receiveHint(data)

                        # Rule selection phase
                        invalid_action = False
                        for rule in policy:
                            move, err = rule(self)
                            if err:
                                continue
                            self.playMove(move, s)
                            if self.print_to_console:
                                print(f"{self.player_name} plays: {move}")
                            data, invalid_action = self.listen(s)
                            if not invalid_action:
                                self.receiveHint(data)
                                break

                        self.receiveHint(data)

                    finally:
                        _lock.release()


if __name__ == "__main__":
    ip = argv[1]
    port = int(argv[2])
    name = argv[3]

    lock = Lock()

    load_strategy_from_file = utils.doWeHaveBestStrategy()

    player_process = Process(target=SmartClient(
        name,
        ip,
        port,
        load_strategy_from_file=load_strategy_from_file,
        print_to_console=True).start,
                             args=(lock, ))
    player_process.start()