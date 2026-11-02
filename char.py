import pygame
import os

class player:
    def __init__(self, col, row, image):
        self.col = col
        self.row = row
        self.image = pygame.transform.scale(image, (46, 46))

    def draw(self, surface, grid_x, grid_y, tile_size):
        cell_rect = pygame.Rect(
            grid_x + self.col * tile_size,
            grid_y + self.row * tile_size,
            tile_size, tile_size
        )

        image_rect = self.image.get_rect(center=cell_rect.center)
        surface.blit(self.image, image_rect)

