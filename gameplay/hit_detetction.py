import pygame
from abc import ABC, abstractmethod
from config.config import Config

class Hit(ABC):
    """ Abstract base class for a hit detection class
    defines methods to determin the side the character was hit on"""
    @abstractmethod
    def hit_left():
        pass

    @abstractmethod
    def hit_right():
        pass

    @abstractmethod
    def hit_top():
        pass

    @abstractmethod
    def hit_right():
        pass

    def detect_hit():
        pass


class HitDetection(Hit):
    """ handle hit detection for the trainer"""

    def __init__(self):

        # variable to ensure sound is played only once on each collision
        self.__play_sound = 0
        
        # dict to relate the direction to hit check method
        self.__detectors = {
            'left': self.hit_left,
            'right': self.hit_right, 
            'up': self.hit_top, 
            'down': self.hit_bottom

        }

    # each hit detector uses the sprites mask to get the relvent points such as centerx and centery
    # this gives pixel perfect collision rather than using rects, they then reset play sound to 0
    
    def hit_left(self,  sprite1: pygame.sprite.Sprite, sprite_group):
        """ check if a sprite collides with the group on its left"""
        for sprite in sprite_group:
            # if the sprite's center x value is to the right (greater than) the  group sprite's right value, 
            # and the sprite's center y is within the span (top to bottom) of the group sprite, then 
            # there is a valid collision on the left of the sprite
            if sprite1.left + 20  >= sprite.right and sprite.bottom >= sprite1.centery >= sprite.top:
                return True
        self.__play_sound = 0
        return False

    def hit_right(self,sprite1: pygame.sprite.Sprite, sprite_group):
        """ check if a sprite collides with the group on its right"""
        for sprite in sprite_group:
            # if the sprite's center x value is to the left (less than) the  group sprite's left value, 
            # and the sprite's center y is within the span (top to bottom) of the group sprite, then 
            # there is a valid collision on the right of the sprite
            if sprite1.right - 20  <= sprite.left and (sprite.bottom >=sprite1.centery >= sprite.top):
                return True
        self.__play_sound = 0
        return False

    def hit_top(self, sprite1: pygame.sprite.Sprite, sprite_group):
        """ check if a sprite collides with the group on its top"""

        for sprite in sprite_group:

            # if the sprite's center y valuue is below (greater than) the  group sprite's bottom value, 
            # and the sprite's center x is within the span (left to right) of the group sprite, then 
            # there is a valid collision on the top of the sprite
            if sprite1.top + 20 >= sprite.bottom and (sprite.left <= sprite1.centerx  <= sprite.right):
                return True
        self.__play_sound = 0
        return False
        

    def hit_bottom(self, sprite1: pygame.sprite.Sprite, sprite_group):
        """ check if a sprite collides with the group on its bottom"""
        for  sprite in sprite_group:
            # if the sprite's center y value is above (less than) the  group sprite's top value, 
            # and the sprite's center x is within the span (left to right) of the group sprite, then 
            # there is a valid collision on the bottom of the sprite
            if sprite1.bottom - 20  <= sprite.top and (sprite.left <= sprite1.centerx  <= sprite.right):
                return True
        self.__play_sound = 0
        return False

    def detect_hit(self, sprite1: pygame.sprite.Sprite, sprite_group):

        """ detect collisions and direction of collision between one sprite and anothe set of sprties"""
        
        # keep updating the sprite speed 
        for direc in sprite1.current_state.animations:
            sprite1.current_state.animations[direc][0] = sprite1.current_state.speed


        # first check if the sprite collides with the gorup using the rect method since mask collisiobs are expensive
        if pygame.sprite.spritecollide(sprite1, sprite_group, False): 

            # then check for mask collisions, since sprites are abnormally shaped
            collisions = pygame.sprite.spritecollide(sprite1, sprite_group, False, pygame.sprite.collide_mask)  
            
            # if a  mask collision is detected
            if collisions:

                # use the create mask function to keep updating the outline valuse of the sprites that have been collided with
                for sprite in collisions:
                    sprite.create_mask()

                # run the relevant detect hit method for the corresponding direction that the sprite is travelling in
                if self.__detectors[sprite1.current_state.direction](sprite1, collisions):

                    # set the speed to 0 so it cannot move
                    sprite1.current_state.animations[sprite1.current_state.direction][0] = 0

                    # play the collide noise only once until a new collision is detected
                    if self.__play_sound == 0:
                        pygame.mixer.Sound(r'./assets/sounds/collide.ogg').play()

                        self.__play_sound += 1
