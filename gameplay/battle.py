from config.config import Config
from gameplay.timers import Timers, Timer
from abc import ABC, abstractmethod


class PokemonIterator:
    """ define an iterator pattern for pokemon lineups for trainer and challenger"""
    def __init__(self, collection):
        self._collection = collection
        self._position = 0
    
    def has_next(self):
        """ function to check if there is another value in the list after the current value"""
        return self._position <  len(self._collection)
    
    def _current(self):
        """ return the current value at the current index"""
        if not len(self._collection):
            return 
        
        return self._collection[self._position]
    
    def __next__(self):
        """ move forward one position on the array of values"""
        if self.has_next():
            value = self._collection[self._position]
            if value.states['fainted']:
                self._position += 1
            self._position += 1
        else:
            raise StopIteration()
        
        return value
    
class AbstractLineup(ABC):

    """ Abstract Base Class to set up an interface for a lineup of pokemon"""

    @abstractmethod
    def mediator(self):
        pass

    @abstractmethod
    def get_current(self):
        pass

    @abstractmethod
    def add(self):
        pass

    @abstractmethod
    def remove(self):
        pass

    @abstractmethod
    def __len__(self):
        pass

    @abstractmethod
    def __iter__(self):
        pass

    
class Lineup(AbstractLineup):
    """Concrete line up is udes to maintain and iterate through the trainer/challenger's pokemon when necessary"""
    def __init__(self, collection):
        self._collection = collection
        self._mediator = None

    @property
    def mediator(self):
        """ get the battle mediator for a line up of pokemon"""
        return self._mediator

    @mediator.setter
    def mediator(self, new_mediator):
        """ set the battle mediator for a line up """
        assert(isinstance(new_mediator, BattleMediator))
        self._mediator = new_mediator

    def __len__(self):
        """ return the number of pokemon remaining in the lineup"""
        return len(self._collection)
    
    def get_current(self):
        """ get the currentl pokemon in the lineup"""
        return PokemonIterator(self._collection)._current()

    def __iter__(self):
        """ used to iterate over the line up"""
        return PokemonIterator(self._collection)

    def add(self, item):
        """ add an item to the iterable"""
        self._collection.append(item)

    def remove(self):
        """remove a single element from the beginning of the iterable"""
        self._collection.pop(0)

class BattleMediator:

    """ Mediator pattern for battle between the lineup of the trainer and challenger"""

    def __init__(self, trainer_lineup, challenger_lineup, bd):

        self.trainer_lineup = trainer_lineup        # an iteratable of trainer pokemon
        self.challenger_lineup = challenger_lineup  # an iteratable of challenger pokemon
        self.message = ''                           # the message to be displayed in the battle narrator


        # group of timers to delay pieces of code
        self.timers = Timers()
        self.timers.add(Timer('delay_choose', Config.FRAMERATE))        # delays the opponent choose message
        self.timers.add(Timer('delay_outcome', Config.FRAMERATE * 2))   # displays the outcome for a given amount of time
        self.timers.add(Timer('delay_switch_turn', Config.FRAMERATE/2)) # delays the challenger attack
     
        #  possible states of the battle
        self.battle_states = {
            'turn':'trainer',       # manages turns, can be trainer or challenger
            'end': False,           # checks if the battle is over and messgae has played
            'allow_attacks':False,  # checks if attacks are permitted at the time, avoids spamming attacks
        }

        # build director to create and display gui elements
        self.bd = bd  

    def current_fight(self, screen):
        """ handle the current fight between trainer and challenger"""

        if self._check_challenger_win():
            # check if the challenger has won and handle it accordingly
            self._handle_battle_end(screen, 'challenger')
            if self.battle_states['end']:
                return False
            
        elif self._check_trainer_win():
            # check if the trainer has won and handle it according
            self._handle_battle_end(screen, 'trainer')
            if self.battle_states['end']:
                return True
        else:
            # if neither has won, continue the battle
            self._handle_battle(screen)

    def _check_challenger_win(self):
        # if the trainer has no pokemon left, the challenger has won
        return len(self.trainer_lineup) == 0
    
    def _check_trainer_win(self):
        # if the challenger has no pokemon left, the trainer has won
        return len(self.challenger_lineup) == 0

    def _handle_battle_end(self, screen, winner):
        """ handles the end of the battle, accepts trainer or challenger as the winner"""

        win_check = True if winner == 'trainer' else False
        self.battle_states['trainer_win'] = win_check
        outcome = self.bd.create_battle_end(win=win_check) # conditional rendering of outcome message bsed on winner
        width, height = outcome.surface.get_size()
        # display  the outcome message on the screen
        outcome.display(screen, ((Config.SCREEN_WIDTH - width)/2, Config.CENTER[1] - height/2 ))

        
        # use the timer to delay the message of the outcome the battle
        #  and keeps it on the screen for a given amount of time
        self.timers['delay_outcome'].wait()
        if self.timers['delay_outcome'].is_finished():

            # once the message is finished being displayed, the battle has officially ended
            self.battle_states['end'] = True
      
   
    def _handle_battle(self, screen):
        """ handles the moves and switching turn of the battle"""

        # always create the narrator with an updated message
        self.narrator = self.bd.create_battle_narrator(self.message)

        # define the current pokemon for each lineup
        trainer_pokemon = self.trainer_lineup.get_current()
        challenger_pokemon = self.challenger_lineup.get_current()

        # attacks are allowed if both pokemon are in the ready position and neither of them are attacjing
        self.battle_states['allow_attacks'] = (
            challenger_pokemon.states['ready'] and trainer_pokemon.states['ready'] 
            ) and (not challenger_pokemon.states['attack'] and not trainer_pokemon.states['attack'])

        # handle the trainers turn
        self._handle_turn(screen, trainer_pokemon, challenger_pokemon, by='trainer')

        # add a delay when switching turns
        self.timers['delay_choose'].wait()
        if self.timers['delay_choose'].is_finished():
                
            # once the delay is complete, handle the challenger's turn
            self._handle_turn(screen, challenger_pokemon, trainer_pokemon, by='challenger')
            

            # if neither of them has won already and it is the challengers turn, an automatic attack is allowed from
            # the challanger, which is then sent to the mediator to be handled all over again
            if not self._check_challenger_win() and not self._check_trainer_win():

                self.timers['delay_switch_turn'].wait()
                if self.battle_states['turn'] == 'challenger' and self.timers['delay_switch_turn'].is_finished():
                    
                    self.challenger_lineup.get_current().attack(self)

        # display the updated message in the narrator   
        self.narrator.display(screen, (0, Config.SCREEN_HEIGHT - self.narrator.surface.get_height()))

    def _turn_variables(self, by):
        """ configure the variables for the trainer and challenger's turns respectively """

        if by == 'trainer':
            in_direction = 'right'
            out_direction = 'left'
            name = 'Trainer'
            current_lineup = self.trainer_lineup
        
        elif by == 'challenger':
            in_direction = 'left'
            out_direction = 'right'
            name = 'Opp'
            current_lineup = self.challenger_lineup

        return in_direction, out_direction, name, current_lineup

    def _handle_current_alive(self, screen, in_direction, name, current_turn, oppose_turn, by):
        """ handle the turn if the pokemon is alive"""

        # the gui elements are displayed
        current_turn.show_elements(screen, in_direction, self.bd)

        # if the pokemon is not yet in the 'ready' position, this means that a pokemon is floating in
        # for the first time to battle so the message is updated to notify that
        # the trainer/challenger is choosing a new pokemon
        if not current_turn.states['ready']:
            self.message = f'{name} chose {current_turn.name}'
        
        # if neither player is attacking, no message is displayed
        elif not oppose_turn.states['attack'] and not current_turn.states['attack']:
            self.message = ''

        # pokemon have a reduce health state, if this is positive their health is reduced by that amount
        # but in a linear manner to give the effect that the health bar is gradually going down 
        if current_turn.states['reduce_health'] >= 0:

            if current_turn.states['reduce_health']  > 0:
                current_turn.hp -= 1 # hp is reduced the same amount as the reduce health
                current_turn.states['reduce_health'] -= 1

            # once the reduce health hits 0, some updates are made
            elif current_turn.states['reduce_health'] == 0:
                
                oppose_turn.states['attack'] = False # it is certain that the opponent is not attacking, so their attack status is set to fales
                self.battle_states['turn'] = by # the turn is switched back to the current player
                
                # the reduce health status is reset to -1 so that this section of the code is not executed until the reduce health is positive again
                current_turn.states['reduce_health'] = -1 

                # if this was the challengers turn, the delay switch timer is reset so that the delay is made on each turn
                if by == 'challenger':
                    self.timers['delay_switch_turn'].reset()

    
    def _handle_current_faint(self, screen, current_turn, out_direction, current_lineup, oppose_turn, by):
            """ handle the current turn if the pokemon haas fainted"""

            # notify the narrator that a poskemon has fainted
            self.message = f'{current_turn.name} has fainted'

            # show the elements but now floating to the out position
            current_turn.show_elements(screen, out_direction, self.bd, out=True)

            # once the pokemon arrives at its offscreen position, its fainted state will be set to true, hence
            # we wait for the pokemon to be fainted
            if current_turn.states['fainted']:
                current_lineup.remove() # remove it from the lineup


                # if  a pokemn has fainted, this means its turn was missed, 
                # so here we keep the turn as whoevers pokemon fainted to allow them to attack
                # if they have another pokemon
                self.battle_states['turn'] = by 

                # turn off the attacking state of the opponent to allow new attacks
                oppose_turn.states['attack'] = False

    
    def _handle_turn(self, screen, current_turn, oppose_turn, by):
        """ create turn variables and execute turns"""
        
        in_direction, out_direction, name, current_lineup = self._turn_variables(by)
                    
        # if the current attacker is still alive
        if current_turn.hp > 0:
            self._handle_current_alive(screen, in_direction, name, current_turn, oppose_turn, by)
       
        # if the pokemon has no more health we handle fainting
        else: 
            self._handle_current_faint(screen, current_turn, out_direction, current_lineup, oppose_turn, by)

    def _handle_attack(self, sender_pokemon, receiver_pokemon, attack): 
        """ takes a sender pokemon, receiver pokemon and attack, this way the sender pokemon
        always executes its attack on the receiver pokemon"""

        # if the battle state conditions for allowing attacks (defined above) have been met
        if self.battle_states['allow_attacks']:

            # turn on the sending pokemons attack state
            sender_pokemon.states['attack'] = True

            # update the message in the narrator is updated to notify that an attack is being executed
            self.message = f'{sender_pokemon.name} used {attack.name}'   

            # the receiver pokemon reduced health state is set to the attack power of the sender
            receiver_pokemon.states['reduce_health'] = attack.power
            

    def send_attack(self, sender, attack):
        """ this function is called by the pokemon to send their attack notifications to the mediator"""
        
        # get the current pokeomn for each lineup
        trainer_pokemon = self.trainer_lineup.get_current()
        challenger_pokemon = self.challenger_lineup.get_current()

        # check the sender and handle attacks accordingly
        # ensures that the trainer can attack only on their turn
        if sender == 'trainer' and self.battle_states['turn'] == 'trainer' and challenger_pokemon:
            self._handle_attack(trainer_pokemon, challenger_pokemon, attack)

        elif sender == 'challenger':
            self._handle_attack(challenger_pokemon, trainer_pokemon, attack)