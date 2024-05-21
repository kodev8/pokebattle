
# Pokemon Sprites
from sprites.sprites import GameSprite  
import pygame
import random
import io     
from config.config import Config 
from abc import ABC, abstractmethod

class AbstractPokemon(ABC):
    """Abstract base class for pokemon interface"""

    @abstractmethod
    def float_in_out(self):
        pass

    @abstractmethod
    def attack():
        pass

    @abstractmethod
    def initialize_for_fight(self):
        pass

    @abstractmethod
    def show_elements(self):
        pass

class Pokemon(GameSprite, ABC):

    """base class for pokemon """
    def __init__(self, poke_info, mediator=None):
        
        super().__init__()

        self.mediator = mediator # mediator to handle battles
        self.name = poke_info['name'] # name fetched from api
        self.moves = poke_info['moves'] # fetched moves from api
    
        self.float_in_pos = 200 # default position to float in when challenging
        self.hp = 200 # default hp when starting a bettle

        self.off_screen_pos = -100, Config.SCREEN_HEIGHT-30 # default position of the screen to float in from or float out to if defeated
        self.gui_elements = [] # this will be all the elements to rendered for a poekmon when battling

        # pokemon state flags
        self.states = {
            'ready':False, #in the ready position, (done floating in)
            'fainted':False, # has been defeated
            'reduce_health':-1, # if the pokemon has been attacked, this will be > 0 and the hp with be reduced accordingly
            'attack':False # if the pokemon is attacking
        }

    def float_in_out(self, direction, speed, out):

        """ handles floating the pokemon on and off the screen and updates their internal state accordingly"""
        if self.gui_elements:

            # float the pokemon in or out based on the out flag, and update it's fainted or ready state
            pos = self.off_screen_pos[0] if out else self.float_in_pos
            poke_state = 'fainted' if out else 'ready'

            # handle floating left and right and updating the the state flags value once done
            if direction == 'right':
                if self.rect.centerx < pos:
                    self.rect.centerx += speed
                    self.states[poke_state] = False

                else:
                    self.states[poke_state] = True
                
            elif direction == 'left':
              
                if self.rect.centerx > pos:
                    self.rect.centerx -= speed
                    self.states[poke_state] = False

                else:
                    self.states[poke_state] =  True

    def initialize_for_fight(self):
        pass

    def show_elements(self, screen, direction, bd, out = False):
        """ shows gui element associated with  the pokemon, moves, name level health."""
        if self.gui_elements:
            if not self.states['ready']:
                self.float_in_out(direction, 5, False)
            else:
                self.float_in_out(direction, 10, out)

            if self.states['ready']:
                
                # updates the health bar based on a pokemons current health
                health_bar = bd.create_pokemon_health_bar(self.hp)[1]
                self.gui_elements[-1][0] = health_bar
                
                for e in self.gui_elements:
                    e[0].display(screen, e[1])

        screen.blit(self.image, self.rect)

class Attack:
    """class for an attack to keep track of it's name and power"""
    def __init__(self, name: str, power: int):
        self.name = name
        self.power = power
        
class TrainerPokemon(Pokemon, AbstractPokemon):
    """ class for trainer pokemon"""
    def __init__(self, poke_info, mediator=None):

        super().__init__(poke_info, mediator)

        # get the back image and trasnform it
         # get the back image and trasnform it
        if type(poke_info['back']) == bytes:
            self.image = pygame.image.load(io.BytesIO(poke_info['back']))
        else:
            self.image = pygame.image.load(poke_info['back'])

        self.image = pygame.transform.scale(self.image, (350 * Config.WIDTH_SCALE,350 * Config.HEIGHT_SCALE))
        # create a list of all moves and assign a randome power value by choosing for random moves
        self.moves = [Attack(move['move']['name'] ,random.randint(40, 80)) for 
                      move in random.sample(self.moves, 4)]

    def initialize_for_fight(self, bd):
        """ create the gui elements and set the states for all pokemon before a battle"""
        
        # redefine states and position for a new fight
        self.states = {
            'ready':False,
            'fainted':False,
            'reduce_health':-1,
            'attack':False
        }
        self.rect = self.image.get_rect(midbottom=(self.off_screen_pos))

        # define and place all elements on the scrren accordingling and 
        # add them to the gui elements to ensure they are displayed in the right order (z value)
        bottom_corner = Config.SCREEN_WIDTH/2, Config.SCREEN_HEIGHT *2/3
        
        info_layer = bd.create_pokemon_info_tile('Lv. 100', self.name)
        info_layer_pos = (bottom_corner[0],
                        bottom_corner[1] - 10 - info_layer.surface.get_height())

        health_bar = bd.create_pokemon_health_bar(self.hp)
        bar_outline_pos = (bottom_corner[0] +20 ,
                            bottom_corner[1] + 30 - info_layer.surface.get_height())
        
        bar_hp_pos = bar_outline_pos[0]+2, bar_outline_pos[1]+2

        for index, move in enumerate(self.moves):
            move_tile = bd.create_move_tile(f"{move.name} [ {index+1} ]")
            self.gui_elements.append([move_tile, (index % 2 * move_tile.surface.get_width() +bottom_corner[0], 
                                                index // 2 * move_tile.surface.get_height()+bottom_corner[1])])

        self.gui_elements.append([info_layer, info_layer_pos])
        self.gui_elements.append([health_bar[0], bar_outline_pos])
        self.gui_elements.append([health_bar[1], bar_hp_pos])  # added list last so we know the index of the health bar so it can be updated

    def attack(self, mediator, control):
        """ send an attack to the relevant mediator"""
        mediator.send_attack('trainer', self.moves[control-1])
 
class OtherPokemon(Pokemon, AbstractPokemon):
    """ class for challenger pokemon"""

    def __init__(self, poke_info, mediator=None):
        super().__init__(poke_info, mediator)

        #  get the pokemon facing forward image
        if type(poke_info['front']) == bytes:
            self.image = pygame.image.load(io.BytesIO(poke_info['front']))
        else:
            self.image = pygame.image.load((poke_info['front']))

        # update it's new offscreen position since it will be coming in from the next direction
        self.off_screen_pos = Config.SCREEN_WIDTH + 100, 300 * Config.HEIGHT_SCALE

        # front images are a bit larger so we scale them down as opposed to the back images
        self.image = pygame.transform.scale(self.image, (300 * Config.WIDTH_SCALE,300 * Config.HEIGHT_SCALE))

        self.rect = self.image.get_rect(midbottom=(self.off_screen_pos))

        # generate random moves same as in Trainer Pokemon
        self.moves = [Attack(move['move']['name'] ,random.randint(30, 60)) for 
                      move in random.sample(self.moves, 4)]
        
        self.float_in_pos = Config.SCREEN_WIDTH-(200*Config.WIDTH_SCALE)
        self.gui_elements=[]

    def initialize_for_fight(self, bd):
        """ create the gui elements for the challenger pokemon"""
        info_layer = bd.create_pokemon_info_tile('Lv. 100', self.name)
        self.gui_elements.append([info_layer, (0, 0)])

        health_bar = bd.create_pokemon_health_bar(self.hp)
        bar_outline_pos = 20, 40
        
        bar_hp_pos = bar_outline_pos[0]+2, bar_outline_pos[1]+2

        self.gui_elements.append([health_bar[0], bar_outline_pos])
        self.gui_elements.append([health_bar[1], bar_hp_pos])

    def attack(self, mediator):
        """ choose a randome move and send the attack to the mediator"""
        move = random.choice(self.moves)
        mediator.send_attack('challenger', move)