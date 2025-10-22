import argparse
import multiprocessing
DEFAULT_CONCURRENT_WORKERS = multiprocessing.cpu_count()


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
