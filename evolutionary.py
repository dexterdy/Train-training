import copy
import math
from multiprocessing.pool import Pool
import random
import multiprocessing
import functools
from tqdm import tqdm
from algorithmInterface import Schedule, NoAlgorithmSchedule, TrainSchedule
from typing import TYPE_CHECKING
from citiesToInt import cities_to_int

from compositeTrack import network_to_TSP

if TYPE_CHECKING:
    from network import TrainNetwork, City
    from compositeTrack import CompositeTrack


DummySchedule = list[list["CompositeTrack"]]


def dummy_to_real(dummies: list[DummySchedule]) -> list["Schedule"]:
    return [
        NoAlgorithmSchedule([TrainSchedule(False, route) for route in schedule])
        for schedule in dummies
    ]


def real_to_dummy(schedules: list["Schedule"]) -> list[DummySchedule]:
    return [
        [train.route for train in schedule.trainSchedules] for schedule in schedules
    ]


def init_pool(
    tsp: dict[tuple[int, int], "CompositeTrack"], size: int, amountTrains: int
) -> list[DummySchedule]:
    tracks = list(tsp.values())
    schedules: list[DummySchedule] = []
    for _ in range(size):
        trains: list[list["CompositeTrack"]] = []
        for _ in range(amountTrains):
            trains.append([random.choice(tracks)])
        schedules.append(trains)
    return schedules


def select(
    pool: list[DummySchedule],
    network: "TrainNetwork",
    processes: Pool,
) -> list[DummySchedule]:
    realSchedules = dummy_to_real(pool)
    mappedSchedules = list(
        enumerate(processes.map(network.get_average_travel_time, realSchedules))
    )
    sortedSchedules = sorted(mappedSchedules, key=lambda x: x[1])
    bestPart = sortedSchedules[: math.ceil(len(pool) / 4)]
    randomPart = random.sample(
        sortedSchedules[math.ceil(len(pool) / 4) :],
        math.ceil(len(pool) / 2) - len(bestPart),
    )
    return [pool[i] for i, _ in bestPart] + [pool[i] for i, _ in randomPart]


def mutateSchedule(
    tsp: dict[tuple[int, int], "CompositeTrack"],
    cities: list[int],
    schedule: DummySchedule,
) -> DummySchedule:
    child = schedule[:]
    itemsToMutate = random.sample(list(enumerate(child)), math.ceil(len(child) / 2))
    for j, item in itemsToMutate:
        chance = random.random()
        if len(item) == 1 or chance <= 0.5:
            child[j] = mutateInsert(item, tsp, cities)
        else:
            child[j] = mutateDelete(item, tsp)
    return child


def mutate(
    pool: list[DummySchedule],
    tsp: dict[tuple[int, int], "CompositeTrack"],
    cities: list[int],
    processes: Pool,
) -> list[DummySchedule]:
    newItems: list[DummySchedule] = processes.map(
        functools.partial(mutateSchedule, tsp, cities), pool[:]
    )

    pool.extend(newItems)
    return pool


def mutateInsert(
    item: list["CompositeTrack"],
    tsp: dict[tuple[int, int], "CompositeTrack"],
    cities: list[int],
) -> list["CompositeTrack"]:
    newRoute = item[:]
    insertPosition = random.randint(-1, len(item))
    cityToInsert = random.choice(cities)
    if insertPosition == -1:
        newRoute.insert(0, tsp[cityToInsert, item[0].start.id])
    elif insertPosition == len(item):
        newRoute.append(tsp[item[-1].end.id, cityToInsert])
    else:
        newTrack1 = tsp[item[insertPosition].start.id, cityToInsert]
        newTrack2 = tsp[cityToInsert, item[insertPosition].end.id]
        newRoute.pop(insertPosition)
        newRoute.insert(insertPosition, newTrack1)
        newRoute.insert(insertPosition + 1, newTrack2)
    return newRoute


def mutateDelete(
    item: list["CompositeTrack"], tsp: dict[tuple[int, int], "CompositeTrack"]
) -> list["CompositeTrack"]:
    newRoute = item[:]
    removePosition = random.randint(0, len(item))
    if removePosition == 0:
        newRoute.pop(0)
    elif removePosition == len(item):
        newRoute.pop(-1)
    else:
        newTrack = tsp[
            newRoute[removePosition - 1].start.id, newRoute[removePosition].end.id
        ]
        newRoute.pop(removePosition)
        newRoute.pop(removePosition - 1)
        newRoute.insert(removePosition - 1, newTrack)
    return newRoute


class EvolutionaryAlgorithm(Schedule):
    def __init__(
        self,
        inputNetwork: "TrainNetwork",
        amountTrains: int,
        amountGenerations: int,
        poolSize: int,
        initSchedule: Schedule | None = None,
    ):
        processes = multiprocessing.Pool()
        tsp = network_to_TSP(inputNetwork.cities)
        if initSchedule is not None:
            pool = real_to_dummy([copy.deepcopy(initSchedule) for _ in range(poolSize)])
        else:
            pool = init_pool(tsp, poolSize, amountTrains)
        numberCities = cities_to_int(inputNetwork.cities)

        for _ in tqdm(range(amountGenerations)):
            pool = select(pool, inputNetwork, processes)
            pool = mutate(pool, tsp, numberCities, processes)

        realpool = dummy_to_real(pool)
        mappedSchedules = list(
            enumerate(processes.map(inputNetwork.get_average_travel_time, realpool))
        )
        sortedSchedules = sorted(mappedSchedules, key=lambda x: x[1])

        self.trainSchedules = realpool[sortedSchedules[0][0]].trainSchedules
