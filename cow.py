import pygame
from settings import *
from support import *
from random import randint
from timer import Timer

class Cow(pygame.sprite.Sprite):
    def __init__(
        self,
        pos,
        groups,
        collision_sprites):
        super().__init__(groups)

        # import graphics from support
        self.import_assets()
        self.status = 'idle_right'
        self.frame_index = 0

        # player setup
        self.image = self.animations[self.status][self.frame_index]
        self.rect = self.image.get_rect(center = pos)
        self.z = LAYERS['main']

        # movement attributes
        self.direction = pygame.math.Vector2()
        self.direction.x = randint(-1, 1)
        self.direction.y = randint(-1, 1)
        self.pos = pygame.math.Vector2(self.rect.center)
        self.speed = 50

        # collisions
        self.hitbox = self.rect.copy().inflate((-10, -100))
        self.hitbox.y += COW_Y_OFFSET
        self.collision_sprites = collision_sprites

        # timers
        self.timers = {
            'animation': Timer(6000)
        }

    def import_assets(self):
        self.animations = {
            'idle_left': [], 
            'walk_left': [], 
            'sit_left': [], 
            'eat_left': [],
            'love_left': [],
            'idle_right': [], 
            'walk_right': [], 
            'sit_right': [], 
            'eat_right': [],
            'love_right': []
        }

        for animation in self.animations.keys():
            full_path = '../graphics/cow/' + animation
            self.animations[animation] = import_folder(full_path)

    def animate(self, dt):
        self.frame_index += 4 * dt
        if self.frame_index >= len(self.animations[self.status]):
            self.frame_index = 0
        
        self.image = self.animations[self.status][int(self.frame_index)]

    def move(self, dt) -> None:
        # normalize movement vector
        if self.direction.magnitude() > 0:
            self.direction = self.direction.normalize()

        # horizontal movement output
        self.pos.x += self.direction.x * self.speed * dt
        self.hitbox.centerx = round(self.pos.x)
        self.rect.centerx = self.hitbox.centerx
        self.collision('horizontal')

        # vertical movement output
        self.pos.y += self.direction.y * self.speed * dt
        self.hitbox.centery = round(self.pos.y)
        self.rect.centery = self.hitbox.centery
        self.collision('vertical')

    def update_timers(self):
        for timer in self.timers.values():
            timer.update()

    def collision(self, direction):
        for sprite in self.collision_sprites.sprites():
            if sprite != self and hasattr(sprite, 'hitbox'):
                if sprite.hitbox.colliderect(self.hitbox):
                    if ANALYTICS and COW:
                        print('cow collision!')

                    if direction == 'horizontal':
                        if self.direction.x > 0: # moving right
                            self.hitbox.right = sprite.hitbox.left
                        if self.direction.x < 0: # moving left
                            self.hitbox.left = sprite.hitbox.right
                        self.rect.centerx = self.hitbox.centerx
                        self.pos.x = self.hitbox.centerx

                    if direction == 'vertical':
                        if self.direction.y > 0: # moving down
                            self.hitbox.bottom = sprite.hitbox.top
                        if self.direction.y < 0: # moving up
                            self.hitbox.top = sprite.hitbox.bottom
                        self.rect.centery = self.hitbox.centery
                        self.pos.y = self.hitbox.centery

    def get_status(self):
        # set action
        rand_max = 100
        x = randint(0, rand_max)
        if x < 40:
            self.status = 'idle_'
        elif x < 60:
            self.status = 'eat_'
        elif x < 80:
            self.status = 'sit_'
        else:
            self.status = 'walk_'
            while True:
                self.direction.x = randint(-1, 1)
                self.direction.y = randint(-1, 1)
                if self.direction.magnitude != 0:
                    break
        
        # set direction
        if self.direction.x == -1:
            self.status += 'left'
        elif self.direction.x == 1:
            self.status += 'right'
        elif randint(0, 1) == 0:
            self.status += 'right'
        else:
            self.status += 'left'

        if ANALYTICS and COW:
            print(self.direction)
            print(self.status)

        # start animation timer
        self.timers['animation'].activate()

    def update(self, dt):
        if not self.timers['animation'].active:
            self.get_status()
        self.update_timers()
        if self.status == 'walk_left' or self.status == 'walk_right':
            self.move(dt)
        self.animate(dt)
