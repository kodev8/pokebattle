from gui_builders.gui import GUIDirector, Element
from sprites.sprites import GameSprite
from config.config import Config
from sprites.spritesheets import SpriteSheet
from abc import ABC, abstractmethod

class OakState(ABC):
    """ base class for any of professor oak's states"""
   
    def __init__(self, oak):
        # oak is the professor oak singleton
        self.oak = oak
        
        # all states use the same spritesheet
        self.sheet = SpriteSheet(image_file=r"assets\spritesheets\oak-spritesheet.png",
                                 json_file=r"assets\spritesheets\sheet_json\oak-spritesheet.json")

        # initial speech psotion is set to 0
        self.speech_count = 0

        # speech is list of strings to display 
        self.speech =[]

        # tiles would be rendered in play level render method
        self.tiles = {}

        self.statement = None
        
    def talk(self) -> Element:
        """ returns the current speech position if possible, else it returns none"""
        if self.speech_count < len(self.speech):
            return self.tiles[self.speech_count]
        
    def create_tiles(self, bd: GUIDirector):
        """ create the speech the tile for an oak state"""
        for index, speech in enumerate(self.speech):
            if index not in self.tiles:
                self.tiles[index] = bd.oak_speech_tiles(speech)

    def setup_image(self, name, scale=(1, 1), offset_x=0, offset_y=0):
        image = self.sheet.parse_sheet(name=name, scale=scale)
        self.oak.image = image
        self.x = (Config.SCREEN_WIDTH - image.get_width()) // 2 - offset_x
        self.y = (Config.SCREEN_HEIGHT- image.get_height()) // 2 - offset_y
        self.oak.image.set_colorkey(Config.BLACK)

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def animate(self):
        pass

class OakHello(OakState):

    def __init__(self, oak):
        super().__init__(oak)
        
        # set the image
        self.setup_image(name='oak-hello')


        # make hello speech
        self.speech =  ["Hey there! Welcome to Pokemon Battle Arena!",
                    "I'm Professor Oak!",  "I'm sure you already know so much about Pokemon!",
                        "So, let's get to the good stuff"]
        
    def animate(self) :
        # check if talk returns a valid statement
        statement = self.talk()

        # if the statement is none we update to the next state
        if not statement:
            self.oak.current_state = OakExplain(self.oak)
        else:
            # the current statement is set to the statementreturned from the talk function
            # and is displayed
            self.statement = statement
    
    def update(self, bd):
        # update professor oack on each animation
        self.create_tiles(bd)
        self.animate() 

            
class OakExplain(OakState):

    def __init__(self, oak):
        super().__init__(oak)
        self.setup_image(name='oak-explain', scale=(0.8, 0.8), offset_x=-50)
        

        self.speech = ["First, you choose your pokemon", 
            "Then You can travel around the village, ","and search look for other trainers.", 
            "From there, Once you agree to battle,","it's all up to you to show your skills!",
            "Be Careful, once your pokemon faints...", "You won't be able to use it for the next fight", "Quick note!",
            "Walking is a bit slow...", "So look out for some items to help", "and Press C for a reminder of the controls",
            "Remember, Have Fun!"]
        
    def animate(self):

        # if talk returns a valid statement
        statement = self.talk()

        # if the statement is none we update to the next state
        if not statement:
            self.oak.current_state = OakBye(self.oak)
        else:
            self.statement = statement

    
    def update(self, bd):
        self.create_tiles(bd)
        self.animate()    


class OakBye(OakState):

    def __init__(self, oak):
        super().__init__(oak)
        self.setup_image(name='oak-bye')
        self.speech=["I'll see you around and maybe we can battle someday.",
            "Go ahead and choose your pokemon!"]
    
    def animate(self) :
        # if talk returns a valid statement
        statement = self.talk()

        # if the statement is none we update to the next state
        if not statement:
            self.oak.current_state = 'intro_end'
        else:
            self.statement = statement
            
    def update(self, bd):
        self.create_tiles(bd)
        self.animate()


class OakLose(OakState):
    # only triggered when the trainer has lost
    def __init__(self, oak):
        super().__init__(oak)
        self.setup_image(name='oak-explain', offset_x=100)
        self.speech=["Better Luck Next Time...", 'Press N to Play Again', 'If not, see you next time!']

    def animate(self):
        # if talk returns a valid statement
        statement = self.talk()

        if not statement:
            self.oak.current_state = 'game_end'
        else:
            self.statement = statement
    
    def update(self, bd):
        self.create_tiles(bd)
        self.animate()


class OakWin(OakState):
    # only triggered when the trainer has lost
    def __init__(self, oak):
        super().__init__(oak)
        self.setup_image(name='oak-win', offset_x=-200)
        self.speech=["Well done !!", 'You Successfully defeated all the challengers!', 
                     'Press T to continue exploring or...', 
                     'Press N to start a new game!', 'If not, see you again Champ!']

    def animate(self):
        # if talk returns a valid statement
        statement = self.talk()

        if not statement:
            self.oak.current_state = 'game_end'
        else:
            self.statement = statement
    
    def update(self, bd):
        self.create_tiles(bd)
        self.animate()


class ProfessorOak(GameSprite):

    """ Professor oak singleton that handles the introduction to the game"""
    __instance = None

    def __new__(cls, *args):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__initialized = False
        return cls.__instance
    
    def __init__(self):
        if self.__initialized: return
        super().__init__()

        # set the initial state to hello
        self.__current_state = OakHello(self)        
        
        self.__initialized = True

    @property
    def current_state(self):
        """ return oak's current state"""
        return self.__current_state

    @current_state.setter
    def current_state(self, state: OakState):
        """ update the current state of the profeessor oak"""
        assert ( isinstance(state, OakState) or (isinstance(state, str) and state in ('intro_end', 'game_end')))
        self.__current_state = state

    def update(self, bd):
        self.__current_state.update(bd)


            