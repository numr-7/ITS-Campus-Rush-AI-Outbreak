import pygame
import char
import random
import os

pygame.init()

WIDTH = 720
HEIGHT = 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ITS Campus Rush: AI Outbreak")

playerImage = pygame.image.load(os.path.join(os.path.dirname(__file__), "player.jpeg")).convert_alpha()
enemyImage = pygame.image.load(os.path.join(os.path.dirname(__file__), "ai.png")).convert_alpha()

finishImage = pygame.image.load(os.path.join(os.path.dirname(__file__), "tc.jpg")).convert_alpha()
finishImage = pygame.transform.scale(finishImage, (44, 44))
finish_col, finish_row = 4, 8

BLACK = (0, 0, 0)

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

class GameController:
    def __init__(self, player, grid_count):
        self.player = player
        self.grid_count = grid_count
        self.phase = "player"

    def handle_event(self, event):
        if self.phase != "player" or event.type != pygame.KEYDOWN:
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
            self.phase = "enemy"

    def update(self):
        if self.phase == "enemy":
            self.enemy_turn()
            self.phase = "player"

    def enemy_turn(self):
        print("enemy's turn")
        # place holder
        pass

player = char.player(0, 0, playerImage)
ai = char.player(8, 0, enemyImage)
game = GameController(player, GRID_COUNT)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            print("Game quitted!")
        else:
            game.handle_event(event)

    game.update()
    screen.fill(BLACK)

    for i in range(GRID_COUNT + 1):
        x = GRID_X + i * TILE_SIZE
        y = GRID_Y + i * TILE_SIZE

        pygame.draw.line(
            screen, GRID_COLOR,
            (x, GRID_Y), (x, GRID_Y + GRID_SIZE)
        )

        pygame.draw.line(
            screen, GRID_COLOR,
            (GRID_X, y), (GRID_X + GRID_SIZE, y)
        )

    player.draw(screen, GRID_X, GRID_Y, TILE_SIZE)
    ai.draw(screen, GRID_X, GRID_Y, TILE_SIZE)
    
    finish_cell = pygame.Rect(
        GRID_X + finish_col * TILE_SIZE,
        GRID_Y + finish_row * TILE_SIZE,
        TILE_SIZE, TILE_SIZE
    )
    finish_rect = finishImage.get_rect(center=finish_cell.center)
    screen.blit(finishImage, finish_rect)

    pygame.display.flip()

pygame.quit()