# 1763 Lines of code
import pygame, sys
from settings import *
from level import Level
import os

class Game:
    def __init__(self):
        x = 0
        y = 28
        os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (x,y)
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Cozy Acres: Bunny's Busy Burrow")
        self.clock = pygame.time.Clock()
        self.level = Level()

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # TODO: write save file
                    pygame.quit()
                    sys.exit()

            dt = self.clock.tick() / 1000
            self.level.run(dt)
            pygame.display.update()
    
if __name__ == '__main__':
    game = Game()
    game.run()
