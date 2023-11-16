import pygame
from config.config import Config
from gameplay.environments import YSortLayer
from abc import ABC, abstractmethod

class Camera(ABC):
    """ Abstarct base class for a type of camera"""
    @abstractmethod
    def _setup_camera():
        pass
    
    @abstractmethod
    def  _camera_target():
        pass
    
    @abstractmethod
    def custom_focus():
        pass

class ExploreCamera(Camera):

    """this class is used to mainatin focus on the trainer's current position by offsetting
    all other sprites/tiles on the screen based on the player's position """

    def __init__(self):

        super().__init__()
        self._setup_camera()

    def _setup_camera(self):
        
        # the initial offsets are set to 0
        self._offset_x = self._offset_y= 0

        # we define a box/rect where the player is alowed to move freely, 
        # once the player begins to exceed any of the inner border values then the camera renders 
        # the other sprites in the new respective postions
        self._inner_borders = {'left':200, 'top':200, 'right':200, 'bottom':100}

        l = self._inner_borders['left']
        t = self._inner_borders['top']

        # width and height of inner box are calculated
        w = Config.SCREEN_WIDTH - self._inner_borders['left'] - self._inner_borders['right']
        h = Config.SCREEN_HEIGHT - self._inner_borders['top'] - self._inner_borders['bottom']

        self.camera_rect = pygame.Rect(l, t, w, h)

        # this groups is keeps track of the individual groups added to the camera group
        # in pygame, group.add adds the sprites only
        # since the sprites will be conditionally rendered (ysorted or not)
        # this list maintains the separate groups

        self._groups = []

    def add_group(self, *groups):
        """ adds the pygame groups to the other group only list"""
        
        for group in groups:
            self._groups.append(group)

    def _camera_target(self, target):

        # the the x and y offsets updated
        self._offset_x = self.camera_rect.left - self._inner_borders['left']
        self._offset_y = self.camera_rect.top - self._inner_borders['top']

        # these conditions check whether the target (in this game will always be the trainer)
        # is in the in the inner border or not. as the target
        if target.rect.left < self.camera_rect.left and self.camera_rect.left > self._inner_borders['left']:
            self.camera_rect.left = target.rect.left

        if target.rect.right > self.camera_rect.right and self.camera_rect.right < Config.MAP_W - self._inner_borders['right']:
            self.camera_rect.right = target.rect.right

        if target.rect.bottom > self.camera_rect.bottom and self.camera_rect.bottom <  Config.MAP_H - self._inner_borders['bottom']:
            self.camera_rect.bottom = target.rect.bottom

        if target.rect.top < self.camera_rect.top and self.camera_rect.top > self._inner_borders['top']:
            self.camera_rect.top = target.rect.top

    def custom_focus(self, screen, focus):
        """ This function serves to render objects based on their position relative to the target (trainer) """
        
        # set the box camera's target (usually is set to the trainer)
        # however this allows anny focus to be given to a camera if neccessary
        self._camera_target(focus)

        #  for each group added, we check if the group layer is ysorted or not
        # if it is y sorted, we sort the sprites by their center y value otherwise, 
        # the sprties order remains the same
        for group in self._groups:

            my_sprites = sorted(group.sprites(), key=lambda s: s.rect.centery) if isinstance(group, YSortLayer)  else group.sprites()
            
            # for every sprite in the corresponding group we set it's position on the screen
            # to it's offset position, this way as the target moves, the surrounding sprites 
            # also move accoridngly. and the sprites are displayed. 
            # It is important to set the sprites new offset position because if they are displayed
            # in their new position but not actually updated, collisions will not work
            for sprite in my_sprites:
     
                offset_pos = (sprite.rect.topleft[0] - self._offset_x,
                                        sprite.rect.topleft[1] - self._offset_y 
                                )
        
                screen.blit(sprite.image, offset_pos)
                sprite.offset = offset_pos     