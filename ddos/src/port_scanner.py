from ..utils.ulog import log
from typing import List, Optional, Tuple
import socket
from concurrent.futures import ThreadPoolExecutor

class PortScanner:
    @staticmethod
    def scan_ports(
        target_ip: str,
        start_port: int = 1,
        end_port: int = 1000,

        max_workers: int = 100,
        timeout: float = 1.0,
    ) -> List[int]:
        log.warning(f"Scanning ports on {target_ip} from {start_port} to {end_port}...")



        open_ports = []

        def check_port(
                port: int
        ) -> Tuple[int, bool]:
            try:
                with socket.socket(
                    socket.AF_INET,
                    socket.SOCK_STREAM,
                )   as sock:
                    sock.settimeout(timeout)
                    result = sock.connect_ex((
                            target_ip,
                            port
                    ))     
                    return port, result == 0
            except Exception as e:
                log.error(f"Error checking port {port} on {target_ip}: {e}")
                return port, False


        with ThreadPoolExecutor(
            max_workers=max_workers
        ) as executor:
            results = executor.map(
                check_port,
                range(start_port, end_port + 1)
            )

            for port, is_open in results:
                if is_open:
                    open_ports.append(port)
                    log.info(f"Port {port} is open on {target_ip}.")

        log.warning(f"Port scanning completed on {target_ip}. Open ports: {open_ports}")

        return open_ports
    

    @staticmethod
    def scan_common_ports(
        target_ip: str,
        timeout: float = 1.0
    ) -> List[int]:
        
        common_ports = [
            21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445, 
            993, 995, 1723, 3306, 3389, 5900, 8080, 8443
        ]

        open_ports = []


        def check_port(
                port: int
        ) -> Tuple[int, bool]:
            try:
                with socket.socket(
                    socket.AF_INET,
                    socket.SOCK_STREAM,
                )   as sock:
                    sock.settimeout(timeout)
                    result = sock.connect_ex((
                            target_ip,
                            port
                    ))     
                    return port, result == 0
            except Exception as e:
                log.error(f"Error checking port {port} on {target_ip}: {e}")
                return port, False


        with ThreadPoolExecutor(
            max_workers=100
        ) as executor:
            results = executor.map(
                check_port,
                common_ports
            )

            for port, is_open in results:
                if is_open:
                    open_ports.append(port)
                    log.info(f"Port {port} is open on {target_ip}.")

        log.warning(f"Common port scanning completed on {target_ip}. Open ports: {open_ports}")

        return open_ports
    