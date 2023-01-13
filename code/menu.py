import pygame
from settings import *
from timer import Timer

class Menu:
    def __init__(self, player, toggle_menu) -> None:
        # general setup
        self.player = player
        self.toggle_menu = toggle_menu
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font('../font/LycheeSoda.ttf', 30)

        # formatting
        self.width = 300
        self.space = 10
        self.padding = 8

        # options
        self.options = list(self.player.item_inventory.keys()) + list(self.player.seed_inventory.keys())
        self.sell_border = len(self.player.item_inventory) - 1
        self.setup()

        # movement
        self.index = 0
        self.timer = Timer(200)

    def display_money(self):
        text_surf = self.font.render(f'${self.player.money}', False, 'Black')
        text_rect = text_surf.get_rect(midbottom = (SCREEN_WIDTH / 2, SCREEN_HEIGHT - 20))

        pygame.draw.rect(self.display_surface, 'White', text_rect.inflate(10, 10), 0, 6)
        self.display_surface.blit(text_surf, text_rect)

    def setup(self):
        # create text surfaces
        self.text_surfs = []
        self.height = 0

        # add items to option list
        for item in self.options:
            text_surf = self.font.render(item, False, 'Black')
            self.text_surfs.append(text_surf)
            self.height += text_surf.get_height() + self.padding * 2

        # create menu rectangle
        self.height += (len(self.text_surfs) - 1) * self.space
        self.menu_top = SCREEN_HEIGHT / 2 - self.height / 2
        self.menu_left = SCREEN_WIDTH / 2 - self.width / 2
        self.main_rect = pygame.Rect(self.menu_left, self.menu_top, self.width, self.height)

        # buy / sell 
        self.buy_text = self.font.render('buy', False, '#000077')
        self.sell_text = self.font.render('sell', False, '#000077')

    def input(self):
        keys = pygame.key.get_pressed()
        self.timer.update()

        # quit menu
        if keys[pygame.K_ESCAPE]:
            self.toggle_menu()

        # selected 
        if not self.timer.active:
            if keys[pygame.K_UP] or keys[pygame.K_w]: # up
                self.index -= 1
                self.timer.activate()

            if keys[pygame.K_DOWN] or keys[pygame.K_s]: # down
                self.index += 1
                self.timer.activate()

            if keys[pygame.K_SPACE] or keys[pygame.K_RETURN]: # buy / sell
                self.timer.activate()

                # get item
                current_item = self.options[self.index]

                # sell
                if self.index <= self.sell_border:
                    if self.player.item_inventory[current_item] > 0:
                        self.player.item_inventory[current_item] -= 1
                        self.player.money += SALE_PRICES[current_item]

                # buy
                else:
                    seed_price = PURCHASE_PRICES[current_item]
                    if self.player.money >= seed_price:
                        self.player.seed_inventory[current_item] += 1
                        self.player.money -= seed_price

        # control the selected index
        if self.index < 0:
            self.index = len(self.options) - 1
        if self.index > len(self.options) - 1:
            self.index = 0

    def show_entry(self, text_surf, amount, price, item_type, top, selected):
        # background
        bg_rect = pygame.Rect(self.main_rect.left, top, self.width, text_surf.get_height() + self.padding * 2)
        pygame.draw.rect(self.display_surface, 'White', bg_rect, 0, 6)

        # text
        text_rect = text_surf.get_rect(midleft = (self.main_rect.left + 20, bg_rect.centery))
        self.display_surface.blit(text_surf, text_rect)

        # amount
        amount_surf = self.font.render(str(amount), False, 'Black')
        amount_rect = amount_surf.get_rect(midright = (self.main_rect.right - 65, bg_rect.centery))
        self.display_surface.blit(amount_surf, amount_rect)

        # price
        if item_type == 'sell': # sell
            price_surf = self.font.render(f'${SALE_PRICES[str(price)]}', False, 'Black')
            price_rect = price_surf.get_rect(midright = (self.main_rect.right - 20, bg_rect.centery))
            self.display_surface.blit(price_surf, price_rect)
        elif item_type == 'buy': # buy
            price_surf = self.font.render(f'${PURCHASE_PRICES[str(price)]}', False, 'Black')
            price_rect = price_surf.get_rect(midright = (self.main_rect.right - 20, bg_rect.centery))
            self.display_surface.blit(price_surf, price_rect)

        # selected
        if selected:
            pygame.draw.rect(self.display_surface, 'Black', bg_rect, 4, 6)
            if self.index <= self.sell_border: # sell
                pos_rect = self.sell_text.get_rect(midleft = (self.main_rect.left + 150, bg_rect.centery))
                self.display_surface.blit(self.sell_text, pos_rect)
            else:                             # buy
                pos_rect = self.buy_text.get_rect(midleft = (self.main_rect.left + 150, bg_rect.centery))
                self.display_surface.blit(self.buy_text, pos_rect)

    def update(self):
        self.input()
        self.display_money()

        for text_index, text_surf in enumerate(self.text_surfs):
            top = self.main_rect.top + text_index * (text_surf.get_height() + self.padding * 2 + self.space)
            # inventory qty
            amount_list = list(self.player.item_inventory.values()) + list(self.player.seed_inventory.values())
            amount = amount_list[text_index]
            # item prices
            price_list = list(self.player.item_inventory.keys()) + list(self.player.seed_inventory.keys())
            price = price_list[text_index]

            item_type = 'sell' if text_index < 4 else 'buy'
            self.show_entry(text_surf, amount, price, item_type, top, self.index == text_index)
