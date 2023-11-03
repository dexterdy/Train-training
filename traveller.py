from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from network import City

passengerID = 0


class Traveller:
    destination: "City"
    id: int
    start: "City"

    def __init__(self, start: "City", destination: "City"):
        global passengerID
        self.destination = destination
        self.id = passengerID
        passengerID += 1
        self.start = start
        # decide route

    def __str__(self) -> str:
        return "start: {}, destination: {}".format(self.start, self.destination)

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, value: "Traveller") -> bool:
        return self.id == value.id
