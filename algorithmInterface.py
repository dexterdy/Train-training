from typing import TYPE_CHECKING
from functools import reduce
from collections import defaultdict

from compositeTrack import CompositeTrack

if TYPE_CHECKING:
    from network import City


class TrainSchedule:
    isIntercity: bool
    route: list["CompositeTrack"]
    cities: dict["City", dict["City", list[tuple[int, int]]]]
    totalLength: int

    def __init__(self, isIntercity: bool, route: list["CompositeTrack"]):
        self.isIntercity = isIntercity
        self.route = route
        self.totalLength: int = reduce(
            lambda x, y: x + 10 + y, map(lambda x: x.totalDistance, route)
        )
        self.__init_cities()

    def __init_cities(self):
        self.cities = dict()
        total = 0
        for track in self.route:
            dist = track.totalDistance
            if track.start not in self.cities:
                self.cities[track.start] = dict()
            if track.end not in self.cities:
                self.cities[track.end] = dict()
            if track.start not in self.cities[track.end]:
                self.cities[track.end][track.start] = []
            if track.end not in self.cities[track.start]:
                self.cities[track.start][track.end] = []
            self.cities[track.start][track.end].append((total, dist + total))
            self.cities[track.end][track.start].append(
                (
                    (self.totalLength - total) * 2 + 10 - dist,
                    (self.totalLength - total) * 2 + 10,
                )
            )
            total += 10 + dist

    def __str__(self) -> str:
        return "IsIntercity: {}, route: {}".format(self.isIntercity, self.route)

    def __repr__(self) -> str:
        return self.__str__()


nodeId = 0


class Node:
    tValue: int
    cValue: int
    canGoTo: list["Node"]
    isPartOf: "City"
    id: int

    def __init__(self, tValue: int, scheduleLength: int, isPartOf: "City"):
        global nodeId
        self.tValue = tValue
        self.cValue = 2 * (scheduleLength + 10)
        self.canGoTo = []
        self.isPartOf = isPartOf
        self.id = nodeId
        nodeId += 1

    def __eq__(self, value: "Node") -> bool:
        return self.id == value.id

    def __hash__(self) -> int:
        return id(self)


class Schedule:
    trainSchedules: list[TrainSchedule]

    def traveler_network(self) -> dict[int, tuple[list[Node], list[Node]]]:
        nodes: dict[int, tuple[list[Node], list[Node]]] = defaultdict(lambda: ([], []))
        for schedule in self.trainSchedules:
            for start, outGoingTracks in schedule.cities.items():
                for end, tracks in outGoingTracks.items():
                    for dep, arr in tracks:
                        startNode = Node(dep, schedule.totalLength, start)
                        endNode = Node(arr, schedule.totalLength, end)
                        startNode.canGoTo.append(endNode)
                        nodes[start.id][0].append(startNode)
                        nodes[end.id][1].append(endNode)

        for outgoingNodes, incommingNodes in nodes.values():
            # one node is actualy many nodes with t-values equal to t0 + 0c ... t0 + xc where xc <= lastTrainTime
            # each such node ni has connections to all nodes of opposite types nj
            # such tj - cj <= ti < tj
            # the cost is tj - ti
            for node in incommingNodes:
                node.canGoTo.extend(outgoingNodes)

        return nodes

    def __str__(self) -> str:
        return "Schedules: {}".format("\n".join([str(x) for x in self.trainSchedules]))

    def __repr__(self) -> str:
        return self.__str__()


class NoAlgorithmSchedule(Schedule):
    def __init__(self, trainSchedules: list[TrainSchedule]):
        self.trainSchedules = trainSchedules
