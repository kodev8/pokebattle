# Pokemon API
import aiohttp
import asyncio
import math
from config.config import Config
from aiohttp.client_exceptions import ClientConnectorError
from abc import ABC, abstractmethod
import random
import platform
import base64
from PIL import Image
import io
from config.requesthandler import JSRequestHandler, PythonRequestHandler
import json

# suppress runtime errors
if platform.system() == 'Windows':
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
    IS_FETCHING = False
    
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

    async def forward_page(self):
        """ go forward a page and fetch it's data"""

        # Facade pattern since Fetch local is abstracted and seems relatively simple *****
        # as long as the current page is less than than the max page the page can go forward
        # if there is no error the respective fetch method is executed
        
        if self.not_at_end():
            FetchPokemon._page += 1
            if not FetchPokemon._ERROR:
                await self.fetch()
  
    def back_page(self):
        """go back a page """
        if FetchPokemon._page != 1:
            FetchPokemon._page -= 1


    def fetch(self) -> list:

        """ fetch pokemon info using a the correct fetching method """

        # similar to the bridge pattern where the fetch is abstarcted to different types of fetch methods
        # the implementation of the FetchMethod interface can be changed without affecting the Fetcher hierarchy.
        return self.local_method.fetch() if not self.designate_fetch_method() else self.async_method.fetch()
            
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
    async def __get_pokemon(self, url, page=False) -> dict:
        # Fetch Page of pokemon e.g. url = "https://pokeapi.co/api/v2/pokemon/?offset=0&limit=20" => {"results": [pokemon1, pokemon2, ...]}

        request_handler = JSRequestHandler(return_type='text') if Config.IS_WEB else PythonRequestHandler()
        data = await request_handler.get(url)

        if not data: return {}
        if type(data) == str:
            data = json.loads(data)

        if page: 
            return data['results']
        else:

            img_front_url, img_back_url = data['sprites']['front_default'], data['sprites']['back_default']
            
            # if pokemon don't have an image from the back we dont consider them
            if not img_back_url or not img_front_url:
                pass
            
            else:

                if Config.IS_WEB:
                    # brh: blob request handler
                    brh = JSRequestHandler(return_type='blob')
                    img_front_bytes = await brh.get(img_front_url) # b64 encoded image 
                    
                    # if type(img_front_bytes) == str:
                    imf_bg4 = base64.b64decode(img_front_bytes.split(',')[1])
                    imf_io = io.BytesIO(imf_bg4)
                    img = Image.open(imf_io)
                    img_front = r'./assets/images/{}-front.png'.format(data['name'])
                    img.save(img_front, 'PNG')
                    # else:
                    #     img_front = img_front_bytes
                    # img_front = await img_front_bytes.read()

                    # async with session.get(img_back_url) as img_back_bytes:
                    img_back_bytes = await brh.get(img_back_url)
                    # if type(img_back_bytes) == str:
                    imb_64 = base64.b64decode(img_back_bytes.split(',')[1])
                    imb_io = io.BytesIO(imb_64)
                    img = Image.open(imb_io)
                    img_back = r'./assets/images/{}-back.png'.format(data['name'])
                    img.save(img_back, 'PNG')
                   
                else:

                    # should be python request handler
                    img_front = await request_handler.get(img_front_url, handle='blob')
                    img_back = await request_handler.get(img_back_url, handle='blob')
 

                # return all the relevant data for this game, i.e. pokemon name, valid moves, front and back sprite
                return {
                        "name":data['name'].split('-')[0], 
                        "moves": data['moves'], 
                        "front":img_front, 
                        'back':img_back
                        }
        
    async def __get_pokemon_page_data(self, links: list[list]):

        """ this fucntion gets the data on each 'page'; 
        each page has size of the limit designated by it's fetcher handler"""

        # create tasks for fetching data from each URL and append them to the tasks list
        # using ensure future to schedule co routines
        tasks = [asyncio.ensure_future(self.__get_pokemon(link['url'])) for link in links]

        #  wait for the completion of all tasks concurrently and get the results                
        fetched_pokemon = await asyncio.gather(*tasks)

            # iterate over the fetched pokemon and add them to the _pokemon dictionary
        for  pokemon in fetched_pokemon:
            if pokemon is not None:
                self.fetcher._data[self.fetcher._page].append(pokemon)
        
        self.fetcher.IS_FETCHING = False
        return self.fetcher._data[self.fetcher._page]
                    
    async def __get_page_data(self) -> dict:
        
        """ gets the data for a page (not on the page) this is a request to the pokepai to """

            # see get_pokemon_page_data for explanation
        url = f"https://pokeapi.co/api/v2/pokemon/?offset={(self.fetcher._page-1) * self.fetcher._LIMIT}&limit={self.fetcher._LIMIT}"

        page = await self.__get_pokemon(url, page=True)
        
        return page
        
    async def fetch(self):
        print('fetching... before')
        # fetch the respective links on a page
        links = await self.__get_page_data()
        self.fetcher.counter = 1 # increments the counter 
        res = await self.__get_pokemon_page_data(links)
        print('fetching... after')

        return res
        

class FetchControls(Fetcher):
    """ controls fetcher based on state of the game"""
    
    _page = 0

    # list of all available controls base on leve
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
