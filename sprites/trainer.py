import pygame
from config.config import Config
from sprites.sprites import ExploreSprite, GameSprite
from sprites.spritesheets import SpriteSheet
from gameplay.battle import Lineup
import math
from gui_builders.gui import GUIBuilder, GUIDirector
from gui_builders.pickup import PickupItem 
from sprites.pokemon import TrainerPokemon
from abc import ABC
from enum import StrEnum 


class TrainerStates(StrEnum):
    """ Trainer states for the trainer class"""
    WALKING = 'walking'
    RUNNING = 'running'
    BIKING = 'biking'

class TrainerDirections(StrEnum):
    """ Trainer directions for the trainer class"""
    UP = 'up'
    DOWN = 'down'
    LEFT = 'left'
    RIGHT = 'right'

class SpeedAnimation:

    def __init__(self, spritesheet: SpriteSheet, speed: int, animations: list[str]):
        """ speed is the speed of the animation and animations is a list of the names of animations for the trainer defined in json file"""
        self.speed = speed
        self.animations =[ spritesheet.parse_sheet(name=animation) for animation in animations ]

class Trainer(ExploreSprite):
    """ Main player of the game; This class controls animations, states and properties of the of the the player"""
    
    def __init__(self):
        super().__init__()

        self.sheet = SpriteSheet(image_file="./assets/spritesheets/poke-trainersheet.png",
                                 json_file="./assets/spritesheets/sheet_json/trainer-moves.json"
                                )
        
        #  initial direction of the trainer; used to update animations
        self.direction = TrainerDirections.DOWN

        # threshold for the user to press, once this value exceeds the threshold, then the user can move
        self.move = 0

        # used to check if the bike state should be activated or not
        self.toggle_bike = False

        # initial state of the trainer
        self.current_state = WalkingState(self)

        # initial image and position of the player
        self.image = self.current_state.animations[self.direction].animations[0]
        self.rect = self.image.get_rect(center=ExploreSprite.get_placement(5.5, -5.5))


        # use the create mask from explore sprites which gives us access to its outline
        self.create_mask()

        # check if the use is challenged by a challenger
        self.is_challenged = None
        self.chal_remaining = 0

        self.pokemon = Lineup([])

        builder = GUIBuilder()
        bd = GUIDirector(builder)
        self.bag = TrainerBag(bd)
    
    def set_state(self, state: 'TrainerState') :
        self.current_state = state 

    def update(self):
        self.direction = self.current_state.direction
        self.current_state.animate()

    def stand(self):
        self.move = 0.5
        self.image = self.current_state.animations[self.direction].animations[0]
    

class TrainerState(ABC):

    """ base class for all states of the trainer, these will control animations and speed of the trainer"""
    MOVE_THRESHOLD = 1.2
    def __init__(self, trainer: Trainer, animation_swap_speed: int):
        
        #  initialize the trainer as an instance variable
        self.trainer = trainer
        self.animation_swap_speed = animation_swap_speed

    # @abstractmethod
    def animate(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_w]:
            self.direction = TrainerDirections.UP
        elif keys[pygame.K_s]:
            self.direction = TrainerDirections.DOWN
        elif keys[pygame.K_a]:
            self.direction = TrainerDirections.LEFT
        elif keys[pygame.K_d]:
            self.direction = TrainerDirections.RIGHT

        if any((keys[pygame.K_w], keys[pygame.K_s], keys[pygame.K_a], keys[pygame.K_d])):
            self.movement(self.animation_swap_speed)

        return keys


    def can_move(self, direction: TrainerDirections):

        """ this function check if the player is within the borders of the map"""
        match direction:
            case TrainerDirections.UP:
                return self.trainer.rect.top > Config.MAP_RECT.top
            case TrainerDirections.DOWN:
                return self.trainer.rect.bottom < Config.MAP_RECT.bottom
            case TrainerDirections.LEFT:
                return self.trainer.rect.left > Config.MAP_RECT.left
            case TrainerDirections.RIGHT:
                return self.trainer.rect.right < Config.MAP_RECT.right
            
    def movement(self, animation_swap_speed):

        self.trainer.move += animation_swap_speed
        num_animations = len(self.trainer.current_state.animations[self.direction].animations)
        if self.trainer.move > self.MOVE_THRESHOLD:
            self.trainer.image = self.animations[self.direction].animations[math.floor(self.trainer.move % num_animations)]
            
            if self.can_move(self.direction):
                match self.direction:
                    case TrainerDirections.UP:
                        self.trainer.rect.y -= self.animations[self.direction].speed
                    case TrainerDirections.DOWN:
                        self.trainer.rect.y += self.animations[self.direction].speed
                    case TrainerDirections.LEFT:
                        self.trainer.rect.x -= self.animations[self.direction].speed
                    case TrainerDirections.RIGHT:
                        self.trainer.rect.x += self.animations[self.direction].speed
            
            # reset the move threshold to avoid extreme values
            if self.trainer.move > self.MOVE_THRESHOLD * num_animations :
                self.trainer.move = self.MOVE_THRESHOLD + 0.1
            self.trainer.create_mask()
    
    def update(self):
        self.animate()

class WalkingState(TrainerState):
    """ handle trianter's walking state """
    def __init__(self, trainer):
        super().__init__(trainer, 0.1)

        self.direction = trainer.direction
        self.speed = 1

        self.animations = {
            TrainerDirections.LEFT:SpeedAnimation(self.trainer.sheet,self.speed, ['player-face-left', 'player-walk-left1', 'player-walk-left2']),
            TrainerDirections.UP: SpeedAnimation(self.trainer.sheet,self.speed, ['player-face-up', 'player-walk-up1', 'player-walk-up2']),
            TrainerDirections.DOWN: SpeedAnimation(self.trainer.sheet,self.speed, ['player-face-down', 'player-walk-down1', 'player-walk-down2']),
            TrainerDirections.RIGHT: SpeedAnimation(self.trainer.sheet,self.speed, ['player-face-right', 'player-walk-right1', 'player-walk-right2'])
        }

        # update the trainer's image  to the first animation in the correct direction
        self.trainer.image = self.animations[self.direction].animations[0]
    

    def animate(self):
        keys = super().animate()

        # check if the trainers bag cntains shoes and switch to the running the state
        if  self.trainer.bag.has_item('run') and keys[pygame.K_LSHIFT] and not self.trainer.toggle_bike:
            self.trainer.set_state(RunningState(self.trainer))
        
        # check if trainer toggles the bike
        elif self.trainer.toggle_bike:
            self.trainer.set_state(BikeState(self.trainer))


class RunningState(TrainerState):
    """ handle trainer's running state"""
    def __init__(self, trainer):
        super().__init__(trainer, 0.1)

        self.direction = trainer.direction
        self.speed = 2
        self.animations = {
            TrainerDirections.LEFT:SpeedAnimation(self.trainer.sheet, self.speed, ['player-face-left', 'player-run-left1', 'player-run-left2']),
            TrainerDirections.UP: SpeedAnimation(self.trainer.sheet, self.speed, ['player-face-up', 'player-walk-up1', 'player-walk-up2']),
            TrainerDirections.DOWN: SpeedAnimation(self.trainer.sheet, self.speed, ['player-face-down', 'player-run-down1', 'player-run-down2']),
            TrainerDirections.RIGHT: SpeedAnimation(self.trainer.sheet, self.speed, ['player-face-right', 'player-run-right1', 'player-run-right2'])
        }

    def animate(self):
        
        keys = super().animate()

        if not keys[pygame.K_LSHIFT] and not self.trainer.toggle_bike:
            self.trainer.set_state(WalkingState(self.trainer))

        elif self.trainer.toggle_bike:
            self.trainer.set_state(BikeState(self.trainer))


class BikeState(TrainerState):
    """ handle trainer's biking state"""
    def __init__(self, trainer):
        super().__init__(trainer, 0.15)
        self.direction = trainer.direction
        self.speed = 3
        self.animations = {
            TrainerDirections.LEFT:SpeedAnimation(self.trainer.sheet,3, ['bike-left1', 'bike-left2', 'bike-left3']),
            TrainerDirections.UP: SpeedAnimation(self.trainer.sheet,3, ['bike-up2', 'bike-up2', 'bike-up3']),
            TrainerDirections.DOWN: SpeedAnimation(self.trainer.sheet,3, ['bike-down1', 'bike-down2', 'bike-down3']),
            TrainerDirections.RIGHT: SpeedAnimation(self.trainer.sheet,3, ['bike-right1', 'bike-right2', 'bike-right3'])
        }

        self.trainer.image = self.animations[self.direction].animations[0]

    def animate(self):

        super().animate()

        if not self.trainer.toggle_bike:
            self.trainer.set_state(WalkingState(self.trainer))

class TestShoes():
    """ test shoes for the trainer to run faster"""
    def __init__(self):
        self.name = 'run'

class TestBike:
    """ test bike for the trainer to bike faster"""
    def __init__(self):
        self.name = 'bike'
        

class TrainerBag(GameSprite):
    """ handle the creation of a bag that is related to the trainer. The bag stores items which can
    alter the trainer's states or any other items in future"""

    def __init__(self, bd):
        super().__init__()
        self.bag_icon = bd.create_bag(r'./assets/images/bag.png')
        w, h = self.bag_icon.surface.get_size()
        self.bag_icon.surface = pygame.transform.scale(self.bag_icon.surface, Config.scaler(w, h))
        self.items = []# store for all items in the bag
        self.show = False # flag if the bag is displayed or not

    def toggle_show(self):
        """toggle if the bag is displayed or not"""
        self.show = not self.show
            
    def has_item(self, check_item: str) -> bool:
        """ checks if an item is in the bag, these are of type pickup item"""
       
        return any(item.name == check_item for item in self.items)
    
    def add_item(self, item: PickupItem):
        """ add an item to the bag"""
        self.items.append(item)


class TrainerMediator:
    """ Trainer Mediator to access and set the trainer specific properties of the the current trainer instance, 
    since the game can be reset, a new instance of the trainer is made. Properties from inheritance can still be accessed otherwise"""

    def __init__(self):
        self.__trainer = None

    def notify_set(self, sender):
        """ create a new trainer inscance, only classes with the _ALLOWED_TRAINER_SET flag can
        have their instances changed by this mediator class create this"""
        if hasattr(sender, '_ALLOWED_TRAINER_SET') and sender._ALLOWED_TRAINER_SET:
            self.__trainer = Trainer()
        
    def notify(self, message):
        """ trainer data accessor and setters"""
    
        if message=='get':
            # conrol the access to the current trainer instance
            if not self.__trainer:
                print('trainer created for testing') # should only be when testing otherwise wrong instance of trainer is being accessed
                self.__trainer = Trainer()
            return self.__trainer

        elif message=='stand':
            # make the trainer stop its current animation and reset it to the first animation in the correct direction
            self.__trainer.stand()

        elif message=='is_challenged':
            # get the challenger who is currently challenging the trainer
            return self.__trainer.is_challenged
        
        elif message == "get_chals":
            # get the number of challengers remaining to be defeated to ein
            return self.__trainer.chal_remaining
        
        elif message == "reduce_chals":
            #  reduce the number of challengers when a battle is won
            self.__trainer.chal_remaining -= 1
        
    def notify_bag(self, message, data=None):
        """ trainer bag accessors and settors """
        
        if message=='toggle_bike':
            # togglr the bike (secondary check to make sure the trainer has the bike)
            if self.__trainer.bag.has_item('bike'):
                self.__trainer.toggle_bike = not self.__trainer.toggle_bike
                if not self.__trainer.toggle_bike: self.__trainer.stand()

        elif message == "toggle_bag":
            # toggle bag to show or not show
            self.__trainer.bag.toggle_show()

        elif message == 'has_item' and data:
            # check if the trainer ahs an item
            return self.__trainer.bag.has_item(data)
        
        elif message == 'add_item' and data:
            # add an item to the trainers bag
            return self.__trainer.bag.add_item(data)
        
    def notify_pokemon(self, message, data=None):
        """ trainer pokemoon accessors and setters"""

        if message == 'add_pokemon':
            # add a pokemon to the traineers lineup
            self.__trainer.pokemon.add(TrainerPokemon(data))

        elif message == 'get_single':
            #  get one pokemn, the lead of the lineup
            return self.__trainer.pokemon.get_current()
        
        elif message == 'get_all':
            #  get all the pokemon in the lineup
            return self.__trainer.pokemon
        
        elif message == 'get_mediator':
            #  get the current mediator for a battle
            return self.__trainer.pokemon.mediator
        
        elif message == 'set_mediator' and data:
            # set the mediator for the current battle
            self.__trainer.pokemon.mediator = data

        