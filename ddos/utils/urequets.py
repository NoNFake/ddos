# from requests import Session
from aiohttp import ClientSession as Session


class UReq:
    def __init__(self):
        self.session = None


    def _session(self):
        self.session = Session()


    def _get(self, url) -> any:
        res = self.session 

