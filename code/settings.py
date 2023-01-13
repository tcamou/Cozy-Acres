import os
from pygame.math import Vector2

# analysis mode
ANALYTICS = True
HITBOX = False
ACTION = False
INVENTORY = True
SHOP = True
COW = False

# gameplay modes
RAIN_MODE = False
RIGID_PLANTS = False
SUPER_SPEED = False
START_ITEMS = True

# volume
MASTER_VOL = 0.1

# new / load
if os.path.getsize('save.json') == 0:
	LOAD = False
else:
	LOAD = True

# screen attributes
SCREEN_WIDTH = 1280 * 3/4
SCREEN_HEIGHT = 720 * 3/4
TILE_SIZE = 64

# overlay positions 
OVERLAY_POSITIONS = {
	'tool' : (40, SCREEN_HEIGHT - 15), 
	'seed': (100, SCREEN_HEIGHT - 5)}

# tool use offset
PLAYER_TOOL_OFFSET = {
	'left': Vector2(-50,40),
	'right': Vector2(50,40),
	'up': Vector2(0,-10),
	'down': Vector2(0,50)
}

# cow hitbox offset
COW_Y_OFFSET = 15

# z-index
LAYERS = {
	'water': 0,
	'ground': 1,
	'soil': 2,
	'soil water': 3,
	'rain floor': 4,
	'house bottom': 5,
	'ground plant': 6,
	'main': 7,
	'house top': 8,
	'fruit': 9,
	'rain drops': 10
}

# apple positions
APPLE_POS = {
	'Small': [(18,17), (30,37), (12,50), (30,45), (20,30), (30,10)],
	'Large': [(30,24), (60,65), (50,50), (16,40),(45,50), (42,70)]
}

# grow speed
GROW_SPEED = {
	'corn': 1,
	'tomato': 0.7
}

# merchant sales
SALE_PRICES = {
	'wood': 4,
	'apple': 2,
	'corn': 10,
	'tomato': 20
}

# merchant purchases
PURCHASE_PRICES = {
	'corn_seed': 4,
	'tomato_seed': 5
}
