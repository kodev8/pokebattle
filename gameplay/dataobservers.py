from abc import ABC, abstractmethod

class DataObservable(ABC):
    """ Abstract base class for a Data Observable, implements the mediator and observer pattern"""
    @abstractmethod
    def attach():
        pass

    @abstractmethod
    def detach():
        pass

    @abstractmethod
    def notify():
        pass

    @abstractmethod
    def set_field():
        pass
    
    @abstractmethod
    def unset_field():
        pass

    @abstractmethod
    def reset_field():
        pass
    
    @abstractmethod
    def detachall():
        pass

class ConcreteLevelData(DataObservable):

    """ parent class for most Data Observables"""
    
    def attach(self, observer):
        """ attach unique observers to list of observers/subscribers"""
        if observer not in self._observers:

            #  if the observer does not already have the _fields property
            # their fields property will be set
            if not hasattr(observer, '_fields'): 
                observer.fields = self._fields

            else:
                # otherwise their fields will be set to the current value of the observable's
                #  _fields' values
                for key, value in self._fields:
                    observer.fields[key] = value

            self._observers.append(observer)

    def detach(self, observer):
        """ detach a single observer to list of observers/subscribers"""

        if observer in self._observers:
            self._observers.remove(observer)

    def detachall(self):
        """ detach all current observers"""
        for observer in self._observers:
            self.detach(observer)

    def notify(self, field):
        """ notify all observers of a change in the given field"""
        for observer in self._observers:
            observer.observe_update(field, self._fields[field])
    
    def set_field(self, field, data, unique=False):
        """ sets the value of a given field, unique determines if that field should be the only value
        once the field is updated, all observers receive the update in their _fields property"""
        if unique:
            self.reset_field(field)
        
        self._fields[field].append(data)
        self.notify(field)
    
    def unset_field(self, field, data):
        """ remove a value from a given a field"""
        self._fields[field].remove(data)
        self.notify(field)

    def reset_field(self, field):
        """ set the field property back to an empty list"""
        self._fields[field] = []
        self.notify(field)

class ChooseLevelData(ConcreteLevelData):
    """ stores and updates data about the choose level"""

    _fields = {
        "chosen":[],
        "hover":[],
        "current_tiles":[]
    }

    _observers = []

class ExploreLevelData(ConcreteLevelData):
    """ stores and updates data about the explore level"""


    _fields = {
        'items':[],
        'timer':[]
    }
    _observers = []