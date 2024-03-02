
from config.config import Config
import pygame
from sprites.sprites import ExploreSprite


class PickupItem(ExploreSprite):
    """ items that can be picked up i.e. added to the bag"""
    def __init__(self, name, image_path, pos, scale):
        super().__init__()
        
        self.name = name
        self.image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(self.image, scale)
        self.rect = self.image.get_rect(center=(pos))

class ItemBuilder:
    """builds items that can be picked up. each item has a name that is 
    used as a unique identifier"""
    def __init__(self):
        self.name = None
        self.image_path = None
        self.pos = None
        self.scale = Config.scaler(32, 32)

    def with_name(self, name):
        self.name = name
        return self

    def with_image_path(self, image_path):
        self.image_path = image_path
        return self

    def with_pos(self, pos):
        self.pos = pos
        return self

    def with_scale(self, scale):
        self.scale = scale
        return self

    def build(self):
        
        item = PickupItem(
            self.name,
            self.image_path,
            self.pos,
            self.scale
        )
        return item
    
class ItemDirector:

    def __init__(self, builder):
        self.builder = builder
        
    def create_running_shoes(self):
        """create the running shoes item"""
        return  self.builder.with_name('run').with_image_path(r'./assets/images/running_shoes.png').with_pos(ExploreSprite.get_placement(5.5, 1)).build()
    
    def create_bike(self):
        """create the bike item"""
        return  self.builder.with_name('bike').with_image_path(r'./assets/images/bike.png' ).with_pos(ExploreSprite.get_placement(-5, -1.5)).build()
