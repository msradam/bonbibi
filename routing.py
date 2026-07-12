"""Deterministic flood routing over the full-resolution depth grid.

The safety math is code, not the LLM: a 4-neighbour BFS over the 256x256
simulated depth field, where a cell is passable when its depth is at or
below the mobility profile's threshold. Given an origin and shelter
candidates, returns the nearest reachable shelter and the path to it.
"""

from collections import deque

SZ = 256


def to_cell(lat: float, lon: float, bbox) -> tuple[int, int]:
    """(lat, lon) -> (row, col); row 0 is the north edge."""
    la0, la1, lo0, lo1 = bbox
    r = int((la1 - lat) / (la1 - la0) * (SZ - 1) + 0.5)
    c = int((lon - lo0) / (lo1 - lo0) * (SZ - 1) + 0.5)
    return max(0, min(SZ - 1, r)), max(0, min(SZ - 1, c))


def to_lonlat(r: int, c: int, bbox) -> list:
    la0, la1, lo0, lo1 = bbox
    return [lo0 + (lo1 - lo0) * (c + 0.5) / SZ, la1 - (la1 - la0) * (r + 0.5) / SZ]


def route_to_shelter(depth, threshold: float, origin, goals):
    """BFS from origin to the nearest of goals over passable cells.

    depth: SZ*SZ array-like (row-major, metres); origin: (r, c);
    goals: list of (r, c). Returns (goal_index, path[(r, c), ...]) or
    (None, []) when no shelter is reachable.
    """
    goal_at = {g: i for i, g in enumerate(goals)}

    def passable(r, c):
        return 0 <= r < SZ and 0 <= c < SZ and depth[r * SZ + c] <= threshold

    if not passable(*origin):
        return None, []
    prev = {origin: None}
    q = deque([origin])
    while q:
        cell = q.popleft()
        if cell in goal_at:
            path = []
            while cell is not None:
                path.append(cell)
                cell = prev[cell]
            path.reverse()
            return goal_at[path[-1]], path
        r, c = cell
        for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if passable(nr, nc) and (nr, nc) not in prev:
                prev[(nr, nc)] = cell
                q.append((nr, nc))
    return None, []


def path_length_m(path, bbox) -> int:
    la0, la1, lo0, lo1 = bbox
    cell_m = (la1 - la0) * 111_320 / SZ
    return int(len(path) * cell_m)


if __name__ == "__main__":
    depth = [0.0] * (SZ * SZ)
    for r in range(SZ):
        depth[r * SZ + 128] = 3.0  # deep north-south wall at c=128
    depth[100 * SZ + 128] = 0.3  # one shallow breach at r=100

    origin, near, far = (128, 40), (126, 40), (128, 220)
    i, path = route_to_shelter(depth, 0.5, origin, [near, far])
    assert (i, path[-1]) == (0, near), "nearest reachable shelter wins"

    i, path = route_to_shelter(depth, 0.5, origin, [far])
    assert i == 0 and (100, 128) in path, "crosses the wall only at the breach"

    i, path = route_to_shelter(depth, 0.2, origin, [far])
    assert i is None, "stranded when the breach is too deep"

    bbox = (40.667, 40.685, -74.02, -73.998)
    r, c = to_cell(*reversed(to_lonlat(60, 60, bbox)), bbox)
    assert abs(r - 60) <= 1 and abs(c - 60) <= 1, "cell<->lonlat round trip"
    print("routing.py self-check OK")
