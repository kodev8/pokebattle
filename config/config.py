import pygame
class Config:
    """ Config Class to set up the game"""
    SCREEN_WIDTH = 700  # window width
    SCREEN_HEIGHT = 500 # window height
    CENTER = (SCREEN_WIDTH/2, SCREEN_HEIGHT/2) # the center of the window
    
    SCALE = 1.75 # the default scaling value
    TILE_SIZE = 32 # the defult tile size, used in Tiled to create the map
    SPRITE_SIZE = (96 * SCALE, 96 * SCALE) # default trainer size
    MAP_W = 30 * TILE_SIZE # the entire map height
    MAP_H = 20 * TILE_SIZE-10 # the entire map width
    MAP_RECT = pygame.Rect(0, 0, MAP_W, MAP_H) # a rectangle formed from the resulting map width

    # COLOR CODES
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    YELLOW = (255, 255, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)

    MAX_POKEMON = 900  # max number of pokemon to search through
    POKEMON_COUNT = 2   # number of pokemon for the trainer
    MAX_CHAL_COUNT = 1 # max number of pokemon the challenger can have
    
    FRAMERATE =  60 # default frame rate

    ERROR_POS = (15, CENTER[1]-60)

    @staticmethod
    def make_fonts(font_type='default'):
        """ this funciton is used to initialize fonts. 
        This can only be done in the file where pygame is initialized
        so this function just maintains a dict of some fonts to be used throughout the game"""


        fonts = {
            "default": {
                "file": r"assets\fonts\poke_font.ttf",
                "sizes":{
                "small": 8,
                "med-small": 10,
                "med": 13,
                "large": 20,
                'xl': 25
                    }
            },
            "solid": {
                "file": r"assets\fonts\poke_solid.ttf",
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