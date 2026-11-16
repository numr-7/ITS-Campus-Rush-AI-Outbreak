import pygame
import char
import random
import os

pygame.init()

WIDTH = 720
HEIGHT = 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ITS Campus Rush: AI Outbreak")
clock = pygame.time.Clock()

BASE_DIR = os.path.dirname(__file__)
playerImage = pygame.image.load(os.path.join(BASE_DIR, "player.jpeg")).convert_alpha()
enemyImage = pygame.image.load(os.path.join(BASE_DIR, "ai.png")).convert_alpha()

tcImage = pygame.image.load(os.path.join(BASE_DIR, "tc.jpg")).convert()

# Menu background: scale to cover the whole window (keeps aspect ratio), crop the extra
_scale = max(WIDTH / tcImage.get_width(), HEIGHT / tcImage.get_height())
_bg_size = (int(tcImage.get_width() * _scale), int(tcImage.get_height() * _scale))
_bg_scaled = pygame.transform.smoothscale(tcImage, _bg_size)
menuBackground = pygame.Surface((WIDTH, HEIGHT))
menuBackground.blit(_bg_scaled, _bg_scaled.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

# Dark overlay so the menu text stays readable (0-255, higher = darker)
menuOverlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
menuOverlay.fill((0, 0, 0, 150))

finishImage = pygame.transform.scale(tcImage.convert_alpha(), (44, 44))
finish_col, finish_row = 4, 8

BLACK = (0, 0, 0)
WHITE = (240, 240, 240)
GRAY = (140, 140, 140)
ACCENT = (70, 130, 220)
BUTTON_BG = (35, 35, 45)

GRID_PADDING = 24
TILE_SIZE = 48

GRID_COUNT = min(
    (WIDTH - 2 * GRID_PADDING) // TILE_SIZE,
    (HEIGHT - 2 * GRID_PADDING) // TILE_SIZE
)

GRID_SIZE = GRID_COUNT * TILE_SIZE
GRID_X = (WIDTH - GRID_SIZE) // 2
GRID_Y = (HEIGHT - GRID_SIZE) // 2
GRID_COLOR = (55, 55, 55)

# Fonts
title_font = pygame.font.SysFont(None, 72)
subtitle_font = pygame.font.SysFont(None, 30)
button_font = pygame.font.SysFont(None, 36)
small_font = pygame.font.SysFont(None, 24)
hud_font = pygame.font.SysFont(None, 22)

# ---------------------------------------------------------------------------
# Game modes: edit / add entries here and they show up in the selection screen.
#   enemies    -> list of (col, row) starting cells, one AI per entry
#   move_limit -> max number of player moves (None = unlimited)
# ---------------------------------------------------------------------------
GAME_MODES = [
    {
        "name": "Casual",
        "desc": "Easier AI",
        "enemies": [(8, 0)],
        "move_limit": None,
    },
    {
        "name": "Challenging",
        "desc": "Harder AI",
        "enemies": [(8, 0)],
        "move_limit": None,
    },
]


class Menu:
    """A simple vertical menu with keyboard + mouse support."""

    def __init__(self, title, options, subtitle="", descriptions=None):
        self.title = title
        self.subtitle = subtitle
        self.options = options
        self.descriptions = descriptions or {}
        self.selected = 0

    def _rects(self):
        w, h, gap = 320, 48, 14
        total = len(self.options) * h + (len(self.options) - 1) * gap
        start_y = HEIGHT // 2 - total // 2 + 40
        return [
            pygame.Rect((WIDTH - w) // 2, start_y + i * (h + gap), w, h)
            for i in range(len(self.options))
        ]

    def handle_event(self, event):
        """Returns ("select", index), ("back", None), or None."""
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

        title = title_font.render(self.title, True, WHITE)
        surface.blit(title, title.get_rect(center=(WIDTH // 2, 70)))

        if self.subtitle:
            sub = subtitle_font.render(self.subtitle, True, ACCENT)
            surface.blit(sub, sub.get_rect(center=(WIDTH // 2, 115)))

        for i, rect in enumerate(self._rects()):
            is_selected = i == self.selected
            pygame.draw.rect(surface, ACCENT if is_selected else BUTTON_BG, rect, border_radius=8)
            label = button_font.render(self.options[i], True, WHITE if is_selected else GRAY)
            surface.blit(label, label.get_rect(center=rect.center))

        desc = self.descriptions.get(self.selected)
        if desc:
            text = small_font.render(desc, True, GRAY)
            surface.blit(text, text.get_rect(center=(WIDTH // 2, HEIGHT - 40)))


class GameController:
    def __init__(self, player, enemies, grid_count, mode):
        self.player = player
        self.enemies = enemies
        self.grid_count = grid_count
        self.mode = mode
        self.phase = "player"
        self.moves = 0
        self.result = None  # None, "win", or "lose"

    def handle_event(self, event):
        if self.phase != "player" or self.result or event.type != pygame.KEYDOWN:
            return

        moves = {
            pygame.K_UP: (0, -1),
            pygame.K_DOWN: (0, 1),
            pygame.K_LEFT: (-1, 0),
            pygame.K_RIGHT: (1, 0)
        }

        if event.key not in moves:
            print("Invalid move!")
            return

        dx, dy = moves[event.key]
        new_col = self.player.col + dx
        new_row = self.player.row + dy

        if 0 <= new_col < self.grid_count and 0 <= new_row < self.grid_count:
            self.player.col = new_col
            self.player.row = new_row
            self.moves += 1
            self.check_result()
            if not self.result:
                self.phase = "enemy"

    def check_result(self):
        if (self.player.col, self.player.row) == (finish_col, finish_row):
            self.result = "win"
        elif any((e.col, e.row) == (self.player.col, self.player.row) for e in self.enemies):
            self.result = "lose"
        elif self.mode["move_limit"] is not None and self.moves >= self.mode["move_limit"]:
            self.result = "lose"

    def update(self):
        if self.phase == "enemy":
            self.enemy_turn()
            self.check_result()
            self.phase = "player"

    def enemy_turn(self):
        print("enemy's turn")
        # place holder: move each enemy in self.enemies here
        pass


def start_game(mode):
    player = char.player(0, 0, playerImage)
    enemies = [char.player(col, row, enemyImage) for col, row in mode["enemies"]]
    return GameController(player, enemies, GRID_COUNT, mode)


def draw_game(game):
    screen.fill(BLACK)

    for i in range(GRID_COUNT + 1):
        x = GRID_X + i * TILE_SIZE
        y = GRID_Y + i * TILE_SIZE

        pygame.draw.line(screen, GRID_COLOR, (x, GRID_Y), (x, GRID_Y + GRID_SIZE))
        pygame.draw.line(screen, GRID_COLOR, (GRID_X, y), (GRID_X + GRID_SIZE, y))

    game.player.draw(screen, GRID_X, GRID_Y, TILE_SIZE)
    for enemy in game.enemies:
        enemy.draw(screen, GRID_X, GRID_Y, TILE_SIZE)

    finish_cell = pygame.Rect(
        GRID_X + finish_col * TILE_SIZE,
        GRID_Y + finish_row * TILE_SIZE,
        TILE_SIZE, TILE_SIZE
    )
    screen.blit(finishImage, finishImage.get_rect(center=finish_cell.center))

    # HUD (left margin)
    limit = game.mode["move_limit"]
    moves_text = f"Moves: {game.moves}" + (f"/{limit}" if limit else "")
    screen.blit(hud_font.render(game.mode["name"], True, ACCENT), (12, 24))
    screen.blit(hud_font.render(moves_text, True, WHITE), (12, 48))
    screen.blit(hud_font.render("Esc: menu", True, GRAY), (12, HEIGHT - 32))

    # Result overlay
    if game.result:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        msg = "You reached the finish!" if game.result == "win" else "You lost!"
        text = title_font.render(msg, True, WHITE)
        screen.blit(text, text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
        hint = small_font.render("Press Enter to return to the menu", True, GRAY)
        screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))


# --- Menus -----------------------------------------------------------------
main_menu = Menu("ITS Campus Rush", ["Play", "Quit"], subtitle="AI Outbreak")
mode_menu = Menu(
    "Select Game Mode",
    [m["name"] for m in GAME_MODES] + ["Back"],
    descriptions={i: m["desc"] for i, m in enumerate(GAME_MODES)},
)

state = "main_menu"  # "main_menu", "mode_select", "playing"
game = None

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
                if action[1] == 0:      # Play
                    mode_menu.selected = 0
                    state = "mode_select"
                else:                   # Quit
                    running = False

        elif state == "mode_select":
            action = mode_menu.handle_event(event)
            if action:
                kind, index = action
                if kind == "back" or index == len(GAME_MODES):  # Esc or "Back"
                    state = "main_menu"
                else:
                    game = start_game(GAME_MODES[index])
                    state = "playing"

        elif state == "playing":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                state = "main_menu"
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and game.result:
                state = "main_menu"
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