import random
from typing import List, Tuple, Set, Dict, Optional, Any
from astar import astar_search

Coord = Tuple[int, int]


def is_solvable(
    start: Coord,
    goal: Coord,
    grid_size: int,
    obstacles: Set[Coord],
    terrain_costs: Optional[Dict[Coord, int]] = None
) -> bool:
    
    path = astar_search(
        start=start,
        goal=goal,
        grid_size=grid_size,
        obstacles=obstacles,
        terrain_costs=terrain_costs
    )
    return bool(path and len(path) > 0)


def generate_map(
    grid_count: int = 9,
    player_start: Coord = (0, 0),
    enemy_starts: Optional[List[Coord]] = None,
    finish: Coord = (4, 8),
    num_obstacles: int = 12,
    grass_ratio: float = 0.15,
    grass_cost: int = 3,
    seed: Optional[int] = None,
    max_attempts: int = 200
) -> Dict[str, Any]:
 
    if enemy_starts is None:
        enemy_starts = [(8, 0)]

    # Gunakan seed acak jika tidak ditentukan
    if seed is None:
        seed = random.randint(1, 999_999)
    rng = random.Random(seed)

    # Petak-petak penting yang TIDAK boleh ditimpa obstacle
    reserved_tiles: Set[Coord] = {player_start, finish}
    for e in enemy_starts:
        reserved_tiles.add(e)

    # Semua kandidat koordinat pada grid
    all_cells: List[Coord] = [
        (c, r)
        for c in range(grid_count)
        for r in range(grid_count)
        if (c, r) not in reserved_tiles
    ]

    target_obstacles = min(num_obstacles, len(all_cells))
    obstacles: Set[Coord] = set()
    terrain_costs: Dict[Coord, int] = {}

    attempts = 0
    while attempts < max_attempts:
        attempts += 1

        # 1. Acak penempatan obstacle
        chosen_obstacles = set(rng.sample(all_cells, target_obstacles))

        # 2. Acak penempatan rumput (terrain cost > 1) dari petak non-obstacle
        free_cells = [cell for cell in all_cells if cell not in chosen_obstacles]
        num_grass = int(len(free_cells) * grass_ratio)
        grass_cells = rng.sample(free_cells, num_grass) if num_grass > 0 else []

        temp_costs: Dict[Coord, int] = {cell: grass_cost for cell in grass_cells}

        # 3. Verifikasi Solvabilitas: Player harus bisa sampai ke finish
        if not is_solvable(player_start, finish, grid_count, chosen_obstacles, temp_costs):
            continue

        # 4. Verifikasi Solvabilitas: Semua bot juga harus bisa sampai ke finish
        all_enemies_solvable = True
        for e_start in enemy_starts:
            if not is_solvable(e_start, finish, grid_count, chosen_obstacles, temp_costs):
                all_enemies_solvable = False
                break

        if all_enemies_solvable:
            obstacles = chosen_obstacles
            terrain_costs = temp_costs
            break
    else:
        # Fallback jika kerapatan obstacle terlalu tinggi
        print(f"[Warning] Gagal menemukan map solvable setelah {max_attempts} percobaan. Mengurangi obstacle.")
        obstacles = set()
        terrain_costs = {}

    # Hitung panjang rute A* untuk logging / debugging
    p_path = astar_search(
        start=player_start,
        goal=finish,
        grid_size=grid_count,
        obstacles=obstacles,
        terrain_costs=terrain_costs
    )
    e_paths = [
        astar_search(
            start=e,
            goal=finish,
            grid_size=grid_count,
            obstacles=obstacles,
            terrain_costs=terrain_costs
        )
        for e in enemy_starts
    ]

    return {
        "seed": seed,
        "obstacles": obstacles,
        "terrain_costs": terrain_costs,
        "player_path_len": len(p_path) if p_path else 0,
        "enemy_paths_len": [len(p) if p else 0 for p in e_paths]
    }


def print_map_preview(
    grid_count: int,
    player_start: Coord,
    enemy_starts: List[Coord],
    finish: Coord,
    obstacles: Set[Coord],
    terrain_costs: Dict[Coord, int]
):
    """Mencetak representasi ASCII dari map untuk debugging di terminal."""
    print(f"\n--- MAP PREVIEW ({grid_count}x{grid_count}) ---")
    print("Legend: P=Player, E=Enemy, F=Finish, #=Obstacle, ~=Grass(Cost>1), .=Road(Cost=1)")
    for r in range(grid_count):
        row_str = []
        for c in range(grid_count):
            pos = (c, r)
            if pos == player_start:
                row_str.append(" P ")
            elif pos in enemy_starts:
                row_str.append(" E ")
            elif pos == finish:
                row_str.append(" F ")
            elif pos in obstacles:
                row_str.append(" # ")
            elif pos in terrain_costs:
                row_str.append(" ~ ")
            else:
                row_str.append(" . ")
        print("".join(row_str))
    print("--------------------------------\n")


if __name__ == "__main__":
    print("Testing mapgen.py...")
    test_seed = 42
    layout = generate_map(
        grid_count=9,
        player_start=(0, 0),
        enemy_starts=[(8, 0)],
        finish=(4, 8),
        num_obstacles=12,
        seed=test_seed
    )

    print(f"Seed: {layout['seed']}")
    print(f"Total Obstacles: {len(layout['obstacles'])}")
    print(f"Total Grass Tiles: {len(layout['terrain_costs'])}")
    print(f"Player A* Path Length: {layout['player_path_len']}")
    print(f"Enemy A* Path Length: {layout['enemy_paths_len']}")

    print_map_preview(
        9,
        (0, 0),
        [(8, 0)],
        (4, 8),
        layout['obstacles'],
        layout['terrain_costs']
    )

    # Test random seeds
    print("Menguji 50 random seed untuk memastikan 100% solvable...")
    for s in range(50):
        res = generate_map(num_obstacles=14, seed=s)
        assert res['player_path_len'] > 0, f"Player buntu pada seed {s}"
        assert all(l > 0 for l in res['enemy_paths_len']), f"Enemy buntu pada seed {s}"
    print("Semua 50 seed valid dan solvable!")
