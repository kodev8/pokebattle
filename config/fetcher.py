# Pokemon API
import aiohttp
import asyncio
import math
from config.config import Config
from aiohttp.client_exceptions import ClientConnectorError
from abc import ABC, abstractmethod
import random

# suppress runtime errors
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class Fetcher(ABC):

    """ abstract base class for a Fetcher to setup fetcher interface"""
    
    @abstractmethod
    def forward_page():
        """ increment the page count by and fetch data using the required fetch method"""
        pass

    @abstractmethod
    def back_page():
        """ decrement the page count by 1 the page count and fetch data using locally
        Always locally since this data has already been fetched asynchronously"""
        pass
    
    @abstractmethod
    def fetch():
        """ Fetch data either locally or asynchronously"""
        pass
    
    @abstractmethod
    def not_at_end():
        """ Check if any more fetches are possible"""
        pass

    @abstractmethod
    def not_at_start():
        "Check if the fetcher is at the first page"
        pass

    @abstractmethod
    def page():
        """returns the current page of the fetcher"""
        pass


class FetchMethod(ABC):
    """ Base Class to set up a fetch method"""
    def __init__(self, fetcher: Fetcher):
        self.fetcher = fetcher

    @abstractmethod
    def fetch(self):
        pass


class FetchPokemon(Fetcher):
    
    """ Class to fetch Pokemon either locally or asynchronously
    Data is store in class variables. Not a singleton to allow change of fetch methods
    on initialization
    """
    _LIMIT = 16 # limit the number of pokemon on each fetch which is the number of pokemon to be displayed on each page
    _counter = 0 # used to check the total of asynchronous fetches have been made
    _page = 1 # initial page id set to 1; page to notify the user of the current page

    __max_page = math.ceil(Config.MAX_POKEMON/_LIMIT ) # calculate max number of pages
    _data = {page_number: [] for page_number in range(1,__max_page+1)} # set up empty list of pokemon for each page
    _ERROR = False # Error flag to check if there is an conenctivity error
    
    def __init__(self, async_method : FetchMethod, local_method : FetchMethod):
        super().__init__()

        # decouples fetcher and it's async method and local method
        self.async_method = async_method(self) 
        self.local_method = local_method(self)

    @classmethod
    def  gen_data(cls) -> dict:

        """ Generate a random pokemon out of the pages that have been fetched"""
    
        if cls._counter > 0:
            # checks if at least 1 async fetch has been made and choose a random page
            gen_page = random.choice([*range(1, cls._counter + 1 )])

            if gen_page:
                # once there is a valid page, choose a random pokemon
                return random.choice(cls._data[gen_page])
            
    @property
    def page(self) -> dict:
        """ gives access to the class variable page"""
        return FetchPokemon._page
    
    @property
    def counter(self) -> int:
        """ gives access to the class variable counter"""

        return FetchPokemon._counter
    
    @counter.setter
    def counter(self, _):
        """ used to increment the count by 1 regardles of the value provided;
        _ used as a throw away variable"""
        FetchPokemon._counter += 1

    def forward_page(self):
        """ go forward a page and fetch it's data"""

        # Facade pattern since Fetch local is abstracted and seems relatively simple *****
        # as long as the current page is less than than the max page the page can go forward
        # if there is no error the respective fetch method is executed
        
        if self.not_at_end():
            FetchPokemon._page += 1
            if not FetchPokemon._ERROR:
                self.fetch()
  
    def back_page(self):
        """go back a page """
        if FetchPokemon._page != 1:
            FetchPokemon._page -= 1


    def fetch(self) -> list:

        """ fetch pokemon info using a the correct fetching method """

        # similar to the bridge pattern where the fetch is abstarcted to different types of fetch methods
        # the implementation of the FetchMethod interface can be changed without affecting the Fetcher hierarchy.
        
        fetch_method = self.async_method if self.designate_fetch_method() else self.local_method
        return fetch_method.fetch()
            
    def not_at_end(self) -> bool:
        """ function determines if the page is less than the max page"""
        return FetchPokemon._page < FetchPokemon.__max_page
    
    def not_at_start(self) -> bool:
        """checks if the page is greater than one - used to conditionally render buttons"""
        return FetchPokemon._page > 1
    
    def designate_fetch_method(self) -> bool:
        """ function used to decide which fetch method should be executed"""
        return len(FetchPokemon._data[FetchPokemon._page]) == 0 


class FetchLocal(FetchMethod):
    """ fetch local handles the responsibility of fetching pokemon locally - 
    meaning it has already been stored in memory and there is no need to contact the api
    """
    def __init__(self, fetcher: Fetcher):
        super().__init__(fetcher)

    def fetch(self):       
        return self.fetcher._data[self.fetcher._page]
    
        
class FetchAysnc(FetchMethod):
    
    """ fetch local handles the responsibility of fetching pokemon asynchronously
      - meaning it is run the backgrouond in a way such that the main game loop is prevented
    from being blocked"""

    def __init__(self, fetcher: Fetcher):
        super().__init__(fetcher)

    # asynchronous function to get the page or pokemon data from the api
    async def __get_pokemon(self, session, url, page=False) -> dict:
        async with session.get(url) as resp:
            data = await resp.json()
        
        # if the page argument is set to true all the results from the page are returned
        if page:
            return data['results']
        
        # otherwise another request is made to get the sprite information as well
        else:

            img_front_url, img_back_url = data['sprites']['front_default'], data['sprites']['back_default']
            
            # if pokemon don't have an image from the back we dont consider them
            if not img_back_url or not img_front_url:
                pass
            
            else:
                async with session.get(img_front_url) as img_front_bytes:
                    img_front = await img_front_bytes.read()

                async with session.get(img_back_url) as img_back_bytes:
                    img_back = await img_back_bytes.read()

                # return all the relevant data for this game, i.e. pokemon name, valid moves, front and back sprite
                return {"name":data['name'].split('-')[0], 
                        "moves": data['moves'], 
                        "front":img_front, 
                        'back':img_back}
        
    async def __get_pokemon_page_data(self, links):

        """ this fucntion gets the data on each 'page'; 
        each page has size of the limit designated by it's fetcher handler"""

        async with aiohttp.ClientSession() as session:
            # links is a list of lists so index to get all the links as a single list
            links = links[0]
            
            # create an empty list to store asyncio tasks
            tasks = []

            # create tasks for fetching data from each URL and append them to the tasks list
            # using ensure future to schedule co routines
            for link in links:
                tasks.append(asyncio.ensure_future(self.__get_pokemon(session, link['url'])))
             
            #  wait for the completion of all tasks concurrently and get the results                
            fetched_pokemon = await asyncio.gather(*tasks)

             # iterate over the fetched pokemon and add them to the _pokemon dictionary
            for  pokemon in fetched_pokemon:
                if pokemon is not None:
                    self.fetcher._data[self.fetcher._page].append(pokemon)
                    
    async def __get_page_data(self) -> dict:
        
        """ gets the data for a page (not on the page) this is a request to the pokepai to """
        async with aiohttp.ClientSession() as session:

            # see get_pokemon_page_data for explanation
            tasks = []
            
            url = f"https://pokeapi.co/api/v2/pokemon/?offset={(self.fetcher._page-1) * self.fetcher._LIMIT}&limit={self.fetcher._LIMIT}"
            tasks.append(asyncio.ensure_future(self.__get_pokemon(session, url, page=True)))

            page = await asyncio.gather(*tasks)
            
            return page
        
    async def __fetch_async(self):
    
        # fetch the respective links on a page
        links = await self.__get_page_data()
        self.fetcher.counter = 1 #nincrements the counter 
        # used these links to get the data for each pokemon on the page
        await self.__get_pokemon_page_data(links)

    def fetch(self):
        
        # try to fetch from the api
        try:

            return asyncio.run(self.__fetch_async())

        # if the request cannot access the api because of a a connection error
        #  an error is raised.
        except ClientConnectorError:
            
            # set the fetcher error to True
            self.fetcher._ERROR = True

            # return False to indicate that no data could be found due to an eror
            return False
        


class FetchControls(Fetcher):
    """ controls fetcher based on state of the game"""
    
    _page = 0

    # list of all available controls base on level/gamestate
    _data = [
    {
        'header': 'Professor Oak Talks...',
        'controls': {
            '[ SPACE ]': 'Next Page',
            'N': 'Skip to Choose'
        }
    },
    {
        'header': 'Choose Pokemon !',
        'controls': {
            '[ SPACE ] | -->': 'Next Page',
            'B | <--': 'Previous page',
            'Left Click [ x1 ]': 'Select Pokemon',
            'Left Click [ x2 ]': 'Unselect Pokemon'
        }
    },
    {
        'header': 'Explore !',
        'controls': {
            'W, A, S, D': 'Move',
            'X': 'Battle when challenged',
            'E': 'Pickup Item',
            'R': 'Toggle Bag',
            'Shift + Move': 'Run [ running shoes ]',
            'F': 'Toggle Bike [ bike ]'
        }
    },
    {
        'header': 'Battle !',
        'controls': {
            '[ 1 - 4 ]': 'Pick move [ 1 - 4 ]'
        }
    },
    {
        'header': 'General',
        'controls': {
            'C': 'Toggle Controls',
            '[ ESC ]': 'End Game'
        }
    }
]

    def forward_page(cls):

        """ increment the page count by 1"""
        if cls.not_at_end():
            cls._page += 1
    

    def back_page(cls):
        """ decrement the page count by 1 """
        if cls.not_at_start():
            cls._page -= 1
    
    def fetch(cls):
        """ Fetch data either locally"""
        return cls._data[cls._page]
    
    def not_at_end(cls):
        """ Check if any more fetches are possible"""
        return cls._page < len(cls._data) - 1

    def not_at_start(cls):
        "Check if the fetcher is at the first page"
        return cls._page > 0
    
    @property
    def page(cls) -> dict:
        """ gives access to the class variable page"""
        return cls._page
