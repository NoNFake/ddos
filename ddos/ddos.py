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


from typing import Optional, Dict, Any
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
from .src.http_flooder import HTTPFlooder, run_http_flood



traceback.install()


# Configurations 
# =========================
SOCK_BUFF_SIZE = 1024 * 1204
MAX_HTTP_PACKET_SIZE = 16 * 1024 * 1024


asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

#  CLASSES
def worker_process(
        target_url: str,
        concurrency: int,
        sleep_time: float
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
                sleep_time
            )
        )

    except KeyboardInterrupt:
        log.warning("Worker process received exit signal. Exiting...")
    except Exception as e:
        log.error(f"Worker process encountered an error: {e}")



def main() -> None:
    parser = create_argument_parser()
    args = parser.parse_args()


    if not validate_arguments(args):
        sys.exit(1)

    print(f"""
    Starting Load Test Configuration:
    - Target URL: {args.target_url}
    - Processes: {args.thread_count}
    - Concurrency per process: {args.concurrency}
    - Sleep time: {args.sleep_time}s
    - Total workers: {args.thread_count * args.concurrency}
    """)

    processes = []

    try:
        for i in range(args.thread_count):
            p = multiprocessing.Process(
                target=worker_process,
                args=(
                    args.target_url,
                    args.concurrency,
                    args.sleep_time
                ),
                name=f"flood_worker_{i}"
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


    except Exception as e:
        log.error(f"Main process encountered an error: {e}")
        sys.exit(1) 


