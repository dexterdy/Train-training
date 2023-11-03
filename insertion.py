import math
from algorithmInterface import Schedule, TrainSchedule
from typing import TYPE_CHECKING
from citiesToInt import cities_to_int

from compositeTrack import CompositeTrack, network_to_TSP

if TYPE_CHECKING:
    from network import TrainNetwork, City


def perform_insertion_algorirthm(
    tsp: dict[tuple[int, int], "CompositeTrack"],
    toVisit: list[int],
) -> list["CompositeTrack"]:
    toVisit = toVisit[:]
    if len(tsp) == 0:
        return []
    # get the smallest track that is not self
    largestTrack = max(
        [tsp[i, j] for i in toVisit for j in toVisit],
        key=lambda x: x.totalDistance,
    )
    route = [largestTrack]
    toVisit.remove(largestTrack.start.id)
    toVisit.remove(largestTrack.end.id)
    while len(toVisit) != 0:
        (index, track), (middle, cost) = min(
            [
                (
                    (trackIndex, track),
                    min(
                        [
                            (
                                cityId,
                                (
                                    tsp[track.start.id, cityId].totalDistance
                                    + tsp[cityId, track.end.id].totalDistance
                                    + 10
                                )
                                - track.totalDistance,
                            )
                            for cityId in toVisit
                        ],
                        key=lambda x: x[1],
                    ),
                )
                for trackIndex, track in enumerate(route)
            ],
            key=lambda x: x[1][1],
        )
        newTrack1 = tsp[track.start.id, middle]
        newTrack2 = tsp[middle, track.end.id]
        toVisit.remove(middle)
        route.pop(index)
        route.insert(index, newTrack1)
        route.insert(index + 1, newTrack2)
    # we now have an optimal route
    return route


def get_route(
    cities: list["City"], toVisit: list[int], amount: int
) -> tuple[list["CompositeTrack"], int]:
    # get rid of none type because our network does not have unreachable nodes
    tsp = network_to_TSP(cities)
    tsp = {k: v for k, v in tsp.items() if k[0] in toVisit and k[1] in toVisit}
    composedRoute = perform_insertion_algorirthm(tsp, toVisit)
    length = math.floor(get_total_length(composedRoute) / amount)
    return composedRoute, length


def get_total_length(tracks: list["CompositeTrack"]):
    total = 0
    # every track gets an extra cost of 10 for the waiting time at the next station
    [total := total + track.totalDistance + 10 for track in tracks]
    return total


def get_final_routes(
    route: list["CompositeTrack"],
    singleRouteLength: int,
    amountTrains: int,
    isInterCity: bool,
) -> list["TrainSchedule"]:
    schedules = []
    totalLength = 0
    trackIndex = 0
    scheduleIndex = 1
    while len(schedules) < amountTrains:
        minTotal = scheduleIndex * singleRouteLength
        newRoute: list[CompositeTrack] = []
        while totalLength < minTotal:
            track = route[trackIndex]
            newRoute.append(track)
            totalLength += track.totalDistance + 10
            trackIndex += 1
        newSchedule = TrainSchedule(isInterCity, newRoute)
        schedules.append(newSchedule)
        scheduleIndex += 1
    return schedules


class InsertionAlgorithm(Schedule):
    def __init__(
        self,
        inputNetwork: "TrainNetwork",
        amountSprinters: int,
        amountIntercities: int,
    ):
        if amountIntercities == 0:
            finalRouteInterCity = []
        else:
            interCityToVisit = list(
                filter(lambda x: x.get_skewed_popularity(3) >= 0.7, inputNetwork.cities)
            )
            tspRouteIntercity, intercityLength = get_route(
                inputNetwork.cities,
                cities_to_int(interCityToVisit),
                amountIntercities,
            )
            finalRouteInterCity = get_final_routes(
                tspRouteIntercity, intercityLength, amountIntercities, True
            )

        if amountSprinters == 0:
            finalRouteSprinter = []
        else:
            tspRouteSprinter, sprinterLength = get_route(
                inputNetwork.cities,
                cities_to_int(inputNetwork.cities),
                amountSprinters,
            )
            finalRouteSprinter = get_final_routes(
                tspRouteSprinter, sprinterLength, amountSprinters, False
            )

        self.trainSchedules = finalRouteInterCity + finalRouteSprinter
