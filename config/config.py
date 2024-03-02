import pygame
import sys
import math
from typing import Tuple
class Config:
    """ Config Class to set up the game"""
    DEFAULT_SCREEN_WIDTH = 700  # window width
    DEFAULT_SCREEN_HEIGHT = 500 # window height

    # browser window size to keep frame
    BROWSER_SCREEN_WIDTH = 1024 # browser window width
    BROWSER_SCREEN_HEIGHT = 600 # browser window height

     # TILE DATA (from the Tiled map editor)
    NUM_TILES_X = 30 # the number of tiles in the x direction
    NUM_TILES_Y = 20 # the number of tiles in the y direction
    
    IS_WEB = sys.platform == "emscripten" # check if the platform is web

    if IS_WEB:
        SCREEN_WIDTH = BROWSER_SCREEN_WIDTH
        SCREEN_HEIGHT = BROWSER_SCREEN_HEIGHT
    else:
        SCREEN_WIDTH = DEFAULT_SCREEN_WIDTH
        SCREEN_HEIGHT = DEFAULT_SCREEN_HEIGHT

    WIDTH_SCALE = SCREEN_WIDTH/DEFAULT_SCREEN_WIDTH # width scale
    HEIGHT_SCALE = SCREEN_HEIGHT/DEFAULT_SCREEN_HEIGHT# height scale
    CENTER = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2) # center of the screen

    if IS_WEB:
        TILE_WIDTH = math.floor(32 * WIDTH_SCALE)
        TILE_HEIGHT = math.floor(32 * HEIGHT_SCALE)
        SPRITE_SCALE = 1.5 * WIDTH_SCALE, 1.5 * HEIGHT_SCALE # scale of the sprite
    else:
        TILE_WIDTH = 32
        TILE_HEIGHT = 32
        SPRITE_SCALE = 1.5, 1.5


    MAP_W = NUM_TILES_X * TILE_WIDTH # the entire map width
    MAP_H = NUM_TILES_Y * TILE_HEIGHT # the entire map width
    TILE_X_SPACING = MAP_W//NUM_TILES_X # the width of each tile
    TILE_Y_SPACING = MAP_H//NUM_TILES_Y # the height of each tile
    
    # reduce by 10 to avoid walk overflow
    MAP_RECT = pygame.Rect(0, 0, MAP_W-10, MAP_H-10) # walkable area

    # COLOR CODES
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    YELLOW = (255, 255, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    PURPLE = (109, 9, 238)

    MAX_POKEMON = 900  # max number of pokemon to search through
    POKEMON_COUNT = 7   # number of pokemon for the trainer

    MAX_CHAL_COUNT = 3 # max number of pokemon the challenger can have

    POKEMON_HP = 200 # max health points for the pokemon
    TRAINER_MIN_DAMAGE = 50
    TRAINER_MAX_DAMAGE = 80
    CHAL_MIN_DAMAGE = 30
    CHAL_MAX_DAMAGE = 60
    
    FRAMERATE =  60 # default frame rate

    @staticmethod
    def make_fonts(font_type='default'):
        """ this funciton is used to initialize fonts. 
        This can only be done in the file where pygame is initialized
        so this function just maintains a dict of some fonts to be used throughout the game"""


        fonts = {
            "default": {
                "file": r"./assets/fonts/poke_font.ttf",
                "sizes":{
                "small": 8,
                "med-small": 10,
                "med": 13,
                "large": 20,
                'xl': 25
                    }
            },
            "solid": {
                "file": r"./assets/fonts/poke_solid.ttf",
                "sizes":{
                "small": 12,
                "med-small": 15,
                "med": 19,
                "large": 23,
                'xl': 28

                    }
                }
            }
        
        if font_type not in fonts:
            font_type = 'default'

        font = fonts[font_type]
        font_file = font['file']
        sizes = font["sizes"]

        output_fonts = {size: pygame.font.Font(font_file, value) for size, value in sizes.items()}
        return output_fonts
    

    @staticmethod
    def scaler(w, h) -> Tuple[int, int]:
        """ Scales sprites, tiles etc based on screen size """
        return Config.WIDTH_SCALE * w, Config.HEIGHT_SCALE * h