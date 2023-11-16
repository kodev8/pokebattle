import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
from config.config import Config
from config.gamestate import GameState, GamePlayer
from gameplay.levels import LevelStore , HandlerCreator
from gui_builders.gui import GUIBuilder, GUIDirector

class MainGameLoop:

    # starts pygame and initiates all subparts, like rendering images, playing sound
    pygame.init()


    # create display surface, set window size
    __screen = pygame.display.set_mode((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))

    icon = pygame.image.load('assets/images/poke-icon.png')
    pygame.display.set_icon(icon)
    

    # set the title of the winow
    pygame.display.set_caption('Pokemon Battle Arena!')

    __clock = pygame.time.Clock() # responsible for handling framerate of the game
    
    # instantiate the GAME STATE Singleton which is used to maintain state of the game
    # throughout all the stages of the game
    _GAME_STATE = GameState()
    _GAME_STATE.screen = __screen # give gamestate access to the screen variable
    _GAME_PLAY = GamePlayer(_GAME_STATE)

    _GAME_PLAY.render_level() # render the current level (gamestate initial stte is always set to the welcome page)

    # create an instance of the trainer
    LevelStore.trainer_mediator.notify_set(LevelStore)

    # set up the event handlers
    event_handler = HandlerCreator.create_handlers(_GAME_STATE, _GAME_PLAY)
    _AUDIO_ERROR = False

    try:
        pygame.mixer.init()
    except Exception as e:
        _AUDIO_ERROR = True
        _error_builder = GUIDirector(GUIBuilder())

    def play(cls):
        while cls._GAME_STATE._running:

            for event in pygame.event.get():
                
                # check if the the x is in top corner is clicked or if if the escape button is pressed
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE): 
                    
                    # then we close the game using the game state manager
                    cls._GAME_STATE._running = False

                # check each handler for every game state. using the chain off res
                # only the corresponding handler will handle key events for the given the state
                for state in cls._GAME_STATE._states:
                    cls.event_handler.handle(state, event)
            
            if not cls._AUDIO_ERROR:
                # run the actual gameplay for the corresponding level
                cls._GAME_PLAY.play_level()

            else:
                audio_err = cls._error_builder.create_error('Audio Error - Try Using Headphones', ' If not plug in and unplug headphones ')
                audio_err.display(cls.__screen, Config.ERROR_POS)

            # update the screen for all animations and changes
            pygame.display.update()

            cls.__clock.tick(Config.FRAMERATE) # limit while loop to run no more than 60 times per second

if __name__ == '__main__':
    # play the game
    MainGameLoop().play()