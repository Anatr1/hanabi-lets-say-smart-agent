import math
import rules
import server
import SmartClient
import time
import pickle
import utils
import numpy as np
from SmartClient import SmartClient
from multiprocessing import Process, Lock

IP = "127.0.0.1"
PORT = 1024
NUM_PLAYERS = 2
NUM_RULES = len(rules.DEFAULT_ORDER)
POPULATION_SIZE = NUM_RULES // 2
TIMEOUT = 100000  # Just to be super sure
EPISODES = 4
STEADY_STATE = 5
MUTATION_RATE = 0.75
PERCENTAGE = 10
EVOLVE_EXISTING_BEST_STRATEGY = True


def playAGame(strategy):
    """plays one istance of a game match between players having all the same strategy and return the obtained score"""
    server_process = Process(target=server.start_server, args=(NUM_PLAYERS, ))
    server_process.start()
    time.sleep(0.5)  #Otherwise the server crashes

    lock = Lock()

    players = []  # Players processes list
    for i in range(0, NUM_PLAYERS):
        player_process = Process(target=SmartClient(
            f"SmartClient-{i}", IP, PORT, rules_order=strategy).start,
                                 args=(lock, ))
        players.append(player_process)
        players[i].start()

    for i in range(0, len(players)):
        players[i].join(TIMEOUT)

    server_process.join(TIMEOUT)

    # Game ended
    players = [
    ]  # Changes content from a list of processes to a list of clients
    for i in range(0, NUM_PLAYERS):
        binary_file = open(f"outputs/SmartClient-{i}", "rb")
        players.append(pickle.load(binary_file))
        binary_file.close()

    # I ignore that server counts as zero-points games the ones that end with storm
    # tokens. I count the points up until that point
    score = 0
    for player in players:
        temp_score = 0
        table_cards = player.game_data["tableCards"]

        for card_stack in table_cards:
            temp_score += len(table_cards[card_stack])

        # Sometimes player get different scores for some reason -> probably it has an outdated table
        if temp_score > score:
            score = temp_score

        # print(f"{player.player_name}: {temp_score}")

    # print(f"Game final score: {score}")
    return score


def evaluateSolution(strategy_individual, number=None, population_length=None):
    """plays [EPISODES] games between players having the same strategy and returns the average obtained score"""
    total_scores = 0
    if number is not None and population_length is not None:
        print(f"Evaluating {strategy_individual}:")

    for ep in range(EPISODES):
        total_scores += playAGame(strategy_individual)
        print(f"Episode: {ep}\n")

    avg_score = total_scores / EPISODES

    if number is not None and population_length is not None:
        print(f"Evaluated solution n° {number+1}/{population_length}\n\n")

    return avg_score


def swapMutation(parent, mutation_rate=MUTATION_RATE):
    """generates a child solution by applying a swapping mutation to its parent"""
    child = parent.copy()
    p = None
    while p is None or p < mutation_rate:
        i1 = np.random.randint(0, NUM_RULES)
        i2 = np.random.randint(0, NUM_RULES)
        temp = child[i1]
        child[i1] = child[i2]
        child[i2] = temp
        p = np.random.random()
    return child


def getTopPercent(population, population_fitness):
    """selects the top PERCENTAGE% individuals with the best fitness in the population"""
    x = math.ceil(len(population) * (PERCENTAGE / 100))

    ind = np.argpartition(population_fitness, -x)[-x:]

    return population[ind]


def evolve():
    """Evolves a strategy -> tries to optimize the rule order"""
    # Best individual
    global_best_solution = []

    # Score of best individual
    global_best_fitness = 0

    # Counter for the steady state
    steady_state = 0

    # Generations counter
    generations = 0

    # Population -> possible orders for the rules
    if not EVOLVE_EXISTING_BEST_STRATEGY:
        population = np.tile(np.array(range(NUM_RULES)), (POPULATION_SIZE, 1))
        # Population is now all in the default order, this could bias the result so we shuffle it
        for i in range(POPULATION_SIZE):
            np.random.shuffle(population[i])
    else:
        # We do not start from a blank state but we're trying to evolve the previously obtained strategy
        population = np.tile(np.array(utils.loadStrategyFromFile()),
                             (POPULATION_SIZE, 1))
        global_best_solution = utils.loadStrategyFromFile()
        global_best_fitness = utils.loadScoreFromFile()

    # Evolution loop
    while steady_state < STEADY_STATE:
        steady_state += 1
        generations += 1
        offspring = []

        # Generate offspring -> Every selected parent must reproduce 10 times through swap mutation
        print("OFFSPRING GENERATION...")
        for parent in population:
            for i in range(10):
                offspring.append(
                    swapMutation(parent,
                                 mutation_rate=(MUTATION_RATE / generations)))

        offspring = np.array(offspring)

        # New offspring is evaluated and new parents are selected
        print("OFFSPRING EVALUTATION...")
        offspring_fitness = []
        for i in range(len(offspring)):
            child_fitness = evaluateSolution(offspring[i],
                                             number=i,
                                             population_length=len(offspring))
            offspring_fitness.append(child_fitness)

            if child_fitness > global_best_fitness:
                global_best_fitness = child_fitness
                global_best_solution = offspring[i]
                # We had an improvement in this generation, so we reset the steady state counter and save to file current best solution
                steady_state = 0
                print("NEW BEST SOLUTION FOUND")
                utils.saveSolutionToFile(global_best_solution,
                                         global_best_fitness)

        # Parent Selection -> Pick the top 10% individuals
        print("OFFSPRING SELECTION...")
        population = getTopPercent(offspring, offspring_fitness)

        print(
            f"\n\n\n\n\n\nGeneration n° {generations} - Global best: {global_best_fitness}"
        )
        time.sleep(2)

        # Time limit
        if generations == 100:
            break

    return global_best_solution, global_best_fitness


if __name__ == "__main__":
    print(evolve())
