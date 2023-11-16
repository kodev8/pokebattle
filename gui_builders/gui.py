from config.config import Config
import pygame
import io

class Element:
    """ base class for gui elements """
    def __init__(self, surface):
        self.surface = surface

    def display(self, screen, pos):
        """display button on the screen"""
        screen.blit(self.surface, pos)

class GUIElement(Element):
    def __init__(self, surface):
        super().__init__(surface)

class Button(Element):
    """ create button to display"""
    def __init__(self, surface, id):
        super().__init__(surface)
        self.id = id
        self.rect = self.surface.get_rect()
        self.width = surface.get_width() 
        self.height = surface.get_height()

    # although all buttons don't have onclick and hover implementations in their event handlers,
    # it is somehting I would hope to implement in the future
    def onclick(self, screen, color=Config.GREEN):

        pygame.draw.rect(screen, color ,self.rect , 3)

    def onhover(self, screen, color=Config.YELLOW):
        """highlight border when hovered"""

        pygame.draw.rect(screen, color ,self.rect , 3)

    def update_rect(self, x, y):
        self.rect = pygame.Rect(x, y, self.width, self.height)
        
    def __eq__(self, other):
        """ define a new function to test equlaity of buttons
        It is used to identify one button is the same as onther"""
        return self.id == other.id

class GUIBuilder:

    """ Builder for buttons and other gui elements """
    def __init__(self):
        self.surface = None
        self.rect = None


    def style(self, width=50, height=30, bg=Config.WHITE, border_width=5, border_radius=50, opacity=255, id=None, fill=True):

        """ styling the surface"""
        self.surface = pygame.Surface((width, height))
        self.surface.set_alpha(opacity)
        self.rect = pygame.Rect(0, 0, width, height)

        if fill:
            self.surface.fill(bg)
            
        pygame.draw.rect(self.surface, bg, (0, 0, width, height), border_width, border_radius=border_radius)
        return self
    

    def add_text(self,  text="", font='default', font_size='med', bold=False, font_color = Config.BLACK, offset=(0, 0)):
        """ adding text using the correct font as defined in config"""
        font = Config.make_fonts(font)[font_size]
        if bold: 
            font.set_bold(True)
        text_surface = font.render(text, True, font_color)
        place_at = (self.surface.get_rect().centerx - offset[0],self.surface.get_rect().centery - offset[1] )
        text_rect = text_surface.get_rect(center=place_at)
        self.surface.blit(text_surface, text_rect)
        return self
    
    def add_image(self, file, scale=None, offset=(0,0), ):

        """ adding images to buttons"""
        if type(file) == bytes:
            
            # *****if the file passed is in bytes we create an in memory buffer to store the bites
            file = io.BytesIO(file)

        image = pygame.image.load(file).convert_alpha()
        
        if scale:
            # scale the image if necessary
            image = pygame.transform.scale(image, scale)
        
        # set the bounding rect of the image which is used to display the image
        # using the buttons center as the images center
        image.get_rect(center=self.surface.get_rect().center)
        
        # used to place the image on the button, centered by default;
        # offset is used to position the image if necessary
        place_at = (self.surface.get_rect().centerx - offset[0], self.surface.get_rect().centery - offset[1] )
        
        # display the image on the surface
        self.surface.blit(image, image.get_rect(center=place_at))

        return self
    

    def add_border(self, border_color=Config.BLACK):
        """ draws a rect on the edge of the surfaces currect rect"""
        pygame.draw.rect(self.surface, border_color, self.rect, 2)
        return self

    def build_button(self, id=None):
        # create the button
        return Button(self.surface, id)
    
    def build(self):
        return GUIElement(self.surface)
    

class GUIDirector:

    def __init__(self, builder):
        self.builder = builder
      
    def create_fetcher_button(self, text):
        """create style for the next and previous labels"""
        start_menu = {
            'width':150, 'border_radius':10, 'opacity':200, 'border_width':5, 'bg':Config.BLUE
        }
        return  self.builder.style(**start_menu).add_text(text, font_size='small', font_color=Config.WHITE).build()
    
    def create_pokemon_tile(self, rows, spacing, image, name):
        # create the tile for pokemon to be displayed on
        style = {
            'width': Config.SCREEN_WIDTH/rows-spacing-5,
            'height': Config.SCREEN_HEIGHT/rows-spacing-5,
        }

        # note that this is built using build button
        return self.builder.style(**style).add_image(image, offset=(0, 15)).add_text(name.upper(), offset=(0, -35)).build_button(id=name)
    
    def oak_speech_tiles(self, text):
        """create professor oaks speech tiles"""
        style = {
            'width': Config.SCREEN_WIDTH-20,
            'height': Config.SCREEN_HEIGHT/4,
            
        }
        return self.builder.style(**style).add_text(text, font_size='med').add_text('[ SPACE ]', offset=(-200, -30)).build()
    
    
    def create_continue_button(self, text):
        """ create the button that is displayed """ 
        style = {
            'width': 300,
            'height': 50, 
            'bg': Config.GREEN,
            'opacity':230
            
        }
        return  self.builder.style(**style).add_text(text, font_size='small', bold=True, font_color=Config.BLACK).build()

    def create_move_tile(self, text):
        """create the tile that dispalys the pokemons moves"""
        style={
            'bg':	(255, 253, 208), 
            'width':Config.SCREEN_WIDTH/4, 
            'height':Config.SCREEN_HEIGHT/6,
        }
        
        return self.builder.style(**style).add_border(Config.BLACK).add_text(text.capitalize(), font_size='small').build()
    
    def create_pokemon_info_tile(self, text1, text2):
        """ create the tile that displays the pokemons name and level"""

        style = {
            'width':Config.SCREEN_WIDTH/2, 
            'height':Config.SCREEN_HEIGHT/6-20,
        }
        return self.builder.style(**style).add_border(Config.GREEN)\
                        .add_text(text1, font="solid", offset=(100, 10))\
                            .add_text(text2.upper(), offset=(-100, 10)).build_button()
    

    def create_battle_narrator(self, text):

        """create the tile for the narrtor of the battle"""
       
        style={
            'bg':	(255, 253, 208), 
            'width':Config.SCREEN_WIDTH/2, 
            'height':Config.SCREEN_HEIGHT/6,
        }
        
        return self.builder.style(**style).add_border(Config.BLACK).add_text(text.upper(), font_size='med-small').build()
    

    def create_pokemon_health_bar(self, hp):

        """design a the health bar based on the pokemons hp"""

        if hp <= 0:
            bg = Config.WHITE
        elif hp <= 50:
            bg = Config.RED
        elif hp >=110:
            bg = Config.GREEN
        
        else: 
            bg = Config.YELLOW

        width = (Config.SCREEN_WIDTH/2 - 50)
        height = 10
        
        border_style = {
            'width':width+2, 
            'height':height,
            'border_width':10, 
            'bg':Config.WHITE
            }

        bar_style = border_style.copy()
        bar_style['bg'] = bg
        bar_style['height'] = height-4
        bar_style['width'] =  width/200 * hp -2 if hp > 0 else 1

        outline = self.builder.style(**border_style).add_border().build()
        health = self.builder.style(**bar_style).build()
        return  outline, health
    
    def create_bag(self, image):

        """style the bag to display"""
        style = {
            'height': Config.SCREEN_HEIGHT/3,
            'width': 100
        }

        return self.builder.style(**style).add_border().add_image(image, offset=(0, 50), scale=(36, 36)).build()

    def create_choose_count(self, text):
        """ create the choose count indicator in the choose level"""
        style = {
            'height':25,
            'width': 70, 
            'bg':Config.RED,
            # 'fill':True,
            "opacity":200
        }

        return self.builder.style(**style).add_border().add_text(text, font_size='small').build()


    def create_control(self, control, desc):
        """ creates tiles that are displayed in the control menu"""
        style = {
            'width': Config.SCREEN_WIDTH - 50, 
            'height': 50,
            'opacity':180
        }

        return self.builder.style(**style).add_border().add_text(control, font='solid', font_size='large', offset=(200, 0))\
                .add_text(desc, font='solid', font_size='large',offset=(-100, 0)).build()

    def create_control_header(self, text):
        style ={
            'width': 400, 
            'height': 50,
            'opacity':225,
        }
        return self.builder.style(**style).add_text(text, font="solid", font_size='xl').build()
       
    
    def create_error(self, type, desc):
        style = {
            'width': Config.SCREEN_WIDTH - 50, 
            'height': 100, 
            'fill': True,
            'bg': Config.RED
        }

        return self.builder.style(**style).add_border().add_image(r'assets/images/error.png', offset=(290, 0), scale= (50, 50))\
            .add_text(type, offset=(0, 10), font='solid', font_size='large', font_color=Config.WHITE)\
            .add_text(desc, offset=(0, -20), font='solid', font_color=Config.WHITE).build()
    
    def create_battle_end(self, win=True):

        if win:
            text = 'Congratulations! You won this round'
            image = r'assets/images/trophy.png'
            bg = Config.GREEN

        else:
            text = 'Sorry! You Lost this round'
            image = r'assets/images/gameover.png'
            bg = (109, 9, 238)

        style = {
            'width': Config.SCREEN_WIDTH - 100,
            'height': 100,
            'fill': True,
            'bg': bg
        }

        return self.builder.style(**style).add_border().add_text(text, offset = (-20, 0)).add_image(image, offset=(250, 0), scale =(50, 50)).build()

    