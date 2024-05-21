import pygame
from config.config import Config
from gui_builders.gui import GUIBuilder, GUIDirector
from sprites.challenger import  Challenger
from sprites.trainer import Trainer
from gameplay.hit_detetction import Hit
from sprites.professor_oak import ProfessorOak, OakWin
from gameplay.battle import BattleMediator
from gui_builders.pickup import  PickupItem
from gameplay.dataobservers import DataObservable
from gameplay.render_level import LevelRenderer
from abc import ABC, abstractmethod
from config.fetcher import Fetcher
from gameplay.timers import Timer
from gameplay.environments import *


# DEF_OFFSETX = 150 # default offset on x axis of dislplaying gui elements
# DEF_OFFSETY = 500 # default offset on y axis 

class Level(ABC):

    """ base class for all stages of the game
        which defines level interface
    """
    def __init__(self, 
                 screen: pygame.Surface, 
                 gamestate: str, 
                 renderer: LevelRenderer):
        
        self.screen = screen
        self.gamestate = gamestate
        self.renderer = renderer
        builder = GUIBuilder() # each is defined with a builder 
        self.bd = GUIDirector(builder) # and a director to use when necessary

    # play level to define how game play on that level should work
    @abstractmethod
    def play_level():
        pass


class WelcomeLevel(Level):

    def __init__(self, screen, gamestate, renderer: GameMapBackDrop):
        super().__init__(screen, gamestate, renderer)

        self.image, self.pos = self.renderer.render_environment()
        self.oak = ProfessorOak()
    
    
    async def play_level(self):
        
        self.screen.fill(Config.WHITE) #fill background with white

        # place backdrop on the screen at the given pos
        self.screen.blit(self.image, self.pos)
        
        # check if professor oaks state is finished meaning he has finished his intro speech
        if self.oak.current_state == 'intro_end':

            # once he is finished, the game is switched to the loading state
            self.gamestate.change_state('loading')
        
        # end the game base don his state
        elif self.oak.current_state == 'game_end':
            self.gamestate._running = False

        else:
            # otherewise display him and speeach tile on the sceen
            self.screen.blit(self.oak.image, (self.oak.current_state.x, self.oak.current_state.y)) # render his image
            oak_tile = self.oak.current_state.statement # get the current text tile in his speech
            
            if oak_tile:
                oak_tile.display(self.screen, (0, Config.SCREEN_HEIGHT - oak_tile.surface.get_height())) # display the tile
           
            #  update his image/speech state accordingly
            self.oak.update(self.bd)

class ChooseLevel(Level):
    """ class for the choose level"""

    def __init__(self, screen, gamestate,renderer: GameEnvironment, data_observable: DataObservable, fetcher: Fetcher):
        super().__init__(screen, gamestate, renderer)
        self.image, self.pos = self.renderer.render_environment()
        self.fetcher = fetcher # set up fetcher

        # create observable and attach delf
        self.choose_level_data = data_observable
        self.choose_level_data.attach(self)
        
        self.cols = self.rows = 4
        self.spacing = (Config.SCREEN_WIDTH - 
                        (Config.SCREEN_WIDTH/self.cols-20)*self.cols)/self.cols-self.cols  # spacing calculation for space between pokemon tiles
    

    def observe_update(self, field, data):
        """ receive updates from observable """
        self._fields[field] = data

    @property
    def fields(self):
        if hasattr(self, '_fields'):
            return self._fields

    @fields.setter
    def fields(self, new_fields):
            self._fields = new_fields

    async def play_level(self):
        print(self.fetcher.IS_FETCHING)
        
        # place backdrop on the screen at the given pos
        self.screen.blit(self.image, self.pos)
        if not self.fetcher._ERROR: # check if the fetcher encountered an error
            try:
                # if the page has not yet be initialised , fetch the pokemon on the counter'th page
                # i.e. if count is 0 then get the fetcher's first page
                # each page has 16 pokemon as explained in fetcher

                if self.fetcher.counter == 0:
                    result = await self.fetcher.fetch()
                    if result == False: 
                        # this exception is used avoid rendering the rest of the page before
                        # the fetcher error check is checked again. This way we can exit the 
                        # if statement early and render the error message
                        raise Exception()

                self._render_tiles_eff()
                self._display_tiles_with_hover_and_click()
                self._display_pokemon_count()
                self._continue_to_exolore()
                self._display_next_previous()
                 
            except Exception as e:
                # TODO: add logging for errors
                pass
                
        else:
            
            # create and display error message
            error_message = self.bd.create_error('Sorry :( Cannot establish a conenction:', 'Please Try again')
            error_message.display(self.screen, (Config.CENTER[0]-error_message.surface.get_width()//2, Config.CENTER[1]-error_message.surface.get_height()//2))

    def _render_tiles_eff(self):

        # for every pokemon on the page,  the respective tile with a name and image is created 
        for ind, pokemon_data in enumerate(self.fetcher._data[self.fetcher._page]):

            # check the number of current tiles against the page limit
            # the number of tiles per page is always refreshed from 0 so it is safe to check it against the limit
            # this check ensures that the pokemon_tiles are not constantly recreated when displaying on the screen
            if len(self._fields['current_tiles']) != self.fetcher._LIMIT:
                pokemon_tile = self.bd.create_pokemon_tile(self.cols, self.spacing, pokemon_data['front'], pokemon_data['name'])
                
                # create a list of tile, data pairs; the __eq__ definition of a button using id 
                # allows us to use the id to check if the pokemon button is in the list
                if pokemon_tile not in [tile[0] for tile in self._fields['current_tiles']]:
                    
                    # update the current tiles in the data observable data, this pushes notification to all other observers of the observable
                    self.choose_level_data.set_field('current_tiles', (pokemon_tile, pokemon_data))

                # calculate the position of the tile based on it's index in the list, this way we get a sort of wrapping effect
                # using the modulus to determine the row and the floor to deterimine the column
                pos = (ind % self.cols * (pokemon_tile.width + self.spacing) + self.spacing,
                        ind // self.rows * (pokemon_tile.height + self.spacing) + self.spacing)

                # updte the tiles bounding rect to palce the hover rect in the correct position 
                pokemon_tile.update_rect(pos[0], pos[1])

    def _display_tiles_with_hover_and_click(self):

        for pk_tile, _  in (self._fields['current_tiles']):
            pk_tile.display(self.screen, pk_tile.rect)

            # activate onclick for pokeomn selceted
            if pk_tile in [data[0] for data in self._fields['chosen']]:
                pk_tile.onclick(self.screen)

            # if the pokemon has been hovered on, the data stores hover is updated 
            # and the on hover function is executed
            if self._fields['hover']:
                self._fields['hover'][0].onhover(self.screen, Config.RED)  

    def _display_pokemon_count(self):
        # create and dispaly a counter indicator to show how many pokemon have been selected
        pokemon_counter = self.bd.create_choose_count(f"{len(self._fields['chosen'])} / {Config.POKEMON_COUNT}")
        pokemon_counter.display(self.screen ,(0, Config.SCREEN_HEIGHT-pokemon_counter.surface.get_height()))

    def _continue_to_exolore(self):
        if len(self._fields['chosen']) ==  Config.POKEMON_COUNT:
            self.start_explore = self.bd.create_continue_button("[ ENTER ] to Explore the Village Now!")
            self.start_explore.display(self.screen, (Config.CENTER[0]-150, Config.SCREEN_HEIGHT-50))

    def _display_next_previous(self):

        # create next and previous buttons
        fetcher_next = self.bd.create_fetcher_button(f" Next Page ({self.fetcher.page+1})")
        fetcher_prev = self.bd.create_fetcher_button(f"Prev Page ({self.fetcher.page-1})")

        if self.fetcher.not_at_end():
            w = fetcher_next.surface.get_width()
            fetcher_next.display(self.screen, (Config.SCREEN_WIDTH - w, 0))

        # render the previous page as long as the current page number greater than 1  
        if self.fetcher.not_at_start():
            fetcher_prev.display(self.screen, (0, 0))
        
class HomeTownLevel(Level):
    
    """ first stage where the trainer can explore the hometown"""

    def __init__(self, screen, gamestate, renderer: GameMapTSX, player_hit: Hit, trainer: Trainer, data_observable: DataObservable):
        super().__init__(screen, gamestate, renderer)
        
        # set games current trainer instance
        # self.trainer_mediator = trainer_mediator
        self.trainer = trainer
        # trainer_mediator.notify('get')

        # set up the explore observable and attach itself to listen to changes in explore level data
        self.explore_level_data = data_observable
        self.explore_level_data.attach(self)
        
        # camera for focusing the player movement and ysort layer is a group of sprites as explained in environments 
        self.cam, self.ysortlayer = self.renderer.render_environment()
        
        # set this to the initial group of sprites that the train can collide with
        self.trainer_collide = self.ysortlayer

        #  then add the trainer to the group to be displayed
        self.ysortlayer.add(self.trainer)
        
        # set up the player hit detetction 
        self.player_hit = player_hit
        # create a decorator for the layer to filter the layer
        self.positive_layer_filter = DecoratorPositiveFilter(self.ysortlayer)

        # get the items by filtering for pickup items
        for item in self.positive_layer_filter.get_sprites(PickupItem):
            self.explore_level_data.set_field('items', item)

        # control music player 
        self.music = 0 # makes sure the music is only play once
        self.sound =  pygame.mixer.Sound(r'./assets/sounds/battle-start.ogg')

        # a timer to control the blink screen when a battle is initiated
        timer = Timer('delay_blink_screen', Config.FRAMERATE * 3)
        timer.time = -1 # set to -1 to allow the trainer to move

        # notify the observable and all its other observers about the timer
        self.explore_level_data.set_field('timer', timer, unique=True)


    async def play_level(self):
        
        # create a negative filter for the updated ysort layer
        self.negative_layer_filter = DecoratorNegativeFilter(self.ysortlayer)
        
        self._handle_item()

        # focus the camera on the trainer
        self.cam.custom_focus(self.screen, self.trainer)

        # detect collisions between the trainer and all sprites in the trainer collide list
        self.player_hit.detect_hit(self.trainer, self.trainer_collide)

         # update the trainer based on its animation state, this is only done 
        #  when the timer is not set, if the timer is set
        #  a battle is about to begin and the trainer cant move
        if self._fields['timer'][0].time < 0:
            self.trainer.update()

        self._handle_challengers()
        self._set_challenger()

        # handle toggling the bag on or off
        self._handle_toggle_bag()
        self._battle_start()
        

    def _battle_start(self):

        if self._fields['timer'][0].time > 0:
            self._fields['timer'][0].wait()
            if self.music == 0:
                    self.music +=1
                    self.sound.play()
            if (self._fields['timer'][0].time // 10) % 2 == 0: 
                self.screen.fill(Config.BLACK)

        if self._fields['timer'][0].is_finished(): 
            self.music = 0
            self._fields['timer'][0].time = -1
            self.explore_level_data.set_field('timer', self._fields['timer'][0], unique=True)
            self.gamestate.change_state('battle')

    def observe_update(self, field, data):
        # receive updates form the observeble
        self._fields[field] = data

    @property
    def fields(self):
        if hasattr(self, '_fields'):
            return self._fields
        else:
            pass

    @fields.setter
    def fields(self, new_fields):
            self._fields = new_fields

    def _set_challenger(self):
        # filter the list of challengers by the one who is actually challenging
        current_chal = list(filter(lambda c: c.challenging, self.positive_layer_filter.get_sprites(Challenger)))
        
        # update the trainer is challenged, this way the trainer can choose to engage in battle or not
        self.trainer.is_challenged = current_chal[0] if current_chal else None
    def _handle_item(self):
        """ handle siplaying the items of they are in the bag or not """
        for item in self._fields['items']:


            # check if any items is in the bag
            if self.trainer.bag.has_item(item.name) and item in self.ysortlayer:
                
                # if so remove the item from ysort layer
                item.kill()
                
                # update the items with which the trauner can collide, i.e. remove the sprite picked up
                self.trainer_collide = self.negative_layer_filter.get_sprites(Trainer)
                # unset the item in the observable
                self.explore_level_data.unset_field('items', item)

    def _handle_challengers(self):

        for challenger in self.renderer.challengers:
            
            # update the challenger based on if it is alerted by the trainer
            challenger.update(self.screen, self.trainer) 
            challenger.create_mask()

            # each lineup of pokemon is given a mediator to handle a potential battle with the trainer
            if not challenger.pokemon.mediator:
                # increment the number of challengers that the trainer must face in order to detect the overall win
                self.trainer.chal_remaining += 1
                challenger.pokemon.mediator = BattleMediator(self.trainer.pokemon, challenger.pokemon, self.bd)


    def _handle_toggle_bag(self):
        # the bag can be toggled to show all the items collected
        if self.trainer.bag.show:
            # display the bag
            self.trainer.bag.bag_icon.display(self.screen, (10, 10))
            # use the item index to display it in the right position
            for index, item in enumerate(self.trainer.bag.items, 1):
                w, h = item.image.get_size()
                w, h = w * Config.WIDTH_SCALE, h * Config.HEIGHT_SCALE
                image = pygame.transform.scale(item.image, (w, h))
                self.screen.blit(image, (45, index*h + h))
 
class LoadingLevel(Level):
    """ Intermediate stage of the game, to display when fetcher is loading data"""
    def __init__(self, screen, gamestate, renderer: GameMapBackDrop):
        super().__init__(screen, gamestate, renderer)
        self.image, self.pos =  self.renderer.render_environment()

    async def play_level(self):
        self.screen.blit(self.image, self.pos)
        self.gamestate.change_state('choose')

class ControlsLevel(Level):
    """ display the controls page"""

    def __init__(self, screen, gamestate, renderer: GameMapBackDrop, fetcher: Fetcher):
        super().__init__(screen, gamestate, renderer)
        self.image, self.pos =  renderer.render_environment()
        self.show = False
        self.fetcher = fetcher

        self.data = None
        self.header = None
        self.ctrls = []

    async def play_level(self):

        fetched = self.fetcher.fetch()
       
        self.screen.blit(self.image, self.pos)
        #  for each control, display it in the correct position

        if self.data != fetched:
            self.data = fetched
            self.header = self.bd.create_control_header(self.data['header'])
            self.ctrls = []
            for control, desc in self.data['controls'].items():
                self.ctrls.append(self.bd.create_control(control, desc))

        for index, ctrl in enumerate(self.ctrls, 1):
            ctrl.display(self.screen, (25, (index  * ctrl.surface.get_height() + 20 + (index * 20))))
        self.header.display(self.screen, (Config.CENTER[0] - (Config.SCREEN_WIDTH//2)//2, 20))
        self._display_next_previous()

    def _display_next_previous(self):

        # create next and previous buttons
        fetcher_next = self.bd.create_fetcher_button(f" Next Page ({self.fetcher.page+2})")
        fetcher_prev = self.bd.create_fetcher_button(f"Prev Page ({self.fetcher.page+1})")

        if self.fetcher.not_at_end():
            w = fetcher_next.surface.get_width()
            fetcher_next.display(self.screen, (Config.SCREEN_WIDTH-w, 0))

        # render the previous page as long as the current page number greater than 1  
        if self.fetcher.not_at_start():
            fetcher_prev.display(self.screen, (0, 0))

class BattleLevel(Level):

    def __init__(self, screen, gamestate, renderer, trainer_mediator):
        super().__init__(screen, gamestate, renderer)
        self.image, self.pos =  self.renderer.render_environment()
        self.oak = ProfessorOak()

        # define the trainer_mediator, and the challenger that is currently challenging the trainer
        self.trainer_mediator = trainer_mediator
        self.challenger = self.trainer_mediator.notify('is_challenged')
        
        # set the mediator of the level and trainer pokemon so they share the same instance of the battle mediator
        self.mediator = self.challenger.pokemon.mediator 

        # set the trainer pokemon mediator to the current mediator
        self.trainer_mediator.notify_pokemon('set_mediator', self.challenger.pokemon.mediator )
        
        # initialize the pokemon in trainer and challenger lineup
        for pokemon in self.trainer_mediator.notify_pokemon('get_all'):
            pokemon.initialize_for_fight(self.bd)

        for pokemon in self.challenger.pokemon:
            pokemon.initialize_for_fight(self.bd)

        self._music = 0 # ontrol music to play oce
        self.sound = pygame.mixer.Sound(r'./assets/sounds/battle-repeat.ogg')
       
    async def play_level(self):

        self.screen.blit(self.image, self.pos)
        
        #  handle the current fight in the mediator
        win_check = self.mediator.current_fight(self.screen)

        # play the music once 
        if self._music == 0 and win_check== None:
            self.sound.play(loops=-1)
            self._music += 1

        # stop the sound if a winner is found
        if win_check != None:
            self.sound.stop()

            # if the trainer won, they can continue exploring and the challenger is defeated and can no longer regen pokemon to battle
            if win_check== True:
                self.challenger.defeated = True
                self.trainer_mediator.notify('reduce_chals')
                self.gamestate.change_state('explore_hometown')

            # if the trainer lost, they are sent back to the intro screen with oak in his lose state
            elif win_check == False:
                self.oak.current_state = self.renderer.lose_state(self.oak)
                self.gamestate.change_state('welcome')


        self._overall_win()

    def _overall_win(self):
        self.trainer_mediator.notify('get_chals')
        if self.trainer_mediator.notify('get_chals') <= 0:
            oak = ProfessorOak()
            oak.current_state = OakWin(oak)
            self.gamestate.change_state('welcome')

