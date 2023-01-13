import pygame
from settings import *
from pytmx.util_pygame import load_pygame
from support import *
from random import choice
from json import dump, load

class SoilTile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups) -> None:
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft = pos)
        self.z = LAYERS['soil']

class WaterTile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups) -> None:
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft = pos)
        self.z = LAYERS['soil water']

class Plant(pygame.sprite.Sprite):
    def __init__(self, type, groups, soil, check_watered) -> None:
        super().__init__(groups)

        # setup
        self.type = type
        self.frames = import_folder(f'../graphics/fruit/{type}')
        self.soil = soil
        self.check_watered = check_watered

        # growth attributes
        self.age = 0
        self.max_age = len(self.frames) - 1
        self.grow_speed = GROW_SPEED[type]
        self.harvestable = False

        # sprite setup
        self.image = self.frames[self.age]
        self.y_offset = -16 if type == 'corn' else -8
        self.rect = self.image.get_rect(midbottom = soil.rect.midbottom + pygame.math.Vector2(0, self.y_offset))
        self.z = LAYERS['ground plant']

    def grow(self):
        if self.check_watered(self.rect.center):
            # increase age
            if self.age < self.max_age:
                self.age += self.grow_speed
            else:
                self.harvestable = True
                if not RIGID_PLANTS:
                    self.hitbox = self.rect.copy().inflate(-26, -self.rect.height * 0.4)

            # update z-index for above-ground plant
            if int(self.age) > 0:
                self.z = LAYERS['main']
                if RIGID_PLANTS:
                    self.hitbox = self.rect.copy().inflate(-26, -self.rect.height * 0.4)

            # update sprite
            self.image = self.frames[int(self.age)]
            self.rect = self.image.get_rect(midbottom = self.soil.rect.midbottom + pygame.math.Vector2(0, self.y_offset))

class SoilLayer:
    def __init__(self, all_sprites, collision_sprites) -> None:
        # sprite groups
        self.all_sprites = all_sprites
        self.collision_sprites = collision_sprites
        self.soil_sprites = pygame.sprite.Group()
        self.water_sprites = pygame.sprite.Group()
        self.plant_sprites = pygame.sprite.Group()

        # graphics
        self.soil_surf = pygame.image.load('../graphics/soil/o.png')
        self.soil_surfs = import_folder_dict('../graphics/soil/')
        self.water_surfs = import_folder('../graphics/soil_water/')

        # create grid
        self.create_soil_grid()
        self.create_hit_rects()

        # import audio
        self.hoe_sound = pygame.mixer.Sound('../audio/hoe.wav')
        self.hoe_sound.set_volume(0.1 * MASTER_VOL)
        self.plant_sound = pygame.mixer.Sound('../audio/plant.wav')
        self.plant_sound.set_volume(0.2 * MASTER_VOL)

    def create_soil_grid(self):
        ground = pygame.image.load('../graphics/world/ground.png')
        h_tiles = ground.get_width() // TILE_SIZE
        v_tiles = ground.get_height() // TILE_SIZE

        # load grid from JSON
        if LOAD:
            with open('save.json', 'r') as openfile:
                self.grid = load(openfile)
            self.create_soil_tiles()
        else:
            self.grid = [[[] for col in range(h_tiles)] for row in range(v_tiles)]
            farmable_tiles = load_pygame('../data/map.tmx').get_layer_by_name('Farmable').tiles()
            for x, y, surface in farmable_tiles:
                self.grid[y][x].append('F')

    def create_hit_rects(self):
        self.hit_rects = []
        for row_index, row in enumerate(self.grid):
            for col_index, cell in enumerate(row):
                if 'F' in cell:
                    x = col_index * TILE_SIZE
                    y = row_index * TILE_SIZE
                    rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                    self.hit_rects.append(rect)

    def get_hit(self, point):
        for rect in self.hit_rects:
            if rect.collidepoint(point):
                # play audio
                self.hoe_sound.play()

                # tile update
                x = rect.x // TILE_SIZE
                y = rect.y // TILE_SIZE
                if 'F' in self.grid[y][x]:
                    self.grid[y][x].append('X')
                    self.create_soil_tiles()
                    if self.raining:
                        self.water_all()

                # write to JSON
                with open("save.json", "w") as outfile:
                    dump(self.grid, outfile)

    def water(self, target_pos):
        for soil_sprite in self.soil_sprites.sprites():
            if soil_sprite.rect.collidepoint(target_pos):
                # update soil grid data
                x = soil_sprite.rect.x // TILE_SIZE
                y = soil_sprite.rect.y // TILE_SIZE
                self.grid[y][x].append('W')

                # update soil tile
                pos = soil_sprite.rect.topleft
                surf = choice(self.water_surfs)
                WaterTile(
                    pos = pos,
                    surf = surf,
                    groups = [self.all_sprites, self.water_sprites]
                )

                # write to JSON
                with open("save.json", "w") as outfile:
                    dump(self.grid, outfile)

    def water_all(self):
        # loop through all soil and water (called during rain)
        for row_index, row in enumerate(self.grid):
            for col_index, cell in enumerate(row):
                if 'X' in cell:
                    # update soil tile
                    if 'W' not in cell:
                        cell.append('W')
                    x = col_index * TILE_SIZE
                    y = row_index * TILE_SIZE
                    surf = choice(self.water_surfs)
                    WaterTile(
                        pos = (x, y),
                        surf = surf,
                        groups = [self.all_sprites, self.water_sprites]
                    )

                    # write to JSON
                    with open("save.json", "w") as outfile:
                        dump(self.grid, outfile)

    def remove_water(self):
        # kill water sprites
        for sprite in self.water_sprites.sprites():
            sprite.kill()

        # clean up soil grid
        for row in self.grid:
            for cell in row:
                if 'W' in cell:
                    cell.remove('W')

        # write to JSON
        with open("save.json", "w") as outfile:
            dump(self.grid, outfile)

    def check_watered(self, pos) -> bool:
        x = pos[0] // TILE_SIZE
        y = pos[1] // TILE_SIZE
        cell = self.grid[y][x]
        is_watered = 'W' in cell
        return is_watered

    def plant_seed(self, target_pos, seed):
        for soil_sprite in self.soil_sprites.sprites():
            if soil_sprite.rect.collidepoint(target_pos):
                # play audio
                # self.plant_sound.play()

                # tile update
                x = soil_sprite.rect.x // TILE_SIZE
                y = soil_sprite.rect.y // TILE_SIZE
                if 'C' not in self.grid[y][x] and 'T' not in self.grid[y][x]:
                    if seed == 'corn':
                        letter = 'C'
                    elif seed == 'tomato':
                        letter = 'T'
                    self.grid[y][x].append(letter)
                    Plant(
                        type = seed,
                        groups = [self.all_sprites, self.plant_sprites, self.collision_sprites],
                        soil = soil_sprite,
                        check_watered = self.check_watered
                    )

                # write to JSON
                with open("save.json", "w") as outfile:
                    dump(self.grid, outfile)
            
    def load_seed(self, target_pos, seed):
        if ANALYTICS:
            print('planting seed')
            if load:
                print('from save')

        for soil_sprite in self.soil_sprites.sprites():
            if soil_sprite.rect.collidepoint(target_pos):
                # tile update
                x = soil_sprite.rect.x // TILE_SIZE
                y = soil_sprite.rect.y // TILE_SIZE
                Plant(
                    type = seed,
                    groups = [self.all_sprites, self.plant_sprites, self.collision_sprites],
                    soil = soil_sprite,
                    check_watered = self.check_watered
                )               

    def update_plants(self):
        for plant in self.plant_sprites.sprites():
            plant.grow()        

    def create_soil_tiles(self):
        self.soil_sprites.empty()
        for row_index, row in enumerate(self.grid):
            for col_index, cell in enumerate(row):
                if 'X' in cell:
                    # soil tile options
                    t = 'X' in self.grid[row_index - 1][col_index]
                    b = 'X' in self.grid[row_index + 1][col_index]
                    r = 'X' in row[col_index + 1]
                    l = 'X' in row[col_index - 1]

                    tm = all((l, r, b)) and not t and ('X' in self.grid[row_index + 1][col_index - 1] or 'X' in self.grid[row_index + 1][col_index + 1])
                    bm = all((l, r, t)) and not b and ('X' in self.grid[row_index - 1][col_index - 1] or 'X' in self.grid[row_index - 1][col_index + 1])
                    lm = all((t, r, b)) and not l and ('X' in self.grid[row_index - 1][col_index + 1] or 'X' in self.grid[row_index + 1][col_index + 1])
                    rm = all((t, l, b)) and not r and ('X' in self.grid[row_index - 1][col_index - 1] or 'X' in self.grid[row_index + 1][col_index - 1])

                    # default
                    tile_type = 'o'

                    # all sides
                    if all((t, b, r, l)):
                        tile_type = 'x'
                    
                    # horizontal only
                    if l and not any((t, b, r)):
                        tile_type = 'r'
                    if r and not any((t, b, l)):
                        tile_type = 'l'
                    if l and r and not any((t, b)):
                        tile_type = 'lr'

                    # vertical only
                    if t and not any((b, l, r)):
                        tile_type = 'b'
                    if b and not any((t, l, r)):
                        tile_type = 't'
                    if t and b and not any((l, r)):
                        tile_type = 'tb'

                    # corners
                    if t and l and not any((b, r)):
                        tile_type = 'br'
                    if t and r and not any((b, l)):
                        tile_type = 'bl'
                    if b and l and not any((t, r)):
                        tile_type = 'tr'
                    if b and r and not any((t, l)):
                        tile_type = 'tl'

                    # three-sided path
                    if all((t, b, r)) and not l:
                        tile_type = 'tbr'
                    if all((t, b, l)) and not r:
                        tile_type = 'tbl'
                    if all((t, l, r)) and not b:
                        tile_type = 'tlr'
                    if all((b, l, r)) and not t:
                        tile_type = 'blr'

                    # three-sided middle
                    if tm:
                        tile_type = 'tm'
                    if bm:
                        tile_type = 'bm'
                    if lm:
                        tile_type = 'lm'
                    if rm:
                        tile_type = 'rm'
                    

                    SoilTile(
                        pos = (col_index * TILE_SIZE, row_index * TILE_SIZE),
                        surf = self.soil_surfs[tile_type],
                        groups = [self.all_sprites, self.soil_sprites]
                    )

                if 'C' in cell:
                    self.load_seed(
                        target_pos = (col_index * TILE_SIZE, row_index * TILE_SIZE),
                        seed = 'corn'
                    )

                if 'T' in cell:
                    self.load_seed(
                        target_pos = (col_index * TILE_SIZE, row_index * TILE_SIZE),
                        seed = 'tomato'
                    )
