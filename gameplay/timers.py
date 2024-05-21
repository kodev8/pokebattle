from abc import ABC, abstractmethod


class AbstractTimers(ABC):

    @abstractmethod
    def __getitem__():
        pass

    @abstractmethod
    def add():
        pass

    @abstractmethod
    def remove():
        pass
class AbstractTimer(ABC):

    @abstractmethod
    def __eq__():
        """redefine testing equality of 2 timers"""

        pass
        
    @abstractmethod
    def wait():
        """ wait decrements the timer until it is 0"""
        pass

    @abstractmethod
    def reset():
        """reset the timer to it's original value"""
        pass   

    @abstractmethod
    def is_finished():
        """ checks if a time is"""
        pass

class Timers(AbstractTimers):
    """ collection of timers """
    def __init__(self):
        self.timers = []
      

    def __getitem__(self, timer_type: str):
        """ Redefine indexing the list,similar to a dictionary but it cannot be updated"""
        for i in self.timers:
            if i.timer_type == timer_type:
                return i
        return
        
    def add(self, timer):
        """ define add method for appending to the group of timers"""

        assert isinstance(timer, AbstractTimer)
        if timer not in self.timers:
            self.timers.append(timer)

    def remove(self, timer: AbstractTimer):
        """ remove timer from a group of timers"""
        self.timers.remove(timer)





class Timer(AbstractTimer):

    """Timer class to delay code"""

    def __init__(self, timer_type, time):
        self.base_time = time
        self.timer_type = timer_type
        self.time = time

    def __eq__(self, other):
        """redefine testing equality of 2 timers"""
        assert isinstance(other, Timer)
        return self.timer_type == other.timer_type

    def wait(self):
        """ wait decrements the timer until it is 0"""
        if self.time > 0:
            self.time -= 1

    def reset(self):
        """reset the timer to it's original value"""
        self.time = self.base_time
        
    def is_finished(self):
        """ checks if a time is"""
        return self.time == 0