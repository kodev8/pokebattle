import pygame
import json 
from config.config import Config

class SpriteSheet:
    """Spritesheet allows sprites to be animated without needing to load new files
     on each animation """
    
    def __init__(self, image_file, json_file):
        self.filename = image_file # file with images
        self.sheet = pygame.image.load(image_file).convert_alpha()
        
        with open(json_file) as f:
            # load the json with the coordinates of each animation
            self.animations = json.load(f)
    
    def get_sprite(self, x, y, w, h, scale) -> pygame.Surface:
        
        """displayes the sprite on a pyagme surface"""
        # empty surface
        sprite = pygame.Surface((w, h))

        # render everything except this color
        sprite.set_colorkey((255, 255, 255))

        # render image on empty surface
        sprite.blit(self.sheet, (0, 0), (x, y , w, h))
        
        # return the scaled image
        return  pygame.transform.scale(sprite, (w*scale[0], h*scale[1]))
    
    def parse_sheet(self, name, scale=Config.SPRITE_SCALE, format=None) -> pygame.Surface:
        
        """ gets the sprites coordinates from the json file and returns
        the sprite on a new surface"""
        
        coords = self.animations['frames'][name]['frame']

        if format:
            wratio = format[0]/coords['w']
            hratio = format[1]/coords['h']
            scale = (wratio * Config.SPRITE_SCALE[0], hratio * Config.SPRITE_SCALE[1])
            
        return self.get_sprite(coords['x'], coords['y'], coords['w'], coords['h'], scale)