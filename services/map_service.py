import os
import random
from typing import List, Set

maps = {}
path = os.path.join(os.path.dirname(__file__), "maps.csv")
with open(path, "r") as maps_file:
    # Ignore header
    lines = maps_file.readlines()[1:]

    for line in lines:
        name, weight = line.strip().split(",")
        maps[name] = float(weight)


def get_maps(num_maps=2, exclude: Set[str] = set()) -> List[str]:
    if num_maps + len(exclude) > len(maps):
        raise ValueError("Asking for and excluding too many maps")

    results = []
    new_exclude = exclude.copy()
    for i in range(num_maps):
        single_map = get_map_weighted(new_exclude)
        results.append(single_map)
        new_exclude = new_exclude.union({single_map})

    return results


def get_map_weighted(exclude: Set[str] = []) -> str:
    map_pool = list(maps.keys() - exclude)
    weights = [maps[m] for m in map_pool]
    return random.choices(map_pool, weights=weights)[0]


def get_all_map_names_alphabetical():
    return sorted(list(maps.keys()))
