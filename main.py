import pygame
import char
import random
import os
import math
import mapgen
from astar import astar_search
from gbfs import gbfs_search

pygame.init()

WIDTH = 720
HEIGHT = 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ITS Campus Rush: AI Outbreak")
clock = pygame.time.Clock()

#images
BASE_DIR = os.path.dirname(__file__)
playerImage = pygame.image.load(os.path.join(BASE_DIR, "player.jpeg")).convert_alpha()
enemyImage = pygame.image.load(os.path.join(BASE_DIR, "ai.png")).convert_alpha()
tcImage = pygame.image.load(os.path.join(BASE_DIR, "tc.jpg")).convert()

# Load obstacle & grass assets (Venya)
OBSTACLES_DIR = os.path.join(BASE_DIR, "assets", "obstacles")
obstacle_images_raw = []
for fname in ["batuBesar_1.png", "batuBesar_2.png", "batuKecil_1.png", "batuKecil_2.png"]:
    fpath = os.path.join(OBSTACLES_DIR, fname)
    if os.path.exists(fpath):
        obstacle_images_raw.append(pygame.image.load(fpath).convert_alpha())

grass_images_raw = []
for fname in ["rumput_1.png", "rumput_2.png", "rumput_3.png"]:
    fpath = os.path.join(OBSTACLES_DIR, fname)
    if os.path.exists(fpath):
        grass_images_raw.append(pygame.image.load(fpath).convert_alpha())

WHITE = (245, 245, 250)
GRAY = (150, 155, 170)
DIM = (95, 100, 118)
ACCENT = (70, 130, 220)
ACCENT_LIGHT = (150, 190, 255)
BUTTON_BG = (30, 32, 42)
BUTTON_BORDER = (62, 66, 84)
PANEL_BG = (14, 16, 24)
PANEL_BORDER = (50, 54, 70)
GREEN = (90, 210, 130)
RED = (235, 85, 85)
BLACK = (0, 0, 0)
GRID_COLOR = (55, 55, 55)

player_max_energy = 10
ENEMY_MAX_ENERGY = 10
PLAYER_MOVE_COST = 1
ENEMY_TURN_COST = 1 
ENEMY_DELAY = 600

GRID_PADDING = 24

#font
def make_font(size, bold=False):
    font = pygame.font.Font(None, size)
    font.set_bold(bold)
    return font

title_font = make_font(84, bold=True)
subtitle_font = make_font(40, bold=True)
button_font = make_font(36, bold=True)
desc_font = make_font(26)
hint_font = make_font(22)
label_font = make_font(20, bold=True)
hud_font = make_font(24, bold=True)
hud_value_font = make_font(50, bold=True)
result_title_font = make_font(60, bold=True)
result_sub_font = make_font(28)

#bg
_scale = max(WIDTH / tcImage.get_width(), HEIGHT / tcImage.get_height())
_bg_size = (int(tcImage.get_width() * _scale), int(tcImage.get_height() * _scale))
_bg_scaled = pygame.transform.smoothscale(tcImage, _bg_size)
menuBackground = pygame.Surface((WIDTH, HEIGHT))
menuBackground.blit(_bg_scaled, _bg_scaled.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

menuOverlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
for y in range(HEIGHT):
    t = y / (HEIGHT - 1)
    pygame.draw.line(menuOverlay, (8, 10, 20, int(120 + 100 * t)), (0, y), (WIDTH, y))

#posisi(note , idk kayanya player nanti harusnya di randomize or not)
GAME_MODES = [
    {
        "name": "Casual",
        "desc": "Easier AI (Greedy Best-First Search)",
        "grid": 9,
        "finish": (4, 8),
        "enemies": [(8, 0)],
        "move_limit": None,
        "obstacles": 10,
        "algorithm": "gbfs",
    },
    {
        "name": "Challenging",
        "desc": "Harder AI (A* Optimal Search)",
        "grid": 9,
        "finish": (4, 8),
        "enemies": [(8, 0)],
        "move_limit": None,
        "player_energy": 16,
        "obstacles": 15,
        "algorithm": "astar",
    },
]

#helpers
def blit_text(surface, text, font, color, pos, anchor="center", shadow=True):
    img = font.render(text, True, color)
    rect = img.get_rect(**{anchor: pos})
    if shadow:
        surface.blit(font.render(text, True, (0, 0, 0)), rect.move(2, 2))
    surface.blit(img, rect)
    return rect


def draw_panel(surface, rect, color=PANEL_BG, alpha=200, radius=14, border=None):
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, (*color, alpha), panel.get_rect(), border_radius=radius)
    surface.blit(panel, rect.topleft)
    if border:
        pygame.draw.rect(surface, border, rect, width=1, border_radius=radius)


#menu
class Menu:
    def __init__(self, title, options, subtitle="", descriptions=None, hint=""):
        self.title = title
        self.subtitle = subtitle
        self.options = options
        self.descriptions = descriptions or {}
        self.hint = hint
        self.selected = 0

    def _rects(self):
        w, h, gap = 340, 52, 16
        total = len(self.options) * h + (len(self.options) - 1) * gap
        start_y = HEIGHT // 2 - total // 2 + 30
        return [
            pygame.Rect((WIDTH - w) // 2, start_y + i * (h + gap), w, h)
            for i in range(len(self.options))
        ]

    def handle_event(self, event):
        count = len(self.options)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % count
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % count
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return ("select", self.selected)
            elif event.key == pygame.K_ESCAPE:
                return ("back", None)

        elif event.type == pygame.MOUSEMOTION:
            for i, rect in enumerate(self._rects()):
                if rect.collidepoint(event.pos):
                    self.selected = i

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self._rects()):
                if rect.collidepoint(event.pos):
                    self.selected = i
                    return ("select", i)

        return None

    def draw(self, surface):
        surface.blit(menuBackground, (0, 0))
        surface.blit(menuOverlay, (0, 0))

        blit_text(surface, self.title, title_font, WHITE, (WIDTH // 2, 66))
        if self.subtitle:
            blit_text(surface, self.subtitle, subtitle_font, ACCENT_LIGHT, (WIDTH // 2, 116))

        ticks = pygame.time.get_ticks()
        for i, rect in enumerate(self._rects()):
            selected = i == self.selected
            if selected:
                pulse = (math.sin(ticks / 250) + 1) / 2
                grow = 8 + int(pulse * 6)
                draw_panel(surface, rect.inflate(grow, grow), ACCENT,
                           alpha=50 + int(pulse * 50), radius=16)
                pygame.draw.rect(surface, ACCENT, rect, border_radius=10)
                pygame.draw.rect(surface, ACCENT_LIGHT, rect, width=1, border_radius=10)
            else:
                draw_panel(surface, rect, BUTTON_BG, alpha=215, radius=10, border=BUTTON_BORDER)

            color = WHITE if selected else GRAY
            blit_text(surface, self.options[i], button_font, color, rect.center)

        # description pill
        desc = self.descriptions.get(self.selected)
        if desc:
            tw, th = desc_font.size(desc)
            pill = pygame.Rect(0, 0, tw + 36, th + 12)
            pill.center = (WIDTH // 2, HEIGHT - 70)
            draw_panel(surface, pill, PANEL_BG, alpha=180, radius=14)
            blit_text(surface, desc, desc_font, GRAY, pill.center, shadow=False)

        if self.hint:
            blit_text(surface, self.hint, hint_font, DIM, (WIDTH // 2, HEIGHT - 24))

class GameController:
    def __init__(self, player, enemies, mode):
        self.player = player
        self.enemies = enemies
        self.mode = mode
        self.grid_count = mode["grid"]
        self.finish = mode["finish"]

        self.tile = (HEIGHT - 2 * GRID_PADDING) // self.grid_count
        self.size = self.tile * self.grid_count
        self.ox = (WIDTH - self.size) // 2
        self.oy = (HEIGHT - self.size) // 2
        finish_px = self.tile - 4
        self.finish_img = pygame.transform.smoothscale(
            tcImage.convert_alpha(), (finish_px, finish_px)
        )

        # Scale obstacle and grass images
        self.obstacle_imgs = [
            pygame.transform.smoothscale(img, (self.tile - 4, self.tile - 4))
            for img in obstacle_images_raw
        ] if obstacle_images_raw else []
        self.grass_imgs = [
            pygame.transform.smoothscale(img, (self.tile - 4, self.tile - 4))
            for img in grass_images_raw
        ] if grass_images_raw else []

        self.obstacles = set()
        self.terrain_costs = {}
        self.obstacle_sprites = {}
        self.grass_sprites = {}

        self.phase = "player" 
        self.enemy_started = 0
        self.moves = 0
        self.max_energy = mode.get("player_energy", player_max_energy)
        self.player_energy = self.max_energy
        self.enemy_max_energy = ENEMY_MAX_ENERGY
        self.enemy_energy = self.enemy_max_energy
        self.result = None     
        self.reason = None
        self.result_choice = 0

    def handle_event(self, event):
        if self.phase != "player" or self.result or event.type != pygame.KEYDOWN:
            return

        moves = {
            pygame.K_UP: (0, -1),
            pygame.K_DOWN: (0, 1),
            pygame.K_LEFT: (-1, 0),
            pygame.K_RIGHT: (1, 0),
        }

        if event.key not in moves:
            return

        dx, dy = moves[event.key]
        new_col = self.player.col + dx
        new_row = self.player.row + dy

        if 0 <= new_col < self.grid_count and 0 <= new_row < self.grid_count:
            # Block player from walking into obstacles
            if (new_col, new_row) in self.obstacles:
                return

            self.player.col = new_col
            self.player.row = new_row
            self.moves += 1
            # Grass / heavier terrain consumes more energy if defined
            cost = self.terrain_costs.get((new_col, new_row), PLAYER_MOVE_COST)
            self.player_energy = max(0, self.player_energy - cost)
            self.check_result()
            if not self.result:
                self.start_enemy_turn()

    def start_enemy_turn(self):
        self.phase = "enemy"
        self.enemy_started = pygame.time.get_ticks()

    def check_result(self):
        if (self.player.col, self.player.row) == self.finish:
            self.result = "win"
        elif any((e.col, e.row) == (self.player.col, self.player.row) for e in self.enemies):
            self.result = "lose"
            self.reason = "caught"
        elif any((e.col, e.row) == self.finish for e in self.enemies):
            self.result = "lose"
            self.reason = "ai_win"
        elif self.player_energy <= 0:
            self.result = "lose"
            self.reason = "energy"
        elif self.mode["move_limit"] is not None and self.moves >= self.mode["move_limit"]:
            self.result = "lose"
            self.reason = "limit"

    def update(self):
        if self.phase == "enemy" and not self.result:
            if pygame.time.get_ticks() - self.enemy_started >= ENEMY_DELAY:
                self.enemy_turn()
                self.check_result()
                if not self.result:
                    self.phase = "player"

    def enemy_turn(self):
        self.enemy_energy = max(0, self.enemy_energy - ENEMY_TURN_COST)
        algo = self.mode.get("algorithm", "astar")
        search_fn = gbfs_search if algo == "gbfs" else astar_search

        for enemy in self.enemies:
            path = search_fn(
                start=(enemy.col, enemy.row),
                goal=self.finish,
                grid_size=self.grid_count,
                obstacles=self.obstacles,
                terrain_costs=self.terrain_costs
            )
            if path and len(path) > 1:
                enemy.col, enemy.row = path[1]
    
    def handle_result_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
                self.result_choice = 1 - self.result_choice
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return "retry" if self.result_choice == 0 else "back"
            elif event.key == pygame.K_ESCAPE:
                return "back"

        elif event.type == pygame.MOUSEMOTION:
            for i, rect in enumerate(result_button_rects()):
                if rect.collidepoint(event.pos):
                    self.result_choice = i

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(result_button_rects()):
                if rect.collidepoint(event.pos):
                    return "retry" if i == 0 else "back"

        return None


def start_game(mode):
    player = char.player(0, 0, playerImage)
    enemies = [char.player(col, row, enemyImage) for col, row in mode["enemies"]]
    game = GameController(player, enemies, mode)

    # Implementasi Randomization (Tugas #5)
    # Setiap game baru dimulai atau Retry, posisi obstacle dan rumput diacak!
    num_obs = mode.get("obstacles", 12)
    layout = mapgen.generate_map(
        grid_count=game.grid_count,
        player_start=(player.col, player.row),
        enemy_starts=[(e.col, e.row) for e in enemies],
        finish=game.finish,
        num_obstacles=num_obs,
    )

    game.obstacles = layout["obstacles"]
    game.terrain_costs = layout["terrain_costs"]
    game.map_seed = layout["seed"]

    # Pasangkan varian gambar batu dan rumput acak ke tiap petak
    rng = random.Random(layout["seed"])
    if game.obstacle_imgs:
        for obs in game.obstacles:
            game.obstacle_sprites[obs] = rng.choice(game.obstacle_imgs)
    if game.grass_imgs:
        for grass in game.terrain_costs:
            game.grass_sprites[grass] = rng.choice(game.grass_imgs)

    print(f"[Randomization] Map di-generate dengan seed {layout['seed']}: {len(game.obstacles)} obstacles, {len(game.terrain_costs)} rumput.")
    return game


def cell_rect(game, col, row):
    return pygame.Rect(game.ox + col * game.tile, game.oy + row * game.tile,
                       game.tile, game.tile)

def draw_board(game):
    # 1. Gambar petak rumput (terrain cost)
    for pos in game.terrain_costs:
        c_rect = cell_rect(game, *pos)
        grass_tint = pygame.Surface((game.tile, game.tile), pygame.SRCALPHA)
        grass_tint.fill((46, 125, 50, 45))
        screen.blit(grass_tint, c_rect)
        if pos in game.grass_sprites:
            img = game.grass_sprites[pos]
            screen.blit(img, img.get_rect(center=c_rect.center))

    # 2. Gambar garis grid
    for i in range(game.grid_count + 1):
        x = game.ox + i * game.tile
        y = game.oy + i * game.tile
        pygame.draw.line(screen, GRID_COLOR, (x, game.oy), (x, game.oy + game.size))
        pygame.draw.line(screen, GRID_COLOR, (game.ox, y), (game.ox + game.size, y))

    # 3. Gambar Finish
    finish_cell = cell_rect(game, *game.finish)
    screen.blit(game.finish_img, game.finish_img.get_rect(center=finish_cell.center))

    # 4. Gambar Obstacle (Batu)
    for pos in game.obstacles:
        c_rect = cell_rect(game, *pos)
        if pos in game.obstacle_sprites:
            img = game.obstacle_sprites[pos]
            screen.blit(img, img.get_rect(center=c_rect.center))
        else:
            pygame.draw.rect(screen, (100, 100, 100), c_rect.inflate(-6, -6), border_radius=6)

def draw_hud(game):
    limit = game.mode["move_limit"]
    moves_text = f"Moves: {game.moves}" + (f"/{limit}" if limit else "")
    algo_name = "GBFS" if game.mode.get("algorithm") == "gbfs" else "A*"
    screen.blit(hud_font.render(f"{game.mode['name']} [{algo_name}]", True, ACCENT), (12, 24))
    screen.blit(hud_font.render(moves_text, True, WHITE), (12, 48))
    screen.blit(hud_font.render(f"Seed: {game.map_seed}", True, DIM), (12, 72))
    screen.blit(hud_font.render("Esc: menu", True, GRAY), (12, HEIGHT - 32))

    x = game.ox + game.size + 16

    if game.result:
        turn_text, turn_color = "Game over", GRAY
    elif game.phase == "player":
        turn_text, turn_color = "Your turn", ACCENT
    else:
        turn_text, turn_color = "AI turn", RED
    screen.blit(hud_font.render(turn_text, True, turn_color), (x, 24))

    screen.blit(hud_font.render("Energy", True, GRAY), (x, 60))

    active = not game.result
    you_marker = "> " if active and game.phase == "player" else "  "
    ai_marker = "> " if active and game.phase == "enemy" else "  "
    screen.blit(hud_font.render(f"{you_marker}You: {game.player_energy}/{game.max_energy}", True, WHITE), (x, 84))
    screen.blit(hud_font.render(f"{ai_marker}AI: {game.enemy_energy}/{game.enemy_max_energy}", True, RED), (x, 108))

def result_card_rect():
    card = pygame.Rect(0, 0, 460, 250)
    card.center = (WIDTH // 2, HEIGHT // 2)
    return card

def result_button_rects():
    card = result_card_rect()
    w, h, gap = 170, 46, 20
    x0 = card.centerx - (w * 2 + gap) // 2
    y = card.y + 150
    return [pygame.Rect(x0, y, w, h), pygame.Rect(x0 + w + gap, y, w, h)]


def draw_result(game):
    dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    dim.fill((0, 0, 0, 160))
    screen.blit(dim, (0, 0))

    won = game.result == "win"
    color = GREEN if won else RED

    card = result_card_rect()
    draw_panel(screen, card, PANEL_BG, alpha=235, radius=20, border=color)

    title = "Mission Complete!" if won else "Game Over"
    blit_text(screen, title, result_title_font, color, (card.centerx, card.y + 55))

    if won:
        sub = f"You reached the finish in {game.moves} moves"
    elif game.reason == "caught":
        sub = "The AI caught you"
    elif game.reason == "ai_win":
        sub = "The AI reached Informatics first"
    elif game.reason == "energy":
        sub = "You ran out of energy"
    else:
        sub = "You ran out of moves"
    blit_text(screen, sub, result_sub_font, WHITE, (card.centerx, card.y + 105), shadow=False)

    labels = ["Retry", "Back"]
    for i, rect in enumerate(result_button_rects()):
        selected = i == game.result_choice
        if selected:
            pygame.draw.rect(screen, ACCENT, rect, border_radius=10)
            pygame.draw.rect(screen, ACCENT_LIGHT, rect, width=1, border_radius=10)
            text_color = WHITE
        else:
            draw_panel(screen, rect, BUTTON_BG, alpha=215, radius=10, border=BUTTON_BORDER)
            text_color = GRAY
        blit_text(screen, labels[i], hud_font, text_color, rect.center)

def draw_game(game):
    screen.fill(BLACK)
    draw_board(game)
    draw_hud(game)

    game.player.draw(screen, game.ox, game.oy, game.tile)
    for enemy in game.enemies:
        enemy.draw(screen, game.ox, game.oy, game.tile)

    if game.result:
        draw_result(game)

#main menu or landing page
main_menu = Menu(
    "ITS Campus Rush", ["Play", "Quit"],
    subtitle="AI Outbreak",
)
mode_menu = Menu(
    "Select Game Mode",
    [m["name"] for m in GAME_MODES] + ["Back"],
    subtitle="Choose your challenge",
)

state = "main_menu"
game = None

if __name__ == "__main__":
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                print("Game quitted!")
                continue

            if state == "main_menu":
                action = main_menu.handle_event(event)
                if action and action[0] == "select":
                    if action[1] == 0:  
                        mode_menu.selected = 0
                        state = "mode_select"
                    else:       
                        running = False

            elif state == "mode_select":
                action = mode_menu.handle_event(event)
                if action:
                    kind, index = action
                    if kind == "back" or index == len(GAME_MODES): 
                        state = "main_menu"
                    else:
                        game = start_game(GAME_MODES[index])
                        state = "playing"

            elif state == "playing":
                if game.result:
                    action = game.handle_result_event(event)
                    if action == "retry":
                        game = start_game(game.mode)
                    elif action == "back":
                        mode_menu.selected = GAME_MODES.index(game.mode)
                        state = "mode_select"
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    mode_menu.selected = GAME_MODES.index(game.mode)
                    state = "mode_select"
                else:
                    game.handle_event(event)

        if state == "playing":
            game.update()
            draw_game(game)
        elif state == "mode_select":
            mode_menu.draw(screen)
        else:
            main_menu.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
