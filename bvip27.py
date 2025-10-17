import base64
import hashlib
import json
import os
import platform
import random
import re
import string
import subprocess
import sys
import time
import urllib.parse
import uuid
from datetime import datetime, timedelta, timezone
from time import sleep

# Check and install necessary libraries
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    import pytz
    import requests
except ImportError:
    print('__Đang cài đặt các thư viện cần thiết, vui lòng chờ...__')
    # Use sys.executable to ensure pip corresponds to the current python environment
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "colorama", "pytz"])
    print('__Cài đặt hoàn tất, vui lòng chạy lại Tool__')
    sys.exit()

# =====================================================================================
# PART 2: AUTHENTICATION SOURCE CODE (FROM kbum1.py)
# =====================================================================================

# CONFIGURATION
FREE_CACHE_FILE = 'free_key_cache.json'      # Cache file for free key
VIP_CACHE_FILE = 'vip_cache.json'            # Cache file for VIP key
HANOI_TZ = pytz.timezone('Asia/Ho_Chi_Minh') # Hanoi timezone
VIP_KEY_URL = "https://raw.githubusercontent.com/DUONGKP2401/KEY-VIP.txt/main/KEY-VIP.txt" # URL containing the list of VIP keys

# Encrypt and decrypt data using base64
def encrypt_data(data):
    return base64.b64encode(data.encode()).decode()

def decrypt_data(encrypted_data):
    return base64.b64decode(encrypted_data.encode()).decode()

# Colors for display
xnhac = "\033[1;36m"
do = "\033[1;31m"
luc = "\033[1;32m"
vang = "\033[1;33m"
xduong = "\033[1;34m"
hong = "\033[1;35m"
trang = "\033[1;39m"
end = '\033[0m'

# Authentication banner
def authentication_banner():
    os.system("cls" if os.name == "nt" else "clear")
    banner_text = f"""
████████╗██████╗░██╗░░██╗
╚══██╔══╝██╔══██╗██║░██╔╝
░░░██║░░░██║░░██║█████═╝░
░░░██║░░░██║░░██║██╔═██╗░
░░░██║░░░██████╔╝██║░╚██╗
░░░╚═╝░░░╚═════╝░╚═╝░░╚═╝
══════════════════════════
Admin: DUONG phung
Tool BUMX FB-TDK- hỗ trợ proxy- làm job cảm xúc-VIP
══════════════════════════
"""
    for char in banner_text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(0.0001)

# DEVICE ID AND IP ADDRESS FUNCTIONS
def get_device_id():
    """Generates a stable device ID based on CPU information."""
    system = platform.system()
    try:
        if system == "Windows":
            cpu_info = subprocess.check_output('wmic cpu get ProcessorId', shell=True, text=True, stderr=subprocess.DEVNULL)
            cpu_info = ''.join(line.strip() for line in cpu_info.splitlines() if line.strip() and "ProcessorId" not in line)
        else:
            try:
                cpu_info = subprocess.check_output("cat /proc/cpuinfo", shell=True, text=True)
            except:
                cpu_info = platform.processor()
        if not cpu_info:
            cpu_info = platform.processor()
    except Exception:
        cpu_info = "Unknown"

    hash_hex = hashlib.sha256(cpu_info.encode()).hexdigest()
    only_digits = re.sub(r'\D', '', hash_hex)
    if len(only_digits) < 16:
        only_digits = (only_digits * 3)[:16]

    return f"DEVICE-{only_digits[:16]}"

def get_ip_address():
    """Gets the user's public IP address."""
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        ip_data = response.json()
        return ip_data.get('ip')
    except Exception as e:
        print(f"{do}Lỗi khi lấy địa chỉ IP: {e}{trang}")
        return None

def display_machine_info(ip_address, device_id):
    """Displays the banner, IP address, and Device ID."""
    authentication_banner()
    if ip_address:
        print(f"{trang}[{do}<>{trang}] {do}Địa chỉ IP: {vang}{ip_address}{trang}")
    else:
        print(f"{do}Không thể lấy địa chỉ IP của thiết bị.{trang}")

    if device_id:
        print(f"{trang}[{do}<>{trang}] {do}Mã Máy: {vang}{device_id}{trang}")
    else:
        print(f"{do}Không thể lấy Mã Máy của thiết bị.{trang}")

def save_vip_key_info(device_id, key, expiration_date_str):
    """Saves VIP key information to a local cache file."""
    data = {'device_id': device_id, 'key': key, 'expiration_date': expiration_date_str}
    encrypted_data = encrypt_data(json.dumps(data))
    with open(VIP_CACHE_FILE, 'w') as file:
        file.write(encrypted_data)
    print(f"{luc}Đã lưu thông tin Key VIP cho lần đăng nhập sau.{trang}")

def load_vip_key_info():
    """Loads VIP key information from the local cache file."""
    try:
        with open(VIP_CACHE_FILE, 'r') as file:
            encrypted_data = file.read()
        return json.loads(decrypt_data(encrypted_data))
    except (FileNotFoundError, json.JSONDecodeError, TypeError):
        return None

def display_remaining_time(expiry_date_str):
    """Calculates and displays the remaining time for a VIP key."""
    try:
        expiry_date = datetime.strptime(expiry_date_str, '%d/%m/%Y').replace(hour=23, minute=59, second=59)
        now = datetime.now()

        if expiry_date > now:
            delta = expiry_date - now
            days = delta.days
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            print(f"{xnhac}Key VIP của bạn còn lại: {luc}{days} ngày, {hours} giờ, {minutes} phút.{trang}")
        else:
            print(f"{do}Key VIP của bạn đã hết hạn.{trang}")
    except ValueError:
        print(f"{vang}Không thể xác định ngày hết hạn của key.{trang}")

def check_vip_key(machine_id, user_key):
    """Checks the VIP key from the URL on GitHub."""
    print(f"{vang}Đang kiểm tra Key VIP...{trang}")
    try:
        response = requests.get(VIP_KEY_URL, timeout=10)
        if response.status_code != 200:
            print(f"{do}Lỗi: Không thể tải danh sách key (Status code: {response.status_code}).{trang}")
            return 'error', None

        key_list = response.text.strip().split('\n')
        for line in key_list:
            parts = line.strip().split('|')
            if len(parts) >= 4:
                key_ma_may, key_value, _, key_ngay_het_han = parts

                if key_ma_may == machine_id and key_value == user_key:
                    try:
                        expiry_date = datetime.strptime(key_ngay_het_han, '%d/%m/%Y')
                        if expiry_date.date() >= datetime.now().date():
                            return 'valid', key_ngay_het_han
                        else:
                            return 'expired', None
                    except ValueError:
                        continue
        return 'not_found', None
    except requests.exceptions.RequestException as e:
        print(f"{do}Lỗi kết nối đến server key: {e}{trang}")
        return 'error', None
        
def seeded_shuffle_js_equivalent(array, seed):
    seed_value = 0
    for i, char in enumerate(seed):
        seed_value = (seed_value + ord(char) * (i + 1)) % 1_000_000_000
    def custom_random():
        nonlocal seed_value
        seed_value = (seed_value * 9301 + 49297) % 233280
        return seed_value / 233280.0
    shuffled_array = array[:]
    current_index = len(shuffled_array)
    while current_index != 0:
        random_index = int(custom_random() * current_index)
        current_index -= 1
        shuffled_array[current_index], shuffled_array[random_index] = shuffled_array[random_index], shuffled_array[current_index]
    return shuffled_array

def save_free_key_info(device_id, key, expiration_date):
    """Saves free key information to a json file based on device_id."""
    data = {device_id: {'key': key, 'expiration_date': expiration_date.isoformat()}}
    encrypted_data = encrypt_data(json.dumps(data))
    with open(FREE_CACHE_FILE, 'w') as file:
        file.write(encrypted_data)

def load_free_key_info():
    """Loads free key information from the json file."""
    try:
        with open(FREE_CACHE_FILE, 'r') as file:
            encrypted_data = file.read()
        return json.loads(decrypt_data(encrypted_data))
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def check_saved_free_key(device_id):
    """Checks for a saved free key for the current device_id."""
    data = load_free_key_info()
    if data and device_id in data:
        try:
            expiration_date = datetime.fromisoformat(data[device_id]['expiration_date'])
            if expiration_date > datetime.now(HANOI_TZ):
                return data[device_id]['key']
        except (ValueError, KeyError):
            return None
    return None

def generate_free_key_and_url(device_id):
    """Creates a free key based on device_id and a URL to bypass the link."""
    today_str = datetime.now(HANOI_TZ).strftime('%Y-%m-%d')
    seed_str = f"TDK_FREE_KEY_{device_id}_{today_str}"
    hashed_seed = hashlib.sha256(seed_str.encode()).hexdigest()
    digits = [d for d in hashed_seed if d.isdigit()][:10]
    letters = [l for l in hashed_seed if 'a' <= l <= 'f'][:5]
    while len(digits) < 10:
        digits.extend(random.choices(string.digits))
    while len(letters) < 5:
        letters.extend(random.choices(string.ascii_lowercase))
    key_list = digits + letters
    shuffled_list = seeded_shuffle_js_equivalent(key_list, hashed_seed)
    key = "".join(shuffled_list)
    now_hanoi = datetime.now(HANOI_TZ)
    expiration_date = now_hanoi.replace(hour=21, minute=0, second=0, microsecond=0)
    url = f'https://tdkbumxkey.blogspot.com/2025/10/lay-link.html?m={key}'
    return url, key, expiration_date

def get_shortened_link_phu(url):
    """Shortens the link to get the free key."""
    try:
        token = "6725c7b50c661e3428736919"
        api_url = f"https://link4m.co/api-shorten/v2?api={token}&url={urllib.parse.quote(url)}"
        response = requests.get(api_url, timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"status": "error", "message": f"Lỗi {response.status_code}: Không thể kết nối đến dịch vụ rút gọn URL."}
    except Exception as e:
        return {"status": "error", "message": f"Lỗi khi rút gọn URL: {e}"}

def process_free_key(device_id):
    """Handles the entire process of obtaining a free key based on device_id."""
    if datetime.now(HANOI_TZ).hour >= 21:
        print(f"{do}Đã qua 21:00 giờ Việt Nam, key miễn phí cho hôm nay đã hết hạn.{trang}")
        print(f"{vang}Vui lòng quay lại vào ngày mai để nhận key mới.{trang}")
        time.sleep(3)
        return False

    url, key, expiration_date = generate_free_key_and_url(device_id)
    shortened_data = get_shortened_link_phu(url)

    if shortened_data and shortened_data.get('status') == "error":
        print(f"{do}{shortened_data.get('message')}{trang}")
        return False

    link_key_shortened = shortened_data.get('shortenedUrl')
    if not link_key_shortened:
        print(f"{do}Không thể tạo link rút gọn. Vui lòng thử lại.{trang}")
        return False

    print(f'{trang}[{do}<>{trang}] {hong}Vui Lòng Vượt Link Để Lấy Key Free (Hết hạn 21:00 hàng ngày).{trang}')
    print(f'{trang}[{do}<>{trang}] {hong}Link Để Vượt Key Là {xnhac}: {link_key_shortened}{trang}')

    while True:
        keynhap = input(f'{trang}[{do}<>{trang}] {vang}Key Đã Vượt Là: {luc}')
        if keynhap == key:
            print(f'{luc}Key Đúng! Mời Bạn Dùng Tool{trang}')
            if datetime.now(HANOI_TZ) >= expiration_date:
                print(f"{do}Rất tiếc, key này đã hết hạn vào lúc 21:00. Vui lòng quay lại vào ngày mai.{trang}")
                return False
            time.sleep(2)
            save_free_key_info(device_id, keynhap, expiration_date)
            return True
        else:
            print(f'{trang}[{do}<>{trang}] {hong}Key Sai! Vui Lòng Vượt Lại Link {xnhac}: {link_key_shortened}{trang}')

def main_authentication():
    ip_address = get_ip_address()
    device_id = get_device_id()
    display_machine_info(ip_address, device_id)

    if not device_id:
        print(f"{do}Không thể lấy thông tin Mã Máy. Vui lòng kiểm tra lại thiết bị.{trang}")
        return False

    # 1. Prioritize checking for a saved VIP key
    cached_vip_info = load_vip_key_info()
    if cached_vip_info and cached_vip_info.get('device_id') == device_id:
        try:
            expiry_date = datetime.strptime(cached_vip_info['expiration_date'], '%d/%m/%Y')
            if expiry_date.date() >= datetime.now().date():
                print(f"{luc}Đã tìm thấy Key VIP hợp lệ, tự động đăng nhập...{trang}")
                display_remaining_time(cached_vip_info['expiration_date'])
                sleep(3)
                return True
            else:
                print(f"{vang}Key VIP đã lưu đã hết hạn. Vui lòng lấy hoặc nhập key mới.{trang}")
        except (ValueError, KeyError):
            print(f"{do}Lỗi file lưu key VIP. Vui lòng nhập lại key.{trang}")

    # 2. If no VIP key, check for a saved free key for the day
    if check_saved_free_key(device_id):
        expiry_str = f"21:00 ngày {datetime.now(HANOI_TZ).strftime('%d/%m/%Y')}"
        print(f"{trang}[{do}<>{trang}] {hong}Key free hôm nay vẫn còn hạn (Hết hạn lúc {expiry_str}). Mời bạn dùng tool...{trang}")
        time.sleep(2)
        return True

    # 3. If no key is saved, display the selection menu
    while True:
        print(f"{trang}========== {vang}MENU LỰA CHỌN{trang} ==========")
        print(f"{trang}[{luc}1{trang}] {xduong}Nhập Key VIP{trang}")
        print(f"{trang}[{luc}2{trang}] {xduong}Lấy Key Free (Hết hạn 21:00 hàng ngày){trang}")
        print(f"{trang}======================================")

        try:
            choice = input(f"{trang}[{do}<>{trang}] {xduong}Nhập lựa chọn của bạn: {trang}")
            print(f"{trang}═══════════════════════════════════")

            if choice == '1':
                vip_key_input = input(f'{trang}[{do}<>{trang}] {vang}Vui lòng nhập Key VIP: {luc}')
                status, expiry_date_str = check_vip_key(device_id, vip_key_input)

                if status == 'valid':
                    print(f"{luc}Xác thực Key VIP thành công!{trang}")
                    save_vip_key_info(device_id, vip_key_input, expiry_date_str)
                    display_remaining_time(expiry_date_str)
                    sleep(3)
                    return True
                elif status == 'expired':
                    print(f"{do}Key VIP của bạn đã hết hạn. Vui lòng liên hệ admin.{trang}")
                elif status == 'not_found':
                    print(f"{do}Key VIP không hợp lệ hoặc không tồn tại cho mã máy này.{trang}")
                else: # status == 'error'
                    print(f"{do}Đã xảy ra lỗi trong quá trình xác thực. Vui lòng thử lại.{trang}")
                sleep(2)

            elif choice == '2':
                return process_free_key(device_id)

            else:
                print(f"{vang}Lựa chọn không hợp lệ, vui lòng nhập 1 hoặc 2.{trang}")

        except KeyboardInterrupt:
            print(f"\n{trang}[{do}<>{trang}] {do}Cảm ơn bạn đã dùng Tool !!!{trang}")
            sys.exit()


# =====================================================================================
# PART 3: MAIN TOOL SOURCE CODE (FROM TDK.py)
# =====================================================================================

# ================== GLOBAL VARIABLES ==================
proxy_list = []
proxy_rotator = None

# ================== PROXY MANAGEMENT ==================
class ProxyRotator:
    def __init__(self, proxies: list):
        self.proxies = proxies[:] if proxies else []
        self.i = 0

    def has_proxy(self):
        return bool(self.proxies)

    def current(self):
        if not self.proxies:
            return None
        return self.proxies[self.i % len(self.proxies)]

    def rotate(self):
        if not self.proxies:
            return None
        self.i = (self.i + 1) % len(self.proxies)
        return self.current()

def to_requests_proxies(proxy_str):
    if not proxy_str:
        return None
    p = proxy_str.strip().split(':')
    # Supports both formats: user:pass:host:port or host:port:user:pass
    if len(p) == 4:
        try:
            host, port, user, past = p
            int(port)
        except ValueError:
            user, past, host, port = p
        return {
            'http':  f'http://{user}:{past}@{host}:{port}',
            'https': f'http://{user}:{past}@{host}:{port}',
        }
    # Format host:port
    if len(p) == 2:
        host, port = p
        return {
            'http':  f'http://{host}:{port}',
            'https': f'http://{host}:{port}',
        }
    return None

def check_proxy_fast(proxy_str):
    """Quickly check proxy"""
    try:
        _sess = requests.Session()
        r = _sess.get(
            'http://www.google.com/generate_204',
            proxies=to_requests_proxies(proxy_str),
            timeout=6
        )
        return r.status_code in (204, 200)
    except Exception:
        return False

def get_proxy_info(proxy_str):
    """Get public IP info of the proxy"""
    try:
        _sess = requests.Session()
        r = _sess.get(
            'https://api64.ipify.org',
            proxies=to_requests_proxies(proxy_str),
            timeout=10
        )
        if r.status_code == 200:
            return r.text.strip()
    except:
        try:
            _sess = requests.Session()
            r = _sess.get(
                'http://api.ipify.org',
                proxies=to_requests_proxies(proxy_str),
                timeout=10
            )
            if r.status_code == 200:
                return r.text.strip()
        except:
            pass
    return "Unknown"

def check_proxy(proxy):
    """Check proxy via kiemtraip.vn"""
    session = requests.Session()
    try:
        response = session.post('https://kiemtraip.vn/check-proxy',
            data={'option': 'checkCountry', 'changeTimeout': '5000', 
                  'changeUrl': 'http://www.google.com', 'proxies': str(proxy)},
            timeout=10).text
        if '<span class="text-success copy">' in response:
            ip = response.split('<span class="text-success copy">')[1].split()[0].split('</span>')[0]
            return {'status': "success", 'ip': ip}
        else:
            return {'status': "error", 'ip': None}
    except:
        return {'status': "error", 'ip': None}

def add_proxy():
    """Add proxy manually"""
    i = 1
    proxy_list = []
    prints(255,255,0,"Nhập Proxy Theo Dạng: username:password:host:port hoặc host:port:username:password")
    prints(255,255,0,"Nhấn Enter để bỏ qua và tiếp tục không dùng proxy.")
    while True:
        proxy = input(f'Nhập Proxy Số {i}: ').strip()
        if proxy == '':
            if i == 1:
                return []
            break
        try:
            check = check_proxy(proxy)
            if check['status'] == "success":
                i += 1
                prints(0,255,0,f'Proxy Hoạt Động: {check["ip"]}')
                proxy_list.append(proxy)
            else:
                prints(255,0,0,'Proxy Die! Vui Lòng Nhập Lại !!!')
        except Exception as e:
            prints(255,0,0,f'Lỗi Kiểm Tra Proxy: {str(e)}')
    return proxy_list

def rotate_proxy():
    """Rotate to the next proxy and check if it's live"""
    global proxy_rotator
    if not proxy_rotator or not proxy_rotator.has_proxy():
        return None
    
    tried = 0
    prints(255,255,0,'🔄 Đang tìm proxy live...')
    while tried < len(proxy_rotator.proxies):
        new_proxy = proxy_rotator.rotate()
        prints(255,255,0,f'🔍 Kiểm tra proxy: {new_proxy}')
        if check_proxy_fast(new_proxy):
            proxy_ip = get_proxy_info(new_proxy)
            prints(0,255,0,f'✅ Proxy live: {new_proxy} (IP: {proxy_ip})')
            return new_proxy
        else:
            prints(255,0,0,f'❌ Proxy die: {new_proxy}')
        tried += 1
    
    prints(255,0,0,'❌ Không tìm thấy proxy live nào!')
    return None

def clear_screen():
    os.system('cls' if platform.system() == "Windows" else 'clear')

def banner():
    banner_text = """
████████╗██████╗░██╗░░██╗
╚══██╔══╝██╔══██╗██║░██╔╝
░░░██║░░░██║░░██║█████═╝░
░░░██║░░░██║░░██║██╔═██╗░
░░░██║░░░██████╔╝██║░╚██╗
░░░╚═╝░░░╚═════╝░╚═╝░░╚═╝
    """
    colors = [
        (255, 0, 0), (255, 127, 0), (255, 255, 0), (0, 255, 0),
        (0, 0, 255), (75, 0, 130), (148, 0, 211)
    ]
    color_index = 0
    for line in banner_text.split('\n'):
        for char in line:
            if char != ' ':
                r, g, b = colors[color_index % len(colors)]
                prints(r, g, b, char, end='')
                time.sleep(0.0005)
                color_index += 1
            else:
                print(' ', end='')
        print()

    prints(247, 255, 97, "═" * 50)

    contacts = [
        ("👥 Zalo Group", "https://zalo.me/g/ddxsyp497"),
        ("✈️ Telegram", "@tankeko12"),
        ("👑 Admin", "DUONG PHUNG"),
        ("Mua proxy tại ", "https://long2k4.id.vn/")
    ]

    for label, info in contacts:
        prints(100, 200, 255, f"  {label:<15}: ", end="")
        prints(255, 255, 255, info)

    prints(247, 255, 97, "═" * 50)
    print()

def decode_base64(encoded_str):
    decoded_bytes = base64.b64decode(encoded_str)
    decoded_str = decoded_bytes.decode('utf-8')
    return decoded_str

def encode_to_base64(_data):
    byte_representation = _data.encode('utf-8')
    base64_bytes = base64.b64encode(byte_representation)
    base64_string = base64_bytes.decode('utf-8')
    return base64_string

def prints(*args, **kwargs):
    # Default color: white
    r, g, b = 255, 255, 255
    text = "text"
    end = "\n"

    # Argument handling
    if len(args) == 1:
        text = args[0]
    elif len(args) >= 3:
        r, g, b = args[0], args[1], args[2]
        if len(args) >= 4:
            text = args[3]
    if "text" in kwargs:
        text = kwargs["text"]
    if "end" in kwargs:
        end = kwargs["end"]

    print(f"\033[38;2;{r};{g};{b}m{text}\033[0m", end=end)

def facebook_info(cookie: str, proxy: str = None, timeout: int = 15):
    try:
        session = requests.Session()
        
        if proxy:
            session.proxies = to_requests_proxies(proxy)
        
        session_id = str(uuid.uuid4())
        fb_dtsg = ""
        jazoest = ""
        lsd = ""
        name = ""
        user_id = cookie.split("c_user=")[1].split(";")[0]

        headers = {
            "authority": "www.facebook.com",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-language": "vi",
            "sec-ch-prefers-color-scheme": "light",
            "sec-ch-ua": '"Chromium";v="106", "Google Chrome";v="106", "Not;A=Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/106.0.0.0 Safari/537.36",
            "viewport-width": "1366",
            "Cookie": cookie
        }

        url = session.get(f"https://www.facebook.com/{user_id}", headers=headers, timeout=timeout).url
        response = session.get(url, headers=headers, timeout=timeout).text

        fb_token = re.findall(r'\["DTSGInitialData",\[\],\{"token":"(.*?)"\}', response)
        if fb_token:
            fb_dtsg = fb_token[0]

        jazo = re.findall(r'jazoest=(.*?)\"', response)
        if jazo:
            jazoest = jazo[0]

        lsd_match = re.findall(r'"LSD",\[\],\{"token":"(.*?)"\}', response)
        if lsd_match:
            lsd = lsd_match[0]

        get = session.get("https://www.facebook.com/me", headers=headers, timeout=timeout).url
        url = "https://www.facebook.com/" + get.split("%2F")[-2] + "/" if "next=" in get else get
        response = session.get(url, headers=headers, params={"locale": "vi_VN"}, timeout=timeout)

        data_split = response.text.split('"CurrentUserInitialData",[],{')
        json_data_raw = "{" + data_split[1].split("},")[0] + "}"
        parsed_data = json.loads(json_data_raw)

        user_id = parsed_data.get("USER_ID", "0")
        name = parsed_data.get("NAME", "")

        if user_id == "0" and name == "":
            print("[!] Cookie is invalid or expired.")
            return {'success': False}
        elif "828281030927956" in response.text:
            print("[!] Account is under a 956 checkpoint.")
            return {'success': False}
        elif "1501092823525282" in response.text:
            print("[!] Account is under a 282 checkpoint.")
            return {'success': False}
        elif "601051028565049" in response.text:
            print("[!] Account action is blocked (spam).")
            return {'success': False}

        json_data = {
            'success': True,
            'user_id': user_id,
            'fb_dtsg': fb_dtsg,
            'jazoest': jazoest,
            'lsd': lsd,
            'name': name,
            'session': session,
            'session_id': session_id,
            'cookie': cookie,
            'headers': headers
        }
        return json_data

    except Exception as e:
        print(f"[Facebook.info] Error: {e}")
        return {'success': False}

def get_post_id(session,cookie,link):
    prints(255,255,0,f'Đang lấy post id',end='\r')
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9,vi;q=0.8',
        'dpr': '1',
        'priority': 'u=0, i',
        'sec-ch-prefers-color-scheme': 'light',
        'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'cookie': cookie,
    }
    try:
        response = session.get(link, headers=headers, timeout=15).text
        response= re.sub(r"\\", "", response)
        
        page_id=''
        post_id=''
        stories_id=''
        permalink_id=''
        try:
            if '"post_id":"' in str(response):
                permalink_id=re.findall('"post_id":".*?"',response)[0].split(':"')[1].split('"')[0]
                prints(255,255,0,f'permalink_id là: {permalink_id[:20]}      ',end='\r')
        except:
            pass
        try:
            if 'posts' in str(response):
                post_id=response.split('posts')[1].split('"')[0]
                post_id=post_id.replace("/", "")
                post_id = re.sub(r"\\", "", post_id)
                prints(255,255,0,f'Post id là: {post_id[:20]}       ',end='\r')
        except:
            pass
        try:
            if 'storiesTrayType' in response and not '"profile_type_name_for_content":"PAGE"' in response:
                stories_id=re.findall('"card_id":".*?"',response)[0].split('":"')[1].split('"')[0]
                prints(255,255,0,f'stories_id là: {stories_id[:20]}      ',end='\r')
        except:
            pass
        try:
            if '"page_id"' in response:
                page_id=re.findall('"page_id":".*?"',response)[0].split('id":"')[1].split('"')[0]
                prints(255,255,0,f'page_id là: {page_id[:20]}        ',end='\r')
        except:
            pass
        return {'success':True,'post_id':post_id,'permalink_id':permalink_id,'stories_id':stories_id,'page_id':page_id}
    except Exception as e:
        print(Fore.RED+f'Lỗi khi lấy ID post: {e}')
        return {'success':False}

def react_post_perm(data,object_id,type_react, proxy=None):
    prints(255,255,0,f'Đang thả {type_react} vào {object_id[:20]}       ',end='\r')

    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,vi;q=0.8',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://www.facebook.com',
        'priority': 'u=1, i',
        'referer': 'https://www.facebook.com/'+str(object_id),
        'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'x-fb-friendly-name': 'CometUFIFeedbackReactMutation',
        'x-fb-lsd': data['lsd'],
        'cookie': data['cookie'],
    }
    react_list = {"LIKE": "1635855486666999","LOVE": "1678524932434102","CARE": "613557422527858","HAHA": "115940658764963","WOW": "478547315650144","SAD": "908563459236466","ANGRY": "444813342392137"}
    
    json_data = {
        'av': str(data['user_id']),
        '__user': str(data['user_id']),
        'fb_dtsg': data['fb_dtsg'],
        'jazoest': str(data['jazoest']),
        'lsd': str(data['lsd']),
        'fb_api_caller_class': 'RelayModern',
        'fb_api_req_friendly_name': 'CometUFIFeedbackReactMutation',
        'variables': '{"input":{"attribution_id_v2":"CometSinglePostDialogRoot.react,comet.post.single_dialog,via_cold_start,'+str(int(time.time()*1000))+',893597,,,","feedback_id":"'+encode_to_base64(str('feedback:'+object_id))+'","feedback_reaction_id":"'+str(react_list.get(type_react.upper()))+'","feedback_source":"OBJECT","is_tracking_encrypted":true,"tracking":["AZWEqXNx7ELYfHNA7b4CrfdPexzmIf2rUloFtOZ9zOxrcEuXq9Nr8cAdc1kP5DWdKx-DdpkffT5hoGfKYfh0Jm8VlJztxP7elRZBQe5FqkP58YxifFUwdqGzQnJPfhGupHYBjoq5I5zRHXPrEeuJk6lZPblpsrYQTO1aDBDb8UcDpW8F82ROTRSaXpL-T0gnE3GyKCzqqN0x99CSBp1lCZQj8291oXhMoeESvV__sBVqPWiELtFIWvZFioWhqpoAe_Em15uPs4EZgWgQmQ-LfgOMAOUG0TOb6wDVO75_PyQ4b8uTdDWVSEbMPTCglXWn5PJzqqN4iQzyEKVe8sk708ldiDug7SlNS7Bx0LknC7p_ihIfVQqWLQpLYK6h4JWZle-ugySqzonCzb6ay09yrsvupxPUGp-EDKhjyEURONdtNuP-Fl3Oi1emIy61-rqISLQc-jp3vzvnIIk7r_oA1MKT065zyX-syapAs-4xnA_12Un5wQAgwu5sP9UmJ8ycf4h1xBPGDmC4ZkaMWR_moqpx1k2Wy4IbdcHNMvGbkkqu12sgHWWznxVfZzrzonXKLPBVW9Y3tlQImU9KBheHGL_ADG_8D-zj2S9JG2y7OnxiZNVAUb1yGrVVrJFnsWNPISRJJMZEKiYXgTaHVbZBX6CdCrA7gO25-fFBvVfxp2Do3M_YKDc5Ttq1BeiZgPCKogeTkSQt1B67Kq7FTpBYJ05uEWLpHpk1jYLH8ppQQpSEasmmKKYj9dg7PqbHPMUkeyBtL69_HkdxtVhDgkNzh1JerLPokIkdGkUv0RALcahWQK4nR8RRU2IAFMQEp-FsNk_VKs_mTnZQmlmSnzPDymkbGLc0S1hIlm9FdBTQ59--zU4cJdOGnECzfZq4B5YKxqxs0ijrcY6T-AOn4_UuwioY"],"session_id":"'+data['session_id']+'","actor_id":"'+str(data['user_id'])+'","client_mutation_id":"1"},"useDefaultActor":false,"__relay_internal__pv__CometUFIReactionsEnableShortNamerelayprovider":false}',
        'server_timestamps': 'true',
        'doc_id': '24034997962776771',
    }
    try:
        if proxy:
            data['session'].proxies = to_requests_proxies(proxy)
        response = data['session'].post('https://www.facebook.com/api/graphql/', headers=headers, data=json_data, timeout=15).text
        return True
    except Exception:
        return False

def react_post_defaul(data,object_id,type_react, proxy=None):
    prints(255,255,0,f'Đang thả {type_react} vào {object_id[:20]}       ',end='\r')

    react_list = {"LIKE": "1635855486666999","LOVE": "1678524932434102","CARE": "613557422527858","HAHA": "115940658764963","WOW": "478547315650144","SAD": "908563459236466","ANGRY": "444813342392137"}
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,vi;q=0.8',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://www.facebook.com',
        'priority': 'u=1, i',
        'referer': 'https://www.facebook.com/'+str(object_id),
        'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'x-fb-friendly-name': 'CometUFIFeedbackReactMutation',
        'x-fb-lsd': data['lsd'],
        'cookie': data['cookie'],
    }
    
    json_data = {
        'av': str(data['user_id']),
        '__user': str(data['user_id']),
        'fb_dtsg': data['fb_dtsg'],
        'jazoest': data['jazoest'],
        'lsd': data['lsd'],
        'fb_api_caller_class': 'RelayModern',
        'fb_api_req_friendly_name': 'CometUFIFeedbackReactMutation',
        'variables': '{"input":{"attribution_id_v2":"CometSinglePostDialogRoot.react,comet.post.single_dialog,via_cold_start,'+str(int(time.time()*1000))+',912367,,,","feedback_id":"'+encode_to_base64(str('feedback:'+object_id))+'","feedback_reaction_id":"'+str(react_list.get(type_react.upper()))+'","feedback_source":"OBJECT","is_tracking_encrypted":true,"tracking":["AZWEqXNx7ELYfHNA7b4CrfdPexzmIf2rUloFtOZ9zOxrcEuXq9Nr8cAdc1kP5DWdKx-DdpkffT5hoGfKYfh0Jm8VlJztxP7elRZBQe5FqkP58YxifFUwdqGzQnJPfhGupHYBjoq5I5zRHXPrEeuJk6lZPblpsrYQTO1aDBDb8UcDpW8F82ROTRSaXpL-T0gnE3GyKCzqqN0x99CSBp1lCZQj8291oXhMoeESvV__sBVqPWiELtFIWvZFioWhqpoAe_Em15uPs4EZgWgQmQ-LfgOMAOUG0TOb6wDVO75_PyQ4b8uTdDWVSEbMPTCglXWn5PJzqqN4iQzyEKVe8sk708ldiDug7SlNS7Bx0LknC7p_ihIfVQqWLQpLYK6h4JWZle-ugySqzonCzb6ay09yrsvupxPUGp-EDKhjyEURONdtNuP-Fl3Oi1emIy61-rqISLQc-jp3vzvnIIk7r_oA1MKT065zyX-syapAs-4xnA_12Un5wQAgwu5sP9UmJ8ycf4h1xBPGDmC4ZkaMWR_moqpx1k2Wy4IbdcHNMvGbkkqu12sgHWWznxVfZzrzonXKLPBVW9Y3tlQImU9KBheHGL_ADG_8D-zj2S9JG2y7OnxiZNVAUb1yGrVVrJFnsWNPISRJJMZEKiYXgTaHVbZBX6CdCrA7gO25-fFBvVfxp2Do3M_YKDc5Ttq1BeiZgPCKogeTkSQt1B67Kq7FTpBYJ05uEWLpHpk1jYLH8ppQQpSEasmmKKYj9dg7PqbHPMUkeyBtL69_HkdxtVhDgkNzh1JerLPokIkdGkUv0RALcahWQK4nR8RRU2IAFMQEp-FsNk_VKs_mTnZQmlmSnzPDymkbGLc0S1hIlm9FdBTQ59--zU4cJdOGnECzfZq4B5YKxqxs0ijrcY6T-AOn4_UuwioY"],"session_id":"'+str(data['session_id'])+'","actor_id":"'+data['user_id']+'","client_mutation_id":"1"},"useDefaultActor":false,"__relay_internal__pv__CometUFIReactionsEnableShortNamerelayprovider":false}',
        'server_timestamps': 'true',
        'doc_id': '24034997962776771',
    }
    try:
        if proxy:
            data['session'].proxies = to_requests_proxies(proxy)
        response = data['session'].post('https://www.facebook.com/api/graphql/', headers=headers, data=json_data, timeout=15)
        response.raise_for_status()
        return True
    except:
        return False

def react_stories(data,object_id, proxy=None):
    prints(255,255,0,f'Đang tim story {object_id[:20]}      ',end='\r')

    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,vi;q=0.8',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://www.facebook.com',
        'priority': 'u=1, i',
        'referer': 'https://www.facebook.com/',
        'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'x-fb-friendly-name': 'useStoriesSendReplyMutation',
        'x-fb-lsd': data['lsd'],
        'cookie': data['cookie']
    }

    json_data = {
        'av': str(data['user_id']),
        '__user': str(data['user_id']),
        'fb_dtsg': data['fb_dtsg'],
        'jazoest': str(data['jazoest']),
        'lsd': data['lsd'],
        'fb_api_caller_class': 'RelayModern',
        'fb_api_req_friendly_name': 'useStoriesSendReplyMutation',
        'variables': '{"input":{"attribution_id_v2":"StoriesCometSuspenseRoot.react,comet.stories.viewer,via_cold_start,'+str(int(time.time()*1000))+',33592,,,","lightweight_reaction_actions":{"offsets":[0],"reaction":"❤️"},"message":"❤️","story_id":"'+str(object_id)+'","story_reply_type":"LIGHT_WEIGHT","actor_id":"'+str(data['user_id'])+'","client_mutation_id":"2"}}',
        'server_timestamps': 'true',
        'doc_id': '9697491553691692',
    }
    try:
        if proxy:
            data['session'].proxies = to_requests_proxies(proxy)
        response = data['session'].post('https://www.facebook.com/api/graphql/',  headers=headers, data=json_data, timeout=15).json()
        if response.get('extensions', {}).get('is_final') == True:
            return True
        else:
            return False
    except Exception:
        return False

def react_post(data,link,type_react, proxy=None):
    res_object_id=get_post_id(data['session'],data['cookie'],link)
    if not res_object_id.get('success'):
        return False
        
    if res_object_id.get('stories_id'):
        return react_stories(data,res_object_id['stories_id'], proxy)
    elif res_object_id.get('permalink_id'):
        return react_post_perm(data,res_object_id['permalink_id'],type_react, proxy)
    elif res_object_id.get('post_id'):
        return react_post_defaul(data,res_object_id['post_id'],type_react, proxy)
    return False

def comment_fb(data, object_id, msg, proxy=None):
    prints(255, 255, 0, f'Đang comment vào {object_id[:20]}        ', end='\r')

    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,vi;q=0.8',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://www.facebook.com',
        'priority': 'u=1, i',
        'referer': 'https://www.facebook.com/',
        'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'x-fb-friendly-name': 'useCometUFICreateCommentMutation',
        'x-fb-lsd': data['lsd'],
        'cookie': data['cookie'],
    }

    json_data = {
        'av': data['user_id'],
        '__user': str(data['user_id']),
        'fb_dtsg': data['fb_dtsg'],
        'jazoest': data['jazoest'],
        'lsd': data['lsd'],
        'fb_api_caller_class': 'RelayModern',
        'fb_api_req_friendly_name': 'useCometUFICreateCommentMutation',
        'variables': '{"feedLocation":"DEDICATED_COMMENTING_SURFACE","feedbackSource":110,"groupID":null,"input":{"client_mutation_id":"4","actor_id":"'+str(data['user_id'])+'","attachments":null,"feedback_id":"'+str(encode_to_base64('feedback:'+str(object_id)))+'","formatting_style":null,"message":{"ranges":[],"text":"'+msg+'"},"attribution_id_v2":"CometHomeRoot.react,comet.home,via_cold_start,'+str(int(time.time()*1000))+',521928,4748854339,,","is_tracking_encrypted":true,"tracking":["AZX3K9tlBCG5xFInZx-hvHkdaGUGeTF2WOy5smtuctk2uhOd_YMY0HaF_dyAE8WU5PjpyFvAAM8x4Va39jb7YmcxubK8j4k8_16X1jtlc_TqtbWFukq-FUR93cTOBLEldliV6RILPNqYHH_a88DnwflDtg8NvluALzkLO-h8N8cxTQoSUQDPh206jaottUIfOxdZheWcqroL_1IaoZq9QuhwAUY4qu551-q7loObYLWHMcqA7XZFpDm6SPQ8Ne86YC3-sDPo093bfUGHae70FqOts742gWgnFy_t4t7TgRTmv1zsx0CXPdEh-xUx3bXPC6NEutzyNyku7Kdqgg1qTSabXknlJ7KZ_u9brQtmzs7BE_x4HOEwSBuo07hcm-UdqjaujBd2cPwf-Via-oMAsCsTywY-riGnW49EJhhycbj4HvshcHRDqk4iUTOaULV2CAOL7nGo5ACkUMoKbuWFl34uLoHhFJnpWaxPUef3ceL0ed19EChlYsnFl122VMJzRf6ymNtBQKbSfLkDF_1QYIofGvcRktaZOrrhnHdwihCPjBbHm17a3Cc3ax2KNJ6ViUjdj--KFE704jEjkJ9RXdZw3UIO-JjkvbCCeJ3Y-viGeank-vputYKtK1L05t2q5_6ool7PCIOufjNUrACbyeuOiLTyicyVvT013_jbYefSkhJ55PAtIqKn3JVbUpEWBYTWO8mkbU_UyjOnnhCZcagjWXYHKQ_Ne2gfLZN_WrpbEcLKdOtEm-l8J1RdnvYSTc13XVd85eL-k3da2OTamH7cJ_7bS6eJhQ0oSsrlGSJahq_JT9TV5IOffVeZWJ_SpcBwdPvzCRlMJIRljjSmgrCtfJrak8OgGtZM6jIZp6iZluUDlPEv1c_apazECx9CPC3pM1iu4QVdSdEzyBXbhul5hMDkSon4ahxJbWQ5ALpj-QAjfiCyz-aM0L5BqZLRug8_MdPk_ZWO3e70OX2LGHWKsd0ZGWP5kzpMqSMnkgTN5fGQ4A1QJ6EdEisqjclnSrD258ghVgKVEK9_PcIpGmmseB7fzrL1c5R65D4UZQq-kEpsuM42EhkAgfEEzrCTosmpRd7xibmd6aoVsOqCvJrvy_83bLE3-YTkhotHJeQxuLPWF1uvDSkhc_cs3ApJ1xFxHDZc5dikuMXne1azhKp5","{\\"assistant_caller\\":\\"comet_above_composer\\",\\"conversation_guide_session_id\\":\\"'+data['session_id']+'\\",\\"conversation_guide_shown\\":null}"],"feedback_source":"DEDICATED_COMMENTING_SURFACE","idempotence_token":"client:'+str(uuid.uuid4())+'","session_id":"'+data['session_id']+'"},"inviteShortLinkKey":null,"renderLocation":null,"scale":1,"useDefaultActor":false,"focusCommentID":null,"__relay_internal__pv__CometUFICommentAvatarStickerAnimatedImagerelayprovider":false,"__relay_internal__pv__IsWorkUserrelayprovider":false}',
        'server_timestamps': 'true',
        'doc_id': '9379407235517228',
    }
    try:
        if proxy:
            data['session'].proxies = to_requests_proxies(proxy)
        response = data['session'].post('https://www.facebook.com/api/graphql/', headers=headers, data=json_data, timeout=15).json()
        comment_text = response['data']['comment_create']['feedback_comment_edge']['node']['preferred_body']['text']
        prints(5, 255, 0, f'Đã comment "{comment_text}"', end='\r')
        if comment_text == msg:
            return comment_text  # Trả về text của comment để xác minh
        return None
    except Exception as e:
        prints(255, 0, 0, f"Lỗi khi comment: {e}")
        return None

def verify_comment_presence(session, post_link, comment_text, cookie, proxy):
    """
    Kiểm tra xem một comment có thực sự hiển thị trên bài viết không.
    """
    prints(255, 255, 0, f'Đang xác minh bình luận...', end='\r')
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9,vi;q=0.8',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'cookie': cookie,
    }
    try:
        proxies = to_requests_proxies(proxy) if proxy else None
        response = session.get(post_link, headers=headers, proxies=proxies, timeout=15)
        response.raise_for_status()
        # Kiểm tra đơn giản bằng cách tìm text trong nội dung trang
        if comment_text in response.text:
            prints(0, 255, 0, 'Xác minh bình luận thành công!      ')
            return True
        else:
            prints(255, 0, 0, 'Không tìm thấy bình luận, có thể đã bị ẩn!')
            return False
    except Exception as e:
        prints(255, 0, 0, f'Lỗi khi xác minh bình luận: {e}')
        return False # Mặc định là thất bại nếu có lỗi

def dexuat_fb(data,object_id,msg, proxy=None):
    prints(255,255,0,f'Đang đề xuất Fanpage {object_id[:20]}        ',end='\r')
    if len(msg)<=25:
        msg+=' '*(26-len(msg))

    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,vi;q=0.8',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://www.facebook.com',
        'priority': 'u=1, i',
        'referer': 'https://www.facebook.com/'+object_id,
        'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'x-fb-friendly-name': 'ComposerStoryCreateMutation',
        'x-fb-lsd': data['lsd'],
        'cookie': data['cookie']
    }

    json_data = {
        'av': str(data['user_id']),
        '__user': str(data['user_id']),
        'fb_dtsg': data['fb_dtsg'],
        'jazoest': data['jazoest'],
        'lsd': data['lsd'],
        'fb_api_caller_class': 'RelayModern',
        'fb_api_req_friendly_name': 'ComposerStoryCreateMutation',
        'variables': '{"input":{"composer_entry_point":"inline_composer","composer_source_surface":"page_recommendation_tab","idempotence_token":"'+str(uuid.uuid4()) + "_FEED"+'","source":"WWW","audience":{"privacy":{"allow":[],"base_state":"EVERYONE","deny":[],"tag_expansion_state":"UNSPECIFIED"}},"message":{"ranges":[],"text":"'+str(msg)+'"},"page_recommendation":{"page_id":"'+str(object_id)+'","rec_type":"POSITIVE"},"logging":{"composer_session_id":"'+data['session_id']+'"},"navigation_data":{"attribution_id_v2":"ProfileCometReviewsTabRoot.react,comet.profile.reviews,unexpected,'+str(int(time.time()*1000))+','+str(random.randint(111111,999999))+',250100865708545,,;ProfileCometTimelineListViewRoot.react,comet.profile.timeline.list,via_cold_start,'+str(int(time.time()*1000))+','+str(random.randint(111111,999999))+',250100865708545,,"},"tracking":[null],"event_share_metadata":{"surface":"newsfeed"},"actor_id":"'+str(data['user_id'])+'","client_mutation_id":"1"},"feedLocation":"PAGE_SURFACE_RECOMMENDATIONS","feedbackSource":0,"focusCommentID":null,"scale":1,"renderLocation":"timeline","useDefaultActor":false,"isTimeline":true,"isProfileReviews":true,"__relay_internal__pv__CometUFIShareActionMigrationrelayprovider":true,"__relay_internal__pv__FBReels_deprecate_short_form_video_context_gkrelayprovider":true,"__relay_internal__pv__StoriesArmadilloReplyEnabledrelayprovider":true,"__relay_internal__pv__FBReelsIFUTileContent_reelsIFUPlayOnHoverrelayprovider":true}',
        'server_timestamps': 'true',
        'doc_id': '24952395477729516',
    }
    try:
        if proxy:
            data['session'].proxies = to_requests_proxies(proxy)
        response_json = data['session'].post('https://www.facebook.com/api/graphql/', headers=headers, data=json_data, timeout=15).json()
        
        post_id = response_json['data']['story_create']['profile_review_edge']['node']['post_id']
        my_id = response_json['data']['story_create']['profile_review_edge']['node']['feedback']['owning_profile']['id']
        link_post = f'https://www.facebook.com/{my_id}/posts/{post_id}'
        
        link_p=get_lin_share(data,link_post, proxy)
        return link_p
    except Exception as e:
        prints(5,255,0,f'Lỗi khi đánh giá Fanpage: {e}')
        return False

def wallet(authorization):
    headers = {
        'User-Agent': 'Dart/3.3 (dart:io)',
        'Content-Type': 'application/json',
        'lang': 'en',
        'version': '37',
        'origin': 'app',
        'authorization': authorization,
    }
    try:
        response = requests.get('https://api-v2.bumx.vn/api/business/wallet', headers=headers, timeout=10).json()
        return response.get('data', {}).get('balance', 'N/A')
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"
    except json.JSONDecodeError:
        return "Error decoding server response"

def load(session,authorization,job):
    prints(255,255,0,f'Đang mở nhiệm vụ...',end='\r')

    headers = {
        'User-Agent': 'Dart/3.3 (dart:io)',
        'Content-Type': 'application/json',
        'lang': 'en',
        'version': '37',
        'origin': 'app',
        'authorization': authorization,
    }

    json_data = {'buff_id': job['buff_id']}
    try:
        response = session.post('https://api-v2.bumx.vn/api/buff/load-mission', headers=headers, json=json_data, timeout=10).json()
        return response
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception:
        prints(255,0,0,f'Lỗi khi tải thông tin NV')
        return None

def get_job(session,authorization):
    prints(255,255,0,f'Đang lấy nhiệm vụ...',end='\r')
    headers = {
        'User-Agent': 'Dart/3.3 (dart:io)',
        'lang': 'en',
        'version': '37',
        'origin': 'app',
        'authorization': authorization,
    }
    params = {'is_from_mobile': 'true'}
    
    try:
        response = session.get('https://api-v2.bumx.vn/api/buff/mission', params=params, headers=headers, timeout=10)
        response.raise_for_status()
        response_json = response.json()
    except requests.exceptions.RequestException:
        prints(255,0,0,f'Lỗi khi lấy NV')
        return []
    except json.JSONDecodeError:
        prints(255,0,0,f'Lỗi giải mã JSON khi lấy NV.')
        return []

    prints(Fore.LIGHTWHITE_EX+f"Đã tìm thấy {response_json.get('count', 0)} NV",end='\r')
    
    JOB=[]
    for i in response_json.get('data', []):
        json_job={
            "_id":i['_id'],
            "buff_id":i['buff_id'],
            "type":i['type'],
            "name":i['name'],
            "status":i['status'],
            "object_id":i['object_id'],
            "business_id":i['business_id'],
            "mission_id":i['mission_id'],
            "create_date":i['create_date'],
            "note":i['note'],
            "require":i['require'],
        }
        JOB.insert(0,json_job)
    return JOB

def reload(session, authorization, type_job, retries=3):
    prints(255, 255, 0, f'Đang tải danh sách nhiệm vụ {type_job}...', end='\r')
    if retries == 0:
        prints(255, 0, 0, f'Tải danh sách NV {type_job} thất bại. Bỏ qua.')
        return

    headers = {
        'User-Agent': 'Dart/3.3 (dart:io)',
        'Content-Type': 'application/json',
        'lang': 'en',
        'version': '37',
        'origin': 'app',
        'authorization': authorization,
    }
    json_data = {'type': type_job}
    try:
        response = session.post('https://api-v2.bumx.vn/api/buff/get-new-mission', headers=headers, json=json_data, timeout=10).json()
    except Exception:
        prints(255, 0, 0, f'Lỗi khi tải lại NV. Thử lại trong 2s...')
        time.sleep(2)
        return reload(session, authorization, type_job, retries - 1)

def submit(session,authorization,job,reslamjob,res_load):
    prints(255,255,0,f'Đang nhấn hoàn thành nhiệm vụ',end='\r')
    headers = {
        'User-Agent': 'Dart/3.3 (dart:io)',
        'Content-Type': 'application/json',
        'lang': 'en',
        'version': '37',
        'origin': 'app',
        'authorization': authorization,
    }
    json_data = {
        'buff_id': job['buff_id'],
        'comment': None, 'comment_id': None, 'code_submit': None,
        'attachments': [], 'link_share': '', 'code': '',
        'is_from_mobile': True, 'type': job['type'], 'sub_id': None, 'data': None,
    }

    if job['type']=='like_facebook':
        json_data['comment'] = 'tt nha'
    elif job['type']=='like_poster':
        json_data['comment'] = res_load.get('data')
        json_data['comment_id'] = res_load.get('comment_id')
    elif job['type']=='review_facebook':
        json_data['comment'] = 'Helo Bạn chúc Bạn sức khỏe '
        json_data['link_share'] = reslamjob
    
    try:
        response = session.post('https://api-v2.bumx.vn/api/buff/submit-mission', headers=headers, json=json_data, timeout=10).json()
        if response.get('success') == True:
            message = response.get('message', '')
            _xu = '0'
            sonvdalam = '0'
            try:
                _xu = message.split('cộng ')[1].split(',')[0]
                sonvdalam = message.split('làm: ')[1]
            except IndexError:
                pass
            return [True,_xu,sonvdalam]
        return [False,'0','0']
    except Exception:
        prints(255,0,0,f'Lỗi khi submit')
        return [False,'0','0']
    
def report(session, authorization, job, retries=3):
    prints(255, 255, 0, f'Đang báo lỗi...', end='\r')
    if retries == 0:
        prints(255, 0, 0, f'Báo lỗi thất bại sau nhiều lần thử. Bỏ qua...')
        return

    headers = {
        'User-Agent': 'Dart/3.3 (dart:io)',
        'Content-Type': 'application/json',
        'lang': 'en',
        'version': '37',
        'origin': 'app',
        'authorization': authorization,
    }
    json_data = {'buff_id': job['buff_id']}
    try:
        response = session.post('https://api-v2.bumx.vn/api/buff/report-buff', headers=headers, json=json_data, timeout=10).json()
        prints(255, 165, 0, 'Đã báo lỗi thành công và bỏ qua NV.')
    except Exception:
        prints(255, 165, 0, f'Báo lỗi không thành công, thử lại... ({retries-1} lần còn lại)')
        time.sleep(2)
        return report(session, authorization, job, retries - 1)

def lam_job(data, jobs, type_job_doing, current_proxy=None):
    prints(255, 255, 0, f'Đang làm NV...', end='\r')
    link = 'https://www.facebook.com/' + jobs['object_id']
    
    # Mặc định kết quả
    result = {'success': False, 'verification_failed': False, 'payload': None}

    if type_job_doing == 'review_facebook':
        res_get_post_id = get_post_id(data['session'], data['cookie'], link)
        if res_get_post_id.get('page_id'):
            dexuat_result = dexuat_fb(data, res_get_post_id['page_id'], jobs['data'], current_proxy)
            if dexuat_result:
                result['success'] = True
                result['payload'] = dexuat_result
    
    elif type_job_doing == 'like_facebook':
        react_type = 'LIKE'
        icon = jobs.get('icon', '').lower()
        if 'love' in icon or 'thuongthuong' in icon: react_type = 'LOVE'
        elif 'care' in icon: react_type = 'CARE'
        elif 'wow' in icon: react_type = 'WOW'
        elif 'sad' in icon: react_type = 'SAD'
        elif 'angry' in icon: react_type = 'ANGRY'
        elif 'haha' in icon: react_type = 'HAHA'
        
        react_success = react_post(data, link, react_type.upper(), current_proxy)
        if react_success:
            prints(255, 255, 0, f'Đã thả {react_type}, chờ 10 giây để ổn định...')
            time.sleep(10) # Đợi 10 giây theo yêu cầu
            result['success'] = True
            result['payload'] = True

    elif type_job_doing == 'like_poster':
        res_get_post_id = get_post_id(data['session'], data['cookie'], link)
        post_id_to_comment = res_get_post_id.get('post_id') or res_get_post_id.get('permalink_id')
        if post_id_to_comment:
            comment_text = comment_fb(data, post_id_to_comment, jobs['data'], current_proxy)
            if comment_text:
                prints(255, 255, 0, 'Comment thành công, chờ 10 giây để xác minh...')
                time.sleep(10)
                is_verified = verify_comment_presence(data['session'], link, comment_text, data['cookie'], current_proxy)
                if is_verified:
                    result['success'] = True
                    result['payload'] = True
                else:
                    # Verification failed, mark it
                    result['verification_failed'] = True

    return result

def countdown(seconds):
    seconds = int(seconds)
    if seconds < 1: return
    for i in range(seconds, 0, -1):
        prints(147, 112, 219, '[', end='')
        prints(0, 255, 127, "TDK", end='')
        prints(147, 112, 219, ']', end='')
        prints(255, 255, 255, '[', end='')
        prints(255, 215, 0, "WAIT", end='')
        prints(255, 255, 255, ']', end='')
        prints(255, 20, 147, ' ➤ ', end='')
        prints(0, 191, 255, f"⏳ {i}s...", end='\r')
        time.sleep(1)
    print(' ' * 50, end='\r')

def get_lin_share(data,link, proxy=None):
    headers = {
        'accept': '*/*',
        'accept-language': 'vi,en;q=0.9',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://www.facebook.com',
        'priority': 'u=1, i',
        'referer': link,
        'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'x-fb-friendly-name': 'useLinkSharingCreateWrappedUrlMutation',
        'x-fb-lsd': data['lsd'],
        'cookie': data['cookie'],
    }

    payload = {
        'av': data['user_id'],
        '__user': data['user_id'],
        'fb_dtsg': data['fb_dtsg'],
        'jazoest': data['jazoest'],
        'lsd': data['lsd'],
        'fb_api_caller_class': 'RelayModern',
        'fb_api_req_friendly_name': 'useLinkSharingCreateWrappedUrlMutation',
        'variables': '{"input":{"client_mutation_id":"3","actor_id":"'+str(data['user_id'])+'","original_content_url":"'+link+'","product_type":"UNKNOWN_FROM_DEEP_LINK"}}',
        'server_timestamps': 'true',
        'doc_id': '30568280579452205',
    }
    try:
        proxies = to_requests_proxies(proxy) if proxy else None
        response = requests.post('https://www.facebook.com/api/graphql/',  headers=headers, data=payload, proxies=proxies, timeout=15).json()
        return response['data']['xfb_create_share_url_wrapper']['share_url_wrapper']['wrapped_url']
    except Exception as e:
        prints(255,0,0,f'Lỗi khi lấy link share của post: {e}')
        return ''

def add_account_fb(session,authorization,user_id):
    headers = {
        'Content-Type': 'application/json',
        'lang': 'en',
        'version': '37',
        'origin': 'app',
        'authorization': authorization,
    }
    json_data = {'link': f'https://www.facebook.com/profile.php?id={str(user_id)}'}
    try:
        response = session.post('https://api-v2.bumx.vn/api/account-facebook/connect-link', headers=headers, json=json_data, timeout=10).json()
        prints(255,255,0,f"Khai báo tài khoản FB: {response.get('message', 'No message')}")
    except Exception as e:
        prints(255,0,0,f"Lỗi khai báo tài khoản FB: {e}")

def rgb(r, g, b, text):
    return f"\033[38;2;{r};{g};{b}m{text}\033[0m"

def print_state(status_job,_xu,jobdalam,dahoanthanh,tongcanhoanthanh,type_job, name_acc, bumx_acc_num):
    hanoi_tz = timezone(timedelta(hours=7))
    now = datetime.now(hanoi_tz).strftime("%H:%M:%S")
    type_NV = {'like_facebook':'CAMXUC', 'like_poster':'COMMENT', 'review_facebook':'FANPAGE'}
    
    status_color = rgb(0,255,0,status_job.upper()) if status_job.lower()=='complete' else rgb(255,255,0,status_job.upper())

    print(f"[{rgb(255,165,0,f'BUMX-{bumx_acc_num}')}]"
          f"[{rgb(255, 255, 255, name_acc)}]"
          f"[{Fore.LIGHTWHITE_EX}{now}{Fore.LIGHTGREEN_EX}]"
          f"[{Fore.LIGHTWHITE_EX}{dahoanthanh}/{tongcanhoanthanh}{Fore.LIGHTGREEN_EX}]"
          f"[{rgb(3, 252, 252, type_NV.get(type_job, 'UNKNOWN'))}{Fore.LIGHTGREEN_EX}]"
          f"[{status_color}{Fore.LIGHTGREEN_EX}]"
          f"[{Fore.LIGHTWHITE_EX}+{_xu.strip()}{Fore.LIGHTGREEN_EX}]"
          f"[{Fore.LIGHTWHITE_EX}Đã làm:{jobdalam.strip()}{Fore.LIGHTGREEN_EX}]")

def switch_facebook_account(cookie, authorization, bumx_session, proxy=None):
    prints(0, 255, 255, "\n--- Chuyển đổi tài khoản Facebook ---")
    data = facebook_info(cookie, proxy)
    if not data or not data.get('success'):
        prints(255, 0, 0, 'Cookie không hợp lệ. Bỏ qua tài khoản này.')
        return None
    
    prints(5, 255, 0, f"Đang sử dụng tài khoản: {data['name']} ({data['user_id']})")
    add_account_fb(bumx_session, authorization, data['user_id'])
    return data

def main_bumx_free():
    global proxy_list, proxy_rotator
    
    banner()
    
    proxy_list = []
    proxy_rotator = None
    
    if os.path.exists('tdk-proxy-vip.json'):
        prints(66, 245, 245,'Phát hiện file proxy đã lưu.')
        x=input(Fore.LIGHTWHITE_EX+'Bạn có muốn dùng lại proxy đã lưu không? (y/n): ')
        if x.lower()=='y':
            try:
                with open('tdk-proxy-vip.json', 'r') as f:
                    proxy_list = json.load(f)
                proxy_rotator = ProxyRotator(proxy_list)
                prints(0,255,0,f'Đã tải {len(proxy_list)} proxy từ file.')
            except:
                prints(255,0,0,'Lỗi đọc file proxy, sẽ nhập mới.')
                proxy_list = add_proxy()
                proxy_rotator = ProxyRotator(proxy_list)
                if proxy_list:
                    with open('tdk-proxy-vip.json', 'w') as f:
                        json.dump(proxy_list, f)
        else:
            proxy_list = add_proxy()
            proxy_rotator = ProxyRotator(proxy_list)
            if proxy_list:
                with open('tdk-proxy-vip.json', 'w') as f:
                    json.dump(proxy_list, f)
    else:
        prints(66, 245, 245,'Chưa có file proxy, sẽ nhập mới.')
        proxy_list = add_proxy()
        proxy_rotator = ProxyRotator(proxy_list)
        if proxy_list:
            with open('tdk-proxy-vip.json', 'w') as f:
                json.dump(proxy_list, f)

    # === MULTI BUMX ACCOUNT INPUT ===
    num_bumx_accounts = int(input(Fore.LIGHTCYAN_EX + 'Nhập số lượng tài khoản Bumx muốn chạy: '))
    authorizations_list = []
    for i in range(num_bumx_accounts):
        auth_file = f'tdk-auth-bumx-{i+1}.txt'
        authorization = ''
        if os.path.exists(auth_file):
            x = input(Fore.LIGHTCYAN_EX + f'Bạn có muốn dùng lại authorization Bumx đã lưu trong file {auth_file} không (y/n): ').lower()
            if x == 'y':
                with open(auth_file, 'r', encoding='utf-8') as f:
                    authorization = f.read().strip()
            else:
                authorization = input(Fore.LIGHTWHITE_EX + f'Nhập authorization Bumx thứ {i+1} của Bạn: ').strip()
                with open(auth_file, 'w', encoding='utf-8') as f:
                    f.write(authorization)
                prints(5, 255, 0, f'Đã lưu authorization vào {auth_file}')
        else:
            authorization = input(Fore.LIGHTWHITE_EX + f'Nhập authorization Bumx thứ {i+1} của Bạn: ').strip()
            with open(auth_file, 'w', encoding='utf-8') as f:
                f.write(authorization)
            prints(5, 255, 0, f'Đã lưu authorization vào {auth_file}')
        if authorization:
            authorizations_list.append(authorization)

    if not authorizations_list:
        prints(255,0,0, "Không có authorization Bumx nào được nhập. Dừng tool.")
        sys.exit(1)
    
    bumx_switch_threshold = int(input(Fore.LIGHTCYAN_EX + 'Sau bao nhiêu nhiệm vụ thì đổi tài khoản Bumx: '))
    
    bumx_session = requests.Session()

    # === MULTI FACEBOOK ACCOUNT INPUT ===
    num_cookies = int(input(Fore.LIGHTCYAN_EX + 'Nhập số lượng cookie Facebook muốn chạy: '))
    cookies_list = []
    for i in range(num_cookies):
        cookie_file = f'tdk-cookie-fb-bumx-{i+1}.txt'
        cookie = ''
        if os.path.exists(cookie_file):
            x = input(Fore.LIGHTCYAN_EX + f'Bạn có muốn dùng lại cookie FB đã lưu trong file {cookie_file} không (y/n): ').lower()
            if x == 'y':
                with open(cookie_file, 'r', encoding='utf-8') as f:
                    cookie = f.read().strip()
            else:
                cookie = input(Fore.LIGHTCYAN_EX + f'Nhập cookie FB thứ {i+1} của Bạn: ').strip()
                with open(cookie_file, 'w', encoding='utf-8') as f:
                    f.write(cookie)
                prints(5, 255, 0, f'Đã lưu cookie vào {cookie_file}')
        else:
            cookie = input(Fore.LIGHTCYAN_EX + f'Nhập cookie FB thứ {i+1} của Bạn: ').strip()
            with open(cookie_file, 'w', encoding='utf-8') as f:
                f.write(cookie)
            prints(5, 255, 0, f'Đã lưu cookie vào {cookie_file}')
        if cookie:
            cookies_list.append(cookie)

    if not cookies_list:
        prints(255,0,0, "Không có cookie nào được nhập. Dừng tool.")
        sys.exit(1)

    fb_switch_threshold = int(input(Fore.LIGHTCYAN_EX + 'Sau bao nhiêu nhiệm vụ thì đổi cookie FB: '))

    list_type_job=[]
    prints(66, 245, 245, '''
Các loại nhiệm vụ:
 1. Thả cảm xúc bài viết
Nhập 1 NV cần làm : ''',end='')
    
    x=input()
    job_map = {'1': 'like_facebook', '2': 'like_poster', '3': 'review_facebook'}
    for i in x:
        job_type = job_map.get(i)
        if job_type:
            list_type_job.append(job_type)
        else:
            prints(255,0,0,f'Lựa chọn "{i}" không hợp lệ. Vui lòng chạy lại tool và nhập lại!')
            sys.exit(1)

    SO_NV=int(input('Làm bao nhiêu NV thì dừng: '))
    SO_NV1=SO_NV
    total_completed_tasks=0
    demsk=0
    
    delay1=int(input('Nhập delay tối thiểu khi làm job (giây): '))
    delay2=int(input('Nhập delay tối đa khi làm job (giây): '))

    current_cookie_index = 0
    tasks_on_current_cookie = 0
    valid_cookies = []

    current_auth_index = 0
    tasks_on_current_auth = 0
    authorization = authorizations_list[current_auth_index]
    prints(5,255,0,f'Bắt đầu với tài khoản Bumx-1. Số dư: {wallet(authorization)}')
    
    current_proxy = proxy_rotator.current() if proxy_rotator else None

    if current_proxy and not check_proxy_fast(current_proxy):
        prints(255,255,0,'❌ Proxy ban đầu bị lỗi, đang tìm proxy khác...')
        current_proxy = rotate_proxy()

    if current_proxy:
        proxy_ip = get_proxy_info(current_proxy)
        prints(0,255,255,f'🔗 Đang sử dụng proxy để kiểm tra cookie: {current_proxy}')
        prints(0,255,255,f'🌐 IP public: {proxy_ip}')
    else:
        prints(255,255,0,'⚠️  Không sử dụng proxy')
    
    for ck in cookies_list:
        info = facebook_info(ck, current_proxy)
        if info and info.get('success'):
            valid_cookies.append(ck)
        else:
            prints(255, 165, 0, f"Cookie ...{ck[-20:]} không hợp lệ, sẽ được bỏ qua.")
    
    if not valid_cookies:
        prints(255,0,0,"Không có cookie nào hợp lệ. Vui lòng kiểm tra lại.")
        sys.exit(1)
        
    data = switch_facebook_account(valid_cookies[current_cookie_index], authorization, bumx_session, current_proxy)
    if not data:
        prints(255,0,0,"Cookie đầu tiên không hợp lệ. Không thể bắt đầu.")
        sys.exit(1)

    clear_screen()
    banner()

    force_fb_switch = False
    while total_completed_tasks < SO_NV1:
        try:
            if current_proxy and not check_proxy_fast(current_proxy):
                prints(255,255,0,'❌ Proxy hiện tại chết, đang xoay sang proxy khác...')
                current_proxy = rotate_proxy()
                if current_proxy:
                    proxy_ip = get_proxy_info(current_proxy)
                    prints(0,255,255,f'✅ Đã chuyển sang proxy mới: {current_proxy}')
                    prints(0,255,255,f'🌐 IP public: {proxy_ip}')
                else:
                    prints(255,0,0,'❌ Không còn proxy live, tiếp tục không proxy.')
                    current_proxy = None
            
            # === BUMX ACCOUNT SWITCHING LOGIC ===
            if tasks_on_current_auth >= bumx_switch_threshold and len(authorizations_list) > 1:
                current_auth_index = (current_auth_index + 1) % len(authorizations_list)
                authorization = authorizations_list[current_auth_index]
                tasks_on_current_auth = 0
                prints(0, 255, 255, f"\n--- Chuyển đổi sang tài khoản Bumx thứ {current_auth_index + 1} ---")
                prints(5,255,0,f'Số dư tài khoản mới: {wallet(authorization)}')
                add_account_fb(bumx_session, authorization, data['user_id'])
            
            # === FACEBOOK ACCOUNT SWITCHING LOGIC ===
            if (tasks_on_current_cookie >= fb_switch_threshold and len(valid_cookies) > 1) or force_fb_switch:
                current_cookie_index = (current_cookie_index + 1) % len(valid_cookies)
                new_data = switch_facebook_account(valid_cookies[current_cookie_index], authorization, bumx_session, current_proxy)
                
                force_fb_switch = False # Reset flag
                
                if new_data:
                    data = new_data
                    tasks_on_current_cookie = 0
                else:
                    prints(255, 0, 0, f"Lỗi với cookie thứ {current_cookie_index+1}, loại bỏ khỏi danh sách chạy.")
                    valid_cookies.pop(current_cookie_index)
                    if not valid_cookies:
                        prints(255,0,0,"Tất cả cookie đều lỗi. Dừng tool.")
                        break
                    current_cookie_index = current_cookie_index % len(valid_cookies) # Recalculate index
                    data = switch_facebook_account(valid_cookies[current_cookie_index], authorization, bumx_session, current_proxy)
                    tasks_on_current_cookie = 0
            
            if not list_type_job:
                prints(5,255,0,'Đã hết loại nhiệm vụ để làm.')
                break

            # === JOB FETCHING AND PROCESSING LOGIC ===
            for type_job in list_type_job:
                if total_completed_tasks >= SO_NV1: break
                
                reload(bumx_session, authorization, type_job)
                time.sleep(4)
                all_available_jobs = get_job(bumx_session, authorization)
                
                # Filter jobs for the current type
                jobs_for_current_type = [job for job in all_available_jobs if job['type'] == type_job]
                
                if not jobs_for_current_type:
                    prints(255,255,0,f'Không tìm thấy NV loại {type_job}, chuyển loại tiếp theo.')
                    time.sleep(5)
                    continue

                for job in jobs_for_current_type:
                    if total_completed_tasks >= SO_NV1: break
                    if force_fb_switch: break # Exit inner loop to switch account

                    try:
                        res_load = load(bumx_session, authorization, job)
                        time.sleep(random.randint(2, 4))
                        
                        if not (res_load and res_load.get('success')):
                            raise Exception("Load nhiệm vụ thất bại")
                        
                        delay = random.randint(delay1, delay2)
                        start_job_time = time.time()
                        
                        # Perform the Facebook action and verification
                        job_result = lam_job(data, res_load, job['type'], current_proxy)
                        
                        if job_result['success']:
                            res_submit = submit(bumx_session, authorization, job, job_result['payload'], res_load)
                            if res_submit[0]:
                                total_completed_tasks += 1
                                tasks_on_current_cookie += 1
                                tasks_on_current_auth += 1
                                print_state('complete', res_submit[1], res_submit[2], total_completed_tasks, SO_NV1, job['type'], data['name'], current_auth_index + 1)
                                
                                # Accurate delay calculation
                                elapsed_time = time.time() - start_job_time
                                countdown(delay - elapsed_time)
                            else:
                                raise Exception("Submit nhiệm vụ thất bại")
                        else:
                            # This block handles both action failure and verification failure
                            prints(255, 165, 0, f"Hành động FB thất bại hoặc xác minh không thành công. Báo lỗi NV.")
                            report(bumx_session, authorization, job)
                            demsk += 1
                            time.sleep(3)
                            
                            if job_result['verification_failed']:
                                prints(255, 0, 0, "Phát hiện comment bị ẩn. Sẽ đổi cookie FB ở vòng lặp tiếp theo.")
                                force_fb_switch = True
                                break # Exit from the job list loop to trigger the switch

                    except Exception as e:
                        prints(255, 165, 0, f"NV lỗi, báo cáo và bỏ qua: {e}")
                        report(bumx_session, authorization, job)
                        demsk += 1
                        time.sleep(4)
                
                if force_fb_switch: break # Exit from the job type loop as well

        except KeyboardInterrupt:
            prints(255,255,0, "\nĐã dừng bởi người dùng.")
            break
        except Exception as e:
            prints(255,0,0,f'Lỗi vòng lặp chính: {e}')
            time.sleep(10)

    prints(5,255,0,f'\n--- HOÀN THÀNH ---')
    prints(5,255,0,f'Số nhiệm vụ đã hoàn thành: {total_completed_tasks}')
    prints(5,255,0,f'Số nhiệm vụ đã bỏ qua: {demsk}')
    prints(5,255,0,f'Tổng: {demsk+total_completed_tasks}')

if __name__ == "__main__":
    try:
        
        is_authenticated = main_authentication()

        if is_authenticated:
            print(f"\n{luc}Xác thực thành công. Bắt đầu chạy tool chính...{trang}")
            time.sleep(2)
            main_bumx_free()
        else:
            
            print(f"\n{do}Xác thực không thành công. Dừng chương trình.{trang}")
            sys.exit()

    except Exception as e:

        print(f"\n{do}Tool đang bị lỗi, xin chờ...{trang}")
        
        with open("error_log.txt", "a") as f:
            f.write(f"{datetime.now()}: {str(e)}\n")
        time.sleep(3)
        sys.exit()
