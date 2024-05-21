from config.config import Config
import platform
import asyncio 
from urllib.parse import urlencode
import aiohttp

class JSRequestHandler:
    """
    WASM compatible request handler
    auto-detects emscripten environment and sends requests using JavaScript Fetch API
    """

    GET = "GET"
    POST = "POST"
    _js_code = ""
    # _init = False

    def __init__(self, return_type):
        
        self.return_type = return_type

        # if not self._init:
        self.init()
        self.debug = True
        self.result = None
        # if not self.is_emscripten:
        #     try:
        #         import requests

        #         self.requests = requests
        #     except ImportError:
        #         pass

    def init(self):
        if Config.IS_WEB:
        # updated function from pygbag fetch to allow different return types

            self._js_code = """
            window.Fetch = {}
            // generator functions for async fetch API
            // script is meant to be run at runtime in an emscripten environment
            // Fetch API allows data to be posted along with a POST request
            window.Fetch.POST = function * POST (url, data)
            {
                // post info about the request
                console.log('POST: ' + url + 'Data: ' + data);
                var request = new Request(url, {headers: {'Accept': 'application/json','Content-Type': 'application/json'},
                    method: 'POST',
                    body: data});
                var content = 'undefined';
                fetch(request)
            .then(resp => resp.text())
            .then((resp) => {
                    console.log(resp);
                    content = resp;
            })
            .catch(err => {
                    // handle errors
                    console.log("An Error Occurred:")
                    console.log(err);
                });
                while(content == 'undefined'){
                    yield;
                }
                yield content;
            }
            // Only URL to be passed
            // when called from python code, use urllib.parse.urlencode to get the query string
            window.Fetch.GET = function * GET (url)
            {
                console.log('GET: ' + url);
                var request = new Request(url, { method: 'GET' })
                var content = 'undefined';
                fetch(request)
            .then(resp => resp.""" +self.return_type+"""())
            .then((resp) => {
                    console.log(resp); 
                    """ + self.return_string() + """
            })
            .catch(err => {
                    // handle errors
                    console.log("An Error Occurred:");
                    console.log(err);
                });
                while(content == 'undefined'){
                    // generator
                    yield;
                }

                yield content;
            }
            """
            # try:
            platform.window.eval(self._js_code)
            
    def return_string(self):
        if self.return_type == 'blob':
            return """
        var reader = new FileReader();
        reader.readAsDataURL(resp);
        reader.onloadend = function() {
        var base64data = reader.result;
        content = base64data;
        }
        """
        return """
        content = resp;
"""

    @staticmethod
    def read_file(file):
        # synchronous reading of file intended for evaluating on initialization
        # use async functions during runtime
        with open(file, "r") as f:
            data = f.read()
        return data

    @staticmethod
    def print(*args, default=True):
        try:
            for i in args:
                platform.window.console.log(i)
        except AttributeError:
            pass
        except Exception as e:
            return e
        if default:
            print(*args)

    async def get(self, url, params=None, doseq=False):
        # await asyncio.sleep(5)
        if params is None:
            params = {}

        if Config.IS_WEB:
            query_string = urlencode(params, doseq=doseq)
            await asyncio.sleep(0)
            content = await platform.jsiter(platform.window.Fetch.GET(url + "?" + query_string))
            self.result = content
        else:  
            # get .content when return_type is blob for image data  
            res = self.requests.get(url, params)
            self.result = res.content if self.return_type == 'blob' else res.text
        return self.result
    

class PythonRequestHandler:
    """
    Python compatible request handler
    use aiohttp to send requests in a python environment
    """

    async def get(self, url, handle='json'):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if handle == 'json':
                    return await response.json()
                elif handle == 'text':
                    return await response.text()
                elif handle == 'blob':
                    return await response.read()

    

    
