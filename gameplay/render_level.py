from abc import ABC, abstractmethod
from config.config import Config
from sprites.sprites import ExploreSprite
from sprites.challenger import Challenger
from gameplay.environments import GameEnvironment, Layer, YSortLayer
from gui_builders.pickup import ItemDirector
from gameplay.camera import Camera
from sprites.professor_oak import OakState
from typing import Tuple

class LevelRenderer(ABC):
    """ base class for level renderers"""
    def __init__(self, 
                 backdrop_renderer : GameEnvironment, 
                backdrop_file : str):
    
        self.backdrop = backdrop_renderer(backdrop_file)

    @abstractmethod
    def render_environment() -> Tuple:
        pass
        
class WelcomeRenderer(LevelRenderer):
    """ Concrete welcomer renderer for professor oak"""
    def __init__(self, backdrop_renderer, backdrop_file):
        super().__init__(backdrop_renderer, backdrop_file)
        
    def render_environment(self):
        return self.backdrop.create_env(resize=(Config.scaler(2.5, 1.5))) #render backdrop image
    
    @property
    def controls(self):
       return {
           ' [ SPACE ]': 'Next Page',
           ' N ': 'Skip to Choose'
        }


class ChooseRenderer(LevelRenderer):
    """ render choose backdrop"""

    def __init__(self, backdrop_renderer : GameEnvironment, backdrop_file : str):
        super().__init__(backdrop_renderer, backdrop_file)

    def render_environment(self):

        return self.backdrop.create_env()
    
    @property
    def controls(self):
       return {
           ' [ SPACE ]': 'Next Page',
           ' N ': 'Skip to Choose'
        }
    
class ExploreLevelRenderer(LevelRenderer):
    """ base class for explore levels"""
    def __init__(self, 
                camera: Camera, 
                backdrop_renderer : GameEnvironment, 
                backdrop_file : str, 
                baselayer: Layer,
                ysortlayer: YSortLayer,
                item_creator: ItemDirector, 
                ):

       # create the camera object
        self.camera = camera
        self.backdrop = backdrop_renderer(backdrop_file)
        self.baselayer = baselayer
        self.ysortlayer = ysortlayer
        self.item_creator = item_creator

    
class HomeTownRenderer(ExploreLevelRenderer):
    """ Render and set up Hometown level"""

    def __init__(self, 
                camera: Camera, 
                backdrop_renderer : GameEnvironment, 
                backdrop_file : str, 
                baselayer: Layer,
                ysortlayer: YSortLayer,
                item_creator: ItemDirector, 
                ):
        
        super().__init__(camera,
                backdrop_renderer,
                backdrop_file,
                baselayer, 
                ysortlayer,
                item_creator)

    def render_environment(self) -> Tuple[Camera, YSortLayer]:

        hometown = self.backdrop # load the tmx file provided
        hometown_base_grass = hometown.create_env(layers=['base','grass'], layer_group=self.baselayer)     # create the base layers
        self.hometown_ysort = hometown.create_env(layers=['houses', 'extra'], layer_group=self.ysortlayer)  # create the ysorted layers and addthem to the ysort group 

        # create challengers: this could be abstacted to a builder or even prototype in the future
        self.challengers = self._create_challengers()
        
        items = self._create_items()

        # add them to the y sort layer 
        self.hometown_ysort.add(*items, *self.challengers)

        # use the cam addgroup to keep track of the groups added
        self.camera.add_group(hometown_base_grass, self.hometown_ysort)

        return self.camera, self.hometown_ysort 
    
    def _create_items(self):

        items = [
        self.item_creator.create_running_shoes(),
        self.item_creator.create_bike()
        ]

        return items
    
    def _create_challengers(self):

        # { facing_direction: (x, y) }
        challenger_data = {
            'up': ExploreSprite.get_placement(7, -1),
            'down': ExploreSprite.get_placement(-3, 5), 
            'left': ExploreSprite.get_placement(-9, 9), 
            'right': ExploreSprite.get_placement(3, 3) 
        }
        return Challenger.inititialize_challengers(challenger_data)

class LoadingRenderer(LevelRenderer):
    """ render loading backdrop"""

    def __init__(self, 
                backdrop_renderer : GameEnvironment, 
                backdrop_file : str):
        super().__init__(backdrop_renderer, backdrop_file)

    def render_environment(self):
        return self.backdrop.create_env() #render backdrop image
    
class ControlRenderer(LevelRenderer):
    """ render controls backdrop"""
    def __init__(self, 
                backdrop_renderer : GameEnvironment, 
                backdrop_file : str):

        super().__init__(backdrop_renderer, backdrop_file)

    def render_environment(self):

        return self.backdrop.create_env() #render backdrop image


class BattleRenderer(LevelRenderer):
    """ render battle backdrop"""

    def __init__(self, 
                backdrop_renderer : GameEnvironment, 
                backdrop_file : str, 
                lose_state : OakState ):
        
        super().__init__(backdrop_renderer, backdrop_file)

        # define professor for lose state
        self.lose_state = lose_state
    

    def render_environment(self):
        return self.backdrop.create_env() #render backdrop image
    


   
