import pygame
from sprites.sprites import *
from sprites.professor_oak import ProfessorOak, OakLose, OakWin
from sprites.trainer import TrainerMediator
from config.fetcher import Fetcher
from config.config import Config
from gameplay.dataobservers import DataObservable
from abc import ABC, abstractmethod

# create singleton gamesate

class Handler(ABC):

    @abstractmethod
    def handle():
        pass

class EventHandler(Handler):
    """base class of an event handler, handle user input
     This uses the chain of responsibility pattern to handle events
     based on the current gamestate. Once the state has a handler,
     all events would be handled within corresponding handler. 
     Otherwise it is passed to the next until no handler is found
     All event handlers are defined in the same manner:
     1) the state requested is checked against the game state
     2) if this is true, we hadle that event
     3) if not it is passed to this class to handle which then sends 
     the request to the next possible handler defined
     * if no handler is found, return None
     Dependecies for each handler are mainly injected to focus on decoupling and modularity
    """
    def __init__(self, gamestate):
        self.next_handler = None
        self.gamestate = gamestate

    def handle(self, state, event):
        """ handle key and/or mouse events in the given state"""
        if self.next_handler:
            return self.next_handler.handle(state, event)
        return None


class WelcomeHandler(EventHandler):
    """ handles events in the welcome level"""

    def __init__(self,gamestate,  gameplayer):
        super().__init__(gamestate)
        self.oak = ProfessorOak()
        self.gameplayer = gameplayer

    def handle(self, state, event):
        if state == 'welcome' and self.gamestate.current_state == state:
            
            # if the space bar is pressed we update professor oak's state in the speech 
            # and if necessary, his sprite is updated
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.type == pygame.MOUSEBUTTONDOWN:
                    self.oak.current_state.speech_count += 1
                
            # allows to skip to the choose level of the game
                elif event.key == pygame.K_n:

                    if isinstance(self.oak.current_state, OakLose) or isinstance(self.oak.current_state, OakWin):
                        # if oak is in his lose state, the game is reset
                        self.gameplayer.reset()
                        self.gamestate.change_state('choose')

                    else:
                        self.gamestate.change_state('loading')

                elif isinstance(self.oak.current_state, OakWin) and event.key == pygame.K_t:
                    self.gamestate.change_state('explore_hometown')

                



            return True
            
        return super().handle(state, event)

class ChooseHandler(EventHandler):
    """handles events when picking pokemon to start a  new  game"""

    def __init__(self, data_observable: DataObservable, fetcher: Fetcher, gamestate, trainer_mediator: TrainerMediator):
        super().__init__(gamestate)

        self.fetcher = fetcher

        # set up data observable which now gives it access to its own _fields property
        self.choose_level_data = data_observable
        # attach the handler to the observable
        self.choose_level_data.attach(self)

        # create the mediator used to access a trainer's properties
        self.trainer_mediator = trainer_mediator

    @property
    def fields(self):
        if hasattr(self, '_fields'):
            return self._fields
        else:
            pass

    @fields.setter
    def fields(self, new_fields):
            self._fields = new_fields

    def handle_keys(self, event):
        """ handle key events in the chooselevel"""

        if event.type == pygame.KEYDOWN:

            # swich pages forawrd and back and clear the refernce of current tiles each time
            if event.key == pygame.K_SPACE or event.key == pygame.K_RIGHT:
                self.fetcher.forward_page()
                self.choose_level_data.reset_field('current_tiles')
    
            elif event.key == pygame.K_b or event.key == pygame.K_LEFT:
                self.fetcher.back_page()
                self.choose_level_data.reset_field('current_tiles')
                
            # add pokemon to the trainers lineup and go to exploring
            if len(self._fields['chosen']) == Config.POKEMON_COUNT and event.key == pygame.K_RETURN:
                    for pokemon in self._fields['chosen']:
                        self.trainer_mediator.notify_pokemon('add_pokemon', pokemon[1])
                    
                    # choose level handler is finished and detached from the observer
                    self.choose_level_data.detach(self)
                    self.gamestate.change_state('explore_hometown')
                        

    def handle_mouse(self, event):
        """ handle mouse events in the choose level"""
        mouse_pos = pygame.mouse.get_pos()

        tiles = self._fields['current_tiles']

        # check if any rect of the tiles collide with the mouse
        if all(not tile[0].rect.collidepoint(mouse_pos) for tile in tiles):
            self.choose_level_data.reset_field('hover')

        else:
            # for tile in self.choose_level_data.current_pokemon_tiles:
            for tile in tiles:

                # check the current pokemon tiles to find which is colliding with the mouse
                if tile[0].rect.collidepoint(mouse_pos):
                    
                    # if a tile is not already chosen then set it to the hover tile
                    if tile[0] not in [x[0] for x in self._fields['chosen']]:
                        self.choose_level_data.set_field('hover', tile[0], unique=True)

                        # if it is clicked on, remove it from being hovered
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            self.choose_level_data.reset_field('hover')

                            # if the number of chosen pokemon is less than 3 we add it to the list of chosen pokemon
                            if len(self._fields['chosen']) < Config.POKEMON_COUNT :
                                pygame.mixer.Sound(r'assets/sounds/poke-click.ogg').play() # play click sound
                                self.choose_level_data.set_field('chosen', tile)


                    # if the tile is already chosen
                    else:
                        # if we click on it again it should be removed from the chosen field
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            self.choose_level_data.unset_field('chosen', tile)


    def observe_update(self, field, data):
        """ used to accept updates from the observable"""
        self._fields[field] = data

    def handle(self, state, event): # handles keyboar and mouse movemnts
        if state == 'choose' and self.gamestate.current_state == state:

            self.handle_keys(event)
            self.handle_mouse(event)

            return True
        return super().handle(state, event)


class ExploreHandler(EventHandler):
    
    """ handle events in all the explore levels,
    allows for extension but is closed for modification. i.e. 
    new levels can be created but all explore levels events would 
    be handled here """

    def __init__(self,gamestate, trainer_mediator: TrainerMediator, data_observable: DataObservable):

        super().__init__(gamestate)
        self.music = 0 # handle playing music once

        # setup mediator and observable and _fields
        self.trainer_mediator = trainer_mediator
        self.explore_level_data = data_observable
        self.explore_level_data.attach(self)

    

    def observe_update(self, field, data):
        """ used to accept updates from the observable"""
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

    def handle(self, state, event):
        if 'explore' in state and state in self.gamestate.current_state:
            
            # handle the animation when the trainer stops moving
            if event.type == pygame.KEYUP and event.key in [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d]:
                self.trainer_mediator.notify('stand')
                
            if event.type == pygame.KEYDOWN:
                # if the x key is pressed when a chanllenger challenges the trainer, go to the battle state
                if event.key == pygame.K_x and self.trainer_mediator.notify('is_challenged'):
                    
                    # the timer field is reset and the new timer is sent to the observable to update all other listeners
                    self._fields['timer'][0].reset()
                    self.explore_level_data.set_field('timer', self._fields['timer'][0], unique=True)
                
                # pick up items using e key
                if event.key == pygame.K_e:
                    
                    for item in self._fields['items']:

                        # check if the trainer is touching the item
                        if pygame.sprite.collide_rect(self.trainer_mediator.notify('get') , item):

                            # play the pick up sound and add the item to the bag
                            pygame.mixer.Sound(r'assets/sounds/found-item.ogg').play()
                            self.trainer_mediator.notify_bag('add_item', item)

                # toggle the bike when f is pressed
                if event.key == pygame.K_f:
                    if self.trainer_mediator.notify_bag('has_item', 'bike'):
                        self.trainer_mediator.notify_bag('toggle_bike')

                # toggle showing th bag when r is pressed
                if event.key == pygame.K_r:
                    self.trainer_mediator.notify_bag('toggle_bag')

            return True
        return super().handle(state, event)
    

class BattleHandler(EventHandler):
    """ handle key events in the battle state"""

    def __init__(self, gamestate, trainer_mediator: TrainerMediator):
        super().__init__(gamestate)
        # define a list of allowed events and their corresponding values
        # values are used to index the pokemons move and select the correct one
        self.allowed_events = {pygame.K_1:1, pygame.K_2:2, pygame.K_3:3, pygame.K_4:4} # dict used to help index the list of attck moves
        self._music = 0 # handle playing music only once

        self.trainer_mediator = trainer_mediator

    def handle(self, state, event):
        
        if state == 'battle' and self.gamestate.current_state == state:

            # use keys and current mediator to attack
            if event.type == pygame.KEYDOWN and event.key in self.allowed_events:

                if self.trainer_mediator.notify_pokemon('get_all'):
                    att_pokemon = self.trainer_mediator.notify_pokemon('get_single') # get the current trainer pokemon
                    att_pokemon.attack(self.trainer_mediator.notify_pokemon('get_mediator'), self.allowed_events[event.key]) # attack using mediator

            return True
        return super().handle(state, event)
    
class ControlHandler(EventHandler):
    """ handle key events in the controls state"""

    def __init__(self,gamestate, fetcher: Fetcher):
        super().__init__(gamestate)
        self.fetcher = fetcher

    def handle(self, state, event):
        # handles whether to display controls or not
        if state == 'controls':
            if event.type == pygame.KEYDOWN:
            

                # if the c button is pressed and we are already on the controls page, it will switch back to the previous page
                if self.gamestate.current_state == 'controls':
                    if event.key == pygame.K_c:
                        self.gamestate.change_state(self.gamestate.previous_state)

                    elif event.key == pygame.K_RIGHT:
                        self.fetcher.forward_page()

                    elif event.key == pygame.K_LEFT:
                        self.fetcher.back_page()

                # otherwise switch to the control page
                else:
                    if event.key == pygame.K_c:
                        self.gamestate.change_state('controls')

               

            return True
        return super().handle(state, event)
    
