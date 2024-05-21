import pygame
from config.config import Config
from sprites.sprites import ExploreSprite, GameSprite
from sprites.spritesheets import SpriteSheet
from gameplay.battle import Lineup
import math
from gui_builders.gui import GUIBuilder, GUIDirector
from gui_builders.pickup import PickupItem 
from sprites.pokemon import TrainerPokemon
from abc import ABC, abstractmethod


class Trainer(ExploreSprite):
    """ Main player of the game; This class controls animations, states and properties of the of the the player"""
    
    def __init__(self):
        super().__init__()

        self.sheet = SpriteSheet(image_file="./assets/spritesheets/poke-trainersheet.png",
                                 json_file="./assets/spritesheets/sheet_json/trainer-walk.json")
        
        #  initial direction of the trainer; used to update animations
        self.direction = 'down'

        # threshold for the user to press, once this value exceeds the threshold, then the user can move
        self.move = 0

        # used to check if the bike state should be activated or not
        self.toggle_bike = False

        # initial state of the trainer
        self.current_state = WalkingState(self)

        # initial image and position of the player
        self.image = self.current_state.animations[self.direction][1][0]
        # self.rect = self.image.get_rect(center=ExploreSprite.get_placement(5.5, -5.5))
        self.rect = self.image.get_rect(center=ExploreSprite.get_placement(-5.5, -3.5))
# 

        # use the create mask from explore sprites which gives us access to its outline
        self.create_mask()


        # check if the use is challenged by a challenger
        self.is_challenged = None
        self.chal_remaining = 0

        self.pokemon = Lineup([])
       

        builder = GUIBuilder()
        bd = GUIDirector(builder)
        self.bag = TrainerBag(bd)
    
    def set_state(self, state) :
        self.current_state = state 

    def update(self):
        self.direction = self.current_state.direction
        self.current_state.animate()

    def stand(self):
        self.move= 0.5
        self.image = self.current_state.animations[self.direction][1][0]
    

class TrainerState(ABC):

    """ base class for all states of the trainer, these will control animations and speed of the trainer"""

    def __init__(self, trainer):
        
        #  initialize the trainer as an instance variable
        self.trainer = trainer

    @abstractmethod
    def animate(self):
        pass

    @abstractmethod
    def movement(self):
        pass

    def can_move(self, direction):

        """ this function check if the player is within the borders of the map"""
        if direction == 'up':
            return self.trainer.rect.top > Config.MAP_RECT.top 
        elif direction == 'down':
            return self.trainer.rect.bottom < Config.MAP_RECT.bottom 
        elif direction == 'left':
            return self.trainer.rect.left > Config.MAP_RECT.left 
        elif direction == 'right':
            return self.trainer.rect.right < Config.MAP_RECT.right 

    def update(self):
        self.animate()

class WalkingState(TrainerState):
    """ handle trianter's walking state """
    def __init__(self, trainer):
        super().__init__(trainer)

        self.direction = trainer.direction
        self.speed = 1

        
        self.animations = {
        'left':[self.speed,[self.trainer.sheet.parse_sheet(name='player-face-left'), 
                self.trainer.sheet.parse_sheet(name='player-walk-left1'), 
                self.trainer.sheet.parse_sheet(name='player-walk-left2')
                ]], 

        'up': [self.speed, [ self.trainer.sheet.parse_sheet(name='player-face-up'),
                self.trainer.sheet.parse_sheet(name='player-walk-up1'),
                self.trainer.sheet.parse_sheet(name='player-walk-up2')
                ]],

        'down':[self.speed,[
            self.trainer.sheet.parse_sheet(name='player-face-down'),
            self.trainer.sheet.parse_sheet(name='player-walk-down1'),
            self.trainer.sheet.parse_sheet(name='player-walk-down2')
        ]],

        'right':[self.speed,[
            self.trainer.sheet.parse_sheet(name='player-face-right'),
            self.trainer.sheet.parse_sheet(name='player-walk-right1'),
            self.trainer.sheet.parse_sheet(name='player-walk-right2')
        ]]
        }

        # update the trainer's image 
        self.trainer.image = self.animations[self.direction][1][0]
    

    def animate(self):
        
        keys = pygame.key.get_pressed()


        if keys[pygame.K_w]:
            self.direction = 'up'
            self.movement()
        elif keys[pygame.K_s]:
            self.direction = 'down'
            self.movement()
        elif keys[pygame.K_a]:
            self.direction = 'left'
            self.movement()
        elif keys[pygame.K_d]:
            self.direction = 'right'
            self.movement()
            
        # check if the trainers bag cntains shoes and switch to the running the state
        if  self.trainer.bag.has_item('run') and keys[pygame.K_LSHIFT] and not self.trainer.toggle_bike:
            self.trainer.set_state(RunningState(self.trainer))
        
        # check if trainer toggles the bike
        elif self.trainer.toggle_bike:
            self.trainer.set_state(BikeState(self.trainer))
           


    def movement(self):
        self.trainer.move += 0.1
      
        if self.trainer.move > 1.2 :
            self.trainer.image = self.animations[self.direction][1][math.floor(self.trainer.move % 3)]
            if self.direction == 'up' and self.can_move(self.direction):
                self.trainer.rect.y -= self.animations[self.direction][0]

            elif self.direction == 'down' and self.can_move(self.direction):
                self.trainer.rect.y += self.animations[self.direction][0]
            
            elif self.direction == 'left' and self.can_move(self.direction):
                 self.trainer.rect.x -= self.animations[self.direction][0]

            elif self.direction == 'right' and self.can_move(self.direction):
                 self.trainer.rect.x += self.animations[self.direction][0]

            # update the trainers mask
            self.trainer.create_mask()


class RunningState(TrainerState):
    """ handle trainer's running state"""
    def __init__(self, trainer):
        super().__init__(trainer)

        self.direction = trainer.direction
        self.speed = 2
        self.animations = {
        'left':[self.speed,[self.trainer.sheet.parse_sheet(name='player-face-left'), 
                            # self.trainer.sheet.parse_sheet(name='player-lean-left'),
                self.trainer.sheet.parse_sheet(name='player-run-left1'), 
                self.trainer.sheet.parse_sheet(name='player-run-left2')
                ]], 

        'up': [self.speed, [ self.trainer.sheet.parse_sheet(name='player-face-up'),
                self.trainer.sheet.parse_sheet(name='player-walk-up1'),
                self.trainer.sheet.parse_sheet(name='player-walk-up2')
                ]],

        'down':[self.speed,[
            self.trainer.sheet.parse_sheet(name='player-face-down'),

            self.trainer.sheet.parse_sheet(name='player-run-down1'),
            self.trainer.sheet.parse_sheet(name='player-run-down2')
        ]],

        'right':[self.speed,[
            self.trainer.sheet.parse_sheet(name='player-face-right'),
            # self.trainer.sheet.parse_sheet(name='player-lean-right'),
            self.trainer.sheet.parse_sheet(name='player-run-right1'),
            self.trainer.sheet.parse_sheet(name='player-run-right2')
        ]]
        }

    def animate(self):
        
        keys = pygame.key.get_pressed()


        if keys[pygame.K_w]:
            self.direction = 'up'
            self.movement()
        elif keys[pygame.K_s]:
            self.direction = 'down'
            self.movement()
        elif keys[pygame.K_a]:
            self.direction = 'left'
            self.movement()
        elif keys[pygame.K_d]:
            self.direction = 'right'
            self.movement() 

        if not keys[pygame.K_LSHIFT] and not self.trainer.toggle_bike:
            self.trainer.set_state(WalkingState(self.trainer))

        elif self.trainer.toggle_bike:
            self.trainer.set_state(BikeState(self.trainer))

    def movement(self):
        self.trainer.move += 0.15
        if self.trainer.move > 1.2:

            self.trainer.image = self.animations[self.direction][1][math.floor(self.trainer.move % len(self.animations[self.direction][1]))]
            
            if self.direction == 'up' and self.can_move(self.direction):
                self.trainer.rect.y -= self.animations[self.direction][0]

            elif self.direction == 'down' and self.can_move(self.direction):
                self.trainer.rect.y += self.animations[self.direction][0]
            
            elif self.direction == 'left' and self.can_move(self.direction):
                 self.trainer.rect.x -= self.animations[self.direction][0]

            elif self.direction == 'right' and self.can_move(self.direction):
                 self.trainer.rect.x += self.animations[self.direction][0]

            # update the trainers mask
            self.trainer.create_mask()


class BikeState(TrainerState):
    """ handle trainer's biking state"""
    def __init__(self, trainer):
        super().__init__(trainer)

        self.direction = trainer.direction
        self.speed = 3
        self.animations = {
        'left':[self.speed,[self.trainer.sheet.parse_sheet(name='bike-left1'), 
                self.trainer.sheet.parse_sheet(name='bike-left2'), 
                self.trainer.sheet.parse_sheet(name='bike-left3')
                ]], 

        'up': [self.speed, [ self.trainer.sheet.parse_sheet(name='bike-up2'),
                self.trainer.sheet.parse_sheet(name='bike-up2'),
                self.trainer.sheet.parse_sheet(name='bike-up3')
                ]],

        'down':[self.speed,[
            self.trainer.sheet.parse_sheet(name='bike-down1'),
            self.trainer.sheet.parse_sheet(name='bike-down2'),
            self.trainer.sheet.parse_sheet(name='bike-down3')
        ]],

        'right':[self.speed,[
            self.trainer.sheet.parse_sheet(name='bike-right1'),
            self.trainer.sheet.parse_sheet(name='bike-right2'),
            self.trainer.sheet.parse_sheet(name='bike-right3')
        ]]
        }

        self.trainer.image = self.animations[self.direction][1][0]

    def animate(self):
    
        keys = pygame.key.get_pressed()

        if keys[pygame.K_w]:
            self.direction = 'up'
            self.movement()
        elif keys[pygame.K_s]:
            self.direction = 'down'
            self.movement()
        elif keys[pygame.K_a]:
            self.direction = 'left'
            self.movement()
        elif keys[pygame.K_d]:
            self.direction = 'right'
            self.movement() 

        if not self.trainer.toggle_bike:
            self.trainer.set_state(WalkingState(self.trainer))

    def movement(self):
        self.trainer.move += 0.15
        
        if self.trainer.move > 1.2:
            self.trainer.image = self.animations[self.direction][1][math.floor(self.trainer.move % len(self.animations[self.direction][1]))]
            
            if self.direction == 'up' and self.can_move(self.direction):
                self.trainer.rect.y -= self.animations[self.direction][0]

            elif self.direction == 'down' and self.can_move(self.direction):
                self.trainer.rect.y += self.animations[self.direction][0]
            
            elif self.direction == 'left' and self.can_move(self.direction):
                 self.trainer.rect.x -= self.animations[self.direction][0]

            elif self.direction == 'right' and self.can_move(self.direction):
                 self.trainer.rect.x += self.animations[self.direction][0]

            # update the trainers mask
            self.trainer.create_mask()

class TrainerBag(GameSprite):
    """ handle the creation of a bag that is related to the trainer. The bag stores items which can
    alter the trainer's states or any other items in future"""

    def __init__(self, bd):
        super().__init__()
        self.bag_icon = bd.create_bag(r'./assets/images/bag.png')
        w, h = self.bag_icon.surface.get_size()
        self.bag_icon.surface = pygame.transform.scale(self.bag_icon.surface, (w * Config.WIDTH_SCALE, h * Config.HEIGHT_SCALE))
        self.items = []# store for all items in the bag
        self.show = False # flag if the bag is displayed or not
               
    def toggle_show(self):
        """toggle if the bag is displayed or not"""

        if self.show:
            self.show = False
        else:
            self.show = True
            
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

        