from .environments import *
from .camera import ExploreCamera
from .hit_detetction import HitDetection
from config.fetcher import FetchPokemon, FetchAysnc, FetchLocal, FetchControls
from sprites.trainer import TrainerMediator
from gameplay.play_level import *
from sprites.professor_oak import OakLose
from gui_builders.pickup import ItemDirector, ItemBuilder
from gameplay.dataobservers import ChooseLevelData,  ExploreLevelData
from gameplay.render_level import *
from gameplay.event_handlers import *


class LevelStore:
    """ stores and distibutes data to relevant Level classes"""
    _ALLOWED_TRAINER_SET = True
    fetcher = FetchPokemon(FetchAysnc, FetchLocal)
    control_fetcher = FetchControls()
    choose_observable = ChooseLevelData()
    explore_observable = ExploreLevelData()
    trainer_mediator = TrainerMediator()
    observables = [choose_observable, 
                   explore_observable
                   ]

    @classmethod
    def reset(cls):
        """ reset the trainer instance and data fields for each class to start a new game"""
        cls.trainer_mediator.notify_set(cls)
        for observable in cls.observables:
            for field in observable._fields:
                observable._fields[field] = [] 
            
            observable.detachall()

class HandlerCreator:
    """ key board and mouse event handler creator"""

    @staticmethod
    def create_handlers(gs, gp):

        # set up keyboard and mouse event handlers and set the next handler for each
        welcome_handler = WelcomeHandler(gs, gp)
        _choose_handler = ChooseHandler(data_observable=LevelStore.choose_observable, 
                                        fetcher = LevelStore.fetcher, gamestate=gs, 
                                        trainer_mediator=LevelStore.trainer_mediator)
        
        _explore_handler = ExploreHandler(gs, LevelStore.trainer_mediator, data_observable=LevelStore.explore_observable)
        _battle_handler = BattleHandler(gs, trainer_mediator=LevelStore.trainer_mediator)
        _control_handler = ControlHandler(gs, fetcher=LevelStore.control_fetcher)

        welcome_handler.next_handler = _choose_handler
        _choose_handler.next_handler = _explore_handler
        _explore_handler.next_handler = _battle_handler
        _battle_handler.next_handler = _control_handler

        return welcome_handler


class LevelFactory:
    """ Level Factory - Creates levels based on the given state"""

    @staticmethod
    def create_level(level_type, screen, gamestate=None):
        if 'hometown' in level_type:
            return HometownLevelCreator.create(screen, gamestate)
        elif level_type == 'choose':
            return ChooseLevelCreator.create(screen, gamestate)
        elif level_type == 'welcome':
            return WelcomeLevelCreator.create(screen, gamestate)
        elif level_type == 'battle':
            return BattleLevelCreator.create(screen, gamestate)
        elif level_type == 'loading':
            return LoadingLevelCreator.create(screen, gamestate)
        elif level_type == 'controls':
            return ControlsLevelCreator.create(screen, gamestate)
        else:
            return None
        
class AbstractCreator():
    """ Lvevel Createor InterFace: Creates A level by pairing a renderer and level player:
      by focusing on dependency injection to decouple each level from its dependencie"""
    
    def create() -> Level:
        pass

class HometownLevelCreator(AbstractCreator):
    
    @staticmethod
    def create(screen, gamestate):
        renderer = HomeTownRenderer(
            camera=ExploreCamera(),
            backdrop_renderer=GameMapTSX,
            backdrop_file=r'assets/hometown/hometown.tmx',
            baselayer=Layer(),
            ysortlayer=YSortLayer(),
            item_creator=ItemDirector(ItemBuilder()))

        return HomeTownLevel(
            screen=screen,
            gamestate=gamestate,
            renderer=renderer,
            player_hit=HitDetection(),
            trainer=LevelStore.trainer_mediator.notify('get'),
            data_observable=LevelStore.explore_observable
        )

class ChooseLevelCreator(AbstractCreator):
    @staticmethod
    def create(screen, gamestate):
        renderer = ChooseRenderer(
            backdrop_renderer=GameMapBackDrop,
            backdrop_file=r'assets/images/stadium.png'
                    )

        return ChooseLevel(
            screen=screen,
            gamestate=gamestate,
            renderer=renderer,
            data_observable=LevelStore.choose_observable,
            fetcher=LevelStore.fetcher)

class WelcomeLevelCreator(AbstractCreator):
    @staticmethod
    def create(screen, gamestate):
        renderer = WelcomeRenderer(backdrop_renderer=GameMapBackDrop,
            backdrop_file=r'assets/images/oak-lab.jpeg'
        )

        return WelcomeLevel(screen, gamestate, renderer)

class BattleLevelCreator(AbstractCreator):
    @staticmethod
    def create(screen, gamestate):
        renderer = BattleRenderer(
            backdrop_renderer=GameMapBackDrop,
            backdrop_file=r'assets/images/battle.png',
            lose_state=OakLose)

        return BattleLevel(screen, gamestate, renderer, trainer_mediator=LevelStore.trainer_mediator)

class LoadingLevelCreator(AbstractCreator):
    @staticmethod
    def create(screen, gamestate):
        renderer = LoadingRenderer(
            backdrop_renderer=GameMapBackDrop,
            backdrop_file=r'assets/images/loading.jpg'
        )

        return LoadingLevel(screen, gamestate, renderer)

class ControlsLevelCreator(AbstractCreator):
    @staticmethod
    def create(screen, gamestate):
        renderer = ControlRenderer(
            backdrop_renderer=GameMapBackDrop,
            backdrop_file=r'assets/images/controlbg.jpeg'
                    )

        return ControlsLevel(screen, gamestate, renderer, fetcher=LevelStore.control_fetcher)
