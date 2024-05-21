# Top level imports for pygbag version
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import warnings
# import aiohttp
import asyncio
import math
# from aiohttp.client_exceptions import ClientConnectorError
from abc import ABC, abstractmethod
import random
import json 
import math
from pytmx.util_pygame import load_pygame
import io
import sys
import platform
import json
import warnings
from urllib.parse import urlencode
import base64
from PIL import Image
import platform
warnings.filterwarnings("ignore") 


from config.config import Config
if not Config.IS_WEB:
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

from config.gamestate import GameState, GamePlayer
from gameplay.levels import LevelStore , HandlerCreator
from gui_builders.gui import GUIBuilder, GUIDirector
import warnings
import asyncio


# warnings.filterwarnings("ignore") #suppress libpng warning
class MainGameLoop:

    # starts pygame and initiates all subparts, like rendering images, playing sound
    pygame.init()


    # create display surface, set window size
    __screen = pygame.display.set_mode((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))

    icon = pygame.image.load(r'./assets/images/poke-icon.png')
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

    async def play(cls):
        while cls._GAME_STATE._running:
       
            for event in pygame.event.get():
                
                # check if the the x is in top corner is clicked or if if the escape button is pressed only if on pc
                if not Config.IS_WEB:
                    if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE): 
                        
                        # then we close the game using the game state manager
                        cls._GAME_STATE._running = False

                # check each handler for every game state. using the chain off res
                # only the corresponding handler will handle key events for the given the state
                for state in cls._GAME_STATE._states:
                   await  cls.event_handler.handle(state, event)
            
            if not cls._AUDIO_ERROR:
                # run the actual gameplay for the corresponding level
                # await asyncio.gather(cls.async_wrapper(cls._GAME_PLAY.play_level()))
                await cls._GAME_PLAY.play_level()


            else:
                audio_err = cls._error_builder.create_error('Audio Error - Try Using Headphones', ' If not plug in and unplug headphones ')
                w, h = audio_err.surface.get_size()
                audio_err.display(cls.__screen, ((Config.SCREEN_WIDTH - w)/2, Config.CENTER[1] - h//2) )

            # update the screen for all animations and changes
            pygame.display.update()

            cls.__clock.tick(Config.FRAMERATE) # limit while loop to run no more than 60 times per second
            await asyncio.sleep(0)

# if __name__ == '__main__':
#     # play the game
asyncio.run(MainGameLoop().play())