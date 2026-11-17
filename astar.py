import heapq
from typing import List, Tuple, Set, Dict, Optional, Union, Any

# Arah pergerakan 4-arah: (col, row)
DIRECTIONS: List[Tuple[int, int]] = [(0, -1), (0, 1), (-1, 0), (1, 0)]


def _normalize_pos(pos: Any) -> Tuple[int, int]:
    if hasattr(pos, 'col') and hasattr(pos, 'row'):
        return (int(pos.col), int(pos.row))
    if hasattr(pos, 'x') and hasattr(pos, 'y'):
        return (int(pos.x), int(pos.y))
    if isinstance(pos, (list, tuple)) and len(pos) >= 2:
        return (int(pos[0]), int(pos[1]))
    raise TypeError(f"Posisi tidak valid: {pos}")


def manhattan_distance(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar_search(
    start: Union[Tuple[int, int], Any],
    goal: Union[Tuple[int, int], Any],
    grid_size: Union[int, Tuple[int, int], Any] = 9,
    obstacles: Optional[Union[Set[Tuple[int, int]], List[Tuple[int, int]]]] = None,
    grid: Optional[List[List[Union[int, float, str]]]] = None,
    terrain_costs: Optional[Dict[Tuple[int, int], int]] = None,
    return_cost: bool = False
) -> Union[List[Tuple[int, int]], Tuple[List[Tuple[int, int]], int]]:
    start_pos = _normalize_pos(start)
    goal_pos = _normalize_pos(goal)

    if isinstance(grid_size, list) and len(grid_size) > 0 and isinstance(grid_size[0], list):
        grid = grid_size
        grid_size = (len(grid[0]), len(grid))
    elif isinstance(grid_size, (set, frozenset)) or (
        isinstance(grid_size, list) and len(grid_size) > 0 and isinstance(grid_size[0], (tuple, list))
    ):
        obstacles = grid_size
        grid_size = 9

    if grid is not None and len(grid) > 0:
        rows = len(grid)
        cols = len(grid[0])
    elif isinstance(grid_size, int):
        cols, rows = grid_size, grid_size
    elif isinstance(grid_size, (tuple, list)) and len(grid_size) >= 2:
        cols, rows = int(grid_size[0]), int(grid_size[1])
    else:
        cols, rows = 9, 9

    obstacle_set = set(obstacles) if obstacles else set()

    def get_cell_cost(pos: Tuple[int, int]) -> Tuple[bool, int]:
        c, r = pos
        if not (0 <= c < cols and 0 <= r < rows):
            return True, 0
        if pos in obstacle_set:
            return True, 0

        if grid is not None:
            val = grid[r][c]
            if val in (-1, '#', 'X', 'x') or val is None:
                return True, 0
            if isinstance(val, (int, float)):
                cost = int(val) if int(val) >= 1 else 1
                return False, cost

        if terrain_costs and pos in terrain_costs:
            return False, max(1, terrain_costs[pos])

        return False, 1

    is_obs_start, _ = get_cell_cost(start_pos)
    is_obs_goal, _ = get_cell_cost(goal_pos)
    if is_obs_start or is_obs_goal:
        return ([], 0) if return_cost else []

    if start_pos == goal_pos:
        return ([start_pos], 0) if return_cost else [start_pos]

    # f(n) = g(n) + h(n)
    tie_breaker = 0
    h_start = manhattan_distance(start_pos, goal_pos)
    open_heap = []
    heapq.heappush(open_heap, (h_start, h_start, tie_breaker, start_pos))

    cost_so_far: Dict[Tuple[int, int], int] = {start_pos: 0}
    came_from: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start_pos: None}
    path_found = False

    while open_heap:
        f_curr, h_curr, _, current = heapq.heappop(open_heap)

        if current == goal_pos:
            path_found = True
            break

        if cost_so_far[current] < f_curr - h_curr:
            continue

        for dc, dr in DIRECTIONS:
            neighbor = (current[0] + dc, current[1] + dr)
            is_obstacle, move_cost = get_cell_cost(neighbor)

            if is_obstacle:
                continue

            tentative_g = cost_so_far[current] + move_cost

            if neighbor not in cost_so_far or tentative_g < cost_so_far[neighbor]:
                cost_so_far[neighbor] = tentative_g
                h_neighbor = manhattan_distance(neighbor, goal_pos)
                f_neighbor = tentative_g + h_neighbor
                tie_breaker += 1
                heapq.heappush(open_heap, (f_neighbor, h_neighbor, tie_breaker, neighbor))
                came_from[neighbor] = current

    if not path_found:
        return ([], 0) if return_cost else []

    path = []
    curr: Optional[Tuple[int, int]] = goal_pos
    while curr is not None:
        path.append(curr)
        curr = came_from[curr]
    path.reverse()

    total_cost = cost_so_far[goal_pos]
    return (path, total_cost) if return_cost else path


def get_next_move(
    start: Union[Tuple[int, int], Any],
    goal: Union[Tuple[int, int], Any],
    grid_size: Union[int, Tuple[int, int], Any] = 9,
    obstacles: Optional[Union[Set[Tuple[int, int]], List[Tuple[int, int]]]] = None,
    grid: Optional[List[List[Union[int, float, str]]]] = None,
    terrain_costs: Optional[Dict[Tuple[int, int], int]] = None
) -> Optional[Tuple[int, int]]:
    path = astar_search(
        start=start,
        goal=goal,
        grid_size=grid_size,
        obstacles=obstacles,
        grid=grid,
        terrain_costs=terrain_costs,
        return_cost=False
    )

    if path and len(path) > 1:
        return path[1]
    return None