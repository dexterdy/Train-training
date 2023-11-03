from collections import defaultdict
import pickle
import matplotlib.pyplot as plt
import random
from typing import TYPE_CHECKING
from evolutionary import EvolutionaryAlgorithm
from traveller import Traveller
from insertion import InsertionAlgorithm
from pyvis.network import Network
from priorityQueue import PriorityQueue
import math

if TYPE_CHECKING:
    from algorithmInterface import Schedule, Node

trackID = 0


class Track:
    cost: int
    connects: tuple["City", "City"]
    id: int

    def __init__(self, cost: int, cities: tuple["City", "City"]):
        global trackID
        self.cost = cost
        self.connects = cities
        self.id = trackID
        trackID += 1

    def __str__(self) -> str:
        return "Track {} between {} and {} costs {}".format(
            self.id, self.connects[0].id, self.connects[1].id, self.cost
        )

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, value: "Track") -> bool:
        return self.id == value.id


cityID = 0


class City:
    popularity: float
    neighbours: dict["City", "Track"]
    id: int

    def __init__(self):
        global cityID
        self.popularity = random.random()
        self.id = cityID
        cityID += 1
        self.neighbours = {}

    def get_skewed_popularity(self, skewness: float) -> float:
        return self.popularity**skewness

    def is_popular(self) -> bool:
        return self.get_skewed_popularity(3) >= 0.7

    def __str__(self) -> str:
        return "City {}".format(self.id)

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, value: "City") -> bool:
        return self.id == value.id

    def __hash__(self) -> int:
        return id(self)


class TrainNetwork:
    cities: list["City"]
    tracks: list["Track"]
    travellers: list["Traveller"]

    # average tracks must be even
    # the more passes, the more random the network will be, but also the bigger the effect of the popularity scores of the cities
    def __init__(
        self,
        amountCities: int,
        averageTracks: int,
        randomizerPasses: int,
        amountTravellers: int,
    ):
        self.cities = []
        self.tracks = []
        self.travellers = []
        self.__init_cities(amountCities)
        self.__init_tracks(averageTracks, randomizerPasses)
        self.__init_travellers(amountTravellers)

    def __init_cities(self, amountCities):
        for i in range(amountCities):
            city = City()
            self.cities.append(city)

    def __init_tracks(self, averageTracks, passes):
        averageTracks = int(averageTracks / 2)
        # make network where every city has x tracks
        for i, city in enumerate(self.cities):
            nextCities: list["City"] = []
            for x in range(i + 1, i + averageTracks + 1):
                index = x % len(self.cities)
                nextCities.append(self.cities[index])
            nexTracks = list(
                map(
                    lambda nextCity: Track(random.randrange(30, 100), (city, nextCity)),
                    nextCities,
                )
            )
            for track in nexTracks:
                city1 = track.connects[0]
                city2 = track.connects[1]
                city1.neighbours[city2] = track
                city2.neighbours[city1] = track
            self.tracks.extend(nexTracks)

        # make the network random
        for _ in range(passes):
            for track in self.tracks:
                city1 = track.connects[0]
                city2 = track.connects[1]

                nextCity = random.choice(self.cities)
                notFound = True
                maxTries = len(self.cities)
                tries = 0
                while notFound:
                    # prevent edge case where city has track to every other city
                    if tries > maxTries:
                        break
                    if city1.id == nextCity.id or nextCity in city1.neighbours:
                        nextCity = random.choice(self.cities)
                        tries += 1
                    else:
                        notFound = False
                if notFound:
                    continue

                chance = random.random()
                if (
                    nextCity.get_skewed_popularity(4) < chance
                    or len(city2.neighbours) == 1
                ):
                    continue

                city1.neighbours.pop(city2)
                city2.neighbours.pop(city1)
                track.connects = (city1, nextCity)
                city1.neighbours[nextCity] = track
                nextCity.neighbours[city1] = track

    def __init_travellers(self, amountTravellers):
        while len(self.travellers) < amountTravellers:
            city = random.choice(self.cities)
            chance = random.random()
            if city.get_skewed_popularity(1.5) < chance:
                continue

            otherCity = random.choice(self.cities)
            notFound = True
            while notFound:
                if city.id == otherCity.id:
                    otherCity = random.choice(self.cities)
                else:
                    notFound = False

            chance = random.random()

            # skewed for greater difference popular and unpopular destinations
            if otherCity.get_skewed_popularity(3.5) < chance:
                continue
            newTraveller = Traveller(city, otherCity)
            self.travellers.append(newTraveller)

    def get_average_travel_time(self, schedule: "Schedule"):
        travellerNetwork = schedule.traveler_network()
        totalTime = 0
        for traveller in self.travellers:
            # one node is actualy many nodes with t-values equal to t + 0c ... t + xc
            # each "sub"-node s  of node n is identified by its t and x value where ts = tn + xcn
            # sub-nodes si and sj of neighbouring nodes ni and nj are neighbours
            # when tj - cj <= ti < tj with distance tj - ti
            queue: PriorityQueue[tuple["Node", int]] = PriorityQueue()
            visited: dict[int, int] = defaultdict(lambda: 0)
            startingNodes, _ = travellerNetwork[traveller.start.id]
            prev: dict[tuple["Node", int], tuple["Node", int]] = dict()
            last: tuple["Node", int] | None = None
            totalCost: int = int(1e9)
            for v in startingNodes:
                queue.insert((v, 0), v.tValue)
            while len(queue) > 0:
                cost, (v, vx) = queue.pop()
                visited[v.id] += 1
                if v.isPartOf.id == traveller.destination.id:
                    totalCost = cost
                    last = (v, vx)
                    break
                for n in v.canGoTo:
                    # calculate x value
                    lowerBound = (cost - n.tValue) / n.cValue
                    nx = math.ceil(lowerBound)
                    if nx == lowerBound:
                        nx += 1
                    if (
                        visited[n.id] < 2
                    ):  # we don't need to check for cost, because each subnode can only have a single cost
                        prev[n, nx] = (v, vx)
                        newTotalCost = n.tValue + nx * n.cValue
                        queue.modify((n, nx), newTotalCost)
            if last == None:
                totalTime += totalCost
            else:
                path = [last]
                while True:
                    if last not in prev:
                        break
                    last = prev[last]
                    path.append(last)
                path = list(reversed(path))
                totalTime += totalCost - path[0][0].tValue
        return totalTime / len(self.travellers)

    def visualize(self):
        net = Network()
        [
            net.add_node(x.id, label=str(x.id), value=x.get_skewed_popularity(2))
            for x in self.cities
        ]
        [
            net.add_edge(x.connects[0].id, x.connects[1].id, title=str(x.cost))
            for x in self.tracks
        ]
        net.toggle_physics(True)
        net.show("mygraph.html", notebook=False)


if __name__ == "__main__":
    resultsInsertion = []
    resultsEvolutionary = []
    for i in range(100):
        while True:
            try:
                network = TrainNetwork(100, 2, 2, 500)
                ins = InsertionAlgorithm(network, 15, 5)
                resultIns = network.get_average_travel_time(ins)
                evo = EvolutionaryAlgorithm(network, 20, 300, 50, ins)
                resultEvo = network.get_average_travel_time(evo)
                # network.visualize()
                # print("insertion value: " + str(resultIns))
                # print(ins)
                # print("\n")
                # print("evolution value: " + str(resultEvo))
                # print(evo)
                resultsInsertion.append(resultIns)
                resultsEvolutionary.append(resultEvo)
                break
            except:
                cityID = 0
                continue
        print(i)

    with open("results_300gen_initb", "wb+") as file:
        pickle.dump((resultsInsertion, resultsEvolutionary), file)

# ideas:
# try initialize evo pool with solution from insertion
# try deciding to increase/decrease route lengths for every train route at once during mutate step
# show difference with small network sizes
