from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from network import City


def cities_to_int(cities: list["City"]) -> list[int]:
    return list(map(lambda x: x.id, cities))
