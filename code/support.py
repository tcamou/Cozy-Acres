import pygame
from os import walk

def import_folder(path) -> list:
    surface_list = []

    # import graphics and parse to surfaces
    for folder_name, sub_folder, img_files in walk(path):
        for image in img_files:
            full_path = path + '/' + image
            image_surf = pygame.image.load(full_path).convert_alpha()
            surface_list.append(image_surf)

    return surface_list

def import_folder_dict(path) -> dict:
    surface_dict = {}
    for folder_name, sub_folder, img_files in walk(path):
        for image in img_files:
            full_path = path + '/' + image
            image_surf = pygame.image.load(full_path).convert_alpha()
            surface_dict[image.split('.')[0]] = image_surf

    return surface_dict
