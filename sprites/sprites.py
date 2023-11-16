import pygame

class GameSprite(pygame.sprite.Sprite):
    """ base class for a sprite which inherits from pygame sprite"""
    def __init__(self):
        super().__init__()

class ExploreSprite(GameSprite):

    """ base class for sprites on the explore level"""
    def __init__(self):
        super().__init__()

        # offset is used to display the sprite on the screen
        # relative to a specific target for camera
        self.offset = (0, 0)


    def create_mask(self):
        """ creates a mask and outline values of the sprite of the sprite to get a rough outline of the sprite for collisions """
        
        self.mask = pygame.mask.from_surface(self.image)
        
        # we get the outline of the spreite
        outline = self.mask.outline()        
        

        if outline:
            # configure the out line values ot be updated according to the offest
            self.new_outline = [(x + self.offset[0], y + self.offset[1]) for x, y in self.mask.outline()]

            # sort all posits by y value to max and min y values
            sorty = sorted(self.new_outline, key=lambda x: x[1])
            # sort all posits by x value to max and min  xvalues
            sortx = sorted(self.new_outline, key=lambda x: x[0])
            
            # right value is the max x
            self.right = sortx[-1][0]

            # bottom is the max y
            self.bottom = sorty[-1][1]

            # left is the min x
            self.left = sortx[0][0]

            # top is the min y
            self.top = sorty[0][1]

            # calculating center points
            self.centery = (self.top + self.bottom )/2
            self.centerx = (self.left + self.right )/2

class Tile(ExploreSprite):
    """class for tiles rendered from pytmx"""
    
    def __init__(self, pos, image):
        super().__init__()
        self.pos = pos # position to palce the tile
        self.image = image.convert_alpha()
        
        # use for collision detection and camera placement 
        self.rect = self.image.get_rect(topleft=pos)