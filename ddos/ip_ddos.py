import asyncio
import multiprocessing
import platform
import sys
import time

import uvloop
from typing import Optional, Dict, List
from .utils.ulog import log, log_off, log_on



def parse_ports(ports_str: str) -> List[int]:
    if not ports_str:
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


