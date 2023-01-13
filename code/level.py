import pygame
from settings import *
from player import Player
from overlay import Overlay
from sprites import Generic, Water, WildFlower, Tree, Interaction, Particle
from pytmx.util_pygame import load_pygame
from support import *
from transition import Transition
from soil import SoilLayer
from sky import Rain, Sky
from menu import Menu, Inventory
from random import randint
from time import sleep
from cow import Cow

class Level:
    def __init__(self):
        # get display surface
        self.display_surface = pygame.display.get_surface()

        # sprite groups
        self.all_sprites = CameraGroup()
        self.collision_sprites = pygame.sprite.Group()
        self.tree_sprites = pygame.sprite.Group()
        self.interaction_sprites = pygame.sprite.Group()
        self.cow_sprites = pygame.sprite.Group()

        # setup
        self.soil_layer = SoilLayer(self.all_sprites, self.collision_sprites)
        self.setup()
        self.overlay = Overlay(self.player)
        self.transition = Transition(self.reset, self.player)

        # sky
        self.rain = Rain(self.all_sprites)
        self.raining = True if RAIN_MODE else randint(0, 10) < 3
        self.soil_layer.raining = self.raining
        self.sky = Sky()

        # shop
        self.shop_active = False
        self.menu = Menu(
            player = self.player,
            toggle_menu = self.toggle_shop
        )

        # inventory menu
        self.inventory_active = False
        self.inventory = Inventory(
            player = self.player,
            toggle_inventory = self.toggle_inventory
        )

        # import audio
        self.success = pygame.mixer.Sound('../audio/success.wav')
        self.success.set_volume(0.3 * MASTER_VOL)
        self.music = pygame.mixer.Sound('../audio/music.mp3')
        self.music.set_volume(0.1 * MASTER_VOL)
        self.music.play(loops = -1)

    def setup(self):
        # import tiled map 
        tmx_data = load_pygame('../data/map.tmx')

        # load assets from tiled map:
        # house bottom
        for layer in ['HouseFloor', 'HouseFurnitureBottom']:
            for x, y, surf in tmx_data.get_layer_by_name(layer).tiles():
                Generic(
                    pos = (x * TILE_SIZE, y * TILE_SIZE), 
                    surf = surf, 
                    groups = self.all_sprites, 
                    z = LAYERS['house bottom']
                )

        # house top
        for layer in ['HouseWalls', 'HouseFurnitureTop']:
            for x, y, surf in tmx_data.get_layer_by_name(layer).tiles():
                Generic(
                    pos = (x * TILE_SIZE, y * TILE_SIZE), 
                    surf = surf, 
                    groups = self.all_sprites, 
                    z = LAYERS['main']
                )

        # fence
        for x, y, surf in tmx_data.get_layer_by_name('Fence').tiles():
            Generic(
                pos = (x * TILE_SIZE, y * TILE_SIZE), 
                surf = surf, 
                groups = [self.all_sprites, self.collision_sprites], 
                z = LAYERS['main']
            )

        # water
        water_frames = import_folder('../graphics/water')
        for x, y, surf in tmx_data.get_layer_by_name('Water').tiles():
            Water(
                pos = (x * TILE_SIZE, y * TILE_SIZE),
                frames = water_frames,
                groups = self.all_sprites
            )

        # trees
        for obj in tmx_data.get_layer_by_name('Trees'):
            Tree(
                pos = (obj.x, obj.y),
                surf = obj.image,
                groups = [self.all_sprites, self.collision_sprites, self.tree_sprites],
                name = obj.name,
                player_add = self.player_add
            )

        # wildflowers
        for obj in tmx_data.get_layer_by_name('Decoration'):
            WildFlower(
                pos = (obj.x, obj.y),
                surf = obj.image,
                groups = [self.all_sprites, self.collision_sprites]
            )

        # collision tiles
        for x, y, surf in tmx_data.get_layer_by_name('Collision').tiles():
            Generic(
                pos = (x * TILE_SIZE, y * TILE_SIZE),
                surf = pygame.Surface((TILE_SIZE, TILE_SIZE)),
                groups = self.collision_sprites
            )

        # player
        for obj in tmx_data.get_layer_by_name('Player'):
            if obj.name == 'Start':
                self.player = Player(
                    pos = (obj.x, obj.y), 
                    group = self.all_sprites, 
                    collision_sprites = self.collision_sprites,
                    tree_sprites = self.tree_sprites,
                    interaction_sprites = self.interaction_sprites,
                    soil_layer = self.soil_layer,
                    toggle_shop = self.toggle_shop,
                    toggle_inventory = self.toggle_inventory
                )

            if obj.name == 'Bed':
                Interaction(
                    pos = (obj.x, obj.y),
                    size = (obj.width, obj.height),
                    groups = self.interaction_sprites,
                    name = obj.name
                )

            if obj.name == 'Trader':
                Interaction(
                    pos = (obj.x, obj.y),
                    size = (obj.width, obj.height),
                    groups = self.interaction_sprites,
                    name = obj.name
                )

            if obj.name == 'Cow':
                Cow(
                    pos = (obj.x, obj.y),
                    groups = [self.all_sprites, self.collision_sprites, self.cow_sprites],
                    collision_sprites = self.collision_sprites
                )
        
        # ground
        Generic(
            pos = (0, 0),
            surf = pygame.image.load('../graphics/world/ground.png').convert_alpha(),
            groups = self.all_sprites,
            z = LAYERS['ground']
        )

    def toggle_shop(self):
        self.shop_active = not self.shop_active
        sleep(0.1)

    def toggle_inventory(self):
        self.inventory_active = not self.inventory_active
        sleep(0.1)

    def player_add(self, item):
        # update inventory
        self.player.item_inventory[item] += 1

        # play audio
        self.success.play()

    def reset(self):
        # grow plants
        self.soil_layer.update_plants()

        # tree apples
        for tree in self.tree_sprites.sprites():
            for apple in tree.apple_sprites.sprites():
                apple.kill()
            tree.create_fruit()

        # soil water
        self.soil_layer.remove_water()

        # randomize rain
        self.raining = True if RAIN_MODE else randint(0, 10) < 3
        self.soil_layer.raining = self.raining
        if self.raining:
            self.soil_layer.water_all()

        # daylight
        self.sky.start_color = [255, 255, 255]

    def plant_collision(self):
        if self.soil_layer.plant_sprites:
            for plant in self.soil_layer.plant_sprites.sprites():
                if plant.harvestable and plant.rect.colliderect(self.player.hitbox):
                    # update inventory
                    self.player_add(plant.type)
                    if ANALYTICS and INVENTORY:
                        print(self.player.item_inventory)

                    # remove plant + create particle
                    plant.kill()
                    Particle(
                        pos = plant.rect.topleft,
                        surf = plant.image,
                        groups = self.all_sprites,
                        z = LAYERS['main']
                    )

                    # update soil tile data
                    row = plant.rect.centery // TILE_SIZE
                    col = plant.rect.centerx // TILE_SIZE
                    self.soil_layer.grid[row][col].remove('P')

    def cow_collision(self):
        for cow in self.cow_sprites.sprites():
            if cow.rect.colliderect(self.player.hitbox):
                # adjust cow status
                cow.status = 'love_' 
                cow.status += 'left' if cow.direction == -1 else 'right'

    def run(self, dt):
        # load background and sprites
        self.display_surface.fill('black')
        self.all_sprites.custom_draw(self.player)
        
        # updates
        if self.shop_active:
            self.menu.update()
        elif self.inventory_active:
            self.inventory.update()
        else:    
            self.all_sprites.update(dt)
            self.plant_collision()
            self.cow_collision()

        # HUD
        self.overlay.display()

        # rain
        if self.raining and not self.shop_active:
            self.rain.update()

        # daylight
        self.sky.display(dt)

        # transition
        if self.player.sleep:
            self.transition.play()

class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.math.Vector2()

    def custom_draw(self, player):
        self.offset.x = player.rect.centerx - SCREEN_WIDTH / 2
        self.offset.y = player.rect.centery - SCREEN_HEIGHT / 2
        
        for layer in LAYERS.values():    
            for sprite in sorted(self.sprites(), key = lambda sprite: sprite.rect.centery):
                if sprite.z == layer:
                    offset_rect = sprite.rect.copy()
                    offset_rect.center -= self.offset
                    self.display_surface.blit(sprite.image, offset_rect)

                    # hitbox analytics
                    if ANALYTICS and HITBOX:
                        # player
                        if sprite == player:
                            pygame.draw.rect(
                                self.display_surface, 
                                'red', 
                                offset_rect, 
                                5
                            )
                            hitbox_rect = player.hitbox.copy()
                            hitbox_rect.center = offset_rect.center
                            pygame.draw.rect(
                                self.display_surface, 
                                'green', 
                                hitbox_rect, 
                                5
                            )
                            target_pos = offset_rect.center + PLAYER_TOOL_OFFSET[player.status.split('_')[0]]
                            pygame.draw.circle(
                                self.display_surface,
                                'blue',
                                target_pos,
                                5
                            )
