import pygame
from settings import *
from support import *
from timer import Timer
from random import randint
from json import load, dump

class Player(pygame.sprite.Sprite):
    def __init__(
        self, 
        pos, 
        group, 
        collision_sprites, 
        tree_sprites, 
        interaction_sprites,
        soil_layer,
        toggle_shop,
        toggle_inventory) -> None:
        super().__init__(group)

        # import graphics from support
        self.import_assets()
        self.status = 'down_idle'
        self.frame_index = 0

        # player setup
        self.image = self.animations[self.status][self.frame_index]
        self.rect = self.image.get_rect(center = pos)
        self.z = LAYERS['main']

        # movement attributes
        self.direction = pygame.math.Vector2()
        self.pos = pygame.math.Vector2(self.rect.center)
        self.speed = 1000 if SUPER_SPEED else 200

        # collisions
        self.hitbox = self.rect.copy().inflate((-126,-70))
        self.collision_sprites = collision_sprites

        # timers
        self.timers = {
            'tool use': Timer(800, self.use_tool),
            'tool switch': Timer(200),
            'seed use': Timer(350, self.use_seed),
            'seed switch': Timer(200)
        }

        # tool attributes
        self.tools = ['hoe', 'axe', 'water']
        self.tool_index = 0
        self.selected_tool = self.tools[self.tool_index]

        # seed attributes
        self.seeds = ['corn_seed', 'tomato_seed']
        self.seed_index = 0
        self.selected_seed = self.seeds[self.seed_index]

        # inventory
        if LOAD:
            with open('items.json', 'r') as openfile:
                self.item_inventory = load(openfile)
            with open('seeds.json', 'r') as openfile:
                self.seed_inventory = load(openfile)
            with open('money.json', 'r') as openfile:
                self.money = load(openfile)
        else:
            start_items = randint(0, 20) if START_ITEMS else 0
            self.item_inventory = {
                'wood': start_items,
                'apple': start_items,
                'corn': start_items,
                'tomato': start_items
            }
            self.seed_inventory = {
                'corn_seed': 5,
                'tomato_seed': 5
            }
            self.money = 25

        # interactions
        self.tree_sprites = tree_sprites
        self.interaction_sprites = interaction_sprites
        self.sleep = False
        self.soil_layer = soil_layer
        self.toggle_shop = toggle_shop
        self.toggle_inventory = toggle_inventory

        # import audio
        self.water_sound = pygame.mixer.Sound('../audio/water.mp3')
        self.water_sound.set_volume(0.2 * MASTER_VOL)

    def use_tool(self) -> None:
        if ANALYTICS and ACTION:
            print('tool use')
        
        # chop tree   // axe
        if self.selected_tool == 'axe':
            for tree in self.tree_sprites.sprites():
                if tree.rect.collidepoint(self.target_pos):
                    tree.damage()

        # till soil   // hoe
        if self.selected_tool == 'hoe':
            self.soil_layer.get_hit(self.target_pos)

        # water plant // water
        if self.selected_tool == 'water':
            # update soil
            self.soil_layer.water(self.target_pos)

            # play audio
            self.water_sound.play()

    def get_target_pos(self) -> None:
        self.target_pos = self.rect.center + PLAYER_TOOL_OFFSET[self.status.split('_')[0]]

    def use_seed(self) -> None:
        if self.seed_inventory[self.selected_seed] > 0:
            temp_seed = self.selected_seed.replace('_seed', '')
            if (self.soil_layer.plant_seed(self.target_pos, temp_seed)):
                self.seed_inventory[self.selected_seed] -= 1

        # save to JSON
        with open('seeds.json', 'w') as openfile:
            dump(self.seed_inventory, openfile)

    def import_assets(self) -> None:
        self.animations = {
            'up': [], 'down': [], 'left': [], 'right': [],
            'up_idle': [], 'down_idle': [], 'left_idle': [], 'right_idle': [],
            'up_hoe': [], 'down_hoe': [], 'left_hoe': [], 'right_hoe': [],
            'up_axe': [], 'down_axe': [], 'left_axe': [], 'right_axe': [],
            'up_water': [], 'down_water': [], 'left_water': [], 'right_water': []
        }

        for animation in self.animations.keys():
            full_path = '../graphics/character/' + animation
            self.animations[animation] = import_folder(full_path)

    def animate(self, dt) -> None:
        tool = self.status.endswith('e') or self.status.endswith('r') and not self.status.endswith('idle')
        self.frame_index += 8 * dt if tool else 4 * dt
        self.frame_index %= len(self.animations[self.status])
        # if self.frame_index >= len(self.animations[self.status]):
        #     self.frame_index = 0
        
        self.image = self.animations[self.status][int(self.frame_index)]

    def input(self) -> None:
        keys = pygame.key.get_pressed()

        if not self.timers['tool use'].active and not self.sleep:
            # vertical movement input
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.direction.y = -1
                self.status = 'up'
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.direction.y = 1
                self.status = 'down'
            else:
                self.direction.y = 0

            # horizontal movement input
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.direction.x = -1
                self.status = 'left'
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.direction.x = 1
                self.status = 'right'
            else:
                self.direction.x = 0

            # tool use input
            if keys[pygame.K_SPACE]:
                self.timers['tool use'].activate()        
                self.direction = pygame.math.Vector2(0, 0)
                self.frame_index = 0

            # change tool
            if keys[pygame.K_q] and not self.timers['tool switch'].active:
                self.timers['tool switch'].activate()
                self.tool_index += 1
                if self.tool_index >= len(self.tools):
                    self.tool_index = 0
                self.selected_tool = self.tools[self.tool_index]

            # seed use input
            if keys[pygame.K_LALT] or keys[pygame.K_RALT]:
                self.timers['seed use'].activate()        
                self.direction = pygame.math.Vector2(0, 0)
                self.frame_index = 0

            # change seed
            if keys[pygame.K_e] and not self.timers['seed switch'].active:
                self.timers['seed switch'].activate()
                self.seed_index += 1
                if self.seed_index >= len(self.seeds):
                    self.seed_index = 0
                self.selected_seed = self.seeds[self.seed_index]

            # sleep / shop
            if keys[pygame.K_RETURN]:
                collided_interaction_sprite = pygame.sprite.spritecollide(self, self.interaction_sprites, False)
                if collided_interaction_sprite:
                    if collided_interaction_sprite[0].name == 'Trader':
                        self.toggle_shop()
                    elif collided_interaction_sprite[0].name == 'Bed':
                        self.status = 'left_idle'
                        self.sleep = True

            if keys[pygame.K_i]:
                if ANALYTICS and INVENTORY:
                    print('inventory')
                self.toggle_inventory()
                

    def get_status(self) -> None:
        # set idle status
        if self.direction.magnitude() == 0:
            self.status = self.status.split('_')[0] + '_idle'

        # tool use
        if self.timers['tool use'].active:
            self.status = self.status.split('_')[0] + '_' + self.selected_tool

    def update_timers(self) -> None:
        for timer in self.timers.values():
            timer.update()

    def collision(self, direction) -> None:
        for sprite in self.collision_sprites.sprites():
            if hasattr(sprite, 'hitbox'):
                if sprite.hitbox.colliderect(self.hitbox):
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

    def update(self, dt) -> None:
        self.input()
        self.get_status()
        self.update_timers()
        self.get_target_pos()
        self.move(dt)
        self.animate(dt)
