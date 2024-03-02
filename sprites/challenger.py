import pygame
from config.config import Config
from sprites.sprites import ExploreSprite
from sprites.trainer import Trainer
from sprites.pokemon import OtherPokemon
from sprites.spritesheets import SpriteSheet
from gameplay.battle import Lineup
from config.fetcher import FetchPokemon
import random
from typing import Dict
                                 
class Challenger(ExploreSprite):
    """ Challeger sprites are sprites that can potentially have battle with the player"""
    
    def __init__(self, direction, pos):
        super().__init__()

        # setup the sprites' images
        self.sheet = SpriteSheet(image_file=r"assets/spritesheets/challenger-spritesheet.png", 
                        json_file=r"assets/spritesheets/sheet_json/challenger-spritesheet.json")
        self.direction = direction
        self.image = self.sheet.parse_sheet(f"challenger-{self.direction}", format=(28, 32))
        self.rect = self.image.get_rect(center=pos)
        self.image.set_colorkey(Config.BLACK)

        self.__exclamation = pygame.image.load(r'./assets/images/exclaim2.png').convert_alpha()
        
        # resize the exclamation and get the rect to display the excalmation 
        wratio = 28/pos[0] # 28 from testing
        hratio =28/pos[1] 
        self.__exclamation = pygame.transform.scale(self.__exclamation, Config.scaler(wratio * self.rect.midtop[0], hratio *self.rect.midtop[1]))
        self._rect = self.__exclamation.get_rect(center=self.rect.midtop)

        # flag if the challenger is challenging the trainer
        self.challenging = False

        # how far the challenger can 'see', meaning how many pixels the 
        # trainer must be from the challenger in the relevant direction before the trainer is noticed
        self.view_distance =  50

        # flag if the trainer has been defeated
        self.defeated = False

        # lineup of other pokemon objects
        self.pokemon = self._gen_pokemon() 

    @staticmethod
    def inititialize_challengers(data: Dict[str, tuple]):

        """ set up challengers based on data provided
        data: is in the form {direction: pos} and pos is a tuple of x and y cooridinates to place the challenger on a map
        """
        
        challengers = []
        for direction, position in data.items():
            chal = Challenger(direction, position)
            challengers.append(chal)
        return challengers
        
    def _gen_pokemon(self):

        """ this function serves to generate pokemon for the challenger"""

        lineup = Lineup([])
        num_pokemon = random.randint(1, Config.MAX_CHAL_COUNT)

        # generate n random pokemon for the trainer
        for _ in range(num_pokemon):

            # choose a ranom pokemon
            generated_pokemon_data = FetchPokemon.gen_data()
            if generated_pokemon_data:

                # create a pokemon of type other pokemon which can battle the trainer's pokemon
                lineup.add(OtherPokemon(generated_pokemon_data))

        return lineup

    def notice(self, trainer: Trainer):

        """ this function serves to detect whether the player is in the challengers view port 
        if this function returns true, the player can potentially battle the challeger"""
        
        
        # if the challenger is looking up the notice conditions are:
        # 1) the trainers center x value is between the challengers left and right
        # 2) the trainers y value is less (higher on the screen) than the challengers y value 
        # 3) the trainers y value is greater (lower on the screen) than the challengers y value and view distance
        if self.direction == 'up':
            if self.rect.left< trainer.rect.centerx < self.rect.right and (self.rect.bottom - (self.image.get_height() + self.view_distance)) <= trainer.rect.centery <= self.rect.top: # adjust chall up to accountn for ysort 
                return True

         # if the challenger is looking down the notice conditions are:
        # 1) the trainers center x value is between the challengers left and right
        # 2) the trainers y value is greater (lower on the screen) than the challengers y value 
        # 3) the trainers y value is less (higher on the screen) than the challengers y value and view distance
        elif self.direction == 'down':
            if self.rect.left< trainer.rect.centerx < self.rect.right and (self.rect.bottom + self.view_distance) >= trainer.rect.centery >= self.rect.bottom:
                return True

        # if the challenger is looking left the notice conditions are:
        # 1) the trainers center y value is between the challengers top and bottom
        # 2) the trainers x value is less (more left on the screen) than the challengers left value 
        # 3) the trainers x value is greater (more right on the screen) than the challengers left value and view distance
        elif self.direction == 'left':
            if self.rect.top <= trainer.rect.centery <= self.rect.bottom and (self.rect.left - self.view_distance) <= trainer.rect.centerx <= self.rect.centerx:
                return True

        # if the challenger is looking right the notice conditions are:
        # 1) the trainers center y value is between the challengers top and bottom
        # 2) the trainers x value is more (more right on the screen) than the challengers right value 
        # 3) the trainers x value is less (more left on the screen) than the challengers right value and view distance
        elif self.direction == 'right':
            if self.rect.top <= trainer.rect.centery <= self.rect.bottom and (self.rect.right + self.view_distance) >= trainer.rect.centerx >= self.rect.centerx:    
                return True
        else:
            return False
    
    def animate(self, screen: pygame.Surface): 
        # set the challenging to true to let the trainer know he can battle the current challenger
        self.challenging = True

        # exclamation indication on the screen
        screen.blit(self.__exclamation, (self.left, self.top-30))

    def update(self, screen: pygame.Surface, trainer: Trainer):
        # updating the challenger means checking if it has noticed the trainer
        # if the challenger still has pokemon (if the challenger has no pokemon, it has been defeated and coannot notcie the trainer)
        
        if len(self.pokemon) > 0 and not self.defeated and  self.notice(trainer):
            self.animate(screen)
        else:
            self.challenging = False