from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from network import City, Track


class CompositeTrack:
    tracks: list["Track"]
    start: "City"
    end: "City"
    totalDistance: int

    def __init__(
        self,
        tracks: list["Track"],
        totalDistance: int,
        start: "City",
        end: "City",
    ):
        self.tracks = tracks
        self.totalDistance = totalDistance
        self.start = start
        self.end = end

    def __str__(self) -> str:
        return "|start: {}, end: {}, cost:{}|".format(
            self.start.id, self.end.id, self.totalDistance
        )

    def __repr__(self) -> str:
        return self.__str__()


# Solves the all-pairs shortest path
# problem using Floyd Warshall algorithm
def floydWarshall(
    dist: dict[tuple[int, int], "CompositeTrack | None"],
    cities: list["City"],
) -> dict[tuple[int, int], "CompositeTrack | None"]:
    for k in cities:
        for i in cities:
            for j in cities:
                sourceToK = dist[i.id, k.id]
                kToDest = dist[k.id, j.id]
                sourceToDest = dist[i.id, j.id]
                if sourceToK is None or kToDest is None:
                    continue
                if (
                    sourceToDest is None
                    or sourceToK.totalDistance + kToDest.totalDistance
                    < sourceToDest.totalDistance
                ):
                    newTracks = sourceToK.tracks[:]
                    newTracks.extend(kToDest.tracks)
                    totalDistance = sourceToK.totalDistance + kToDest.totalDistance
                    dist[i.id, j.id] = CompositeTrack(
                        newTracks,
                        totalDistance,
                        i,
                        j,
                    )
    return dist


def network_to_TSP(
    cities: list["City"],
) -> dict[tuple[int, int], "CompositeTrack"]:
    result: dict[tuple[int, int], "CompositeTrack | None"] = dict()

    def list_neighbours_fill(city: "City"):
        for other_city in cities:
            if other_city.id == city.id:
                result[city.id, city.id] = CompositeTrack([], 0, city, city)
            elif other_city in city.neighbours:
                track = city.neighbours[other_city]
                result[city.id, other_city.id] = CompositeTrack(
                    [track], track.cost, city, other_city
                )
            else:
                result[city.id, other_city.id] = None

    [list_neighbours_fill(city) for city in cities]
    tsp = floydWarshall(result, cities)
    noNone = len([0 for v in result.values() if v is None]) == 0
    if not noNone:
        raise Exception("accidentally made 2 or more seperate networks")
    else:
        tsp = cast(dict[tuple[int, int], "CompositeTrack"], tsp)
    return tsp
