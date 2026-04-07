опиши что делает проект и как его использовать

# DDoS Attack Simulation Tool
This project is a DDoS (Distributed Denial of Service) attack simulation tool designed to test the resilience of web servers against HTTP flood attacks. It allows users to generate a high volume of HTTP requests to a target server, simulating the effects of a DDoS attack.

## Features
- Simulates HTTP flood attacks by sending a large number of requests to a target server.
- Supports both HTTP and HTTPS protocols.
- Configurable request rate and duration of the attack.
- Provides options for customizing request headers and payloads.
- Implements connection management to optimize resource usage during the attack.

## Usage
1. **Installation**: Clone the repository and install the required dependencies using uv:
```bash
git clone https://github.com/NoNFake/ddos.git
cd ddos
uv install
```

```bash
uv run -m ddos 
```

## Usage Example

```bash
usage: __main__.py (-t <target_url> | -ip <target_ip>) [-p <ports>] [-tr <thread_count>] [-n <sleep_time>]

test tool

options:
  -h, --help            show this help message and exit
  -t, --target_url TARGET_URL
                        Target URL to flood (e.g., http://example.com)
  -ip, --target_ip TARGET_IP
                        Target IP address for UDP/TCP flood
  -p, --port PORT       Target ports for UDP/TCP flood (comma-separated, default:
                        80,443)
  --scan-common         Scan common ports only
  --scan-range SCAN_RANGE
                        Scan a range of ports in the format start-end (e.g., 1-1000)
  -tr, --thread_count THREAD_COUNT
                        Number of threads/processes (default: CPU count = 16)
  -n, --sleep_time SLEEP_TIME
                        Sleep time between requests in seconds (default: 0)
  -c, --concurrency CONCURRENCY
                        Concurrent requests per worker (default: 50)
  -m, --method METHOD   HTTP method to use (default: post) post/get
```