import argparse
import multiprocessing

import socket
DEFAULT_CONCURRENT_WORKERS = multiprocessing.cpu_count()


def create_argument_parser() -> argparse.ArgumentParser:
    


    # HTTP Flooder Argument Parser
    parser = argparse.ArgumentParser(
        description="test tool",
        usage="%(prog)s (-t <target_url> | -ip <target_ip>) [-p <ports>] [-tr <thread_count>] [-n <sleep_time>]"
    )


    group = parser.add_mutually_exclusive_group(required=True)



    group.add_argument(
        "-t", "--target_url",
        type=str,
        help="Target URL to flood (e.g., http://example.com)"
    )
    group.add_argument(
        "-ip", "--target_ip",
        type=str,
        help="Target IP address for UDP/TCP flood"
    )

    parser.add_argument(
        "-p", "--port",
        type=str,
        default="80,443",
        help="Target ports for UDP/TCP flood (comma-separated, default: 80,443)"
    )
    
  
    parser.add_argument("--scan-common", action="store_true", help="Scan common ports only")
    parser.add_argument(
        "--scan-range",
        type=str,
        default="1-1000",
        help="Scan a range of ports in the format start-end (e.g., 1-1000)"
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
    

    parser.add_argument(
            "-m", "--method",
            type=str,
            default='post',
            help="HTTP method to use (default: post) post/get"
        )
    

    # UDP/TCP Flooder Argument Parser
        
    return parser

def validate_arguments(args: argparse.Namespace) -> bool:
    """Validate command line arguments"""
    if args.target_url and not args.target_url.startswith(('http://', 'https://')):
        print("Error: Target URL must start with http:// or https://")
        return False
    
    if args.target_ip:
        try:
            socket.getaddrinfo(args.target_ip, None)
        except socket.gaierror:
            print(f"Error: Invalid target IP address or domain: {args.target_ip}")
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
