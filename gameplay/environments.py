import pygame
from sprites.sprites import Tile
from pytmx.util_pygame import load_pygame
from config.config import Config
from abc import ABC, abstractmethod
from typing import Tuple
    
class Layer(pygame.sprite.Group):
    """ base class for a concrete layer
        this will be used to distingush a from a layer on wich collisions can coccur
        this a safe layer is a layer where the player can walk freely without collisons
        or without needing to y sort the elements on the screen"""
    
    def __init__(self):
        super().__init__()


class YSortLayer(Layer):
    """
    Layer where there are objects where objects must be ysorted
    i.e. depending on the items position on the screen, it is rendered in terms of the lowest
    y coordinate first.
    """

    def __init__(self):
        super().__init__()

    # this function returns the sprites of the ysort group
    def get_sprites(self):
        return self.sprites()
    
class LayerDecorator(ABC, Layer):
    """Decorator interface for layers."""
    @abstractmethod
    def get_sprites(self):
        pass

class DecoratorNegativeFilter(LayerDecorator):
    """Decorator for a layer where object do not meet a given criteria.
    It is a decoractor, in this case, for the y sort layer group.
    """

    def __init__(self, layer):
        self.layer = layer

    def get_sprites(self, check):
        return [sprite for sprite in self.layer.get_sprites() if not isinstance(sprite, check)]


class DecoratorPositiveFilter(LayerDecorator):
    """Decorator for a layer where object do meet a given criteria.
    It is a decoractor, in this case, for the y sort layer group.
    """

    def __init__(self, layer):
        self.layer = layer

    def get_sprites(self, check):
        return [sprite for sprite in self.layer.get_sprites() if isinstance(sprite, check)]


class FlyweightTile:
    """ Flyweight class to store unique images"""
    def __init__(self, image):
        self.image = image
        
class FlyweightTileFactory:
    """ Fly weight factory returns fly weights if they already exist, other wise a new
    one is created"""
    def __init__(self):
        self._tiles = {}

    def get_fly_weight(self, image):

        # the id is the image hash as explained GameMapTSX
        id = image.__hash__()
        if  id not in self._tiles:
            self._tiles[id] = FlyweightTile(image) 
        return self._tiles[id]

class GameEnvironment(ABC):

    # base class for creating a new game environment
    def __init__(self, filename):

        self.filename = filename
        
    @abstractmethod
    def create_env(self):
        pass


class GameMapTSX(GameEnvironment):
    """ laod environment files from a tmx file"""

    def __init__(self, filename):
        super().__init__(filename)
        # we use pytmx to load the information about tiles in a tmx file
        # definae a flyweught factory for generating tiles
        self.flyweight_factory = FlyweightTileFactory()

    def create_env(self, layers: list, layer_group: Layer) -> Layer:
        """ this function servers to create the necessaary tiles and objects required
            for a Game environment *this version sets up thos environments using a tmx file"""
        
        # In tiled, there are separate layers which can be visible or hidden. Depending on a level, layers can be hidden etc.
        # Here, to create a new level, the visible layers are iterated through to generate the map

        self.map = load_pygame(self.filename)

        for layer in self.map.visible_layers:
            
            # a layer is checked if it has data to ensure that is is not already empty
            # and check if the layer name is passed within the allowed list of layers (passed as an argument)
            if hasattr(layer, 'data') and layer.name in layers:
               
                
                # for each layer, get the tiles associated with that layer
                for x, y, image in layer.tiles(): # tile is a tuple of x position, y position and the image on the tile
                    
                    # after some testing, I found that the tile's image are in fact hashable. 
                    # hence the tile's image can be used as their shared state 
                    # since tiles of the same image return the same hash, the image is thus used as the intrinsic state
                    # and the x and y position is the extrinsic state

                    tile_image = self.flyweight_factory.get_fly_weight(image).image


                    # the x and y values are then used to create tile objects from the flyweight image created
                    # they are multiplied to give us the width and height which would be used in the Tile object
                    # correctly display the tile
                    pos = x * Config.TILE_SIZE, y * Config.TILE_SIZE

                    # add the tile to it's respective group, this dependency is injected to decouple the tile from the layer
                    layer_group.add(Tile(pos, tile_image))
               
        return layer_group
        
class GameMapBackDrop(GameEnvironment):
    def __init__(self, filename):
        super().__init__(filename)
        
    def create_env(self, resize=None) -> Tuple[pygame.Surface, Tuple[int, int]]:
        
        """ this function servers to create the necessaary tiles and objects required
            for a Game environment *this version sets up thos environments using an image file"""
        
        backdrop = pygame.image.load(self.filename).convert_alpha() # load the image
       
        # get its height and width
        backdrop_w = backdrop.get_width() 
        backdrop_h = backdrop.get_height()
        
        # get the screen ratios provided if necessary. 
        # This is necessary to render the background as initended, and not using the items width or height
        w_ratio = Config.SCREEN_WIDTH/backdrop_w if not resize else resize[0]
        h_ratio = Config.SCREEN_HEIGHT/backdrop_h if not resize else resize[1]

        # resize images if necessray 
        scaled_backdrop = pygame.transform.scale(backdrop, (backdrop_w* w_ratio, backdrop_h*h_ratio))
        image_rect = scaled_backdrop.get_rect(center=Config.CENTER)

        # place the image on the screen
        return scaled_backdrop, image_rect