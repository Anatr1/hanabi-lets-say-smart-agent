# Computational Intelligence 2021-2022

Exam of computational intelligence 2021 - 2022. It requires teaching the client to play the game of Hanabi (rules can be found [here](https://www.spillehulen.dk/media/102616/hanabi-card-game-rules.pdf)).

## About
*The project is an attempt to reimplement, in a lightweight mode, the procedure described in this paper: https://arxiv.org/abs/1809.09764. Code structure takes inspiration from https://github.com/linomp/computational-intelligence implementation but features a different genetic algorithm used for evolving a strategy and a different ruleset. However, the code was entirely rewritten, corrected and reviewed by me and I am responsible of the whole content of the repo.*

## Client

To start the client:

```bash
python SmartClient.py <IP> <port> <PlayerName>
```

Arguments:

+ IP: IP address of the server (for localhost: 127.0.0.1)
+ port: server TCP port (default: 1024)
+ PlayerName: the name of the player


## Server

To start the server:

```bash
python server.py <minNumPlayers>
```

Arguments:

+ minNumPlayers, __optional__: game does not start until a minimum number of player has been reached. Default = 2


Commands for server:

+ exit: exit from the server

## Evolution

To evolve a strategy:

```bash
python evolve.py
```

## Disclaimer

For time constraints reasons I ran ```evolve.py``` for a limited amount of time and with limited episode numbers. The **currently best score achieved is 12.75** but maybe with more training time it could be a little increased. 
