from gameplay.levels import LevelFactory, LevelStore


class GameState:
    """Singleton Class that manages the stages and state of the overall game"""

    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__initialized = False
        return cls.__instance

    def __init__(self):
        if self.__initialized: return
        
        # boolean to control if pygame is running
        self._running = True

        # the current state of the game.
        self.current_state = 'choose'

        # used to toggle a screen where applicable (for example , control menu)
        self.previous_state = None

        # the screen to display on, which is updated in the maingame loop
        # to avoid circular import
        self.screen = None

        # responsible for playing levels; described below
        self.gameplayer = GamePlayer(self) 

        # dict of allowed - 
        # keys: state
        # values: should rerender
        
        # rerender handles whether the render function of the 
        # level should be called everytime the player switches to that level
        # as the game grows I would consider using a state pattern instead
        # this is used for simplicity

        self._states = {
            'welcome': False,
            'choose': False,
            'explore_hometown': False,
            'loading': False,
            'battle': True,
            'controls': False
        }
        self.__initialized = True

    def change_state(self, state: str) -> None:
        """Change the current state of the game"""

        # checks if the updated state is a valid state and if it is not already the current state
        if state in self._states and state != self.current_state:

            self.previous_state = self.current_state
            self.current_state = state


            # use should_not_rerender
            should_not_rerender = self.previous_state == 'controls'
            self.gameplayer.render_level(should_not_rerender)
    

class GamePlayer:

    """ Singleton to handle playing the game at different states/stages pf the games"""

    __instance = None

    def __new__(cls, *args):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__initialized = False
        return cls.__instance

    def __init__(self, gamestate):
        if self.__initialized: return

        # dictionary of the levels available, key is the state and the level
        # is a class that handles the rendering and gameplay
        self.__levels = {}

        # gamestate provided GameState above
        self.gamestate = gamestate

    def reset(self):
        """ reset all the levels and necessary variables when the player has lost"""
        
        self.__levels.clear() # clear the storage of the levels 
        LevelStore.reset()  # execute reset on level factory class


    def render_level(self, should_not_rerender=False):
        """Render the current level if it has not already been rendered or if it rerender is true"""

        # if the current state level has not been already accessed, or if it is to be rerender
        # we update the level, otherewise we return the already rendered level.
        # this is similar to the flyweight pattern and helps us to not constantly 
        # rerender levels from scrath each time it is called when necessary

        if self.gamestate.current_state not in self.__levels or (self.gamestate._states[self.gamestate.current_state] and not should_not_rerender):
            self.__levels[self.gamestate.current_state] = LevelFactory.create_level(level_type=self.gamestate.current_state, screen=self.gamestate.screen, gamestate=self.gamestate)
        return self.__levels[self.gamestate.current_state]
    
    async def play_level(self):
        """handle the actual game play, key events, displaying, etc."""
        try:
            await self.__levels[self.gamestate.current_state].play_level()
        except KeyError:
            # key error expected when the game is restarted so ensure that the game level is rendered first
            await self.render_level().play_level()